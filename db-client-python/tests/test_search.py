"""Document search: what reaches the wire, and what comes back.

Ranking is the server's business, so these assert on the encoded request and on the decoded result,
not on which document scored highest.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from cyrock_db import CyrockDbClient
from cyrock_db.aio import AsyncCyrockDbClient
from cyrock_db.types import (
    AUTO_ASSIGN_ID,
    FusionStrategy,
    HybridSearchRequest,
    Match,
    MultiVectorSearchRequest,
    RerankOptions,
    SearchRequest,
    TextQuery,
    Vector,
    VectorQuery,
)

COLLECTION = "collection-1"


def _client(server: Any) -> CyrockDbClient:
    return CyrockDbClient(host="127.0.0.1", port=server.port, api_key="api-key")


def _seed(client: CyrockDbClient, count: int = 3) -> None:
    for index in range(count):
        client.upsert(COLLECTION, AUTO_ASSIGN_ID, {"embedding": Vector([float(index)])}, {"i": index})


def test_search_encodesTheRequest_andDecodesMatches(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        _seed(client)
        matches = client.search(
            COLLECTION, SearchRequest(vector_field="embedding", vector=[0.5, 0.25], max_results=2)
        )

    sent = server.docs.requests[-1]
    assert sent.vector_field     == "embedding"
    assert list(sent.vector)     == [0.5, 0.25]
    assert sent.HasField("max_results") and sent.max_results == 2

    assert len(matches) == 2
    assert all(isinstance(each, Match) for each in matches)
    assert matches[0].score > matches[1].score
    assert matches[0].document.metadata["i"] == 0


def test_search_aFilter_isSentOnlyWhenGiven(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        client.search(COLLECTION, SearchRequest("embedding", (1.0,), 5))
        assert server.docs.requests[-1].filter == ""

        client.search(COLLECTION, SearchRequest("embedding", (1.0,), 5, filter="i > 1"))
        assert server.docs.requests[-1].filter == "i > 1"


def test_search_rerankDisabled_isNotSentAtAll(token_server: Any) -> None:
    """An absent rerank message and a disabled one mean the same thing; not sending it is honest."""
    server = token_server()
    with _client(server) as client:
        client.search(COLLECTION, SearchRequest("embedding", (1.0,), 5))
        assert not server.docs.requests[-1].HasField("rerank")


def test_search_rerankEnabled_isSentInFull(token_server: Any) -> None:
    server = token_server()
    options = RerankOptions(enabled=True, model="m", field="body", candidates=64, query="cats")
    with _client(server) as client:
        client.search(COLLECTION, SearchRequest("embedding", (1.0,), 5, rerank=options))

    rerank = server.docs.requests[-1].rerank
    assert (rerank.enabled, rerank.model, rerank.field, rerank.candidates, rerank.query) == (
        True, "m", "body", 64, "cats",
    )


@pytest.mark.parametrize(
    ("top_n", "candidates", "expected"),
    [(5, 0, 50), (100, 0, 200), (30, 0, 120), (5, 7, 7)],
)
def test_rerankOptions_candidatePool_derivesFromTopN(top_n: int, candidates: int, expected: int) -> None:
    """4x top_n, clamped to [50, 200], unless an explicit count was given."""
    assert RerankOptions(candidates=candidates).candidate_pool(top_n) == expected


def test_multiSearch_encodesEveryLegAndItsWeight(token_server: Any) -> None:
    server = token_server()
    request = MultiVectorSearchRequest(
        queries=(VectorQuery("text", (1.0,), 0.7), VectorQuery("image", (2.0, 3.0), 0.3)),
        max_results=4,
        fusion=FusionStrategy.WEIGHTED_SCORE,
    )
    with _client(server) as client:
        client.multi_search(COLLECTION, request)

    sent = server.docs.requests[-1]
    # Weights and vectors are 32-bit floats on the wire, so 0.7 arrives as 0.699999988. Approximate
    # comparison is the correct assertion here, not a workaround: the narrowing is the wire format.
    assert [(q.field_name, list(q.vector)) for q in sent.queries] == [
        ("text", [1.0]),
        ("image", [2.0, 3.0]),
    ]
    assert [q.weight for q in sent.queries] == pytest.approx([0.7, 0.3])
    assert sent.fusion == "WEIGHTED_SCORE"
    assert sent.max_results == 4


def test_hybridSearch_encodesBothVectorAndTextLegs(token_server: Any) -> None:
    server = token_server()
    request = HybridSearchRequest(
        vector_queries=(VectorQuery("embedding", (1.0,), 1.0),),
        text_queries=(TextQuery("content", "machine learning", 2.0),),
        max_results=10,
    )
    with _client(server) as client:
        client.hybrid_search(COLLECTION, request)

    sent = server.docs.requests[-1]
    assert [(q.text_field, q.query) for q in sent.text_queries] == [("content", "machine learning")]
    assert sent.text_queries[0].weight == pytest.approx(2.0)
    assert len(sent.vector_queries) == 1
    assert sent.fusion == "RRF", "RRF is the default fusion, as in Java"


def test_defaultFusion_isRrf() -> None:
    assert MultiVectorSearchRequest(queries=(), max_results=1).fusion is FusionStrategy.RRF
    assert HybridSearchRequest().fusion is FusionStrategy.RRF


def test_bothFacades_returnTheSameMatches(token_server: Any) -> None:
    server  = token_server()
    request = SearchRequest("embedding", (1.0,), 3)
    with _client(server) as client:
        _seed(client)
        blocking = client.search(COLLECTION, request)

    async def awaited() -> tuple[Match, ...]:
        async with AsyncCyrockDbClient(host="127.0.0.1", port=server.port, api_key="api-key") as client:
            return await client.search(COLLECTION, request)

    assert blocking == asyncio.run(awaited())
