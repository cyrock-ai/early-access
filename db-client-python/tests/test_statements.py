"""CyQL statement execution and client-side routing."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from cyrock_db import CyrockDbClient
from cyrock_db.aio import AsyncCyrockDbClient
from cyrock_db.exceptions import CyrockDbClientException
from cyrock_db.types import QueryParameters, QueryResult, StatementClass, StatementResult, StatementType

GRAPH      = "graph-1"
COLLECTION = "collection-1"
PROJECT    = "project-1"


def _client(server: Any) -> CyrockDbClient:
    return CyrockDbClient(host="127.0.0.1", port=server.port, api_key="api-key")


def test_executeStatement_decodesAGraphResponse(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        result = client.execute_statement(GRAPH, "MATCH (n) RETURN n")

    assert isinstance(result, StatementResult)
    assert result.statement_class is StatementClass.READ_QUERY
    assert result.statement_type  is StatementType.MATCH
    assert result.columns == ("n",)
    assert result.rows    == ({"n": 1},)


def test_executeCollectionStatement_decodesACollectionResponse(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        result = client.execute_collection_statement(COLLECTION, "MATCH (d) RETURN d")

    assert result.rows == ({"d": 2},)


def test_executeProjectStatement_decodesAResponseWithNoSummaryField(token_server: Any) -> None:
    """ProjectStatementResponse has no `summary` at all, so the converter must not ask for one."""
    server = token_server()
    with _client(server) as client:
        result = client.execute_project_statement(PROJECT, "SHOW GRAPHS")

    assert result.statement_class is StatementClass.PROJECT_SCOPED_DDL
    assert result.statement_type  is StatementType.SHOW_GRAPHS
    assert result.summary is None


def test_parameters_areSplitIntoVectorsAndScalars(token_server: Any) -> None:
    server = token_server()
    params = QueryParameters.builder().vector("v", [1.0, 2.0]).param("n", 2**53 + 1).build()
    with _client(server) as client:
        client.execute_statement(GRAPH, "MATCH (n) SIMILAR TO $v RETURN n", params)

    sent = server.graph.requests[-1]
    assert list(sent.vectors["v"].values) == [1.0, 2.0]
    assert sent.parameters.fields["n"].int_value == 2**53 + 1, "a LONG must not go through a double"


def test_query_returnsRowsWithoutTheStatementMetadata(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        result = client.query(GRAPH, "MATCH (n) RETURN n")

    assert isinstance(result, QueryResult)
    assert result.columns == ("n",) and result.rows == ({"n": 1},)


def test_queryCollection_returnsRows(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        assert client.query_collection(COLLECTION, "MATCH (d) RETURN d").rows == ({"d": 2},)


# ─── Routing ───────────────────────────────────────────────────────────────


def test_execute_routesProjectDdlToThePlatformServer(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        result = client.execute(PROJECT, GRAPH, "SHOW GRAPHS")

    assert result.statement_class is StatementClass.PROJECT_SCOPED_DDL
    assert server.graph_defs.requests, "it should have gone to the definition service"


def test_execute_routesEverythingElseToTheGraph(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        result = client.execute(PROJECT, GRAPH, "MATCH (n) RETURN n")

    assert result.statement_class is StatementClass.READ_QUERY
    assert server.graph.requests[-1].graph_id == GRAPH


def test_execute_bareCreate_isADataWrite_notProjectDdl(token_server: Any) -> None:
    """The ambiguity the classifier reads two words to resolve."""
    server = token_server()
    with _client(server) as client:
        client.execute(PROJECT, GRAPH, "CREATE (n:Concept {title: 'x'})")

    assert server.graph.requests[-1].graph_id == GRAPH


def test_execute_projectDdlWithoutAProjectId_isRefusedBeforeItLeaves(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client, pytest.raises(CyrockDbClientException) as raised:
        client.execute(None, GRAPH, "SHOW GRAPHS")

    assert raised.value.status_code == 400
    assert "projectId" in raised.value.message


def test_execute_graphStatementWithoutAGraphId_isRefused(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client, pytest.raises(CyrockDbClientException) as raised:
        client.execute(PROJECT, None, "MATCH (n) RETURN n")

    assert raised.value.status_code == 400
    assert "graphId" in raised.value.message


def test_executeCollection_routesTheSameWay(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        client.execute_collection(PROJECT, COLLECTION, "SHOW COLLECTIONS")
        assert server.graph_defs.requests

        client.execute_collection(PROJECT, COLLECTION, "MATCH (d) RETURN d")
        assert server.docs.requests[-1].collection_id == COLLECTION

    with _client(server) as client, pytest.raises(CyrockDbClientException, match="collectionId"):
        client.execute_collection(PROJECT, None, "MATCH (d) RETURN d")


def test_bothFacades_routeIdentically(token_server: Any) -> None:
    server = token_server()
    with _client(server) as client:
        blocking = client.execute(PROJECT, GRAPH, "SHOW GRAPHS")

    async def awaited() -> StatementResult:
        async with AsyncCyrockDbClient(host="127.0.0.1", port=server.port, api_key="api-key") as client:
            return await client.execute(PROJECT, GRAPH, "SHOW GRAPHS")

    assert blocking == asyncio.run(awaited())


def test_bothFacades_refuseAMissingIdTheSameWay(token_server: Any) -> None:
    server = token_server()

    async def awaited() -> CyrockDbClientException:
        async with AsyncCyrockDbClient(host="127.0.0.1", port=server.port, api_key="api-key") as client:
            with pytest.raises(CyrockDbClientException) as raised:
                await client.execute(None, GRAPH, "SHOW GRAPHS")
            return raised.value

    assert asyncio.run(awaited()).status_code == 400
