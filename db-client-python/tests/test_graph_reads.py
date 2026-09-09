"""Graph search, traversal, expansion and recall.

Two of these pin a distinction the codebase has already been bitten by once: ``depth`` on a context
window is a hop count, and ``recency_hours`` on a recall is a time window. They used to be one field
with one name (issue #230), and the whole point of separating them is that the types now stop a
caller conflating them.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from cyrock_db import CyrockDbClient
from cyrock_db.aio import AsyncCyrockDbClient
from cyrock_db.types import (
    AddEdgeRequest,
    Direction,
    GraphRecallRequest,
    GraphSearchExpansionRequest,
    LabelMatch,
    NeighborsRequest,
    NodeMatch,
    ReasoningChainRequest,
    SearchSimilarRequest,
    TraverseRequest,
    Vector,
)

GRAPH = "graph-1"


def _client(server: Any) -> CyrockDbClient:
    return CyrockDbClient(host="127.0.0.1", port=server.port, api_key="api-key")


def _seed(client: CyrockDbClient, count: int = 3) -> list[int]:
    return [
        client.add_node(GRAPH, ["Concept"], {"embedding": Vector([float(i)])}, {"i": i})
        for i in range(count)
    ]


def test_searchSimilar_encodesTheQuery_andDecodesMatches(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        _seed(client)
        matches = client.search_similar(
            GRAPH, SearchSimilarRequest("embedding", (0.5,), 2, labels=["Concept"])
        )

    sent = server.graph.requests[-1]
    assert sent.field_name == "embedding"
    assert sent.HasField("max_results") and sent.max_results == 2
    assert sent.label_expression.label == "Concept"

    assert len(matches) == 2
    assert all(isinstance(each, NodeMatch) for each in matches)
    assert matches[0].score > matches[1].score
    assert matches[0].node.metadata["i"] == 0


def test_searchSimilar_foldsExclusionsIntoTheExpression(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        client.search_similar(
            GRAPH,
            SearchSimilarRequest("embedding", (1.0,), 5, labels=["A", "B"],
                                 label_match=LabelMatch.ANY, exclude_labels=["C"]),
        )

    expression = server.graph.requests[-1].label_expression
    assert expression.WhichOneof("expression") == "and"


def test_neighbors_encodesDirectionAndEdgeType(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        node_ids = _seed(client, 2)
        client.add_edge(GRAPH, AddEdgeRequest(node_ids[0], node_ids[1], "LINKS"))
        found = client.neighbors(
            GRAPH, NeighborsRequest(node_ids[0], Direction.OUTGOING, edge_type="LINKS")
        )

    sent = server.graph.requests[-1]
    assert sent.direction == "OUTGOING"
    assert sent.edge_type == "LINKS"
    assert len(found) == 2


def test_neighbors_omitsVectorsUnlessAsked(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        node_ids = _seed(client, 1)
        without  = client.neighbors(GRAPH, NeighborsRequest(node_ids[0]))
        with_it  = client.neighbors(GRAPH, NeighborsRequest(node_ids[0], include_vectors=True))

    assert without[0].vectors == {}
    assert with_it[0].vectors != {}


def test_traverse_encodesDepthAndDirection(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        node_ids = _seed(client, 2)
        client.traverse(GRAPH, TraverseRequest(node_ids[0], max_depth=3, direction=Direction.BOTH))

    sent = server.graph.requests[-1]
    assert sent.HasField("max_depth") and sent.max_depth == 3
    assert sent.direction == "BOTH"


def test_contextWindow_depthIsAHopCount(token_server: Any) -> None:
    """The field is `depth` on the wire and means hops. Contrast recall, below."""
    server = token_server()
    with _client(server) as client:
        _seed(client)
        nodes = client.context_window(GRAPH, GraphSearchExpansionRequest("embedding", (1.0,), 5, depth=2))

    sent = server.graph.requests[-1]
    assert sent.HasField("depth") and sent.depth == 2
    assert len(nodes) == 3


def test_contextWindowGraph_returnsEdgesToo(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        node_ids = _seed(client, 2)
        client.add_edge(GRAPH, AddEdgeRequest(node_ids[0], node_ids[1], "T"))
        window = client.context_window_graph(
            GRAPH, GraphSearchExpansionRequest("embedding", (1.0,), 5, depth=1)
        )

    assert len(window.nodes) == 2
    assert len(window.edges) == 1


def test_recall_recencyHoursIsATimeWindow_notADepth(token_server: Any) -> None:
    """Issue #230: recall read the shared `depth` as hours while contextWindow read it as hops.

    The proto field kept its number through the rename, so the guard that matters is the name.
    """
    server = token_server()
    with _client(server) as client:
        _seed(client)
        client.recall(GRAPH, GraphRecallRequest("embedding", (1.0,), 5, recency_hours=24))

    sent = server.graph.requests[-1]
    assert sent.HasField("recency_hours") and sent.recency_hours == 24
    assert not hasattr(sent, "depth"), "the old name is reserved and must not come back"


@pytest.mark.parametrize("hours", [0, -1])
def test_recall_nonPositiveRecencyWindow_isRejectedClientSide(hours: int) -> None:
    """A zero-hour window is older than every memory, so it would filter out every result."""
    with pytest.raises(ValueError, match="recency_hours must be positive"):
        GraphRecallRequest("embedding", (1.0,), 5, recency_hours=hours)


def test_recallGraph_returnsEdgesToo(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        node_ids = _seed(client, 2)
        client.add_edge(GRAPH, AddEdgeRequest(node_ids[0], node_ids[1], "T"))
        window = client.recall_graph(GRAPH, GraphRecallRequest("embedding", (1.0,), 5, recency_hours=1))

    assert len(window.nodes) == 2 and len(window.edges) == 1


def test_reasoningChain_sendsBothEndpoints(token_server: Any) -> None:
    """Issue #228 was to_id being read nowhere; the client at least has to send it."""
    server = token_server()
    with _client(server) as client:
        node_ids = _seed(client, 2)
        client.reasoning_chain(GRAPH, ReasoningChainRequest(node_ids[0], node_ids[1], max_depth=4))

    sent = server.graph.requests[-1]
    assert sent.HasField("from_id") and sent.from_id == node_ids[0]
    assert sent.to_id == node_ids[1]
    assert sent.HasField("max_depth") and sent.max_depth == 4


def test_reasoningChainGraph_returnsNodesAndEdges(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        node_ids = _seed(client, 2)
        client.add_edge(GRAPH, AddEdgeRequest(node_ids[0], node_ids[1], "T"))
        window = client.reasoning_chain_graph(GRAPH, ReasoningChainRequest(node_ids[0], node_ids[1], 4))

    assert len(window.nodes) == 2 and len(window.edges) == 1


def test_bothFacades_agreeOnSearchSimilar(token_server: Any) -> None:
    server  = token_server()
    request = SearchSimilarRequest("embedding", (1.0,), 3)
    with _client(server) as client:
        _seed(client)
        blocking = client.search_similar(GRAPH, request)

    async def awaited() -> tuple[NodeMatch, ...]:
        async with AsyncCyrockDbClient(host="127.0.0.1", port=server.port, api_key="api-key") as client:
            return await client.search_similar(GRAPH, request)

    assert blocking == asyncio.run(awaited())
