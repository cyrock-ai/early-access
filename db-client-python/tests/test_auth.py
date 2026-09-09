"""The auth interceptors, including the one detail whose failure mode is a hang."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import grpc
import pytest

from cyrock_db._auth import (
    API_KEY_HEADER,
    API_KEY_SERVICES,
    TOKEN_EXCHANGE_METHOD,
    AsyncAuthInterceptor,
    AuthInterceptor,
    bearer,
    uses_api_key,
)
from cyrock_db._proto import cyrock_db_data_pb2 as data_pb2
from cyrock_db._proto import cyrock_db_data_pb2_grpc as data_grpc
from cyrock_db._proto import cyrock_db_platform_pb2 as platform_pb2
from cyrock_db._proto import cyrock_db_platform_pb2_grpc as platform_grpc
from cyrock_db.exceptions import WrongCredentialException, from_rpc_error


def test_bearer_formatsTheAuthorizationHeader() -> None:
    assert bearer("tok") == ("authorization", "Bearer tok")


def test_apiKeyHeader_isTheOneTheServerReads() -> None:
    assert API_KEY_HEADER == "x-api-key"


class _Details:
    def __init__(self, method: Any) -> None:
        self.method         = method
        self.timeout        = None
        self.metadata       = None
        self.credentials    = None
        self.wait_for_ready = None
        self.compression    = None


@pytest.mark.parametrize(
    "method",
    [TOKEN_EXCHANGE_METHOD, TOKEN_EXCHANGE_METHOD.encode()],
    ids=["str", "bytes"],
)
def test_asyncInterceptor_recognisesTheExchangeMethod_asBytesOrText(method: Any) -> None:
    """The bytes case is the bug this guards, and its symptom is a hang, not a wrong header.

    grpc.aio reports ``client_call_details.method`` as bytes where the synchronous interceptor
    reports str. With a str-only comparison the skip-list never matches, so the token exchange goes
    through the interceptor, which awaits the token that exchange is producing. The two then wait on
    each other for ever - no error, no failed test, just a suite that never finishes.
    """
    interceptor = AsyncAuthInterceptor(lambda: None, frozenset({TOKEN_EXCHANGE_METHOD}))  # type: ignore[arg-type,return-value]

    assert interceptor._method_of(_Details(method)) == TOKEN_EXCHANGE_METHOD
    assert interceptor._method_of(_Details(method)) in interceptor._skip_methods


def test_syncInterceptor_addsTheProvidedMetadata() -> None:
    interceptor = AuthInterceptor(lambda _method: [bearer("tok")])
    seen: dict[str, Any] = {}

    def continuation(details: grpc.ClientCallDetails, request: Any) -> str:
        seen["metadata"] = dict(details.metadata or ())
        return "response"

    assert interceptor.intercept_unary_unary(continuation, _Details("/svc/Method"), None) == "response"
    assert seen["metadata"]["authorization"] == "Bearer tok"


def test_syncInterceptor_preservesMetadataTheCallerAlreadySet() -> None:
    interceptor = AuthInterceptor(lambda _method: [bearer("tok")])
    details = _Details("/svc/Method")
    details.metadata = (("x-trace-id", "abc"),)  # type: ignore[assignment]
    seen: dict[str, Any] = {}

    def continuation(call_details: grpc.ClientCallDetails, request: Any) -> None:
        seen["metadata"] = dict(call_details.metadata or ())

    interceptor.intercept_unary_unary(continuation, details, None)  # type: ignore[arg-type]
    assert seen["metadata"]["x-trace-id"]    == "abc"
    assert seen["metadata"]["authorization"] == "Bearer tok"


def test_syncInterceptor_skipsTheMethodsItWasToldTo() -> None:
    interceptor = AuthInterceptor(lambda _method: [bearer("tok")], frozenset({"/svc/Skipped"}))
    seen: dict[str, Any] = {}

    def continuation(details: grpc.ClientCallDetails, request: Any) -> None:
        seen["metadata"] = dict(details.metadata or ())

    interceptor.intercept_unary_unary(continuation, _Details("/svc/Skipped"), None)  # type: ignore[arg-type]
    assert "authorization" not in seen["metadata"]


def test_syncInterceptor_skipsTheMethodsItWasToldTo_onStreamingCallsToo() -> None:
    """The streaming form must consult the same list as the unary one.

    Both asyncio forms check it and the blocking unary form checks it, so a blocking streaming form
    that did not was an asymmetry waiting to bite: the only skipped method today is the unary token
    exchange, so nothing broke, but adding a streaming method to the list would have silently
    authorized it anyway.
    """
    interceptor = AuthInterceptor(lambda _method: [bearer("tok")], frozenset({"/svc/Skipped"}))
    seen: dict[str, Any] = {}

    def continuation(details: grpc.ClientCallDetails, request: Any) -> None:
        seen["metadata"] = dict(details.metadata or ())

    interceptor.intercept_unary_stream(continuation, _Details("/svc/Skipped"), None)  # type: ignore[arg-type]
    assert "authorization" not in seen["metadata"]

    interceptor.intercept_unary_stream(continuation, _Details("/svc/Watched"), None)  # type: ignore[arg-type]
    assert seen["metadata"]["authorization"] == "Bearer tok"


# ─── The credential-per-service contract ─────────────────────────────────────────────────────────
#
# API_KEY_SERVICES is hand-copied from a Java constructor and is exactly the kind of second copy that
# drifts (issue #464). credential-by-service.tsv in the proto module is now the one authority; these hold
# this list to it. Skipped in a published wheel, where the reactor is not beside us - the same treatment
# test_types_mirror_java.py and test_cyql_routing.py give their cross-language fixtures.

FIXTURE = (
    Path(__file__).resolve().parents[2] / "proto" / "src" / "main" / "resources" / "credential-by-service.tsv"
)

_needs_fixture = pytest.mark.skipif(
    not FIXTURE.is_file(),
    reason="the proto module is not beside this checkout; nothing to check against",
)


def _contract() -> dict[str, str]:
    """The contract as ``{fully-qualified service: credential}``."""
    rows = {}
    for line in FIXTURE.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        credential, service = stripped.split("\t", 1)
        rows[service] = credential
    return rows


@_needs_fixture
def test_apiKeyServices_matchesTheContract_exactly() -> None:
    """The hand-maintained tuple must be exactly the API_KEY rows of the shared table.

    A definition service dropped from the tuple would silently send it the exchanged token, which the
    server refuses - the very failure #464 is about, back again in the copy that was meant to prevent it.
    """
    from_contract = tuple(
        sorted(f"/{service}/" for service, credential in _contract().items() if credential == "API_KEY")
    )
    assert tuple(sorted(API_KEY_SERVICES)) == from_contract, (
        "cyrock_db._auth.API_KEY_SERVICES has drifted from credential-by-service.tsv.\n"
        "Update the tuple to match the table (which the Java build holds to the wiring)."
    )


@_needs_fixture
def test_usesApiKey_agreesWithTheContract_forEveryService() -> None:
    """Every service in the table routes to the credential the table records, method path and all."""
    for service, credential in _contract().items():
        method = f"/{service}/SomeMethod"
        assert uses_api_key(method) is (credential == "API_KEY"), (
            f"{service} is recorded as {credential} but uses_api_key says otherwise"
        )


@_needs_fixture
def test_theContract_coversBothCredentials() -> None:
    """A table with only one credential could not catch a service mapped to the wrong one."""
    credentials = set(_contract().values())
    assert credentials == {"API_KEY", "BEARER"}, f"unexpected credentials in the table: {credentials}"


# ─── The enforcing test double refuses the wrong credential (issue #464, point 4) ─────────────────
#
# Until the test servers enforce the split, an auth test asserts nothing - which is how the unit test that
# first covered this asserted the wrong behaviour and passed. These run against a server that reads the same
# contract and refuses the wrong credential, so they would have caught it.


@_needs_fixture
def test_enforcingServer_definitionServiceWithTheApiKey_isAccepted(enforcing_server: object) -> None:
    server = enforcing_server()  # type: ignore[operator]
    response = platform_grpc.TokenGrpcServiceStub(server.channel).Exchange(
        platform_pb2.Empty(), metadata=(("x-api-key", "obs_key"),)
    )
    assert response.token, "the API key is the right credential for a definition/token service"


@_needs_fixture
def test_enforcingServer_definitionServiceWithTheExchangedToken_isRefused(enforcing_server: object) -> None:
    """The exact mistake from the issue: the exchanged token where the API key belongs."""
    server = enforcing_server()  # type: ignore[operator]
    with pytest.raises(grpc.RpcError) as raised:
        platform_grpc.TokenGrpcServiceStub(server.channel).Exchange(
            platform_pb2.Empty(), metadata=(("authorization", "Bearer tok"),)
        )
    assert raised.value.code() == grpc.StatusCode.UNAUTHENTICATED
    assert isinstance(from_rpc_error(raised.value), WrongCredentialException)


@_needs_fixture
def test_enforcingServer_dataServiceWithTheBearerToken_isAccepted(enforcing_server: object) -> None:
    server = enforcing_server()  # type: ignore[operator]
    result = data_grpc.DocumentGrpcServiceStub(server.channel).List(
        data_pb2.ListDocumentsRequest(collection_id="c", offset=0),
        metadata=(("authorization", "Bearer tok"),),
    )
    assert list(result.documents) == [], "the bearer token is the right credential for a data service"


@_needs_fixture
def test_enforcingServer_dataServiceWithTheApiKey_isRefused(enforcing_server: object) -> None:
    server = enforcing_server()  # type: ignore[operator]
    with pytest.raises(grpc.RpcError) as raised:
        data_grpc.DocumentGrpcServiceStub(server.channel).List(
            data_pb2.ListDocumentsRequest(collection_id="c", offset=0),
            metadata=(("x-api-key", "obs_key"),),
        )
    assert raised.value.code() == grpc.StatusCode.UNAUTHENTICATED
    assert isinstance(from_rpc_error(raised.value), WrongCredentialException)
