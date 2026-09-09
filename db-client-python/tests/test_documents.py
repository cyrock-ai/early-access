"""Document CRUD on both facades, against a real server that stores what it is sent.

Both clients are exercised through the same table of scenarios, because the point of the two-facade
design is that they behave identically - and a test that only covers one of them is exactly how that
stops being true.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

import grpc
import pytest

from cyrock_db import CyrockDbClient
from cyrock_db.aio import AsyncCyrockDbClient
from cyrock_db.exceptions import ForbiddenException, NotFoundException
from cyrock_db.types import AUTO_ASSIGN_ID, Document, Text, Vector

COLLECTION = "collection-1"


def _sync(server: Any, **options: Any) -> CyrockDbClient:
    return CyrockDbClient(host="127.0.0.1", port=server.port, api_key="api-key", **options)


def _async(server: Any, **options: Any) -> AsyncCyrockDbClient:
    return AsyncCyrockDbClient(host="127.0.0.1", port=server.port, api_key="api-key", **options)


def _both(server: Any) -> list[tuple[str, Callable[[str], Any]]]:
    """Runs one named operation on each facade, awaiting the async one, and returns both results."""
    def run(operation: str, *args: Any, **kwargs: Any) -> tuple[Any, Any]:
        with _sync(server) as client:
            blocking = getattr(client, operation)(*args, **kwargs)

        async def awaited() -> Any:
            async with _async(server) as client:
                return await getattr(client, operation)(*args, **kwargs)

        return blocking, asyncio.run(awaited())

    return run  # type: ignore[return-value]


# ─── Upsert and read back ───────────────────────────────────────────────────


def test_upsert_autoAssignId_letsTheStoreChoose(token_server: Any) -> None:
    server = token_server()
    with _sync(server) as client:
        assigned = client.upsert(COLLECTION, AUTO_ASSIGN_ID, {"embedding": Vector([1.0, 2.0])}, {"n": 1})

    assert assigned >= 0
    sent = server.docs.requests[-1]
    assert sent.HasField("id") and sent.id == AUTO_ASSIGN_ID, (
        "the id is sent as given; the server reads any negative value as auto-assign"
    )


def test_upsert_idZero_addressesDocumentZero_notAutoAssign(token_server: Any) -> None:
    """The reason the proto field carries presence at all: 0 is a real document id."""
    server = token_server()
    with _sync(server) as client:
        assigned = client.upsert(COLLECTION, 0, {"embedding": Vector([1.0])}, {})

    assert assigned == 0
    assert server.docs.requests[-1].id == 0


def test_upsert_aTextVector_asksTheServerToEmbed(token_server: Any) -> None:
    server = token_server()
    with _sync(server) as client:
        client.upsert(COLLECTION, AUTO_ASSIGN_ID, {"caption": Text("a cat on a mat")}, {})

    field = server.docs.requests[-1].vectors["caption"]
    assert field.text == "a cat on a mat"
    assert list(field.values) == [], "text and values are alternatives, not both"


def test_getById_returnsWhatWasStored_metadataTypesIntact(token_server: Any) -> None:
    """A LONG past the double mantissa has to survive the whole client round trip, not just the codec."""
    server   = token_server()
    metadata = {"big": 2**53 + 1, "flag": True, "name": "x", "ratio": 0.5, "tags": ["a", "b"]}

    with _sync(server) as client:
        document_id = client.upsert(COLLECTION, AUTO_ASSIGN_ID, {"embedding": Vector([1.0, 2.0])}, metadata)
        read        = client.get_by_id(COLLECTION, document_id)

    assert read.id             == document_id
    assert read.vectors        == {"embedding": (1.0, 2.0)}
    assert read.metadata["big"]   == 2**53 + 1
    assert read.metadata["flag"]  is True
    assert read.metadata["tags"]  == ["a", "b"]
    assert read.metadata["ratio"] == 0.5


def test_getById_absent_raisesNotFound(token_server: Any) -> None:
    server = token_server()
    with _sync(server) as client, pytest.raises(NotFoundException):
        client.get_by_id(COLLECTION, 9999)


# ─── Batch ─────────────────────────────────────────────────────────────────


def test_upsertBatch_returnsIdsInOrder(token_server: Any) -> None:
    server = token_server()
    documents = [
        Document.with_vector([1.0], {"i": 0}),
        Document.with_vector([2.0], {"i": 1}),
        Document(id=42, vectors={"embedding": (3.0,)}, metadata={"i": 2}),
    ]
    with _sync(server) as client:
        ids = client.upsert_batch(COLLECTION, documents)

    assert len(ids) == 3
    assert ids[2] == 42, "an explicit id is honoured inside a batch"
    with _sync(server) as client:
        assert client.get_by_id(COLLECTION, ids[1]).metadata["i"] == 1


def test_upsertBatch_carriesTheExternalKey(token_server: Any) -> None:
    """Issue #225 was batch-written keys never reaching CDC; the client must at least send them."""
    server = token_server()
    with _sync(server) as client:
        client.upsert_batch(COLLECTION, [Document(vectors={"embedding": (1.0,)}, external_key="k-1")])

    assert server.docs.requests[-1].documents[0].external_key == "k-1"


def test_upsertBatch_empty_sendsAnEmptyBatch(token_server: Any) -> None:
    server = token_server()
    with _sync(server) as client:
        assert client.upsert_batch(COLLECTION, []) == ()


# ─── List and delete ───────────────────────────────────────────────────────


def test_list_pagesThroughTheCollection(token_server: Any) -> None:
    server = token_server()
    with _sync(server) as client:
        for index in range(5):
            client.upsert(COLLECTION, AUTO_ASSIGN_ID, {"embedding": Vector([float(index)])}, {"i": index})

        first = client.list(COLLECTION, 0, 2)
        rest  = client.list(COLLECTION, 2, 3)

    assert [each.metadata["i"] for each in first] == [0, 1]
    assert [each.metadata["i"] for each in rest]  == [2, 3, 4]


def test_delete_returnsWhatWasRemoved(token_server: Any) -> None:
    server = token_server()
    with _sync(server) as client:
        document_id = client.upsert(COLLECTION, AUTO_ASSIGN_ID, {"embedding": Vector([1.0])}, {"n": 1})
        removed     = client.delete(COLLECTION, document_id)

        assert removed.id == document_id
        with pytest.raises(NotFoundException):
            client.get_by_id(COLLECTION, document_id)


# ─── External keys ─────────────────────────────────────────────────────────


def test_upsertDocument_byKey_isIdempotent_andSaysWhichHappened(token_server: Any) -> None:
    """The point of the external-key path: re-ingest updates rather than duplicating."""
    server = token_server()
    with _sync(server) as client:
        first  = client.upsert_document(COLLECTION, "doc-1", {"embedding": Vector([1.0])}, {"v": 1})
        second = client.upsert_document(COLLECTION, "doc-1", {"embedding": Vector([2.0])}, {"v": 2})

        assert first.created  is True
        assert second.created is False
        assert first.id == second.id, "the same key addresses the same document"
        assert client.get_document(COLLECTION, "doc-1").metadata["v"] == 2


def test_getDocument_absentKey_raisesNotFound(token_server: Any) -> None:
    server = token_server()
    with _sync(server) as client, pytest.raises(NotFoundException, match="doc-absent"):
        client.get_document(COLLECTION, "doc-absent")


def test_removeDocument_byKey_returnsWhatWasRemoved(token_server: Any) -> None:
    server = token_server()
    with _sync(server) as client:
        created = client.upsert_document(COLLECTION, "doc-1", {"embedding": Vector([1.0])}, {})
        removed = client.remove_document(COLLECTION, "doc-1")

        assert removed.id == created.id
        with pytest.raises(NotFoundException):
            client.get_document(COLLECTION, "doc-1")


# ─── The two facades agree ─────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("operation", "args"),
    [
        ("upsert",       (COLLECTION, AUTO_ASSIGN_ID, {"embedding": Vector([1.0])}, {"n": 7})),
        ("list",         (COLLECTION, 0, 10)),
        ("upsert_batch", (COLLECTION, [Document.with_vector([1.0], {"n": 7})])),
    ],
)
def test_bothFacades_returnTheSameShape(token_server: Any, operation: str, args: tuple[Any, ...]) -> None:
    server = token_server()
    blocking, awaited = _both(server)(operation, *args)
    assert type(blocking) is type(awaited)


def test_bothFacades_readBackTheSameDocument(token_server: Any) -> None:
    server = token_server()
    with _sync(server) as client:
        document_id = client.upsert(COLLECTION, AUTO_ASSIGN_ID, {"embedding": Vector([1.0, 2.0])}, {"n": 7})
        blocking    = client.get_by_id(COLLECTION, document_id)

    async def awaited() -> Document:
        async with _async(server) as client:
            return await client.get_by_id(COLLECTION, document_id)

    assert blocking == asyncio.run(awaited())


def test_bothFacades_raiseTheSameExceptionForTheSameFailure(token_server: Any) -> None:
    server = token_server(docs={"fail_with": grpc.StatusCode.PERMISSION_DENIED, "fail_detail": "no"})

    with _sync(server) as client, pytest.raises(ForbiddenException) as blocking:
        client.list(COLLECTION, 0, 10)

    async def awaited() -> Any:
        async with _async(server) as client:
            with pytest.raises(ForbiddenException) as raised:
                await client.list(COLLECTION, 0, 10)
            return raised.value

    from_async = asyncio.run(awaited())
    assert type(blocking.value) is type(from_async)
    assert blocking.value.status_code == from_async.status_code == 403
