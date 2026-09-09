"""Both transaction surfaces: what each operation encodes to, and what comes back.

Both are all-or-nothing. The per-operation results exist so a partial outcome can be reported
precisely even though the transaction never partially applies, which is why ``OperationResult.error``
means "this is why the whole thing rolled back" rather than "this one failed alone".
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from cyrock_db import CyrockDbClient
from cyrock_db._proto_requests import execute_document_transaction, execute_transaction
from cyrock_db.aio import AsyncCyrockDbClient
from cyrock_db.types import (
    AddEdgeOp,
    AddNodeOp,
    OperationResult,
    RemoveDocumentOp,
    RemoveEdgeOp,
    RemoveNodeOp,
    TransactionResult,
    UpdateEdgeMetadataOp,
    UpdateNodeMetadataOp,
    UpdateVectorOp,
    UpdateWeightOp,
    UpsertDocumentOp,
    UpsertKeyOp,
    UpsertNodeOp,
    Vector,
)

COLLECTION = "collection-1"
GRAPH      = "graph-1"


def _client(server: Any) -> CyrockDbClient:
    return CyrockDbClient(host="127.0.0.1", port=server.port, api_key="api-key")


# ─── Encoding ──────────────────────────────────────────────────────────────


def test_documentOperations_eachEncodeToTheirOwnArm() -> None:
    request = execute_document_transaction(COLLECTION, [
        UpsertDocumentOp(id=-1, vectors={"embedding": Vector([1.0])}, metadata={"n": 1}),
        UpsertKeyOp(external_key="k", vectors={"embedding": Vector([2.0])}),
        RemoveDocumentOp(document_id=7),
    ])

    assert [each.WhichOneof("operation") for each in request.operations] == [
        "upsert", "upsert_by_key", "remove",
    ]
    assert request.operations[0].upsert.id == -1
    assert request.operations[1].upsert_by_key.external_key == "k"
    assert request.operations[2].remove.document_id == 7


def test_graphOperations_eachEncodeToTheirOwnArm() -> None:
    request = execute_transaction(GRAPH, [
        AddNodeOp(labels=["A"], vectors={"embedding": Vector([1.0])}, metadata={"n": 1}),
        AddEdgeOp(1, 2, "T", 0.5, {"why": "x"}),
        RemoveNodeOp.by_id(3),
        RemoveNodeOp.by_key("k"),
        RemoveEdgeOp(4),
        UpdateVectorOp(5, "embedding", [1.0, 2.0]),
        UpdateWeightOp(6, 0.25),
        UpdateNodeMetadataOp(7, {"v": 2}),
        UpdateEdgeMetadataOp(8, {"since": 2099}),
        UpsertNodeOp.create(labels=["B"]),
    ])

    assert [each.WhichOneof("operation") for each in request.operations] == [
        "add_node", "add_edge", "remove_node", "remove_node_by_key", "remove_edge",
        "update_vector", "update_weight", "update_node_metadata", "update_edge_metadata", "upsert_node",
    ]


def test_removeNodeOp_takesExactlyOneAddress() -> None:
    """Java offers byId/byKey factories over one record with two nullable fields; both cannot be set."""
    with pytest.raises(ValueError, match="exactly one"):
        RemoveNodeOp(node_id=1, external_key="k")
    with pytest.raises(ValueError, match="exactly one"):
        RemoveNodeOp()


@pytest.mark.parametrize(
    ("operation", "expects_node_id"),
    [
        (UpsertNodeOp.by_id(9, ["A"]),   True),
        (UpsertNodeOp.by_key("k", ["A"]), False),
        (UpsertNodeOp.create(["A"]),      False),
    ],
)
def test_upsertNodeOp_addressing(operation: UpsertNodeOp, expects_node_id: bool) -> None:
    """`create` sets neither, so the store assigns an id."""
    encoded = execute_transaction(GRAPH, [operation]).operations[0].upsert_node
    assert encoded.HasField("node_id") is expects_node_id


def test_anUnknownOperation_isRefusedRatherThanDropped() -> None:
    """The failure mode this guards is silence: a dropped operation in an all-or-nothing surface."""
    class Invented:
        pass

    with pytest.raises(TypeError, match="Unsupported graph operation"):
        execute_transaction(GRAPH, [Invented()])  # type: ignore[list-item]
    with pytest.raises(TypeError, match="Unsupported collection operation"):
        execute_document_transaction(COLLECTION, [Invented()])  # type: ignore[list-item]


# ─── Round trip ────────────────────────────────────────────────────────────


def test_documentTransaction_returnsOneResultPerOperation(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        result = client.execute_document_transaction(COLLECTION, [
            UpsertDocumentOp(id=-1, vectors={"embedding": Vector([1.0])}),
            RemoveDocumentOp(document_id=1),
        ])

    assert isinstance(result, TransactionResult)
    assert [each.index for each in result.results] == [0, 1]
    assert result.success is True


def test_graphTransaction_returnsOneResultPerOperation(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        result = client.execute_transaction(GRAPH, [AddNodeOp(labels=["A"]), RemoveEdgeOp(1)])

    assert [each.generated_id for each in result.results] == [1000, 1001]
    assert result.success is True


def test_anEmptyTransaction_isAcceptedAndReturnsNothing(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        assert client.execute_transaction(GRAPH, []).results == ()


def test_operationResult_successIsAboutTheAbsenceOfAnError() -> None:
    assert OperationResult(index=0, generated_id=1).success is True
    assert OperationResult(index=0, error="conflict").success is False
    assert TransactionResult(results=(OperationResult(0, error="x"),)).success is False


def test_bothFacades_agreeOnTransactionResults(token_server: Any) -> None:
    server     = token_server()
    operations = [AddNodeOp(labels=["A"]), AddEdgeOp(1, 2, "T")]
    with _client(server) as client:
        blocking = client.execute_transaction(GRAPH, operations)

    async def awaited() -> TransactionResult:
        async with AsyncCyrockDbClient(host="127.0.0.1", port=server.port, api_key="api-key") as client:
            return await client.execute_transaction(GRAPH, operations)

    assert blocking == asyncio.run(awaited())
