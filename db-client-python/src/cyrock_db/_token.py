"""Exchanges an API key for a short-lived JWT, and keeps it fresh.

A port of ``client-java``'s ``GrpcTokenManager``, including the parts that are not obvious.

**Refreshes are coalesced.** The cache holds the exchange itself rather than its result, so the
first caller to find the token missing or expired starts one exchange and everyone arriving while it
is in flight waits on that same one. This matters because a token expires for everybody at once: fan
out a few hundred calls just after expiry and the naive alternative - a lock held across the exchange
RPC - queues every one of them behind a round trip it could have shared.

**A failed exchange is not cached.** It is evicted *before* the waiting callers are failed, so the
next call starts a fresh exchange rather than replaying the failure for the rest of the token's
notional lifetime. An exchange in flight is never stale, so an entry left in place after failing
would be handed to every later caller for the life of the process. That is the one failure here that
is unrecoverable rather than merely wrong, which is why every failure path routes through
:meth:`_fail`.

This class is thread-safe.
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from concurrent.futures import Future

import grpc

from ._auth import API_KEY_HEADER
from ._proto import cyrock_db_platform_pb2 as platform_pb2
from ._proto import cyrock_db_platform_pb2_grpc as platform_grpc
from .exceptions import CyrockDbClientException, UnauthorizedException, from_rpc_error

__all__ = ["AsyncTokenManager", "TokenManager"]

LOG = logging.getLogger(__name__)

# Refresh this long before the server's stated expiry, so a token is never used on its last legs.
SAFETY_MARGIN_SECONDS = 30.0


class _Exchange:
    """One token exchange, cached in place of its result so concurrent callers share it.

    ``expires_at`` starts at infinity and is set to the real expiry when the response lands, which is
    what makes an in-flight exchange never stale: a caller arriving mid-exchange joins it rather than
    starting a second one.
    """

    __slots__ = ("expires_at", "token")

    def __init__(self) -> None:
        self.token: Future[str] = Future()
        self.expires_at: float  = float("inf")

    def is_stale(self) -> bool:
        return time.monotonic() >= self.expires_at


class _AsyncExchange:
    """One token exchange for the asyncio manager. See :class:`_Exchange`."""

    __slots__ = ("expires_at", "token")

    def __init__(self) -> None:
        # get_running_loop, not get_event_loop: this is only ever constructed from inside a
        # coroutine, and get_event_loop is deprecated when called with no loop running - it would
        # start warning, and eventually fail, on a client constructed outside one.
        self.token: asyncio.Future[str] = asyncio.get_running_loop().create_future()
        self.expires_at: float          = float("inf")

    def is_stale(self) -> bool:
        return time.monotonic() >= self.expires_at


class TokenManager:
    """Holds the current JWT, exchanging a new one when there is none or it is about to expire."""

    def __init__(self, channel: grpc.Channel, api_key: str) -> None:
        # grpcio-tools generates .pyi stubs for the _pb2 messages but not for the _pb2_grpc
        # service stubs, so every generated stub constructor is untyped as far as --strict is
        # concerned. Ignored at each construction site rather than by relaxing the setting for the
        # whole module, so real untyped calls in our own code still fail.
        self._stub     = platform_grpc.TokenGrpcServiceStub(channel)  # type: ignore[no-untyped-call]
        self._api_key  = api_key
        self._lock     = threading.Lock()
        self._current: _Exchange | None = None

    def token(self) -> str:
        """The cached token, exchanging a new one if there is none or it is about to expire.

        :raises CyrockDbClientException: if the exchange fails. A transport failure keeps its own status -
            an :class:`UnavailableException` or :class:`DeadlineExceededException` a caller can retry - while
            an empty or missing token stays an :class:`UnauthorizedException` (issue #456).
        """
        exchange, is_leader = self._claim()
        if is_leader:
            self._exchange(exchange)
        # Whether we ran the exchange or joined one, the result arrives the same way. Waiting outside
        # the lock is the point: a follower blocks on the future, not on the mutex.
        return exchange.token.result()

    def invalidate(self) -> None:
        """Drops the cached token, so the next call exchanges a fresh one."""
        with self._lock:
            self._current = None

    def _claim(self) -> tuple[_Exchange, bool]:
        """Returns the exchange to wait on, and whether this caller must run it.

        The lock covers only the decision, never the RPC. Holding it across the round trip is exactly
        the queue this design exists to avoid.
        """
        with self._lock:
            current = self._current
            if current is not None and not current.is_stale():
                return current, False
            started = _Exchange()
            self._current = started
            return started, True

    def _exchange(self, exchange: _Exchange) -> None:
        try:
            response = self._stub.Exchange(
                platform_pb2.Empty(), metadata=((API_KEY_HEADER, self._api_key),)
            )
        except grpc.RpcError as error:
            # Starting or completing the call failed. Project the transport status the way from_rpc_error
            # does, so an UNAVAILABLE or DEADLINE_EXCEEDED reaches the caller as the retryable exception it
            # is rather than a flat 401 that reads as a bad credential and is never retried (issue #456).
            # Without evicting, this entry - never stale, because it never got an expiry - would be served
            # to every later caller forever.
            self._fail(exchange, from_rpc_error(error))
            return
        except Exception as error:  # noqa: BLE001 - see below
            # A channel in a state that refuses newCall, or an interceptor that throws. Not a transport
            # status, so it stays a 401, matching the Java manager. The entry is already cached by now, so
            # letting this propagate would wedge the manager permanently.
            self._fail(exchange, UnauthorizedException(f"Failed to start token exchange: {error}"))
            return

        if not response.token or not response.token.strip():
            # An OK carrying no token has to be a failed exchange rather than a successful one:
            # caching it would leave every later call failing on a token that is present, unusable,
            # and - being cached and unexpired - never refreshed. The server answered and its answer was
            # unusable, so this stays a 401. A protobuf string field is "" when unset, so this is what an
            # empty response actually looks like.
            self._fail(exchange, UnauthorizedException("Token exchange returned an empty token"))
            return

        exchange.expires_at = time.monotonic() + (response.expires_in - SAFETY_MARGIN_SECONDS)
        LOG.debug("Obtained new JWT token via gRPC, expires in %ss", response.expires_in)
        exchange.token.set_result(response.token)

    def _fail(self, exchange: _Exchange, failure: CyrockDbClientException) -> None:
        """Fails an exchange, evicting it first.

        The order matters: whoever retries after a failure must start a new exchange rather than be
        handed this one's failure again for the rest of the token's notional lifetime.
        """
        with self._lock:
            if self._current is exchange:
                self._current = None
        exchange.token.set_exception(failure)


class AsyncTokenManager:
    """The asyncio counterpart of :class:`TokenManager`.

    Same contract, same failure handling. The claim needs no lock: it reads and replaces
    ``_current`` with no ``await`` between, and asyncio will not interleave another coroutine inside
    that. Where the synchronous version has a follower block on a future, here it awaits one, which
    is the whole reason the asynchronous client exists - a refresh no longer parks a thread per
    waiting caller.
    """

    def __init__(self, channel: grpc.aio.Channel, api_key: str) -> None:
        self._stub    = platform_grpc.TokenGrpcServiceStub(channel)  # type: ignore[no-untyped-call]
        self._api_key = api_key
        self._current: _AsyncExchange | None = None

    async def token(self) -> str:
        """The cached token, exchanging a new one if there is none or it is about to expire.

        :raises CyrockDbClientException: if the exchange fails. A transport failure keeps its own status -
            an :class:`UnavailableException` or :class:`DeadlineExceededException` a caller can retry - while
            an empty or missing token stays an :class:`UnauthorizedException` (issue #456).
        """
        exchange, is_leader = self._claim()
        if is_leader:
            await self._exchange(exchange)
        return await exchange.token

    def invalidate(self) -> None:
        """Drops the cached token, so the next call exchanges a fresh one."""
        self._current = None

    def _claim(self) -> tuple[_AsyncExchange, bool]:
        current = self._current
        if current is not None and not current.is_stale():
            return current, False
        started = _AsyncExchange()
        self._current = started
        return started, True

    async def _exchange(self, exchange: _AsyncExchange) -> None:
        try:
            response = await self._stub.Exchange(
                platform_pb2.Empty(), metadata=((API_KEY_HEADER, self._api_key),)
            )
        except grpc.aio.AioRpcError as error:
            self._fail(exchange, from_rpc_error(error))
            return
        except Exception as error:  # noqa: BLE001 - as in the synchronous manager
            self._fail(exchange, UnauthorizedException(f"Failed to start token exchange: {error}"))
            return

        if not response.token or not response.token.strip():
            self._fail(exchange, UnauthorizedException("Token exchange returned an empty token"))
            return

        exchange.expires_at = time.monotonic() + (response.expires_in - SAFETY_MARGIN_SECONDS)
        LOG.debug("Obtained new JWT token via gRPC, expires in %ss", response.expires_in)
        exchange.token.set_result(response.token)

    def _fail(self, exchange: _AsyncExchange, failure: CyrockDbClientException) -> None:
        """Fails an exchange, evicting it first. See :meth:`TokenManager._fail`."""
        if self._current is exchange:
            self._current = None
        exchange.token.set_exception(failure)
