"""The synchronous client's collection CRUD, its options and its failure translation.

Everything runs against a real gRPC server, so what is asserted is the request that reached the wire
and the exception the transport actually produced.
"""

from __future__ import annotations

from typing import Any

import grpc
import pytest

from cyrock_db import CyrockDbClient
from cyrock_db._channel import ClientOptions
from cyrock_db.exceptions import (
    DeadlineExceededException,
    ForbiddenException,
    NotFoundException,
    RetryableException,
    UnavailableException,
)
from cyrock_db.types import (
    Cardinality,
    CollectionDefinition,
    MetadataFieldDefinition,
    MetadataFieldType,
    SimilarityFunction,
    VectorFieldDefinition,
)

DEFINITION = CollectionDefinition(
    name="docs",
    vector_fields=(VectorFieldDefinition(name="embedding", dimension=384),),
    metadata_fields=(MetadataFieldDefinition(name="title", type=MetadataFieldType.STRING,
                            cardinality=Cardinality.HIGH, fulltext=True),),
)


def _client(server: Any, **options: Any) -> CyrockDbClient:
    return CyrockDbClient(host="127.0.0.1", port=server.port, api_key="api-key", **options)


def test_createCollection_sendsTheDefinition_andReturnsWhatTheServerStored(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        created = client.create_collection("project-1", DEFINITION)

    sent = server.collections.requests[-1]
    assert sent.project_id                        == "project-1"
    assert sent.name                              == "docs"
    assert sent.vector_fields[0].dimension        == 384
    assert sent.vector_fields[0].similarity_function == SimilarityFunction.COSINE.value
    assert sent.metadata_fields[0].fulltext is True

    assert created.id   == "generated-id"
    assert created.name == "docs"
    assert created.default_vector_field() is not None
    assert created.default_vector_field().name == "embedding"


def test_definitionCalls_carryTheApiKey_notTheExchangedToken(token_server: Any) -> None:
    """The credential is chosen per service, and the definition services want the raw API key.

    This test previously asserted the opposite and passed, because the in-process server accepts any
    credential. Against a real one the platform server issues the token and then refuses it on its
    own definition services: ``UNAUTHENTICATED: Invalid bearer token``. That is why it is worth
    asserting the *absence* of the bearer here rather than only the presence of the key.
    """
    server = token_server(token="jwt-abc")
    with _client(server) as client:
        client.create_collection("project-1", DEFINITION)

    collection_metadata = dict(server.collections.metadata)
    assert collection_metadata["x-api-key"] == "api-key"
    assert "authorization" not in collection_metadata, (
        "the definition services refuse the exchanged token"
    )


def test_aDefinitionCall_doesNotExchangeAToken(token_server: Any) -> None:
    """Nothing on the definition path needs one, so nothing should pay for one."""
    server = token_server()
    with _client(server) as client:
        client.list_collections("project-1")

    assert server.service.requests == [], "no token exchange for an API-key call"


def test_client_withoutApiKey_sendsNoCredentials(token_server: Any) -> None:
    server = token_server()
    with CyrockDbClient(host="127.0.0.1", port=server.port) as client:
        client.list_collections("project-1")

    assert not server.service.requests, "no API key means no token exchange"
    assert "authorization" not in dict(server.collections.metadata)


def test_listCollections_returnsThemAll(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        client.create_collection("project-1", DEFINITION)
        client.create_collection("project-1", DEFINITION.evolve(name="other"))
        listed = client.list_collections("project-1")

    assert [each.name for each in listed] == ["docs", "other"]
    assert server.collections.requests[-1].project_id == "project-1"


def test_getCollection_findsItById(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        created = client.create_collection("project-1", DEFINITION)
        found   = client.get_collection(created.id)

    assert found.id == created.id


def test_getCollection_absent_raisesNotFound(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client, pytest.raises(NotFoundException, match="Collection not found: nope"):
        client.get_collection("nope")


def test_deleteCollection_returnsWhatWasRemoved(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        created = client.create_collection("project-1", DEFINITION)
        removed = client.delete_collection("project-1", created.id)

        assert removed.id == created.id
        assert client.list_collections("project-1") == ()


def test_renameCollection_sendsIdAndName_andReturnsTheRenamedDefinition(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        created = client.create_collection("project-1", DEFINITION)
        renamed = client.rename_collection(created.id, "renamed-docs")

    sent = server.collections.requests[-1]
    assert sent.id   == created.id
    assert sent.name == "renamed-docs"

    assert renamed.id   == created.id
    assert renamed.name == "renamed-docs"


def test_aServerError_arrivesAsTheMatchingException(token_server: Any) -> None:
    server = token_server(collections={"fail_with": grpc.StatusCode.PERMISSION_DENIED, "fail_detail": "no"})
    with _client(server) as client, pytest.raises(ForbiddenException, match="no") as raised:
        client.list_collections("project-1")

    assert raised.value.status_code == 403


def test_callTimeout_isAppliedPerRequest(token_server: Any) -> None:
    """A slow server must fail with 504, not hang. The Java client uses an interceptor for this."""
    server = token_server(collections={"delay_seconds": 1.0})
    with _client(server, call_timeout=0.05) as client, pytest.raises(DeadlineExceededException) as raised:
        client.list_collections("project-1")

    assert raised.value.status_code == 504


def test_anUnreachableServer_withoutAnApiKey_arrivesAsUnavailable(token_server: Any) -> None:
    server = token_server()
    client = CyrockDbClient(host="127.0.0.1", port=server.port)
    server.server.stop(grace=None)

    with pytest.raises(UnavailableException) as raised:
        client.list_collections("project-1")
    assert raised.value.status_code == 503
    client.close()


def test_anUnreachableServer_onADataCall_arrivesAsUnavailable_matchingJava() -> None:
    """The token exchange projects its own transport status now (issue #456).

    A data-plane call needs the exchanged token, so the exchange is the first thing to touch the
    network. An unreachable server makes that exchange fail with UNAVAILABLE, and the manager projects
    it the way ``from_rpc_error`` does - so the caller sees a retryable ``UnavailableException`` (503),
    not a flat 401 that reads as a bad credential and defeats ``RetryableException``. Definition calls
    carry the API key directly and never exchange, so they already reported 503 (below); this is the
    data plane catching up. client-java behaves identically, so this is parity.
    """
    client = CyrockDbClient(host="127.0.0.1", port=1, api_key="api-key", call_timeout=0.5)

    with pytest.raises(UnavailableException) as raised:
        client.upsert("collection-1", -1, {}, {})
    assert raised.value.status_code == 503
    assert isinstance(raised.value, RetryableException), (
        "a server that is merely down must be retryable, matching the fixed Java manager"
    )
    client.close()


def test_anUnreachableServer_onADefinitionCall_arrivesAsUnavailable() -> None:
    """The other half of #456: no exchange on this path, so the real status survives."""
    client = CyrockDbClient(host="127.0.0.1", port=1, api_key="api-key", call_timeout=0.5)

    with pytest.raises(UnavailableException) as raised:
        client.list_collections("project-1")
    assert raised.value.status_code == 503
    assert isinstance(raised.value, RetryableException)
    client.close()


def test_close_isIdempotent(token_server: Any) -> None:
    server = token_server()
    client = _client(server)
    client.close()
    client.close()


@pytest.mark.parametrize(
    ("option", "value"),
    [("call_timeout", 0), ("call_timeout", -1), ("keepalive_time", 0), ("keepalive_timeout", -5)],
)
def test_options_nonPositiveDuration_isRejected(option: str, value: float) -> None:
    with pytest.raises(ValueError, match="must be positive"):
        ClientOptions(**{option: value})


def test_options_defaults_matchTheJavaBuilder() -> None:
    options = ClientOptions()
    assert options.host          == "localhost"
    assert options.port          == 9090, "9090 is the gateway fronting both planes, not a data-server port"
    assert options.use_plaintext is True
    assert options.api_key       is None
    assert options.call_timeout  is None
    assert options.channel_arguments() == []


def test_options_channelArguments_reflectTheSettings() -> None:
    arguments = dict(
        ClientOptions(keepalive_time=30, keepalive_timeout=5, max_inbound_message_size=8_388_608)
        .channel_arguments()
    )
    assert arguments["grpc.keepalive_time_ms"]           == 30_000
    assert arguments["grpc.keepalive_timeout_ms"]        ==  5_000
    assert arguments["grpc.max_receive_message_length"]  == 8_388_608
