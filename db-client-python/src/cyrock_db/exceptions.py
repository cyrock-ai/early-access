"""The exceptions the client raises, and the gRPC-to-HTTP projection behind their status codes.

Ported from ``client-java``'s ``CyrockDbClientException`` and ``HttpStatusProjection`` so that the
two SDKs report the same type and the same number for the same server failure.
"""

from __future__ import annotations

from collections.abc import Callable

import grpc

__all__ = [
    "CyrockDbClientException",
    "DeadlineExceededException",
    "DurabilityNotConfirmedException",
    "ForbiddenException",
    "NotFoundException",
    "RetryableException",
    "UnauthorizedException",
    "UnavailableException",
    "WrongCredentialException",
    "http_status_for",
]

# The domain and reasons the server qualifies a failure with, per the ErrorInfo contract. Must match
# ai.cyrock.db.proto.error.ErrorReasons.
_ERROR_DOMAIN               = "cyrock.ai"
_DURABILITY_NOT_CONFIRMED   = "DURABILITY_NOT_CONFIRMED"
_API_KEY_REQUIRED           = "API_KEY_REQUIRED"
_BEARER_TOKEN_REQUIRED      = "BEARER_TOKEN_REQUIRED"

# The canonical gRPC-to-HTTP projection, the same table gRPC's own HTTP gateways use and the inverse
# of the server's ResponseStatusGrpcExceptionHandler. StatusCode.value[0] is the gRPC wire ordinal and
# must never be used for this: it reports INTERNAL as 13 and UNAVAILABLE as 14, so a caller retrying
# on >= 500 would silently never retry the two failures that most deserve it (issue #361).
_HTTP_STATUS: dict[grpc.StatusCode, int] = {
    grpc.StatusCode.OK:                  200,
    # The caller, not the server, ended the call. 499 is nginx's "client closed request", which the
    # gRPC gateways adopted for exactly this; there is no standard 4xx for it.
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


def http_status_for(code: grpc.StatusCode) -> int:
    """The HTTP status code a caller expects for a gRPC status.

    An unmapped status - one gRPC adds later - reads as a server-side failure, which is the safe
    guess: it keeps an unknown status out of the 4xx range, where a caller would stop retrying and
    blame its own request.
    """
    return _HTTP_STATUS.get(code, 500)


class CyrockDbClientException(Exception):
    """Raised when a call fails, whether the server reported it or the client refused it.

    Carries an **HTTP** status code, always - never the gRPC wire ordinal. A failure the server
    reported arrives projected onto the HTTP code a caller expects; a failure the client raises
    before the call leaves is constructed with its HTTP status directly. Either way a 503 is a 503,
    not the 14 the wire calls it.

    The number is not a retry rule, though: some 4xx report the server's condition rather than a bad
    request - 429 while it sheds load, 409 on a conflict. The failures worth branching on have a
    subtype instead, so the decision need not be arithmetic at all.
    """

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message     = message


class NotFoundException(CyrockDbClientException):
    """The requested resource does not exist (HTTP 404)."""

    def __init__(self, message: str) -> None:
        super().__init__(404, message)


class ForbiddenException(CyrockDbClientException):
    """The caller's permissions do not cover the request (HTTP 403)."""

    def __init__(self, message: str) -> None:
        super().__init__(403, message)


class UnauthorizedException(CyrockDbClientException):
    """The request is not authenticated (HTTP 401)."""

    def __init__(self, message: str) -> None:
        super().__init__(401, message)


class WrongCredentialException(UnauthorizedException):
    """The right service reached with the wrong credential for it.

    The exchanged token sent to a definition service, or the API key sent to a data-plane service. The
    credential is for a *different* service, not invalid - so the fix is to send the other one, not to
    re-run the token exchange. That distinction is what a bare 401 hides, and chasing a working exchange is
    the hour the per-service split used to cost (issue #464). The server names it with a machine-readable
    reason, so this arrives as its own type rather than something to string-match.

    A kind of :class:`UnauthorizedException` (and so 401): code that already catches an auth failure still
    catches this; catch this specifically to tell "wrong credential for the service" from "bad credential".
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


class RetryableException(CyrockDbClientException):
    """Base for failures that resending the request can plausibly resolve.

    Catch this instead of comparing status codes, because the arithmetic is easy to get wrong in the
    direction that never retries. A retryable failure says nothing about whether the request was
    applied - a deadline can expire on a write the server went on to commit - so an operation that is
    not idempotent needs the same care here as anywhere else.

    Deliberately not covered: 429 (``RESOURCE_EXHAUSTED``), which is the server asking for less load
    rather than for the same request again, and :class:`DurabilityNotConfirmedException`, whose commit
    already stands. Not raised directly; catch it, do not construct it.
    """


class UnavailableException(RetryableException):
    """The server could not be reached or is not accepting requests (HTTP 503)."""

    def __init__(self, message: str) -> None:
        super().__init__(503, message)


class DeadlineExceededException(RetryableException):
    """The call did not complete within its deadline (HTTP 504)."""

    def __init__(self, message: str) -> None:
        super().__init__(504, message)


class DurabilityNotConfirmedException(CyrockDbClientException):
    """The write **committed and is visible**, but the durability flush did not confirm.

    Do not blindly retry - the commit stands, and resending would apply it twice. The caller's
    options are to verify the write, alert, or downgrade the durability mode. Carries 409, the HTTP
    projection of gRPC ``ABORTED``.
    """

    def __init__(self, message: str) -> None:
        super().__init__(409, message)


_TYPED: dict[grpc.StatusCode, Callable[[str], CyrockDbClientException]] = {
    grpc.StatusCode.NOT_FOUND:         NotFoundException,
    grpc.StatusCode.PERMISSION_DENIED: ForbiddenException,
    grpc.StatusCode.UNAUTHENTICATED:   UnauthorizedException,
    grpc.StatusCode.UNAVAILABLE:       UnavailableException,
    grpc.StatusCode.DEADLINE_EXCEEDED: DeadlineExceededException,
}


def _error_reason(error: grpc.RpcError) -> str | None:
    """The ``ai.cyrock`` ErrorInfo reason attached to the failure, if any.

    The reason string, not the status code, is the stable contract with the server (a code like ABORTED or
    UNAUTHENTICATED is shared by many failures). Returns the reason for our domain, or ``None`` when the
    server attached no such detail - in which case the generic mapping takes over.
    """
    try:
        from google.rpc import error_details_pb2
        from grpc_status import rpc_status
    except ImportError:  # pragma: no cover - grpcio-status is a hard dependency
        return None

    try:
        status = rpc_status.from_call(error)
    except (ValueError, AttributeError):
        # No status-details trailer, or an object that is not a call. Neither is an error here: it
        # just means the server did not attach details, so fall through to the generic mapping.
        return None
    if status is None:
        return None

    for detail in status.details:
        if detail.Is(error_details_pb2.ErrorInfo.DESCRIPTOR):
            info = error_details_pb2.ErrorInfo()
            if not detail.Unpack(info):
                # Is() matched but the payload does not parse; treat as absent rather than failing
                # the error path itself.
                continue
            if info.domain == _ERROR_DOMAIN:
                return str(info.reason)
    return None


def from_rpc_error(error: grpc.RpcError) -> CyrockDbClientException:
    """The exception a caller should see for a failed gRPC call.

    Mirrors ``CyrockDbClientGrpc.mapException``, so both SDKs report the same type for the same
    server failure.
    """
    # A grpc.RpcError raised by a call is also a grpc.Call and carries these; one constructed by hand
    # in a test, or a future gRPC that drops them, does not. Guarding keeps the error path from
    # failing on the way to reporting an error.
    code    = error.code() if callable(getattr(error, "code", None)) else grpc.StatusCode.UNKNOWN
    details = error.details() if callable(getattr(error, "details", None)) else None
    message = str(details) if details else str(error)

    reason = _error_reason(error)

    if code == grpc.StatusCode.ABORTED and reason == _DURABILITY_NOT_CONFIRMED:
        return DurabilityNotConfirmedException(message)

    # The right service reached with the wrong credential for it - the exchanged token sent to a
    # definition service, or the API key to a data service. A kind of UNAUTHENTICATED the server named so
    # the caller sends the other credential rather than re-authenticating (issue #464).
    if code == grpc.StatusCode.UNAUTHENTICATED and reason in (_API_KEY_REQUIRED, _BEARER_TOKEN_REQUIRED):
        return WrongCredentialException(message)

    typed = _TYPED.get(code)
    if typed is not None:
        return typed(message)

    # OK cannot arrive here - a call the server completed returns instead of raising - but an
    # exception carrying 200 would be worse than an opaque one: it reads as success in every log and
    # metric keyed on the status code. The projection maps OK to 200 correctly, as a table of HTTP
    # equivalents must; this path is the one that must never say so.
    if code == grpc.StatusCode.OK:
        return CyrockDbClientException(500, message)

    return CyrockDbClientException(http_status_for(code), message)
