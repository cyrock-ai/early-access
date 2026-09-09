"""The asyncio client: the same operations, and the concurrency that is the point of it.

These run the real ``grpc.aio`` transport against a real server, because the parity test compares
signatures only - it cannot tell whether an awaited call actually works.
"""

from __future__ import annotations

import asyncio
from typing import Any

import grpc
import pytest

from cyrock_db.aio import AsyncCyrockDbClient
from cyrock_db.exceptions import ForbiddenException, NotFoundException
from cyrock_db.types import CollectionDefinition, VectorFieldDefinition

COLLECTION = "collection-1"

DEFINITION = CollectionDefinition(
    name="docs",
    vector_fields=(VectorFieldDefinition(name="embedding", dimension=384),),
)


def _client(server: Any, **options: Any) -> AsyncCyrockDbClient:
    return AsyncCyrockDbClient(host="127.0.0.1", port=server.port, api_key="api-key", **options)


async def test_createCollection_roundTrips(token_server: Any) -> None:
    server = token_server()
    async with _client(server) as client:
        created = await client.create_collection("project-1", DEFINITION)

    assert created.id   == "generated-id"
    assert created.name == "docs"
    assert server.collections.requests[-1].project_id == "project-1"


async def test_renameCollection_roundTrips(token_server: Any) -> None:
    server = token_server()
    async with _client(server) as client:
        created = await client.create_collection("project-1", DEFINITION)
        renamed = await client.rename_collection(created.id, "renamed-docs")

    assert renamed.id   == created.id
    assert renamed.name == "renamed-docs"
    assert server.collections.requests[-1].id == created.id


async def test_theCredential_isChosenPerService(token_server: Any) -> None:
    """Data-plane calls carry the exchanged token; definition calls carry the API key.

    Also covers the interceptor stepping aside for the exchange itself - without that it would need
    the token in order to get one, and would deadlock rather than fail.
    """
    server = token_server(token="jwt-async")
    async with _client(server) as client:
        await client.list_collections("project-1")
        await client.list(COLLECTION, 0, 10)

    assert dict(server.collections.metadata)["x-api-key"] == "api-key"
    assert "authorization" not in dict(server.collections.metadata)

    assert dict(server.docs.metadata)["authorization"] == "Bearer jwt-async"
    assert ("x-api-key", "api-key") in server.service.metadata


async def test_concurrentCalls_shareOneTokenExchange(token_server: Any) -> None:
    """The asynchronous analogue of the synchronous coalescing test.

    Twenty calls fired together must produce one exchange, and - the part the synchronous client
    cannot do - none of them occupies a thread while it waits.
    """
    server = token_server()
    async with _client(server) as client:
        results = await asyncio.gather(*(client.list(COLLECTION, 0, 10) for _ in range(20)))

    assert len(results) == 20
    assert len(server.service.requests) == 1, (
        f"20 concurrent callers caused {len(server.service.requests)} token exchanges; they must share one"
    )


async def test_getCollection_absent_raisesNotFound(token_server: Any) -> None:
    server = token_server()
    async with _client(server) as client:
        with pytest.raises(NotFoundException, match="nope"):
            await client.get_collection("nope")


async def test_aServerError_arrivesAsTheSameTypeTheSyncClientRaises(token_server: Any) -> None:
    server = token_server(collections={"fail_with": grpc.StatusCode.PERMISSION_DENIED, "fail_detail": "no"})
    async with _client(server) as client:
        with pytest.raises(ForbiddenException) as raised:
            await client.list_collections("project-1")

        assert raised.value.status_code == 403


async def test_aFailedExchange_isNotCached(token_server: Any) -> None:
    server = token_server(fail_with=grpc.StatusCode.PERMISSION_DENIED)
    async with _client(server) as client:
        # PERMISSION_DENIED projects to its own status (403), not a flat 401 (issue #456).
        with pytest.raises(ForbiddenException):
            await client.list(COLLECTION, 0, 10)

        server.service.fail_with = None
        assert await client.list(COLLECTION, 0, 10) == ()


async def test_deleteCollection_returnsWhatWasRemoved(token_server: Any) -> None:
    server = token_server()
    async with _client(server) as client:
        created = await client.create_collection("project-1", DEFINITION)
        removed = await client.delete_collection("project-1", created.id)

        assert removed.id == created.id
        assert await client.list_collections("project-1") == ()


async def test_close_isIdempotent(token_server: Any) -> None:
    server = token_server()
    client = _client(server)
    await client.close()
    await client.close()
