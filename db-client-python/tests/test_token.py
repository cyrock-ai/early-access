"""The token manager's caching, coalescing and failure behaviour.

The counterpart of ``GrpcTokenManagerTest``. Every test here corresponds to a way the Java manager
can wedge, each of which its comments call out; a Python port that only checked "a token comes back"
would pass while reintroducing all of them.
"""

from __future__ import annotations

import threading
from concurrent import futures
from typing import Any

import grpc
import pytest

from conftest import RecordingTokenService
from cyrock_db._token import SAFETY_MARGIN_SECONDS, TokenManager
from cyrock_db.exceptions import (
    ForbiddenException,
    RetryableException,
    UnauthorizedException,
    UnavailableException,
)


def test_token_calledTwice_exchangesOnce(token_server: Any) -> None:
    server  = token_server(token="jwt-1")
    manager = TokenManager(server.channel, "api-key")

    assert manager.token() == "jwt-1"
    assert manager.token() == "jwt-1"
    assert len(server.service.requests) == 1, "the second call must be served from the cache"


def test_token_sendsTheApiKeyHeader(token_server: Any) -> None:
    server = token_server()
    TokenManager(server.channel, "the-secret").token()

    assert ("x-api-key", "the-secret") in server.service.metadata


def test_token_expired_exchangesAgain(token_server: Any) -> None:
    # expires_in below the safety margin means the token is already stale when it arrives.
    server  = token_server(expires_in=int(SAFETY_MARGIN_SECONDS) - 1)
    manager = TokenManager(server.channel, "api-key")

    manager.token()
    manager.token()
    assert len(server.service.requests) == 2


def test_token_concurrentCallersAfterExpiry_shareOneExchange(token_server: Any) -> None:
    """The reason the cache holds the exchange rather than its result.

    A token expires for everybody at once, so this is the realistic shape: many threads arriving
    together, all needing a token none of them has.
    """
    server  = token_server()
    manager = TokenManager(server.channel, "api-key")
    barrier = threading.Barrier(16)

    def fetch() -> str:
        barrier.wait(timeout=10)
        return manager.token()

    with futures.ThreadPoolExecutor(max_workers=16) as pool:
        results = [future.result(timeout=10) for future in [pool.submit(fetch) for _ in range(16)]]

    assert set(results) == {"test-token"}
    assert len(server.service.requests) == 1, (
        f"16 concurrent callers caused {len(server.service.requests)} exchanges; they must share one"
    )


def test_token_failedExchange_isNotCached(token_server: Any) -> None:
    """A cached failure would be replayed for the rest of the token's notional lifetime."""
    server  = token_server(fail_with=grpc.StatusCode.PERMISSION_DENIED, fail_detail="nope")
    manager = TokenManager(server.channel, "api-key")

    # PERMISSION_DENIED projects to its own status (403), not a flat 401 (issue #456).
    with pytest.raises(ForbiddenException):
        manager.token()

    server.service.fail_with = None
    assert manager.token() == "test-token", "a retry after a failure must start a fresh exchange"
    assert len(server.service.requests) == 2


def test_token_emptyToken_isAFailureNotASuccess(token_server: Any) -> None:
    """Caching an OK with no token wedges the client: present, unusable, and never refreshed."""
    server  = token_server(token="")
    manager = TokenManager(server.channel, "api-key")

    with pytest.raises(UnauthorizedException, match="empty token"):
        manager.token()

    server.service.token = "jwt-recovered"
    assert manager.token() == "jwt-recovered"


def test_token_blankToken_isAlsoAFailure(token_server: Any) -> None:
    server = token_server(token="   ")
    with pytest.raises(UnauthorizedException, match="empty token"):
        TokenManager(server.channel, "api-key").token()


def test_token_transportFailure_surfacesWithItsOwnStatus(token_server: Any) -> None:
    """A server that is merely down must reach the caller as the retryable failure it is (issue #456).

    The exchange projects its status the way ``from_rpc_error`` does, so UNAVAILABLE arrives as a
    retryable ``UnavailableException`` (503) rather than a flat 401 that reads as a bad credential and
    a caller catching ``RetryableException`` never retries.
    """
    server = token_server(fail_with=grpc.StatusCode.UNAVAILABLE, fail_detail="server down")
    with pytest.raises(UnavailableException, match="server down") as raised:
        TokenManager(server.channel, "api-key").token()
    assert raised.value.status_code == 503
    assert isinstance(raised.value, RetryableException)


def test_token_deadChannel_failsRatherThanHanging(token_server: Any) -> None:
    """Starting the call can fail before any response, with the exchange already cached."""
    server  = token_server()
    manager = TokenManager(server.channel, "api-key")
    server.channel.close()

    with pytest.raises(UnauthorizedException):
        manager.token()


def test_invalidate_dropsTheCachedToken(token_server: Any) -> None:
    server  = token_server()
    manager = TokenManager(server.channel, "api-key")

    manager.token()
    manager.invalidate()
    manager.token()

    assert len(server.service.requests) == 2


def test_recordingTokenService_isAServicer() -> None:
    """Guards the fixture itself: a servicer that does not subclass is silently never called."""
    from cyrock_db._proto import cyrock_db_platform_pb2_grpc as platform_grpc

    assert issubclass(RecordingTokenService, platform_grpc.TokenGrpcServiceServicer)
