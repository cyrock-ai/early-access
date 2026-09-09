"""Change Data Capture: the cursor, the reconnect, and the discontinuity contract.

The call itself is one server-streaming RPC and is the least interesting part. What these test is
the behaviour around it, because each rule exists to prevent a specific way of being quietly wrong:
a cursor that does not advance replays forever, one that advances too eagerly loses events, and a
consumer not told about a discontinuity reads on with a hole in its state.
"""

from __future__ import annotations

import asyncio
import threading
from typing import Any

import grpc
import pytest

from conftest import change_event
from cyrock_db import CyrockDbClient
from cyrock_db._watch import PERMANENT_FAILURES
from cyrock_db.aio import AsyncCyrockDbClient
from cyrock_db.exceptions import ForbiddenException
from cyrock_db.types import ChangeEvent, ChangeFilter, ChangeOp, EntityKind, WatchOptions, WatchStart

GRAPH      = "graph-1"
COLLECTION = "collection-1"


def _client(server: Any) -> CyrockDbClient:
    return CyrockDbClient(host="127.0.0.1", port=server.port, api_key="api-key")


class Collector:
    """A listener that records everything, and lets a test wait for a count without sleeping."""

    def __init__(self) -> None:
        self.events:         list[ChangeEvent]     = []
        self.discontinuities: list[ChangeEvent]    = []
        self.snapshots:      int                   = 0
        self.errors:         list[BaseException]   = []
        self._arrived = threading.Condition()

    def on_change(self, event: ChangeEvent) -> None:
        with self._arrived:
            self.events.append(event)
            self._arrived.notify_all()

    def on_discontinuity(self, event: ChangeEvent) -> None:
        self.discontinuities.append(event)

    def on_snapshot_complete(self) -> None:
        with self._arrived:
            self.snapshots += 1
            self._arrived.notify_all()

    def on_error(self, error: BaseException) -> None:
        with self._arrived:
            self.errors.append(error)
            self._arrived.notify_all()

    def wait_for(self, count: int, timeout: float = 5.0) -> None:
        with self._arrived:
            assert self._arrived.wait_for(
                lambda: len(self.events) >= count or self.errors, timeout=timeout
            ), f"only {len(self.events)} events arrived, wanted {count}"

    def wait_for_error(self, timeout: float = 5.0) -> BaseException:
        with self._arrived:
            assert self._arrived.wait_for(lambda: bool(self.errors), timeout=timeout), "no error arrived"
        return self.errors[0]


# ─── Delivery ──────────────────────────────────────────────────────────────


def test_watchGraph_deliversEventsAndTracksTheCursor(token_server: Any) -> None:
    server    = token_server(cdc={"batches": [[change_event(10), change_event(11)]]})
    collector = Collector()

    with _client(server) as client, client.watch_graph(GRAPH, WatchOptions.from_now(), collector) as sub:
        collector.wait_for(2)

        assert [each.lsn for each in collector.events] == [10, 11]
        assert collector.events[0].op is ChangeOp.CREATE
        assert collector.events[0].entity_kind is EntityKind.NODE
        assert sub.last_lsn == 11, "the cursor is what a consumer checkpoints"


def test_aPlainCallable_isAcceptedAsAListener(token_server: Any) -> None:
    """The common case should not need a class."""
    server   = token_server(cdc={"batches": [[change_event(1)]]})
    received: list[ChangeEvent] = []
    done     = threading.Event()

    def on_event(event: ChangeEvent) -> None:
        received.append(event)
        done.set()

    with _client(server) as client, client.watch_graph(GRAPH, WatchOptions.from_now(), on_event):
        assert done.wait(5.0)
    assert received[0].lsn == 1


def test_snapshotComplete_isAMarker_andAdvancesTheCursor(token_server: Any) -> None:
    """The marker is a real record at a real LSN, unlike the snapshot rows before it."""
    server    = token_server(cdc={"batches": [[
        change_event(0, op="SNAPSHOT", entity_id=1),
        change_event(0, op="SNAPSHOT", entity_id=2),
        change_event(7, snapshot_complete=True),
        change_event(8),
    ]]})
    collector = Collector()

    with _client(server) as client, client.watch_graph(
        GRAPH, WatchOptions.with_snapshot(), collector
    ) as sub:
        collector.wait_for(3)

    assert collector.snapshots == 1
    assert sub.last_lsn == 8
    assert [each.op for each in collector.events][:2] == [ChangeOp.SNAPSHOT, ChangeOp.SNAPSHOT]


def test_snapshotRows_doNotMoveTheCursor(token_server: Any) -> None:
    """Snapshot rows are current state, not log positions; resuming from one would skip the log."""
    server    = token_server(cdc={"batches": [[change_event(99, op="SNAPSHOT")]]})
    collector = Collector()

    with _client(server) as client, client.watch_graph(
        GRAPH, WatchOptions.with_snapshot(), collector
    ) as sub:
        collector.wait_for(1)
        assert sub.last_lsn == -1, "a snapshot row must not be mistaken for a log position"


# ─── Discontinuity ─────────────────────────────────────────────────────────


def test_aDiscontinuity_isReportedTwice_andAdvancesThePastIt(token_server: Any) -> None:
    """It reaches on_discontinuity *and* on_change, and the cursor moves past it.

    Not advancing would have every reconnect receive the same marker forever; what is lost is lost,
    and resuming from before it cannot bring the changes back.
    """
    server    = token_server(cdc={"batches": [[change_event(50, op="DISCONTINUITY")]]})
    collector = Collector()

    with _client(server) as client, client.watch_graph(
        GRAPH, WatchOptions.from_now(), collector
    ) as sub:
        collector.wait_for(1)

    assert len(collector.discontinuities) == 1
    assert collector.discontinuities[0].op is ChangeOp.DISCONTINUITY
    assert collector.events[-1].op is ChangeOp.DISCONTINUITY, "it is delivered as a change too"
    assert sub.last_lsn == 50


# ─── Reconnection ──────────────────────────────────────────────────────────


def test_aTransientFailure_reconnects_resumingFromTheLastLsn(token_server: Any) -> None:
    """The reconnect must resume from where delivery got to, not from where the caller started."""
    server = token_server(cdc={"batches": [
        [change_event(10)],
        grpc.StatusCode.UNAVAILABLE,
        [change_event(11)],
    ]})
    collector = Collector()

    with _client(server) as client, client.watch_graph(GRAPH, WatchOptions.from_now(), collector):
        collector.wait_for(2, timeout=15.0)

    assert [each.lsn for each in collector.events] == [10, 11]
    resumed = server.cdc.requests[-1]
    assert resumed.HasField("from_lsn") and resumed.from_lsn == 10, (
        "the reconnect resumed from the last delivered LSN"
    )


def test_theFirstRequest_carriesTheCallersStartPosition(token_server: Any) -> None:
    server = token_server(cdc={"batches": [[]]})
    with _client(server) as client, client.watch_graph(GRAPH, WatchOptions.with_snapshot(), Collector()):
        _wait_for_request(server)

    first = server.cdc.requests[0]
    assert first.HasField("with_snapshot") and first.with_snapshot is True


def test_resumeFrom_sendsThatLsn(token_server: Any) -> None:
    server = token_server(cdc={"batches": [[]]})
    with _client(server) as client, client.watch_graph(GRAPH, WatchOptions.resume_from(42), Collector()):
        _wait_for_request(server)

    assert server.cdc.requests[0].from_lsn == 42


@pytest.mark.parametrize("code", sorted(PERMANENT_FAILURES, key=str))
def test_aPermanentFailure_stopsAndSurfaces(token_server: Any, code: grpc.StatusCode) -> None:
    """These fail identically forever; retrying would just hide the reason."""
    server    = token_server(cdc={"batches": [code]})
    collector = Collector()

    with _client(server) as client:
        subscription = client.watch_graph(GRAPH, WatchOptions.from_now(), collector)
        collector.wait_for_error()

        assert subscription.closed is True
        assert server.cdc.connections == 1, "a permanent failure must not be retried"


def test_aPermanentFailure_arrivesAsTheMatchingException(token_server: Any) -> None:
    server    = token_server(cdc={"batches": [grpc.StatusCode.PERMISSION_DENIED]})
    collector = Collector()

    with _client(server) as client:
        client.watch_graph(GRAPH, WatchOptions.from_now(), collector)
        assert isinstance(collector.wait_for_error(), ForbiddenException)


def test_unauthenticated_isRetryable_becauseAReconnectFetchesAFreshToken() -> None:
    """The one status that looks permanent and is not."""
    assert grpc.StatusCode.UNAUTHENTICATED not in PERMANENT_FAILURES
    assert grpc.StatusCode.PERMISSION_DENIED in PERMANENT_FAILURES


def test_watchingABranch_isRefusedPermanently(token_server: Any) -> None:
    """A branch is an overlay with no retained log, so the server answers FAILED_PRECONDITION."""
    server    = token_server(cdc={"batches": [grpc.StatusCode.FAILED_PRECONDITION]})
    collector = Collector()

    with _client(server) as client:
        client.watch_graph("branch-0", WatchOptions.from_now(), collector)
        collector.wait_for_error()

    assert server.cdc.connections == 1


# ─── Options and filters ───────────────────────────────────────────────────


def test_theFilter_isEncodedInFull(token_server: Any) -> None:
    server  = token_server(cdc={"batches": [[]]})
    options = WatchOptions(
        start=WatchStart.FROM_NOW,
        include_vectors=True,
        filter=ChangeFilter(
            ops=[ChangeOp.CREATE, ChangeOp.DELETE],
            entity_kinds=[EntityKind.NODE],
            labels=["Concept"],
            metadata_predicate="rank > 1",
        ),
    )
    with _client(server) as client, client.watch_graph(GRAPH, options, Collector()):
        _wait_for_request(server)

    sent = server.cdc.requests[0]
    assert sent.include_vectors is True
    assert list(sent.filter.labels) == ["Concept"]
    assert sent.filter.metadata_predicate == "rank > 1"
    assert len(sent.filter.ops) == 2 and len(sent.filter.entity_kinds) == 1


def test_watchCollection_sendsTheCollectionResourceKind(token_server: Any) -> None:
    from cyrock_db._proto import cyrock_db_cdc_pb2 as cdc_pb2

    server = token_server(cdc={"batches": [[]]})
    with _client(server) as client, client.watch_collection(
        COLLECTION, WatchOptions.from_now(), Collector()
    ):
        _wait_for_request(server)

    assert server.cdc.requests[0].resource_kind == cdc_pb2.ResourceKind.COLLECTION
    assert server.cdc.requests[0].resource_id == COLLECTION


def test_watchOptions_negativeResumeLsn_isRejected() -> None:
    with pytest.raises(ValueError, match="from_lsn must not be negative"):
        WatchOptions.resume_from(-1)


def test_close_isIdempotent(token_server: Any) -> None:
    server = token_server(cdc={"batches": [[]]})
    with _client(server) as client:
        subscription = client.watch_graph(GRAPH, WatchOptions.from_now(), Collector())
        subscription.close()
        subscription.close()
        assert subscription.closed is True


# ─── The asyncio form ──────────────────────────────────────────────────────


def test_theAsyncClient_yieldsEventsAsAnIterator(token_server: Any) -> None:
    server = token_server(cdc={"batches": [[change_event(1), change_event(2)]]})

    async def collect() -> list[int]:
        async with AsyncCyrockDbClient(host="127.0.0.1", port=server.port, api_key="api-key") as client:
            return [
                event.lsn
                async for event in await client.watch_graph(GRAPH, WatchOptions.from_now())
            ]

    assert asyncio.run(collect()) == [1, 2]


def test_theAsyncIterator_decodesTheSameEventsAsTheListener(token_server: Any) -> None:
    server    = token_server(cdc={"batches": [[change_event(5, labels=("A",))]] * 2})
    collector = Collector()

    with _client(server) as client, client.watch_graph(GRAPH, WatchOptions.from_now(), collector):
        collector.wait_for(1)

    async def collect() -> list[ChangeEvent]:
        async with AsyncCyrockDbClient(host="127.0.0.1", port=server.port, api_key="api-key") as client:
            return [e async for e in await client.watch_graph(GRAPH, WatchOptions.from_now())]

    assert asyncio.run(collect())[0] == collector.events[0]


def _wait_for_request(server: Any, timeout: float = 5.0) -> None:
    """Waits until the stream has actually opened, so an assertion is not racing the thread."""
    deadline = threading.Event()
    for _ in range(int(timeout * 100)):
        if server.cdc.requests:
            return
        deadline.wait(0.01)
    raise AssertionError("the change stream never opened")
