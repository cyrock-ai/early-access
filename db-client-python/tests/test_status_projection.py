"""Holds the gRPC-to-HTTP projection and the exception mapping to the Java client's.

The counterpart of ``CyrockDbClientGrpcStatusProjectionTest``. The table is asserted value by value
rather than by re-deriving it, because the whole point of issue #361 was that a derived number - the
gRPC wire ordinal - was wrong in the direction nobody notices.
"""

from __future__ import annotations

import grpc
import pytest

from cyrock_db.exceptions import (
    CyrockDbClientException,
    DeadlineExceededException,
    DurabilityNotConfirmedException,
    ForbiddenException,
    NotFoundException,
    RetryableException,
    UnauthorizedException,
    UnavailableException,
    WrongCredentialException,
    from_rpc_error,
    http_status_for,
)

# The canonical projection, as client-java's HttpStatusProjection states it.
EXPECTED_HTTP_STATUS = {
    grpc.StatusCode.OK:                  200,
    grpc.StatusCode.CANCELLED:           499,
    grpc.StatusCode.UNKNOWN:             500,
    grpc.StatusCode.INVALID_ARGUMENT:    400,
    grpc.StatusCode.DEADLINE_EXCEEDED:   504,
    grpc.StatusCode.NOT_FOUND:           404,
    grpc.StatusCode.ALREADY_EXISTS:      409,
    grpc.StatusCode.PERMISSION_DENIED:   403,
    grpc.StatusCode.RESOURCE_EXHAUSTED:  429,
    grpc.StatusCode.FAILED_PRECONDITION: 400,
    grpc.StatusCode.ABORTED:             409,
    grpc.StatusCode.OUT_OF_RANGE:        400,
    grpc.StatusCode.UNIMPLEMENTED:       501,
    grpc.StatusCode.INTERNAL:            500,
    grpc.StatusCode.UNAVAILABLE:         503,
    grpc.StatusCode.DATA_LOSS:           500,
    grpc.StatusCode.UNAUTHENTICATED:     401,
}


@pytest.mark.parametrize(("code", "expected"), list(EXPECTED_HTTP_STATUS.items()))
def test_httpStatusFor_everyStatus_projectsTheCanonicalCode(code: grpc.StatusCode, expected: int) -> None:
    assert http_status_for(code) == expected


def test_httpStatusFor_everyGrpcStatus_isCovered() -> None:
    """A status gRPC adds later must be a deliberate decision, not a silent 500."""
    assert set(EXPECTED_HTTP_STATUS) == set(grpc.StatusCode), (
        "grpc.StatusCode has members the projection table does not name; add them to both."
    )


def test_httpStatusFor_neverReportsTheWireOrdinal() -> None:
    """The regression issue #361 was filed for: INTERNAL as 13 and UNAVAILABLE as 14."""
    assert http_status_for(grpc.StatusCode.INTERNAL)    == 500
    assert http_status_for(grpc.StatusCode.UNAVAILABLE) == 503
    for code in grpc.StatusCode:
        assert http_status_for(code) >= 200, "a projected status is an HTTP code, never an ordinal"


@pytest.mark.parametrize(
    ("code", "expected_type", "expected_status"),
    [
        (grpc.StatusCode.NOT_FOUND,         NotFoundException,         404),
        (grpc.StatusCode.PERMISSION_DENIED, ForbiddenException,        403),
        (grpc.StatusCode.UNAUTHENTICATED,   UnauthorizedException,     401),
        (grpc.StatusCode.UNAVAILABLE,       UnavailableException,      503),
        (grpc.StatusCode.DEADLINE_EXCEEDED, DeadlineExceededException, 504),
    ],
)
def test_fromRpcError_aTypedStatus_raisesItsOwnType(
    token_server: object, code: grpc.StatusCode, expected_type: type, expected_status: int
) -> None:
    server = token_server(fail_with=code, fail_detail="denied by the test")  # type: ignore[operator]
    with pytest.raises(grpc.RpcError) as raised:
        server.token_stub().Exchange(_empty())

    mapped = from_rpc_error(raised.value)
    assert isinstance(mapped, expected_type)
    assert mapped.status_code == expected_status
    assert mapped.message == "denied by the test"


@pytest.mark.parametrize(
    ("code", "expected_status"),
    [
        (grpc.StatusCode.INVALID_ARGUMENT,   400),
        (grpc.StatusCode.RESOURCE_EXHAUSTED, 429),
        (grpc.StatusCode.INTERNAL,           500),
        (grpc.StatusCode.UNIMPLEMENTED,      501),
    ],
)
def test_fromRpcError_anUntypedStatus_keepsTheGenericTypeAndProjectsTheCode(
    token_server: object, code: grpc.StatusCode, expected_status: int
) -> None:
    server = token_server(fail_with=code)  # type: ignore[operator]
    with pytest.raises(grpc.RpcError) as raised:
        server.token_stub().Exchange(_empty())

    mapped = from_rpc_error(raised.value)
    assert type(mapped) is CyrockDbClientException
    assert mapped.status_code == expected_status


def test_fromRpcError_abortedWithTheDurabilityReason_raisesDurabilityNotConfirmed(
    token_server: object,
) -> None:
    server = token_server(attach_durability_reason=True, fail_detail="flush unconfirmed")  # type: ignore[operator]
    with pytest.raises(grpc.RpcError) as raised:
        server.token_stub().Exchange(_empty())

    mapped = from_rpc_error(raised.value)
    assert isinstance(mapped, DurabilityNotConfirmedException)
    assert mapped.status_code == 409


@pytest.mark.parametrize("reason", ["API_KEY_REQUIRED", "BEARER_TOKEN_REQUIRED"])
def test_fromRpcError_unauthenticatedWithACredentialReason_raisesWrongCredential(
    token_server: object, reason: str
) -> None:
    """The right service reached with the wrong credential for it (issue #464)."""
    server = token_server(abort_reason=reason, fail_detail="send the other credential")  # type: ignore[operator]
    with pytest.raises(grpc.RpcError) as raised:
        server.token_stub().Exchange(_empty())

    mapped = from_rpc_error(raised.value)
    assert isinstance(mapped, WrongCredentialException)
    assert isinstance(mapped, UnauthorizedException), "it stays a kind of unauthorized"
    assert mapped.status_code == 401


def test_fromRpcError_plainUnauthenticated_staysGeneric(token_server: object) -> None:
    """Without the reason, UNAUTHENTICATED is a bad credential, not the wrong one for the service."""
    server = token_server(fail_with=grpc.StatusCode.UNAUTHENTICATED)  # type: ignore[operator]
    with pytest.raises(grpc.RpcError) as raised:
        server.token_stub().Exchange(_empty())

    mapped = from_rpc_error(raised.value)
    assert type(mapped) is UnauthorizedException
    assert not isinstance(mapped, WrongCredentialException)


def test_fromRpcError_aForeignDomain_doesNotRaiseWrongCredential(token_server: object) -> None:
    """Another system's ErrorInfo reusing the reason string must not match."""
    server = token_server(abort_reason="API_KEY_REQUIRED", abort_domain="somebody-else.example")  # type: ignore[operator]
    with pytest.raises(grpc.RpcError) as raised:
        server.token_stub().Exchange(_empty())

    mapped = from_rpc_error(raised.value)
    assert not isinstance(mapped, WrongCredentialException)


def test_fromRpcError_abortedWithoutTheReason_staysGeneric(token_server: object) -> None:
    """Plain ABORTED is a conflict, not a durability warning. Both carry 409."""
    server = token_server(fail_with=grpc.StatusCode.ABORTED)  # type: ignore[operator]
    with pytest.raises(grpc.RpcError) as raised:
        server.token_stub().Exchange(_empty())

    mapped = from_rpc_error(raised.value)
    assert type(mapped) is CyrockDbClientException
    assert mapped.status_code == 409


def test_retryable_coversUnavailableAndDeadlineOnly() -> None:
    """429 and a stood-up commit are deliberately not retryable; see RetryableException."""
    assert isinstance(UnavailableException("x"),             RetryableException)
    assert isinstance(DeadlineExceededException("x"),        RetryableException)
    assert not isinstance(DurabilityNotConfirmedException("x"), RetryableException)
    assert not isinstance(CyrockDbClientException(429, "x"),   RetryableException)


def test_everyException_isACyrockDbClientException() -> None:
    for exception_type in (
        NotFoundException, ForbiddenException, UnauthorizedException,
        UnavailableException, DeadlineExceededException, DurabilityNotConfirmedException,
    ):
        assert issubclass(exception_type, CyrockDbClientException)


def _empty() -> object:
    from cyrock_db._proto import cyrock_db_platform_pb2 as platform_pb2
    return platform_pb2.Empty()
