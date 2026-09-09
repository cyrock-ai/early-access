"""Change stream subscriptions.

A port of ``ChangeStreamSubscription``. The interesting behaviour is not the call - it is one
server-streaming RPC - but what happens around it, and every rule below is one the Java version
arrived at for a reason worth keeping.

**Reconnection.** A transient failure reconnects with exponential backoff, 1s doubling to 60s,
resuming from the last delivered LSN. The backoff resets on any received event, so a stream that
flaps does not inherit a minute-long delay from an outage an hour ago. Because a fresh token is
fetched on each connect, this also survives token expiry over a long-lived stream - which is why
``UNAUTHENTICATED`` is treated as retryable rather than fatal.

**Permanent failures stop.** ``PERMISSION_DENIED``, ``FAILED_PRECONDITION``, ``INVALID_ARGUMENT``,
``UNIMPLEMENTED`` and ``NOT_FOUND`` are not worth retrying: they will fail identically forever.
``FAILED_PRECONDITION`` is the one to expect in practice - watching a branch returns it, branches
being overlays with no change log of their own.

**The cursor advances past a discontinuity, deliberately.** A ``DISCONTINUITY`` marker is a real
record at a real LSN, and not advancing past it would have every reconnect receive it again forever.
What is lost is lost: resuming from before it cannot bring the changes back. The consumer is told,
and must re-snapshot.

**Snapshot events do not advance the cursor**, because they are not log positions; the
``snapshot_complete`` marker does, because it is.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable, Iterator
from types import TracebackType
from typing import Any, Protocol

import grpc

from . import _proto_converters as converters
from ._proto import cyrock_db_cdc_pb2 as cdc_pb2
from ._proto import cyrock_db_cdc_pb2_grpc as cdc_grpc
from .exceptions import from_rpc_error
from .types import ChangeEvent, ChangeOp, WatchOptions, WatchStart

__all__ = ["ChangeListener", "ChangeStreamSubscription", "watch_request"]

LOG = logging.getLogger(__name__)

INITIAL_BACKOFF_SECONDS = 1.0
MAX_BACKOFF_SECONDS     = 60.0

# Failures that will fail the same way on every retry. UNAUTHENTICATED is deliberately absent: a
# reconnect fetches a fresh token, so an expired one recovers by itself.
PERMANENT_FAILURES = frozenset({
    grpc.StatusCode.PERMISSION_DENIED,
    grpc.StatusCode.FAILED_PRECONDITION,
    grpc.StatusCode.INVALID_ARGUMENT,
    grpc.StatusCode.UNIMPLEMENTED,
    grpc.StatusCode.NOT_FOUND,
})


class ChangeListener(Protocol):
    """What a subscriber implements. Only :meth:`on_change` is required.

    A plain callable taking one :class:`~cyrock_db.types.ChangeEvent` is accepted anywhere a listener
    is, which covers the common case without a class.
    """

    def on_change(self, event: ChangeEvent) -> None:
        """Called for every event, including a discontinuity marker."""

    def on_discontinuity(self, event: ChangeEvent) -> None:
        """Called before :meth:`on_change` when changes have been lost. Optional."""

    def on_snapshot_complete(self) -> None:
        """Called once, after the initial snapshot and before the live tail. Optional."""

    def on_error(self, error: BaseException) -> None:
        """Called once when the stream stops permanently. Optional."""


def watch_request(
    resource_kind: Any, resource_id: str, options: WatchOptions, from_lsn: int
) -> Any:
    """Builds a ``WatchRequest``.

    ``from_lsn`` is passed separately from ``options`` because a reconnect resumes from the last
    delivered LSN rather than from wherever the caller originally asked to start - the options say
    where the *subscription* began, not where this particular connection should.
    """
    request = cdc_pb2.WatchRequest(
        resource_kind   = resource_kind,
        resource_id     = resource_id,
        include_vectors = options.include_vectors,
    )
    if from_lsn >= 0:
        request.from_lsn = from_lsn
    elif options.start is WatchStart.WITH_SNAPSHOT:
        request.with_snapshot = True
    elif options.start is WatchStart.FROM_LSN:
        request.from_lsn = options.from_lsn
    else:
        request.from_now = True

    change_filter = options.filter
    if change_filter.ops:
        request.filter.ops.extend(cdc_pb2.ChangeOp.Value(each.value) for each in change_filter.ops)
    if change_filter.entity_kinds:
        request.filter.entity_kinds.extend(
            cdc_pb2.EntityKind.Value(each.value) for each in change_filter.entity_kinds
        )
    if change_filter.labels:
        request.filter.labels.extend(change_filter.labels)
    if change_filter.metadata_predicate:
        request.filter.metadata_predicate = change_filter.metadata_predicate
    return request


class ChangeStreamSubscription:
    """A running change stream. Close it to stop, or use it as a context manager.

    The stream runs on its own daemon thread, so a caller that forgets to close one does not keep the
    process alive. Callbacks run on that thread: keep them short, or hand off to your own queue.
    """

    def __init__(
        self,
        stub:          Any,
        resource_kind: Any,
        resource_id:   str,
        options:       WatchOptions,
        listener:      ChangeListener | Callable[[ChangeEvent], None],
    ) -> None:
        self._stub          = stub
        self._resource_kind = resource_kind
        self._resource_id   = resource_id
        self._options       = options
        self._listener      = listener
        self._closed        = threading.Event()
        self._last_lsn      = -1
        self._backoff       = INITIAL_BACKOFF_SECONDS
        self._call: Any     = None
        self._thread        = threading.Thread(
            target=self._run, name=f"cdc-watch-{resource_id}", daemon=True
        )
        self._thread.start()

    # ─── Lifecycle ──────────────────────────────────────────────────────────

    @property
    def last_lsn(self) -> int:
        """The last LSN delivered, or -1 before the first event. The value to checkpoint."""
        return self._last_lsn

    @property
    def closed(self) -> bool:
        return self._closed.is_set()

    def close(self) -> None:
        """Stops the stream. Idempotent, and safe to call from a listener callback."""
        self._closed.set()
        call = self._call
        if call is not None:
            call.cancel()

    def __enter__(self) -> ChangeStreamSubscription:
        return self

    def __exit__(
        self,
        exc_type:  type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    # ─── Internals ──────────────────────────────────────────────────────────

    def _run(self) -> None:
        while not self._closed.is_set():
            try:
                self._consume()
            except grpc.RpcError as error:
                if self._closed.is_set():
                    return
                code = error.code() if callable(getattr(error, "code", None)) else None
                if code in PERMANENT_FAILURES:
                    LOG.warning(
                        "Change stream for %s failed permanently: %s", self._resource_id, error
                    )
                    self._closed.set()
                    self._notify_error(from_rpc_error(error))
                    return
                LOG.warning(
                    "Change stream for %s failed, reconnecting: %s", self._resource_id, error
                )
            except Exception as error:  # noqa: BLE001 - a listener that raises must not kill the thread
                LOG.exception("Change stream listener for %s raised", self._resource_id)
                if self._closed.is_set():
                    return
                self._notify_error(error)
                return

            # The server ending the stream cleanly is treated as a disconnect too: the caller asked
            # to keep watching, so reconnect rather than stop silently.
            if self._closed.wait(self._next_backoff()):
                return

    def _next_backoff(self) -> float:
        delay = self._backoff
        self._backoff = min(self._backoff * 2, MAX_BACKOFF_SECONDS)
        return delay

    def _consume(self) -> None:
        request   = watch_request(self._resource_kind, self._resource_id, self._options, self._last_lsn)
        self._call = self._stub.WatchChanges(request)
        for message in self._call:
            if self._closed.is_set():
                return
            # Any delivered event means the connection works, so a later outage starts its backoff
            # from the beginning rather than inheriting a delay from an unrelated one.
            self._backoff = INITIAL_BACKOFF_SECONDS
            self._deliver(converters.to_change_event(message))

    def _deliver(self, event: ChangeEvent) -> None:
        if event.snapshot_complete:
            # A real record at a real LSN, so the cursor advances even though it is a marker.
            self._last_lsn = max(self._last_lsn, event.source.lsn)
            self._call_listener("on_snapshot_complete")
            return

        if event.op is not ChangeOp.SNAPSHOT:
            # Snapshot rows are current state, not log positions, so they do not move the cursor.
            self._last_lsn = event.source.lsn

        if event.op is ChangeOp.DISCONTINUITY:
            LOG.warning(
                "Change stream for %s has a discontinuity at LSN %s: changes before it were committed "
                "but never logged, so this consumer's state is stale until it re-snapshots",
                self._resource_id, event.source.lsn,
            )
            self._call_listener("on_discontinuity", event)

        self._call_listener("on_change", event)

    def _call_listener(self, name: str, *args: Any) -> None:
        """Invokes an optional listener method, tolerating a plain callable and missing hooks."""
        if name == "on_change" and callable(self._listener) and not hasattr(self._listener, "on_change"):
            self._listener(*args)
            return
        hook = getattr(self._listener, name, None)
        if hook is not None:
            hook(*args)

    def _notify_error(self, error: BaseException) -> None:
        hook = getattr(self._listener, "on_error", None)
        if hook is not None:
            hook(error)


def iter_changes(
    stub: Any, resource_kind: Any, resource_id: str, options: WatchOptions
) -> Iterator[ChangeEvent]:
    """A single-pass iterator over a change stream, with no reconnection.

    Used by the asynchronous client's iterator form, and available where a caller wants the raw
    stream. The reconnect, backoff and cursor behaviour lives in
    :class:`ChangeStreamSubscription`; this is deliberately the plain version.
    """
    for message in stub.WatchChanges(watch_request(resource_kind, resource_id, options, -1)):
        yield converters.to_change_event(message)


CDC_STUB = cdc_grpc.ChangeStreamGrpcServiceStub
