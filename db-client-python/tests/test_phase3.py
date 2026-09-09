"""Branching, the community layer, agentic memory and natural-language search."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from cyrock_db import CyrockDbClient
from cyrock_db.aio import AsyncCyrockDbClient
from cyrock_db.types import (
    DetectCommunitiesRequest,
    EntityLinkRequest,
    GetCommunityMembersRequest,
    GetCommunitySummariesRequest,
    GlobalSearchRequest,
    GraphDefinition,
    NlSearchRequest,
    ObserveRequest,
    PutCommunitySummaryRequest,
    RerankOptions,
    Vector,
)

GRAPH      = "graph-1"
COLLECTION = "collection-1"
PROJECT    = "project-1"


def _client(server: Any) -> CyrockDbClient:
    return CyrockDbClient(host="127.0.0.1", port=server.port, api_key="api-key")


# ─── Branching ─────────────────────────────────────────────────────────────


def test_forkGraph_returnsABranchCarryingItsLineage(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        parent = client.create_graph(PROJECT, GraphDefinition(name="base"))
        branch = client.fork_graph(PROJECT, parent.id, "experiment-1")

    assert branch.parent_graph_id == parent.id
    assert branch.branch_name     == "experiment-1"
    assert branch.is_branch()     is True
    assert parent.is_branch()     is False


def test_listBranches_returnsOnlyThatGraphsBranches(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        first  = client.create_graph(PROJECT, GraphDefinition(name="a"))
        second = client.create_graph(PROJECT, GraphDefinition(name="b"))
        client.fork_graph(PROJECT, first.id, "b1")
        client.fork_graph(PROJECT, second.id, "b2")

        branches = client.list_branches(PROJECT, first.id)

    assert [each.branch_name for each in branches] == ["b1"]


def test_mergeGraph_reportsWhatChanged(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        result = client.merge_graph(PROJECT, "branch-0")

    assert (result.nodes_added, result.nodes_removed, result.nodes_updated) == (2, 1, 3)
    assert (result.edges_added, result.edges_removed, result.edges_updated) == (4, 0, 1)


# ─── Communities ───────────────────────────────────────────────────────────


def test_detectCommunities_returnsTheHierarchy(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        hierarchy = client.detect_communities(
            GRAPH, DetectCommunitiesRequest(algorithm="leiden", resolution=1.0, max_levels=3, seed=42)
        )

    sent = server.graph.requests[-1]
    assert (sent.algorithm, sent.max_levels, sent.seed) == ("leiden", 3, 42)
    assert hierarchy.levels == 1
    assert hierarchy.communities[0].id == 7
    assert hierarchy.communities[0].member_node_ids == (1, 2)


def test_getCommunities_omitsMembersUnlessAsked(token_server: Any) -> None:
    """Issue #320: reading a hierarchy used to load every node id whether or not it was wanted."""
    server = token_server()
    with _client(server) as client:
        without = client.get_communities(GRAPH, max_level=2)
        with_it = client.get_communities(GRAPH, max_level=2, include_members=True)

    assert without.communities[0].member_node_ids == ()
    assert with_it.communities[0].member_node_ids == (1, 2)
    assert with_it.communities[0].size == 2, "size is reported either way"


def test_putCommunitySummary_goesThroughTheAtomicBatchPath(token_server: Any) -> None:
    """Issue #319: a batch that failed part-way used to leave earlier items written."""
    server = token_server()
    with _client(server) as client:
        one = client.put_community_summary(
            GRAPH, PutCommunitySummaryRequest(0, 7, "a theme", {"embedding": (1.0, 2.0)})
        )

    assert one == 200
    sent = server.graph.requests[-1]
    assert len(sent.summaries) == 1, "the single write uses the batch RPC"
    assert list(sent.summaries[0].vectors["embedding"].values) == [1.0, 2.0]


def test_putCommunitySummaries_returnsIdsInOrder(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        ids = client.put_community_summaries(GRAPH, [
            PutCommunitySummaryRequest(0, 1, "one"),
            PutCommunitySummaryRequest(0, 2, "two"),
        ])

    assert ids == (200, 201)


@pytest.mark.parametrize(
    ("vectors", "expected"),
    [
        ({"e": ()},        "must not be None or empty"),
        ({"e": None},      "must not be None or empty"),
        ({"  ": (1.0,)},   "must not be None or blank"),
        ({None: (1.0,)},   "must not be None or blank"),
    ],
)
def test_putCommunitySummary_rejectsBadVectors(vectors: dict, expected: str) -> None:
    """The same guard QueryParameters carries, for the same reason (issue #383)."""
    with pytest.raises(ValueError, match=expected):
        PutCommunitySummaryRequest(0, 1, "text", vectors)


def test_getCommunitySummaries_reportsTruncation(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        client.put_community_summaries(GRAPH, [
            PutCommunitySummaryRequest(0, 1, "one"), PutCommunitySummaryRequest(0, 2, "two"),
        ])
        all_of_them = client.get_community_summaries(GRAPH, GetCommunitySummariesRequest(level=0))
        just_one    = client.get_community_summaries(
            GRAPH, GetCommunitySummariesRequest(level=0, limit=1)
        )

    assert len(all_of_them.summaries) == 2 and all_of_them.truncated is False
    assert len(just_one.summaries)    == 1 and just_one.truncated    is True


def test_getCommunityMembers_carriesAPerSetTruncationFlag(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        sets = client.get_community_members(
            GRAPH, GetCommunityMembersRequest(level=0, community_ids=[7], limit=1)
        )

    assert len(sets) == 1
    assert sets[0].community_id == 7
    assert sets[0].truncated is True


def test_getCommunityAssignments_mapsNodesToCommunities(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        assignments = client.get_community_assignments(GRAPH, level=0, node_ids=[1, 2, 3])

    assert assignments.by_node == {1: 7, 2: 7, 3: 7}
    assert assignments.levels == 1


def test_globalSearch_encodesTheRequest_andRanksCommunities(token_server: Any) -> None:
    server = token_server()
    request = GlobalSearchRequest(
        query="what themes", level=1, top_k=5, include_members=True,
        max_members_per_community=10, expand=True, expand_depth=2,
        rerank=RerankOptions(enabled=True, query="what themes"),
    )
    with _client(server) as client:
        results = client.global_search(GRAPH, request)

    sent = server.graph.requests[-1]
    assert (sent.query, sent.level, sent.top_k) == ("what themes", 1, 5)
    assert sent.include_members and sent.expand and sent.expand_depth == 2
    assert sent.rerank.enabled is True, "one RerankOptionsProto serves all three search surfaces"

    assert results[0].community_id == 7
    assert results[0].member_node_ids == (1, 2)


def test_refreshCommunities_reportsPrunedSummariesAndStaleRefs(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        result = client.refresh_communities(GRAPH, DetectCommunitiesRequest(algorithm="leiden"))

    assert result.pruned_summaries == 3
    assert result.stale_communities[0].community_id == 9
    assert result.hierarchy.levels == 1


def test_communityStatus_reflectsWhatHasHappened(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        before = client.community_status(GRAPH)
        client.detect_communities(GRAPH, DetectCommunitiesRequest(algorithm="leiden"))
        client.put_community_summary(GRAPH, PutCommunitySummaryRequest(0, 7, "x"))
        after = client.community_status(GRAPH)

    assert before.detected is False
    assert after.detected  is True
    assert after.summary_count == 1


# ─── Agentic memory ────────────────────────────────────────────────────────


def test_observe_storesAndReportsTheLinksItMade(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        result = client.observe(GRAPH, ObserveRequest(
            labels=["Memory"], vectors={"embedding": Vector([1.0])},
            link_field="embedding", threshold=0.9, max_links=10, metadata={"said": "hello"},
        ))

    sent = server.graph.requests[-1]
    assert sent.link_field == "embedding"
    assert sent.threshold == pytest.approx(0.9)
    assert sent.max_links == 10, "issue #229: linkField, threshold and maxLinks must reach the wire"

    assert result.linked_edge_ids == (501, 502)


def test_observeResult_namesEdgeIds_notNodeIds(token_server: Any) -> None:
    """The wire field is `linked_ids`; the domain name says which ids those are.

    Worth a test rather than only a comment: the ids identify the auto-link *edges*, and a caller who
    reads them as node ids gets plausible-looking numbers that address the wrong entities.
    """
    server = token_server()
    with _client(server) as client:
        result = client.observe(GRAPH, ObserveRequest(labels=["M"]))

    assert result.linked_edge_ids == (501, 502)
    assert result.node_id not in result.linked_edge_ids, (
        "the node id and the edge ids are different id spaces"
    )


def test_entityLink_returnsTheEdgesItCreated(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        edges = client.entity_link(GRAPH, EntityLinkRequest("embedding", 1, 0.8, 5))

    assert edges[0].type == "SIMILAR"
    assert edges[0].source_id == 1


def test_decay_reportsWhatItPruned(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        result = client.decay(GRAPH, 720)

    assert server.graph.requests[-1].max_age_hours == 720
    assert (result.pruned_nodes, result.pruned_edges) == (2, 3)


# ─── Natural-language search ───────────────────────────────────────────────


def test_nlSearchGraph_returnsMatchesAndTheTranslatedQuery(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        result = client.nl_search_graph(GRAPH, NlSearchRequest("cats on mats", "embedding", 5))

    sent = server.nl.requests[-1]
    assert (sent.query, sent.vector_field, sent.max_results) == ("cats on mats", "embedding", 5)
    assert result.translated_query == "translated:cats on mats"
    assert result.query_type == "SEMANTIC"
    assert result.matches[0].metadata == {"t": "x"}


def test_nlSearchCollection_usesTheCollectionEndpoint(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        client.nl_search_collection(COLLECTION, NlSearchRequest("q", "embedding", 3))

    assert server.nl.requests[-1].collection_id == COLLECTION


# ─── Both facades ──────────────────────────────────────────────────────────


def test_bothFacades_agreeAcrossPhase3(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        blocking = (
            client.detect_communities(GRAPH, DetectCommunitiesRequest(algorithm="leiden")),
            client.community_status(GRAPH),
            client.decay(GRAPH, 24),
            client.nl_search_graph(GRAPH, NlSearchRequest("q", "embedding", 1)),
        )

    async def awaited() -> tuple[Any, ...]:
        async with AsyncCyrockDbClient(host="127.0.0.1", port=server.port, api_key="api-key") as client:
            return (
                await client.detect_communities(GRAPH, DetectCommunitiesRequest(algorithm="leiden")),
                await client.community_status(GRAPH),
                await client.decay(GRAPH, 24),
                await client.nl_search_graph(GRAPH, NlSearchRequest("q", "embedding", 1)),
            )

    assert blocking == asyncio.run(awaited())
