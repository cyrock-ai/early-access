"""Graph node and edge operations, and graph definition CRUD.

The label-filter folding gets particular attention: it is the one place where three inputs on the
request collapse into one expression tree, and where getting it wrong produces a filter that quietly
matches the wrong set rather than an error.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from cyrock_db import CyrockDbClient
from cyrock_db._label_filters import to_label_expression
from cyrock_db.aio import AsyncCyrockDbClient
from cyrock_db.exceptions import NotFoundException
from cyrock_db.types import (
    AddEdgeRequest,
    GraphDefinition,
    LabelMatch,
    ListNodesRequest,
    Node,
    UpsertNodeRequest,
    Vector,
    VectorFieldDefinition,
)

GRAPH = "graph-1"


def _client(server: Any) -> CyrockDbClient:
    return CyrockDbClient(host="127.0.0.1", port=server.port, api_key="api-key")


# ─── Definitions ───────────────────────────────────────────────────────────


def test_createGraph_thenGetAndList(token_server: Any) -> None:
    server = token_server()
    definition = GraphDefinition(
        name="concepts",
        node_vector_fields=(VectorFieldDefinition(name="embedding", dimension=8),),
        enable_temporal_tracking=True,
        auto_link_threshold=0.8,
    )
    with _client(server) as client:
        created = client.create_graph("project-1", definition)
        found   = client.get_graph(created.id)
        listed  = client.list_graphs("project-1")

    assert created.name == "concepts"
    assert created.enable_temporal_tracking is True
    assert created.auto_link_threshold == pytest.approx(0.8)
    assert found.id == created.id
    assert [each.id for each in listed] == [created.id]


def test_getGraph_absent_raisesNotFound(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client, pytest.raises(NotFoundException, match="Graph not found: nope"):
        client.get_graph("nope")


def test_deleteGraph_returnsWhatWasRemoved(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        created = client.create_graph("project-1", GraphDefinition(name="temp"))
        removed = client.delete_graph("project-1", created.id)

        assert removed.id == created.id
        assert client.list_graphs("project-1") == ()


# ─── Nodes and edges ───────────────────────────────────────────────────────


def test_addNode_thenGetItBack(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        node_id = client.add_node(
            GRAPH, ["Concept", "Seed"], {"embedding": Vector([1.0, 2.0])}, {"title": "x", "rank": 3}
        )
        node = client.get_node(GRAPH, node_id)

    assert isinstance(node, Node)
    assert node.id     == node_id
    assert node.labels == ("Concept", "Seed")
    assert node.metadata == {"title": "x", "rank": 3}


def test_addNode_duplicateLabels_collapse_keepingOrder(token_server: Any) -> None:
    """Java's Node constructor removes duplicates; the decoded node has to behave the same."""
    assert Node(labels=("A", "B", "A")).labels == ("A", "B")


def test_addEdge_thenGetItBack(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        source = client.add_node(GRAPH, ["A"], None, None)
        target = client.add_node(GRAPH, ["B"], None, None)
        edge_id = client.add_edge(
            GRAPH, AddEdgeRequest(source, target, "RELATES_TO", 0.9, {"why": "test"})
        )
        edge = client.get_edge(GRAPH, edge_id)

    assert (edge.source_id, edge.target_id, edge.type) == (source, target, "RELATES_TO")
    assert edge.weight == pytest.approx(0.9)
    assert edge.metadata == {"why": "test"}


def test_getNode_dispatchesOnTheArgumentType(token_server: Any) -> None:
    """Java overloads getNode on long vs String; Python takes either and dispatches."""
    server = token_server()
    with _client(server) as client:
        result  = client.upsert_node(GRAPH, UpsertNodeRequest(labels=["Keyed"], external_key="k-1"))
        by_id   = client.get_node(GRAPH, result.node_id)
        by_key  = client.get_node(GRAPH, "k-1")

    assert by_id.id == by_key.id == result.node_id
    assert by_key.external_key == "k-1"


def test_removeNode_byIdAndByKey(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        node_id = client.add_node(GRAPH, ["A"], None, None)
        client.remove_node(GRAPH, node_id)
        with pytest.raises(NotFoundException):
            client.get_node(GRAPH, node_id)

        client.upsert_node(GRAPH, UpsertNodeRequest(labels=["B"], external_key="k-2"))
        client.remove_node(GRAPH, "k-2")
        with pytest.raises(NotFoundException):
            client.get_node(GRAPH, "k-2")


def test_getNode_missingId_raisesNotFound(token_server: Any) -> None:
    # A single read of a missing id is a not-found, not a None the caller must guard (#450).
    server = token_server()
    with _client(server) as client, pytest.raises(NotFoundException):
        client.get_node(GRAPH, 999_999)


def test_getEdge_missingId_raisesNotFound(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client, pytest.raises(NotFoundException):
        client.get_edge(GRAPH, 999_999)


def test_upsertNode_byKey_isIdempotent(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        first  = client.upsert_node(GRAPH, UpsertNodeRequest(labels=["A"], external_key="k"))
        second = client.upsert_node(GRAPH, UpsertNodeRequest(labels=["A", "B"], external_key="k"))

    assert first.created  is True
    assert second.created is False
    assert first.node_id == second.node_id


def test_updateVector_weightAndMetadata(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        node_id = client.add_node(GRAPH, ["A"], {"embedding": Vector([1.0])}, {"v": 1})
        client.update_vector(GRAPH, node_id, "embedding", [9.0, 8.0])
        client.update_node_metadata(GRAPH, node_id, {"v": 2})

        other = client.add_node(GRAPH, ["B"], None, None)
        edge_id = client.add_edge(GRAPH, AddEdgeRequest(node_id, other, "T", 0.1, {"since": 2020}))
        client.update_weight(GRAPH, edge_id, 0.75)
        client.update_edge_metadata(GRAPH, edge_id, {"since": 2099})

        assert client.get_node(GRAPH, node_id).metadata == {"v": 2}
        assert client.get_edge(GRAPH, edge_id).weight == pytest.approx(0.75)
        assert client.get_edge(GRAPH, edge_id).metadata == {"since": 2099}
        assert client.get_nodes(GRAPH, [node_id], include_vectors=True)[0].vectors["embedding"] == (9.0, 8.0)


# ─── Reads that are vector-opt-in ──────────────────────────────────────────


def test_listNodes_omitsVectorsUnlessAsked(token_server: Any) -> None:
    """The default is deliberate: collecting vectors is the expensive part of building a node."""
    server = token_server()
    with _client(server) as client:
        client.add_node(GRAPH, ["A"], {"embedding": Vector([1.0, 2.0])}, {})

        without = client.list_nodes(GRAPH, ListNodesRequest())
        with_it = client.list_nodes(GRAPH, ListNodesRequest(include_vectors=True))

    assert without[0].vectors == {}
    assert with_it[0].vectors == {"embedding": (1.0, 2.0)}


def test_getNodes_collapsesDuplicates_andSkipsUnknownIds(token_server: Any) -> None:
    """A shorter result does not mean something was missing; compare against distinct ids sent."""
    server = token_server()
    with _client(server) as client:
        first  = client.add_node(GRAPH, ["A"], None, None)
        second = client.add_node(GRAPH, ["B"], None, None)
        found  = client.get_nodes(GRAPH, [first, first, second, 9999])

    assert [each.id for each in found] == [first, second]


def test_inducedSubgraph_keepsOnlyEdgesBetweenTheGivenNodes(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        a = client.add_node(GRAPH, ["A"], None, None)
        b = client.add_node(GRAPH, ["B"], None, None)
        c = client.add_node(GRAPH, ["C"], None, None)
        client.add_edge(GRAPH, AddEdgeRequest(a, b, "IN"))
        client.add_edge(GRAPH, AddEdgeRequest(b, c, "OUT"))

        window = client.induced_subgraph(GRAPH, [a, b])

    assert [each.id for each in window.nodes] == [a, b]
    assert [each.type for each in window.edges] == ["IN"], "the edge to c is outside the set"


# ─── Label filters ─────────────────────────────────────────────────────────


def test_labelFilter_noLabels_meansNoConstraint() -> None:
    assert to_label_expression([], LabelMatch.ALL, []) is None
    assert to_label_expression(None, LabelMatch.ANY, None) is None


def test_labelFilter_singleLabel_isABareLeaf() -> None:
    expression = to_label_expression(["Concept"], LabelMatch.ALL, [])
    assert expression.WhichOneof("expression") == "label"
    assert expression.label == "Concept"


@pytest.mark.parametrize(
    ("match", "expected"), [(LabelMatch.ALL, "and"), (LabelMatch.ANY, "or")]
)
def test_labelFilter_twoLabels_combineByTheMatchMode(match: LabelMatch, expected: str) -> None:
    assert to_label_expression(["A", "B"], match, []).WhichOneof("expression") == expected


def test_labelFilter_exclusionsAreAlwaysConjunctive_evenUnderAnyMatch() -> None:
    """The asymmetry worth pinning: "A or B, and not C" - never "A or B or not C".

    The wrong folding would not error; it would match very nearly everything.
    """
    expression = to_label_expression(["A", "B"], LabelMatch.ANY, ["C"])
    assert expression.WhichOneof("expression") == "and"

    conjunction = getattr(expression, "and")
    assert conjunction.left.WhichOneof("expression")  == "or"
    assert conjunction.right.WhichOneof("expression") == "not"
    assert getattr(conjunction.right, "not").label == "C"


def test_labelFilter_onlyExclusions_negatesEachOne() -> None:
    expression = to_label_expression([], LabelMatch.ALL, ["X"])
    assert expression.WhichOneof("expression") == "not"
    assert getattr(expression, "not").label == "X"


def test_labelFilter_rejectsNoneInsideTheList() -> None:
    with pytest.raises(ValueError, match="must not contain None"):
        to_label_expression(["A", None], LabelMatch.ALL, [])  # type: ignore[list-item]


def test_listNodes_sendsTheFoldedExpression(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        client.list_nodes(GRAPH, ListNodesRequest(labels=["A"], exclude_labels=["B"], sample_seed=42))

    sent = server.graph.requests[-1]
    assert sent.HasField("label_expression")
    assert sent.label_expression.WhichOneof("expression") == "and"
    assert sent.HasField("sample_seed") and sent.sample_seed == 42


# ─── Both facades ──────────────────────────────────────────────────────────


def test_bothFacades_agreeOnNodes(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        node_id  = client.add_node(GRAPH, ["A"], {"embedding": Vector([1.0])}, {"n": 1})
        blocking = client.get_node(GRAPH, node_id)

    async def awaited() -> Node:
        async with AsyncCyrockDbClient(host="127.0.0.1", port=server.port, api_key="api-key") as client:
            return await client.get_node(GRAPH, node_id)

    assert blocking == asyncio.run(awaited())


def test_bothFacades_agreeOnTheKeyedPath(token_server: Any) -> None:
    server = token_server()

    async def awaited() -> Node:
        async with AsyncCyrockDbClient(host="127.0.0.1", port=server.port, api_key="api-key") as client:
            await client.upsert_node(GRAPH, UpsertNodeRequest(labels=["A"], external_key="ak"))
            return await client.get_node(GRAPH, "ak")

    node = asyncio.run(awaited())
    assert node.external_key == "ak"
