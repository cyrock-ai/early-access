"""The asyncio client.

The Python face of ``CyrockDbAsyncClient``: every operation the synchronous client has, awaited
rather than blocking. What it buys is what the Java one buys - **concurrency without threads**. The
synchronous client parks a thread for every round trip, so fifty searches at once wants fifty
threads doing nothing but waiting; here they are in flight on one connection and none waits.

**Where it diverges from Java, and why.** In Java, ``client.async()`` returns a view sharing the
synchronous client's channel, credentials and lifecycle - one connection, one ``close()``. Python
cannot do that: ``grpc.Channel`` and ``grpc.aio.Channel`` are separate objects, and an aio channel
must be created on the running event loop. So this is a separately constructed, separately closed
client rather than a view, and there is no ``.async()`` to reach it by. A reader coming from the
Java client will look for one; this is the place they will not find it.

**Ordering.** Two coroutines started together have no order - a read fired alongside its own write
may not see it. Await the first before starting the second when the order is the point. Concurrent
writes to one collection apply in arrival order, not submission order.

**Thread-safe** in the asyncio sense: one instance serves a whole application, on its own loop.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping, Sequence
from types import TracebackType
from typing import Any

import grpc

from . import _proto_converters as converters
from . import _proto_requests as requests
from ._auth import (
    TOKEN_EXCHANGE_METHOD,
    AsyncAuthInterceptor,
    api_key_header,
    bearer,
    uses_api_key,
)
from ._channel import ClientOptions
from ._cyql_routing import is_project_scoped
from ._proto import cyrock_db_cdc_pb2 as cdc_pb2
from ._proto import cyrock_db_cdc_pb2_grpc as cdc_grpc
from ._proto import cyrock_db_data_pb2_grpc as data_grpc
from ._proto import cyrock_db_graph_pb2_grpc as graph_grpc
from ._proto import cyrock_db_nlsearch_pb2_grpc as nlsearch_grpc
from ._proto import cyrock_db_platform_pb2 as platform_pb2
from ._proto import cyrock_db_platform_pb2_grpc as platform_grpc
from ._token import AsyncTokenManager
from ._watch import watch_request
from .exceptions import CyrockDbClientException, NotFoundException, from_rpc_error
from .types import (
    AddEdgeRequest,
    ChangeEvent,
    CollectionDefinition,
    CollectionOperation,
    CommunityAssignments,
    CommunityHierarchy,
    CommunityMemberSet,
    CommunityStatus,
    CommunitySummaries,
    DecayResult,
    DetectCommunitiesRequest,
    Document,
    Edge,
    EntityLinkRequest,
    GetCommunityMembersRequest,
    GetCommunitySummariesRequest,
    GlobalSearchRequest,
    GlobalSearchResult,
    GraphDefinition,
    GraphOperation,
    GraphRecallRequest,
    GraphSearchExpansionRequest,
    GraphWindow,
    HybridSearchRequest,
    ListNodesRequest,
    Match,
    MergeResult,
    MultiVectorSearchRequest,
    NeighborsRequest,
    NeighborsWindow,
    NlSearchRequest,
    NlSearchResult,
    Node,
    NodeMatch,
    ObserveRequest,
    ObserveResult,
    PutCommunitySummaryRequest,
    QueryParameters,
    QueryResult,
    ReasoningChainRequest,
    RefreshCommunitiesResult,
    SearchRequest,
    SearchSimilarRequest,
    StatementResult,
    TransactionResult,
    TraverseRequest,
    UpsertNodeRequest,
    UpsertNodeResult,
    UpsertResult,
    VectorInput,
    WatchOptions,
)

__all__ = ["AsyncCyrockDbClient"]


class AsyncCyrockDbClient:
    """An asyncio connection to CYROCK.AI DB.

    Use as an async context manager, or await :meth:`close`::

        async with AsyncCyrockDbClient(api_key="...") as client:
            collection = await client.create_collection(project_id, definition)
    """

    def __init__(self, **options: Any) -> None:
        self._options = ClientOptions(**options)

        credentials  = self._options.credentials()
        arguments    = self._options.channel_arguments()
        interceptors = []
        if self._options.api_key is not None:
            # One channel, with the interceptor stepping aside for the exchange that produces the
            # token. grpc.aio takes interceptors at construction and has no equivalent of
            # grpc.intercept_channel, so the synchronous client's two-views-of-one-channel split is
            # not available here.
            interceptors.append(
                AsyncAuthInterceptor(self._metadata, frozenset({TOKEN_EXCHANGE_METHOD}))
            )

        self._channel: grpc.aio.Channel = (
            grpc.aio.insecure_channel(self._options.target, options=arguments, interceptors=interceptors)
            if credentials is None
            else grpc.aio.secure_channel(
                self._options.target, credentials, options=arguments, interceptors=interceptors
            )
        )

        self._tokens = (
            AsyncTokenManager(self._channel, self._options.api_key)
            if self._options.api_key is not None
            else None
        )
        # See the note in _token.py: protoc types the _pb2 messages but not the _pb2_grpc service
        # stubs, so every generated stub constructor is untyped under --strict.
        self._collection_stub = platform_grpc.CollectionDefinitionGrpcServiceStub(  # type: ignore[no-untyped-call]
            self._channel
        )
        self._document_stub = data_grpc.DocumentGrpcServiceStub(self._channel)  # type: ignore[no-untyped-call]
        self._graph_stub = graph_grpc.GraphGrpcServiceStub(self._channel)  # type: ignore[no-untyped-call]
        self._graph_definition_stub = platform_grpc.GraphDefinitionGrpcServiceStub(  # type: ignore[no-untyped-call]
            self._channel
        )
        self._nl_search_stub = nlsearch_grpc.NlSearchGrpcServiceStub(self._channel)  # type: ignore[no-untyped-call]
        self._cdc_stub = cdc_grpc.ChangeStreamGrpcServiceStub(self._channel)  # type: ignore[no-untyped-call]

    async def _metadata(self, method: str) -> list[tuple[str, str]]:
        """The credential for one call. Per service, not per plane - see ``API_KEY_SERVICES``."""
        assert self._tokens is not None  # noqa: S101 - only installed when there is a token manager
        assert self._options.api_key is not None  # noqa: S101 - as above
        if uses_api_key(method):
            return [api_key_header(self._options.api_key)]
        return [bearer(await self._tokens.token())]

    # ─── Lifecycle ──────────────────────────────────────────────────────────

    async def close(self) -> None:
        """Closes the connection. Idempotent."""
        await self._channel.close()

    async def __aenter__(self) -> AsyncCyrockDbClient:
        return self

    async def __aexit__(
        self,
        exc_type:  type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.close()

    # ─── Collection definitions ─────────────────────────────────────────────

    async def create_collection(self, project_id: str, definition: CollectionDefinition) -> CollectionDefinition:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.create_collection`."""
        return converters.to_collection_definition(
            await self._invoke(
                self._collection_stub.Create, requests.create_collection(project_id, definition)
            )
        )

    async def get_collection(self, collection_id: str) -> CollectionDefinition:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.get_collection`."""
        listed = await self._invoke(self._collection_stub.ListAll, platform_pb2.Empty())

        for candidate in listed.collections:
            if candidate.id == collection_id:
                return converters.to_collection_definition(candidate)
        raise NotFoundException(f"Collection not found: {collection_id}")

    async def list_collections(self, project_id: str) -> tuple[CollectionDefinition, ...]:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.list_collections`."""
        return converters.to_collection_definitions(
            await self._invoke(
                self._collection_stub.ListForProject, requests.project_id_request(project_id)
            )
        )

    async def delete_collection(self, project_id: str, collection_id: str) -> CollectionDefinition:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.delete_collection`."""
        return converters.to_collection_definition(
            await self._invoke(
                self._collection_stub.Delete,
                requests.collection_id_request(project_id, collection_id),
            )
        )

    async def rename_collection(self, collection_id: str, new_name: str) -> CollectionDefinition:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.rename_collection`."""
        return converters.to_collection_definition(
            await self._invoke(
                self._collection_stub.Update,
                requests.update_collection(collection_id, new_name),
            )
        )

    # ─── Documents ──────────────────────────────────────────────────────────

    async def upsert(
        self,
        collection_id: str,
        document_id:   int,
        vectors:       Mapping[str, VectorInput] | None = None,
        metadata:      Mapping[str, Any] | None         = None,
    ) -> int:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.upsert`."""
        response = await self._invoke(
            self._document_stub.Upsert,
            requests.upsert_document(collection_id, document_id, vectors, metadata),
        )
        return int(response.id)

    async def upsert_batch(self, collection_id: str, documents: Sequence[Document]) -> tuple[int, ...]:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.upsert_batch`."""
        response = await self._invoke(
            self._document_stub.UpsertBatch, requests.upsert_documents_batch(collection_id, documents)
        )
        return tuple(response.ids)

    async def get_by_id(self, collection_id: str, document_id: int) -> Document:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.get_by_id`."""
        return converters.to_document(
            await self._invoke(
                self._document_stub.GetById, requests.get_document_by_id(collection_id, document_id)
            )
        )

    async def list(self, collection_id: str, offset: int, limit: int) -> tuple[Document, ...]:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.list`."""
        return converters.to_documents(
            await self._invoke(
                self._document_stub.List, requests.list_documents(collection_id, offset, limit)
            )
        )

    async def delete(self, collection_id: str, document_id: int) -> Document:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.delete`."""
        return converters.to_document(
            await self._invoke(
                self._document_stub.Delete, requests.delete_document(collection_id, document_id)
            )
        )

    async def upsert_document(
        self,
        collection_id: str,
        external_key:  str,
        vectors:       Mapping[str, VectorInput] | None = None,
        metadata:      Mapping[str, Any] | None         = None,
    ) -> UpsertResult:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.upsert_document`."""
        response = await self._invoke(
            self._document_stub.UpsertByKey,
            requests.upsert_document_by_key(collection_id, external_key, vectors, metadata),
        )
        return UpsertResult(id=response.id, created=response.created)

    async def get_document(self, collection_id: str, external_key: str) -> Document:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.get_document`."""
        return converters.to_document(
            await self._invoke(
                self._document_stub.GetByKey, requests.get_document_by_key(collection_id, external_key)
            )
        )

    async def remove_document(self, collection_id: str, external_key: str) -> Document:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.remove_document`."""
        return converters.to_document(
            await self._invoke(
                self._document_stub.RemoveByKey,
                requests.remove_document_by_key(collection_id, external_key),
            )
        )


    # ─── Document search ────────────────────────────────────────────────────

    async def search(self, collection_id: str, request: SearchRequest) -> tuple[Match, ...]:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.search`."""
        return converters.to_matches(
            await self._invoke(self._document_stub.Search, requests.search(collection_id, request))
        )

    async def multi_search(
        self, collection_id: str, request: MultiVectorSearchRequest
    ) -> tuple[Match, ...]:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.multi_search`."""
        return converters.to_matches(
            await self._invoke(
                self._document_stub.MultiSearch, requests.multi_search(collection_id, request)
            )
        )

    async def hybrid_search(
        self, collection_id: str, request: HybridSearchRequest
    ) -> tuple[Match, ...]:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.hybrid_search`."""
        return converters.to_matches(
            await self._invoke(
                self._document_stub.HybridSearch, requests.hybrid_search(collection_id, request)
            )
        )


    # ─── Graph definitions ──────────────────────────────────────────────────

    async def create_graph(self, project_id: str, definition: GraphDefinition) -> GraphDefinition:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.create_graph`."""
        return converters.to_graph_definition(
            await self._invoke(
                self._graph_definition_stub.Create, requests.create_graph(project_id, definition)
            )
        )

    async def get_graph(self, graph_id: str) -> GraphDefinition:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.get_graph`."""
        listed = await self._invoke(self._graph_definition_stub.ListAll, platform_pb2.Empty())
        for candidate in listed.graphs:
            if candidate.id == graph_id:
                return converters.to_graph_definition(candidate)
        raise NotFoundException(f"Graph not found: {graph_id}")

    async def list_graphs(self, project_id: str) -> tuple[GraphDefinition, ...]:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.list_graphs`."""
        return converters.to_graph_definitions(
            await self._invoke(
                self._graph_definition_stub.ListForProject, requests.project_id_request(project_id)
            )
        )

    async def delete_graph(self, project_id: str, graph_id: str) -> GraphDefinition:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.delete_graph`."""
        return converters.to_graph_definition(
            await self._invoke(
                self._graph_definition_stub.Delete, requests.graph_id_request(project_id, graph_id)
            )
        )

    # ─── Graph nodes and edges ──────────────────────────────────────────────

    async def add_node(
        self,
        graph_id: str,
        labels:   Sequence[str],
        vectors:  Mapping[str, VectorInput] | None = None,
        metadata: Mapping[str, Any] | None         = None,
    ) -> int:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.add_node`."""
        response = await self._invoke(
            self._graph_stub.AddNode, requests.add_node(graph_id, labels, vectors, metadata)
        )
        return int(response.node_id)

    async def add_edge(self, graph_id: str, request: AddEdgeRequest) -> int:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.add_edge`."""
        response = await self._invoke(self._graph_stub.AddEdge, requests.add_edge(graph_id, request))
        return int(response.edge_id)

    async def get_node(self, graph_id: str, node: int | str) -> Node:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.get_node`."""
        if isinstance(node, str):
            response = await self._invoke(
                self._graph_stub.GetNodeByKey, requests.get_node_by_key(graph_id, node)
            )
        else:
            response = await self._invoke(self._graph_stub.GetNode, requests.get_node(graph_id, node))
        return converters.to_node(response.node)

    async def get_edge(self, graph_id: str, edge_id: int) -> Edge:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.get_edge`."""
        response = await self._invoke(self._graph_stub.GetEdge, requests.get_edge(graph_id, edge_id))
        return converters.to_edge(response.edge)

    async def remove_node(self, graph_id: str, node: int | str) -> None:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.remove_node`."""
        if isinstance(node, str):
            await self._invoke(
                self._graph_stub.RemoveNodeByKey, requests.remove_node_by_key(graph_id, node)
            )
        else:
            await self._invoke(self._graph_stub.RemoveNode, requests.remove_node(graph_id, node))

    async def remove_edge(self, graph_id: str, edge_id: int) -> None:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.remove_edge`."""
        await self._invoke(self._graph_stub.RemoveEdge, requests.remove_edge(graph_id, edge_id))

    async def update_vector(
        self, graph_id: str, node_id: int, field_name: str, vector: Sequence[float]
    ) -> None:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.update_vector`."""
        await self._invoke(
            self._graph_stub.UpdateVector, requests.update_vector(graph_id, node_id, field_name, vector)
        )

    async def update_weight(self, graph_id: str, edge_id: int, weight: float) -> None:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.update_weight`."""
        await self._invoke(
            self._graph_stub.UpdateWeight, requests.update_weight(graph_id, edge_id, weight)
        )

    async def update_node_metadata(
        self, graph_id: str, node_id: int, metadata: Mapping[str, Any]
    ) -> None:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.update_node_metadata`."""
        await self._invoke(
            self._graph_stub.UpdateNodeMetadata,
            requests.update_node_metadata(graph_id, node_id, metadata),
        )

    async def update_edge_metadata(
        self, graph_id: str, edge_id: int, metadata: Mapping[str, Any]
    ) -> None:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.update_edge_metadata`."""
        await self._invoke(
            self._graph_stub.UpdateEdgeMetadata,
            requests.update_edge_metadata(graph_id, edge_id, metadata),
        )

    async def list_nodes(self, graph_id: str, request: ListNodesRequest) -> tuple[Node, ...]:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.list_nodes`."""
        return converters.to_nodes(
            await self._invoke(self._graph_stub.ListNodes, requests.list_nodes(graph_id, request))
        )

    async def get_nodes(
        self, graph_id: str, node_ids: Sequence[int], include_vectors: bool = False
    ) -> tuple[Node, ...]:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.get_nodes`."""
        return converters.to_nodes(
            await self._invoke(
                self._graph_stub.GetNodes, requests.get_nodes(graph_id, node_ids, include_vectors)
            )
        )

    async def induced_subgraph(
        self, graph_id: str, node_ids: Sequence[int], include_vectors: bool = False
    ) -> GraphWindow:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.induced_subgraph`."""
        return converters.to_graph_window(
            await self._invoke(
                self._graph_stub.InducedSubgraph,
                requests.induced_subgraph(graph_id, node_ids, include_vectors),
            )
        )

    async def upsert_node(self, graph_id: str, request: UpsertNodeRequest) -> UpsertNodeResult:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.upsert_node`."""
        response = await self._invoke(
            self._graph_stub.UpsertNode, requests.upsert_node(graph_id, request)
        )
        return UpsertNodeResult(node_id=response.node_id, created=response.created)


    # ─── Graph search and traversal ─────────────────────────────────────────

    async def search_similar(self, graph_id: str, request: SearchSimilarRequest) -> tuple[NodeMatch, ...]:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.search_similar`."""
        return converters.to_node_matches(
            await self._invoke(self._graph_stub.SearchSimilar, requests.search_similar(graph_id, request))
        )

    async def neighbors(self, graph_id: str, request: NeighborsRequest) -> tuple[Node, ...]:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.neighbors`."""
        return converters.to_nodes(
            await self._invoke(self._graph_stub.Neighbors, requests.neighbors(graph_id, request))
        )

    async def neighbors_graph(self, graph_id: str, request: NeighborsRequest) -> NeighborsWindow:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.neighbors_graph`."""
        return converters.to_neighbors_window(
            await self._invoke(self._graph_stub.Neighbors, requests.neighbors(graph_id, request))
        )

    async def traverse(self, graph_id: str, request: TraverseRequest) -> tuple[Node, ...]:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.traverse`."""
        return converters.to_nodes(
            await self._invoke(self._graph_stub.Traverse, requests.traverse(graph_id, request))
        )

    async def context_window(self, graph_id: str, request: GraphSearchExpansionRequest) -> tuple[Node, ...]:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.context_window`."""
        return converters.to_nodes(
            await self._invoke(self._graph_stub.ContextWindow, requests.context_window(graph_id, request))
        )

    async def context_window_graph(self, graph_id: str, request: GraphSearchExpansionRequest) -> GraphWindow:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.context_window_graph`."""
        return converters.to_graph_window(
            await self._invoke(self._graph_stub.ContextWindow, requests.context_window(graph_id, request))
        )

    async def recall(self, graph_id: str, request: GraphRecallRequest) -> tuple[Node, ...]:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.recall`."""
        return converters.to_nodes(
            await self._invoke(self._graph_stub.Recall, requests.recall(graph_id, request))
        )

    async def recall_graph(self, graph_id: str, request: GraphRecallRequest) -> GraphWindow:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.recall_graph`."""
        return converters.to_graph_window(
            await self._invoke(self._graph_stub.Recall, requests.recall(graph_id, request))
        )

    async def reasoning_chain(self, graph_id: str, request: ReasoningChainRequest) -> tuple[Node, ...]:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.reasoning_chain`."""
        return converters.to_nodes(
            await self._invoke(self._graph_stub.ReasoningChain, requests.reasoning_chain(graph_id, request))
        )

    async def reasoning_chain_graph(self, graph_id: str, request: ReasoningChainRequest) -> GraphWindow:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.reasoning_chain_graph`."""
        return converters.to_graph_window(
            await self._invoke(self._graph_stub.ReasoningChain, requests.reasoning_chain(graph_id, request))
        )


    # ─── Transactions ───────────────────────────────────────────────────────

    async def execute_document_transaction(
        self, collection_id: str, operations: Sequence[CollectionOperation]
    ) -> TransactionResult:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.execute_document_transaction`."""
        return converters.to_transaction_result(
            await self._invoke(
                self._document_stub.ExecuteTransaction,
                requests.execute_document_transaction(collection_id, operations),
            )
        )

    async def execute_transaction(
        self, graph_id: str, operations: Sequence[GraphOperation]
    ) -> TransactionResult:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.execute_transaction`."""
        return converters.to_transaction_result(
            await self._invoke(
                self._graph_stub.ExecuteTransaction,
                requests.execute_transaction(graph_id, operations),
            )
        )


    # ─── CyQL statements ────────────────────────────────────────────────────

    async def execute_statement(
        self, graph_id: str, statement: str, params: QueryParameters | None = None
    ) -> StatementResult:
        """Executes a CyQL statement against a graph: reads, writes and ALTER GRAPH.

        :raises CyrockDbClientException: if the server returns an error
        """
        return converters.to_statement_result(
            await self._invoke(
                self._graph_stub.ExecuteStatement,
                requests.execute_statement(graph_id, statement, params),
            )
        )

    async def execute_collection_statement(
        self, collection_id: str, statement: str, params: QueryParameters | None = None
    ) -> StatementResult:
        """Executes a CyQL statement against a collection.

        :raises CyrockDbClientException: if the server returns an error
        """
        return converters.to_statement_result(
            await self._invoke(
                self._document_stub.ExecuteStatement,
                requests.execute_collection_statement(collection_id, statement, params),
            )
        )

    async def execute_project_statement(
        self, project_id: str, statement: str, params: QueryParameters | None = None
    ) -> StatementResult:
        """Executes project-scoped DDL: CREATE/DROP GRAPH, SHOW, DESCRIBE.

        :raises CyrockDbClientException: if the server returns an error
        """
        return converters.to_statement_result(
            await self._invoke(
                self._graph_definition_stub.ExecuteStatement,
                requests.execute_project_statement(project_id, statement, params),
            )
        )

    async def execute(
        self,
        project_id: str | None,
        graph_id:   str | None,
        statement:  str,
        params:     QueryParameters | None = None,
    ) -> StatementResult:
        """Routes a statement to the right endpoint by reading its leading keywords.

        Project-scoped DDL goes to the platform server, which owns the definitions; everything else
        goes to the graph. See :mod:`cyrock_db._cyql_routing` for what "reading its keywords" does
        and does not cover.

        :raises CyrockDbClientException: 400 if the statement needs an id this call did not supply
        """
        if is_project_scoped(statement):
            if project_id is None:
                raise CyrockDbClientException(400, "Statement is project-scoped; a projectId is required")
            return await self.execute_project_statement(project_id, statement, params)
        if graph_id is None:
            raise CyrockDbClientException(400, "Statement is graph-scoped; a graphId is required")
        return await self.execute_statement(graph_id, statement, params)

    async def execute_collection(
        self,
        project_id:    str | None,
        collection_id: str | None,
        statement:     str,
        params:        QueryParameters | None = None,
    ) -> StatementResult:
        """Routes a statement to the platform server or to a collection. See :meth:`execute`.

        :raises CyrockDbClientException: 400 if the statement needs an id this call did not supply
        """
        if is_project_scoped(statement):
            if project_id is None:
                raise CyrockDbClientException(400, "Statement is project-scoped; a projectId is required")
            return await self.execute_project_statement(project_id, statement, params)
        if collection_id is None:
            raise CyrockDbClientException(
                400, "Statement is collection-scoped; a collectionId is required"
            )
        return await self.execute_collection_statement(collection_id, statement, params)

    async def query(
        self, graph_id: str, query: str, params: QueryParameters | None = None
    ) -> QueryResult:
        """Runs a read query against a graph and returns its rows.

        Unlike the Java client, this does not parse the statement first to reject a write before it
        leaves. Python has no CyQL parser here, so the statement is sent and the server answers - a
        write sent to this method fails on the server rather than in the client, with the server's
        own message.

        :raises CyrockDbClientException: if the server returns an error
        """
        return (await self.execute_statement(graph_id, query, params)).to_query_result()

    async def query_collection(
        self, collection_id: str, query: str, params: QueryParameters | None = None
    ) -> QueryResult:
        """Runs a read query against a collection. See :meth:`query`.

        :raises CyrockDbClientException: if the server returns an error
        """
        return (
            await self.execute_collection_statement(collection_id, query, params)
        ).to_query_result()


    # ─── Branching, communities, memory and NL search ───────────────────────

    async def fork_graph(self, project_id: str, graph_id: str, branch_name: str) -> GraphDefinition:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.fork_graph`."""
        return converters.to_graph_definition(
            await self._invoke(
                self._graph_definition_stub.Fork,
                requests.fork_graph(project_id, graph_id, branch_name),
            )
        )

    async def merge_graph(self, project_id: str, branch_id: str) -> MergeResult:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.merge_graph`."""
        return converters.to_merge_result(
            await self._invoke(
                self._graph_definition_stub.Merge,
                requests.merge_graph(project_id, branch_id),
            )
        )

    async def list_branches(self, project_id: str, graph_id: str) -> tuple[GraphDefinition, ...]:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.list_branches`."""
        return converters.to_graph_definitions(
            await self._invoke(
                self._graph_definition_stub.ListBranches,
                requests.list_branches(project_id, graph_id),
            )
        )

    async def detect_communities(self, graph_id: str, request: DetectCommunitiesRequest) -> CommunityHierarchy:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.detect_communities`."""
        return converters.to_community_hierarchy(
            await self._invoke(
                self._graph_stub.DetectCommunities,
                requests.detect_communities(graph_id, request),
            )
        )

    async def get_communities(self, graph_id: str, max_level: int, include_members: bool = False) -> CommunityHierarchy:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.get_communities`."""
        return converters.to_community_hierarchy(
            await self._invoke(
                self._graph_stub.GetCommunities,
                requests.get_communities(graph_id, max_level, include_members),
            )
        )

    async def get_community_summaries(self, graph_id: str, request: GetCommunitySummariesRequest) -> CommunitySummaries:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.get_community_summaries`."""
        return converters.to_community_summaries(
            await self._invoke(
                self._graph_stub.GetCommunitySummaries,
                requests.get_community_summaries(graph_id, request),
            )
        )

    async def get_community_members(
        self, graph_id: str, request: GetCommunityMembersRequest
    ) -> tuple[CommunityMemberSet, ...]:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.get_community_members`."""
        return converters.to_community_member_sets(
            await self._invoke(
                self._graph_stub.GetCommunityMembers,
                requests.get_community_members(graph_id, request),
            )
        )

    async def get_community_assignments(
        self, graph_id: str, level: int, node_ids: Sequence[int]
    ) -> CommunityAssignments:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.get_community_assignments`."""
        return converters.to_community_assignments(
            await self._invoke(
                self._graph_stub.GetCommunityAssignments,
                requests.get_community_assignments(graph_id, level, node_ids),
            )
        )

    async def global_search(self, graph_id: str, request: GlobalSearchRequest) -> tuple[GlobalSearchResult, ...]:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.global_search`."""
        return converters.to_global_search_results(
            await self._invoke(
                self._graph_stub.GlobalSearch,
                requests.global_search(graph_id, request),
            )
        )

    async def refresh_communities(self, graph_id: str, request: DetectCommunitiesRequest) -> RefreshCommunitiesResult:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.refresh_communities`."""
        return converters.to_refresh_communities_result(
            await self._invoke(
                self._graph_stub.RefreshCommunities,
                requests.detect_communities(graph_id, request),
            )
        )

    async def community_status(self, graph_id: str) -> CommunityStatus:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.community_status`."""
        return converters.to_community_status(
            await self._invoke(
                self._graph_stub.CommunityStatus,
                requests.community_status(graph_id),
            )
        )

    async def observe(self, graph_id: str, request: ObserveRequest) -> ObserveResult:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.observe`."""
        return converters.to_observe_result(
            await self._invoke(
                self._graph_stub.Observe,
                requests.observe(graph_id, request),
            )
        )

    async def entity_link(self, graph_id: str, request: EntityLinkRequest) -> tuple[Edge, ...]:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.entity_link`."""
        return converters.to_edges(
            await self._invoke(
                self._graph_stub.EntityLink,
                requests.entity_link(graph_id, request),
            )
        )

    async def decay(self, graph_id: str, max_age_hours: int) -> DecayResult:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.decay`."""
        return converters.to_decay_result(
            await self._invoke(
                self._graph_stub.Decay,
                requests.decay(graph_id, max_age_hours),
            )
        )

    async def nl_search_collection(self, collection_id: str, request: NlSearchRequest) -> NlSearchResult:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.nl_search_collection`."""
        return converters.to_nl_search_result(
            await self._invoke(
                self._nl_search_stub.SearchCollection,
                requests.nl_search_collection(collection_id, request),
            )
        )

    async def nl_search_graph(self, graph_id: str, request: NlSearchRequest) -> NlSearchResult:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.nl_search_graph`."""
        return converters.to_nl_search_result(
            await self._invoke(
                self._nl_search_stub.SearchGraph,
                requests.nl_search_graph(graph_id, request),
            )
        )

    async def put_community_summary(self, graph_id: str, request: PutCommunitySummaryRequest) -> int:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.put_community_summary`."""
        return (await self.put_community_summaries(graph_id, [request]))[0]

    async def put_community_summaries(
        self, graph_id: str, requests_: Sequence[PutCommunitySummaryRequest]
    ) -> tuple[int, ...]:
        """Asynchronous :meth:`~cyrock_db.client.CyrockDbClient.put_community_summaries`."""
        response = await self._invoke(
            self._graph_stub.PutCommunitySummaries,
            requests.put_community_summaries(graph_id, requests_),
        )
        return tuple(response.ids)


    # ─── Change Data Capture ────────────────────────────────────────────────

    async def watch_graph(
        self, graph_id: str, options: WatchOptions
    ) -> AsyncIterator[ChangeEvent]:
        """Opens a change stream over a graph, as an async iterator.

        **The one place this client is not a mirror of the blocking one.** The synchronous form takes
        a listener because a callback is the only way to deliver events without blocking the caller;
        an async iterator is the same idea with the control inverted, and is what a Python caller
        expects from a stream. So this takes no listener, and returns something to iterate::

            async for event in await client.watch_graph(graph_id, WatchOptions.with_snapshot()):
                ...

        The consequence is that these two methods are on the parity guard's deliberate-omission list,
        as ``watchGraph`` and ``watchCollection`` are on the Java one's - for the same underlying
        reason, that a stream of many events is not a single result.

        **No reconnection.** The blocking subscription reconnects with backoff and resumes from the
        last LSN; iterating stops when the stream does. A caller that needs to resume checkpoints
        ``event.lsn`` and re-opens with :meth:`~cyrock_db.types.WatchOptions.resume_from`.

        :raises CyrockDbClientException: if the server refuses the subscription
        """
        return self._iter_changes(cdc_pb2.ResourceKind.GRAPH, graph_id, options)

    async def watch_collection(
        self, collection_id: str, options: WatchOptions
    ) -> AsyncIterator[ChangeEvent]:
        """Opens a change stream over a collection, as an async iterator. See :meth:`watch_graph`."""
        return self._iter_changes(cdc_pb2.ResourceKind.COLLECTION, collection_id, options)

    async def _iter_changes(
        self, resource_kind: Any, resource_id: str, options: WatchOptions
    ) -> AsyncIterator[ChangeEvent]:
        call = self._cdc_stub.WatchChanges(watch_request(resource_kind, resource_id, options, -1))
        try:
            async for message in call:
                yield converters.to_change_event(message)
        except grpc.aio.AioRpcError as error:
            raise from_rpc_error(error) from None

    # ─── Internals ──────────────────────────────────────────────────────────

    async def _invoke(self, rpc: Any, request: Any) -> Any:
        """Issues one unary call, translating a gRPC failure into this SDK's exception type.

        The asynchronous counterpart of the synchronous client's ``_call``. Introduced once the
        method count made the repeated try/except per call the larger risk: forgetting it on one
        method leaks a raw AioRpcError to a caller who is catching CyrockDbClientException.
        """
        try:
            return await rpc(request, timeout=self._options.call_timeout)
        except grpc.aio.AioRpcError as error:
            raise from_rpc_error(error) from None
