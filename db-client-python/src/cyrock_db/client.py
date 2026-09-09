"""The synchronous client.

The Python face of ``CyrockDbClient`` / ``CyrockDbClientGrpc``: a blocking, domain-typed client over
gRPC that handles the API-key-to-JWT exchange and maps every failure onto
:class:`~cyrock_db.exceptions.CyrockDbClientException`.

Options are keyword arguments rather than a fluent builder; see :class:`~cyrock_db._channel.ClientOptions`
for the full set and their defaults.

**Thread-safe.** One instance serves a whole application, as in Java.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from types import TracebackType
from typing import Any, TypeVar

import grpc

from . import _proto_converters as converters
from . import _proto_requests as requests
from ._auth import AuthInterceptor, api_key_header, bearer, uses_api_key
from ._channel import ClientOptions
from ._cyql_routing import is_project_scoped
from ._proto import cyrock_db_cdc_pb2 as cdc_pb2
from ._proto import cyrock_db_cdc_pb2_grpc as cdc_grpc
from ._proto import cyrock_db_data_pb2_grpc as data_grpc
from ._proto import cyrock_db_graph_pb2_grpc as graph_grpc
from ._proto import cyrock_db_nlsearch_pb2_grpc as nlsearch_grpc
from ._proto import cyrock_db_platform_pb2 as platform_pb2
from ._proto import cyrock_db_platform_pb2_grpc as platform_grpc
from ._token import TokenManager
from ._watch import ChangeListener, ChangeStreamSubscription
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

__all__ = ["CyrockDbClient"]

_T = TypeVar("_T")


class CyrockDbClient:
    """A connection to CYROCK.AI DB.

    Use as a context manager, or call :meth:`close` when finished::

        with CyrockDbClient(api_key="...") as client:
            collection = client.create_collection(project_id, definition)
    """

    def __init__(self, **options: Any) -> None:
        self._options = ClientOptions(**options)

        credentials = self._options.credentials()
        arguments   = self._options.channel_arguments()
        raw_channel = (
            grpc.insecure_channel(self._options.target, options=arguments)
            if credentials is None
            else grpc.secure_channel(self._options.target, credentials, options=arguments)
        )
        self._raw_channel = raw_channel

        # The token exchange authenticates with the API key and must not go through the interceptor
        # that attaches the token it is about to produce, so it runs on the raw channel. Everything
        # else goes through the intercepted one. This is the same split Java makes by giving the
        # token stub its own ApiKeyCallCredentials.
        if self._options.api_key is not None:
            self._tokens: TokenManager | None = TokenManager(raw_channel, self._options.api_key)
            tokens  = self._tokens
            api_key = self._options.api_key

            def credential_for(method: str) -> list[tuple[str, str]]:
                # Per service, not per plane: the definition services refuse the exchanged token.
                # See API_KEY_SERVICES.
                if uses_api_key(method):
                    return [api_key_header(api_key)]
                return [bearer(tokens.token())]

            self._channel: grpc.Channel = grpc.intercept_channel(
                raw_channel, AuthInterceptor(credential_for)
            )
        else:
            self._tokens  = None
            self._channel = raw_channel

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

    # ─── Lifecycle ──────────────────────────────────────────────────────────

    def close(self) -> None:
        """Closes the connection. Idempotent."""
        self._raw_channel.close()

    def __enter__(self) -> CyrockDbClient:
        return self

    def __exit__(
        self,
        exc_type:  type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    # ─── Collection definitions ─────────────────────────────────────────────

    def create_collection(self, project_id: str, definition: CollectionDefinition) -> CollectionDefinition:
        """Creates a collection in the given project.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_collection_definition(
                self._collection_stub.Create(
                    requests.create_collection(project_id, definition), timeout=self._options.call_timeout
                )
            )
        )

    def get_collection(self, collection_id: str) -> CollectionDefinition:
        """Retrieves a collection definition by its id.

        Reads the caller's visible collections and picks the one asked for, rather than calling
        ``GetById``. That is not an oversight: ``GetById`` takes a project id as well, and this
        signature - matching the Java client's - does not have one. Tracked as issue #457; changing
        it is a Java-first change so the two SDKs keep the same surface.

        :raises NotFoundException: if no such collection is visible to this caller
        :raises CyrockDbClientException: if the server returns an error
        """
        def find() -> CollectionDefinition:
            listed = self._collection_stub.ListAll(platform_pb2.Empty(), timeout=self._options.call_timeout)
            for candidate in listed.collections:
                if candidate.id == collection_id:
                    return converters.to_collection_definition(candidate)
            raise NotFoundException(f"Collection not found: {collection_id}")

        return self._call(find)

    def list_collections(self, project_id: str) -> tuple[CollectionDefinition, ...]:
        """Lists every collection in the given project.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_collection_definitions(
                self._collection_stub.ListForProject(
                    requests.project_id_request(project_id), timeout=self._options.call_timeout
                )
            )
        )

    def delete_collection(self, project_id: str, collection_id: str) -> CollectionDefinition:
        """Deletes a collection, returning the definition that was removed.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_collection_definition(
                self._collection_stub.Delete(
                    requests.collection_id_request(project_id, collection_id),
                    timeout=self._options.call_timeout,
                )
            )
        )

    def rename_collection(self, collection_id: str, new_name: str) -> CollectionDefinition:
        """Renames a collection. The id is the identity and never changes; only the display name moves.

        This wraps the update RPC, which carries only the id and the name - it is not a schema change;
        adding or dropping fields is ``ALTER COLLECTION`` via ``execute_collection_statement``.

        :raises CyrockDbClientException: if the name is blank (400), already taken in the project (409),
            or the collection does not exist (404)
        """
        return self._call(
            lambda: converters.to_collection_definition(
                self._collection_stub.Update(
                    requests.update_collection(collection_id, new_name),
                    timeout=self._options.call_timeout,
                )
            )
        )


    # ─── Documents ──────────────────────────────────────────────────────────

    def upsert(
        self,
        collection_id: str,
        document_id:   int,
        vectors:       Mapping[str, VectorInput] | None = None,
        metadata:      Mapping[str, Any] | None         = None,
    ) -> int:
        """Inserts or replaces a document, returning its id.

        :param document_id: :data:`~cyrock_db.types.AUTO_ASSIGN_ID` (or any negative value) to have
            the store assign one. ``0`` is a real id and addresses document 0.
        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: int(
                self._document_stub.Upsert(
                    requests.upsert_document(collection_id, document_id, vectors, metadata),
                    timeout=self._options.call_timeout,
                ).id
            )
        )

    def upsert_batch(self, collection_id: str, documents: Sequence[Document]) -> tuple[int, ...]:
        """Inserts or replaces many documents in one round trip, returning their ids in order.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: tuple(
                self._document_stub.UpsertBatch(
                    requests.upsert_documents_batch(collection_id, documents),
                    timeout=self._options.call_timeout,
                ).ids
            )
        )

    def get_by_id(self, collection_id: str, document_id: int) -> Document:
        """Reads one document by id.

        :raises NotFoundException: if no such document exists
        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_document(
                self._document_stub.GetById(
                    requests.get_document_by_id(collection_id, document_id),
                    timeout=self._options.call_timeout,
                )
            )
        )

    def list(self, collection_id: str, offset: int, limit: int) -> tuple[Document, ...]:
        """Reads a page of documents.

        :param limit: page size. The server bounds this (issue #429): a negative limit, or one above
            its ceiling, is refused with 400 rather than pre-sizing an allocation from it.
        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_documents(
                self._document_stub.List(
                    requests.list_documents(collection_id, offset, limit),
                    timeout=self._options.call_timeout,
                )
            )
        )

    def delete(self, collection_id: str, document_id: int) -> Document:
        """Deletes a document, returning what was removed.

        :raises NotFoundException: if no such document exists
        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_document(
                self._document_stub.Delete(
                    requests.delete_document(collection_id, document_id),
                    timeout=self._options.call_timeout,
                )
            )
        )

    def upsert_document(
        self,
        collection_id: str,
        external_key:  str,
        vectors:       Mapping[str, VectorInput] | None = None,
        metadata:      Mapping[str, Any] | None         = None,
    ) -> UpsertResult:
        """Inserts or replaces a document addressed by the caller's own stable key.

        The idempotent-ingest path: re-sending the same key updates rather than duplicating, and
        :attr:`~cyrock_db.types.UpsertResult.created` says which happened.

        :raises CyrockDbClientException: if the server returns an error
        """
        def upsert() -> UpsertResult:
            response = self._document_stub.UpsertByKey(
                requests.upsert_document_by_key(collection_id, external_key, vectors, metadata),
                timeout=self._options.call_timeout,
            )
            return UpsertResult(id=response.id, created=response.created)

        return self._call(upsert)

    def get_document(self, collection_id: str, external_key: str) -> Document:
        """Reads one document by external key.

        :raises NotFoundException: if no document carries that key
        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_document(
                self._document_stub.GetByKey(
                    requests.get_document_by_key(collection_id, external_key),
                    timeout=self._options.call_timeout,
                )
            )
        )

    def remove_document(self, collection_id: str, external_key: str) -> Document:
        """Deletes a document by external key, returning what was removed.

        :raises NotFoundException: if no document carries that key
        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_document(
                self._document_stub.RemoveByKey(
                    requests.remove_document_by_key(collection_id, external_key),
                    timeout=self._options.call_timeout,
                )
            )
        )


    # ─── Document search ────────────────────────────────────────────────────

    def search(self, collection_id: str, request: SearchRequest) -> tuple[Match, ...]:
        """Vector similarity search over one field, best match first.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_matches(
                self._document_stub.Search(
                    requests.search(collection_id, request), timeout=self._options.call_timeout
                )
            )
        )

    def multi_search(self, collection_id: str, request: MultiVectorSearchRequest) -> tuple[Match, ...]:
        """Searches several vector fields at once, fusing the result lists.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_matches(
                self._document_stub.MultiSearch(
                    requests.multi_search(collection_id, request), timeout=self._options.call_timeout
                )
            )
        )

    def hybrid_search(self, collection_id: str, request: HybridSearchRequest) -> tuple[Match, ...]:
        """Searches vector fields and full-text fields together, fusing the result lists.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_matches(
                self._document_stub.HybridSearch(
                    requests.hybrid_search(collection_id, request), timeout=self._options.call_timeout
                )
            )
        )


    # ─── Graph definitions ──────────────────────────────────────────────────

    def create_graph(self, project_id: str, definition: GraphDefinition) -> GraphDefinition:
        """Creates a graph in the given project.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_graph_definition(
                self._graph_definition_stub.Create(
                    requests.create_graph(project_id, definition), timeout=self._options.call_timeout
                )
            )
        )

    def get_graph(self, graph_id: str) -> GraphDefinition:
        """Reads a graph definition by id.

        Lists the caller's visible graphs and filters, for the same reason
        :meth:`get_collection` does - ``GetById`` also wants a project id this signature has not got.
        Tracked as issue #457.

        :raises NotFoundException: if no such graph is visible to this caller
        :raises CyrockDbClientException: if the server returns an error
        """
        def find() -> GraphDefinition:
            listed = self._graph_definition_stub.ListAll(
                platform_pb2.Empty(), timeout=self._options.call_timeout
            )
            for candidate in listed.graphs:
                if candidate.id == graph_id:
                    return converters.to_graph_definition(candidate)
            raise NotFoundException(f"Graph not found: {graph_id}")

        return self._call(find)

    def list_graphs(self, project_id: str) -> tuple[GraphDefinition, ...]:
        """Lists every graph in the given project.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_graph_definitions(
                self._graph_definition_stub.ListForProject(
                    requests.project_id_request(project_id), timeout=self._options.call_timeout
                )
            )
        )

    def delete_graph(self, project_id: str, graph_id: str) -> GraphDefinition:
        """Deletes a graph, returning the definition that was removed.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_graph_definition(
                self._graph_definition_stub.Delete(
                    requests.graph_id_request(project_id, graph_id), timeout=self._options.call_timeout
                )
            )
        )

    # ─── Graph nodes and edges ──────────────────────────────────────────────

    def add_node(
        self,
        graph_id: str,
        labels:   Sequence[str],
        vectors:  Mapping[str, VectorInput] | None = None,
        metadata: Mapping[str, Any] | None         = None,
    ) -> int:
        """Adds a labelled node, returning its id.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: int(
                self._graph_stub.AddNode(
                    requests.add_node(graph_id, labels, vectors, metadata),
                    timeout=self._options.call_timeout,
                ).node_id
            )
        )

    def add_edge(self, graph_id: str, request: AddEdgeRequest) -> int:
        """Adds a weighted, typed edge, returning its id.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: int(
                self._graph_stub.AddEdge(
                    requests.add_edge(graph_id, request), timeout=self._options.call_timeout
                ).edge_id
            )
        )

    def get_node(self, graph_id: str, node: int | str) -> Node:
        """Reads one node, by id or by external key.

        Java has two overloads, ``getNode(String, long)`` and ``getNode(String, String)``. Python has
        no overloading, so the parameter takes either and dispatches on its type - which keeps the
        method name and the call sites identical across the two SDKs.

        :raises NotFoundException: if no such node exists
        :raises CyrockDbClientException: if the server returns an error
        """
        if isinstance(node, str):
            return self._call(
                lambda: converters.to_node(
                    self._graph_stub.GetNodeByKey(
                        requests.get_node_by_key(graph_id, node), timeout=self._options.call_timeout
                    ).node
                )
            )
        return self._call(
            lambda: converters.to_node(
                self._graph_stub.GetNode(
                    requests.get_node(graph_id, node), timeout=self._options.call_timeout
                ).node
            )
        )

    def get_edge(self, graph_id: str, edge_id: int) -> Edge:
        """Reads one edge by id.

        :raises NotFoundException: if no such edge exists
        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_edge(
                self._graph_stub.GetEdge(
                    requests.get_edge(graph_id, edge_id), timeout=self._options.call_timeout
                ).edge
            )
        )

    def remove_node(self, graph_id: str, node: int | str) -> None:
        """Removes a node and its edges, by id or by external key. See :meth:`get_node`.

        :raises CyrockDbClientException: if the server returns an error
        """
        if isinstance(node, str):
            self._call(
                lambda: self._graph_stub.RemoveNodeByKey(
                    requests.remove_node_by_key(graph_id, node), timeout=self._options.call_timeout
                )
            )
            return
        self._call(
            lambda: self._graph_stub.RemoveNode(
                requests.remove_node(graph_id, node), timeout=self._options.call_timeout
            )
        )

    def remove_edge(self, graph_id: str, edge_id: int) -> None:
        """Removes an edge.

        :raises CyrockDbClientException: if the server returns an error
        """
        self._call(
            lambda: self._graph_stub.RemoveEdge(
                requests.remove_edge(graph_id, edge_id), timeout=self._options.call_timeout
            )
        )

    def update_vector(self, graph_id: str, node_id: int, field_name: str, vector: Sequence[float]) -> None:
        """Replaces one of a node's vectors.

        :raises CyrockDbClientException: if the server returns an error
        """
        self._call(
            lambda: self._graph_stub.UpdateVector(
                requests.update_vector(graph_id, node_id, field_name, vector),
                timeout=self._options.call_timeout,
            )
        )

    def update_weight(self, graph_id: str, edge_id: int, weight: float) -> None:
        """Replaces an edge's weight.

        :raises CyrockDbClientException: if the server returns an error
        """
        self._call(
            lambda: self._graph_stub.UpdateWeight(
                requests.update_weight(graph_id, edge_id, weight), timeout=self._options.call_timeout
            )
        )

    def update_node_metadata(self, graph_id: str, node_id: int, metadata: Mapping[str, Any]) -> None:
        """Replaces a node's metadata.

        :raises CyrockDbClientException: if the server returns an error
        """
        self._call(
            lambda: self._graph_stub.UpdateNodeMetadata(
                requests.update_node_metadata(graph_id, node_id, metadata),
                timeout=self._options.call_timeout,
            )
        )

    def update_edge_metadata(self, graph_id: str, edge_id: int, metadata: Mapping[str, Any]) -> None:
        """Replaces an edge's metadata.

        :raises CyrockDbClientException: if the server returns an error
        """
        self._call(
            lambda: self._graph_stub.UpdateEdgeMetadata(
                requests.update_edge_metadata(graph_id, edge_id, metadata),
                timeout=self._options.call_timeout,
            )
        )

    def list_nodes(self, graph_id: str, request: ListNodesRequest) -> tuple[Node, ...]:
        """Reads a page of nodes, optionally filtered by label and metadata.

        Vectors are not returned unless ``request.include_vectors`` asks for them.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_nodes(
                self._graph_stub.ListNodes(
                    requests.list_nodes(graph_id, request), timeout=self._options.call_timeout
                )
            )
        )

    def get_nodes(
        self, graph_id: str, node_ids: Sequence[int], include_vectors: bool = False
    ) -> tuple[Node, ...]:
        """Reads a named set of nodes.

        An id the graph does not hold is left out rather than failing the call, and duplicates
        collapse - so a shorter result does not by itself mean something was missing. Compare against
        the number of *distinct* ids sent.

        Java spells the default as a second overload; Python uses a default argument.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_nodes(
                self._graph_stub.GetNodes(
                    requests.get_nodes(graph_id, node_ids, include_vectors),
                    timeout=self._options.call_timeout,
                )
            )
        )

    def induced_subgraph(
        self, graph_id: str, node_ids: Sequence[int], include_vectors: bool = False
    ) -> GraphWindow:
        """Reads the given nodes and only the edges that run between them.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_graph_window(
                self._graph_stub.InducedSubgraph(
                    requests.induced_subgraph(graph_id, node_ids, include_vectors),
                    timeout=self._options.call_timeout,
                )
            )
        )

    def upsert_node(self, graph_id: str, request: UpsertNodeRequest) -> UpsertNodeResult:
        """Inserts or replaces a node, addressed by id, by external key, or neither.

        :raises CyrockDbClientException: if the server returns an error
        """
        def upsert() -> UpsertNodeResult:
            response = self._graph_stub.UpsertNode(
                requests.upsert_node(graph_id, request), timeout=self._options.call_timeout
            )
            return UpsertNodeResult(node_id=response.node_id, created=response.created)

        return self._call(upsert)


    # ─── Graph search and traversal ─────────────────────────────────────────

    def search_similar(self, graph_id: str, request: SearchSimilarRequest) -> tuple[NodeMatch, ...]:
        """Approximate-nearest-neighbour search over node vectors.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_node_matches(
                self._graph_stub.SearchSimilar(
                    requests.search_similar(graph_id, request), timeout=self._options.call_timeout
                )
            )
        )

    def neighbors(self, graph_id: str, request: NeighborsRequest) -> tuple[Node, ...]:
        """The nodes one hop from a starting node.

        Returns nodes only, as the Java client does. Use :meth:`neighbors_graph` when you also need
        the connecting edges or the ``truncated`` flag.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_nodes(
                self._graph_stub.Neighbors(
                    requests.neighbors(graph_id, request), timeout=self._options.call_timeout
                )
            )
        )

    def neighbors_graph(self, graph_id: str, request: NeighborsRequest) -> NeighborsWindow:
        """The neighbours of a node as nodes and their edges, plus whether the limit dropped any.

        Unlike :meth:`neighbors`, this surfaces the connecting edges and the ``truncated`` flag, so
        a caller that set ``request.limit`` can tell a full result from a capped one. See issue #458.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_neighbors_window(
                self._graph_stub.Neighbors(
                    requests.neighbors(graph_id, request), timeout=self._options.call_timeout
                )
            )
        )

    def traverse(self, graph_id: str, request: TraverseRequest) -> tuple[Node, ...]:
        """Breadth-first traversal from a starting node.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_nodes(
                self._graph_stub.Traverse(
                    requests.traverse(graph_id, request), timeout=self._options.call_timeout
                )
            )
        )

    def context_window(self, graph_id: str, request: GraphSearchExpansionRequest) -> tuple[Node, ...]:
        """Vector search followed by graph expansion, returning nodes only.

        ``request.depth`` is a hop count here. Contrast :meth:`recall`.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_nodes(
                self._graph_stub.ContextWindow(
                    requests.context_window(graph_id, request), timeout=self._options.call_timeout
                )
            )
        )

    def context_window_graph(self, graph_id: str, request: GraphSearchExpansionRequest) -> GraphWindow:
        """Vector search followed by graph expansion, returning nodes and their edges.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_graph_window(
                self._graph_stub.ContextWindow(
                    requests.context_window(graph_id, request), timeout=self._options.call_timeout
                )
            )
        )

    def recall(self, graph_id: str, request: GraphRecallRequest) -> tuple[Node, ...]:
        """Recalls memories by vector similarity, re-weighted by recency.

        ``request.recency_hours`` is a time window in hours, not a traversal depth.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_nodes(
                self._graph_stub.Recall(
                    requests.recall(graph_id, request), timeout=self._options.call_timeout
                )
            )
        )

    def recall_graph(self, graph_id: str, request: GraphRecallRequest) -> GraphWindow:
        """Recalls memories, returning nodes and their edges. See :meth:`recall`.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_graph_window(
                self._graph_stub.Recall(
                    requests.recall(graph_id, request), timeout=self._options.call_timeout
                )
            )
        )

    def reasoning_chain(self, graph_id: str, request: ReasoningChainRequest) -> tuple[Node, ...]:
        """The shortest path between two nodes, as nodes.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_nodes(
                self._graph_stub.ReasoningChain(
                    requests.reasoning_chain(graph_id, request), timeout=self._options.call_timeout
                )
            )
        )

    def reasoning_chain_graph(self, graph_id: str, request: ReasoningChainRequest) -> GraphWindow:
        """The shortest path between two nodes, as nodes and edges.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_graph_window(
                self._graph_stub.ReasoningChain(
                    requests.reasoning_chain(graph_id, request), timeout=self._options.call_timeout
                )
            )
        )


    # ─── Transactions ───────────────────────────────────────────────────────

    def execute_document_transaction(
        self, collection_id: str, operations: Sequence[CollectionOperation]
    ) -> TransactionResult:
        """Applies document operations atomically: all commit, or none do.

        The per-operation results report a partial outcome precisely, but the transaction itself
        never partially applies - an operation's ``error`` says why the whole thing rolled back.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_transaction_result(
                self._document_stub.ExecuteTransaction(
                    requests.execute_document_transaction(collection_id, operations),
                    timeout=self._options.call_timeout,
                )
            )
        )

    def execute_transaction(
        self, graph_id: str, operations: Sequence[GraphOperation]
    ) -> TransactionResult:
        """Applies graph operations atomically. See :meth:`execute_document_transaction`.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_transaction_result(
                self._graph_stub.ExecuteTransaction(
                    requests.execute_transaction(graph_id, operations),
                    timeout=self._options.call_timeout,
                )
            )
        )


    # ─── CyQL statements ────────────────────────────────────────────────────

    def execute_statement(
        self, graph_id: str, statement: str, params: QueryParameters | None = None
    ) -> StatementResult:
        """Executes a CyQL statement against a graph: reads, writes and ALTER GRAPH.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_statement_result(
                self._graph_stub.ExecuteStatement(
                    requests.execute_statement(graph_id, statement, params),
                    timeout=self._options.call_timeout,
                )
            )
        )

    def execute_collection_statement(
        self, collection_id: str, statement: str, params: QueryParameters | None = None
    ) -> StatementResult:
        """Executes a CyQL statement against a collection.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_statement_result(
                self._document_stub.ExecuteStatement(
                    requests.execute_collection_statement(collection_id, statement, params),
                    timeout=self._options.call_timeout,
                )
            )
        )

    def execute_project_statement(
        self, project_id: str, statement: str, params: QueryParameters | None = None
    ) -> StatementResult:
        """Executes project-scoped DDL: CREATE/DROP GRAPH, SHOW, DESCRIBE.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_statement_result(
                self._graph_definition_stub.ExecuteStatement(
                    requests.execute_project_statement(project_id, statement, params),
                    timeout=self._options.call_timeout,
                )
            )
        )

    def execute(
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
            return self.execute_project_statement(project_id, statement, params)
        if graph_id is None:
            raise CyrockDbClientException(400, "Statement is graph-scoped; a graphId is required")
        return self.execute_statement(graph_id, statement, params)

    def execute_collection(
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
            return self.execute_project_statement(project_id, statement, params)
        if collection_id is None:
            raise CyrockDbClientException(
                400, "Statement is collection-scoped; a collectionId is required"
            )
        return self.execute_collection_statement(collection_id, statement, params)

    def query(
        self, graph_id: str, query: str, params: QueryParameters | None = None
    ) -> QueryResult:
        """Runs a read query against a graph and returns its rows.

        Unlike the Java client, this does not parse the statement first to reject a write before it
        leaves. Python has no CyQL parser here, so the statement is sent and the server answers - a
        write sent to this method fails on the server rather than in the client, with the server's
        own message.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self.execute_statement(graph_id, query, params).to_query_result()

    def query_collection(
        self, collection_id: str, query: str, params: QueryParameters | None = None
    ) -> QueryResult:
        """Runs a read query against a collection. See :meth:`query`.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self.execute_collection_statement(collection_id, query, params).to_query_result()


    # ─── Branching, communities, memory and NL search ───────────────────────

    def fork_graph(self, project_id: str, graph_id: str, branch_name: str) -> GraphDefinition:
        """Forks a graph into an isolated branch.

        Branches are overlays with no change log of their own, so Change Data Capture on a branch is
        refused with FAILED_PRECONDITION.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_graph_definition(
                self._graph_definition_stub.Fork(
                    requests.fork_graph(project_id, graph_id, branch_name),
                    timeout=self._options.call_timeout,
                )
            )
        )

    def merge_graph(self, project_id: str, branch_id: str) -> MergeResult:
        """Merges a branch back into its parent, returning what changed.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_merge_result(
                self._graph_definition_stub.Merge(
                    requests.merge_graph(project_id, branch_id),
                    timeout=self._options.call_timeout,
                )
            )
        )

    def list_branches(self, project_id: str, graph_id: str) -> tuple[GraphDefinition, ...]:
        """Lists a graph's branches.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_graph_definitions(
                self._graph_definition_stub.ListBranches(
                    requests.list_branches(project_id, graph_id),
                    timeout=self._options.call_timeout,
                )
            )
        )

    def detect_communities(self, graph_id: str, request: DetectCommunitiesRequest) -> CommunityHierarchy:
        """Detects communities, tagging nodes with a community id per level.

        Returns the resulting hierarchy.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_community_hierarchy(
                self._graph_stub.DetectCommunities(
                    requests.detect_communities(graph_id, request),
                    timeout=self._options.call_timeout,
                )
            )
        )

    def get_communities(self, graph_id: str, max_level: int, include_members: bool = False) -> CommunityHierarchy:
        """Reads the stored hierarchy.

        ``include_members`` is off by default: this read used to load every node id whether the
        caller wanted them or not, which on a large graph is most of the response (issue #320).
        Java spells the default as a second overload; Python uses a default argument.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_community_hierarchy(
                self._graph_stub.GetCommunities(
                    requests.get_communities(graph_id, max_level, include_members),
                    timeout=self._options.call_timeout,
                )
            )
        )

    def get_community_summaries(self, graph_id: str, request: GetCommunitySummariesRequest) -> CommunitySummaries:
        """Reads stored summaries by level and community id.

        The result's ``truncated`` flag says whether the request's ``limit`` cut the read short.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_community_summaries(
                self._graph_stub.GetCommunitySummaries(
                    requests.get_community_summaries(graph_id, request),
                    timeout=self._options.call_timeout,
                )
            )
        )

    def get_community_members(
        self, graph_id: str, request: GetCommunityMembersRequest
    ) -> tuple[CommunityMemberSet, ...]:
        """Reads community membership, one set per requested community.

        Each set carries its own ``truncated`` flag.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_community_member_sets(
                self._graph_stub.GetCommunityMembers(
                    requests.get_community_members(graph_id, request),
                    timeout=self._options.call_timeout,
                )
            )
        )

    def get_community_assignments(self, graph_id: str, level: int, node_ids: Sequence[int]) -> CommunityAssignments:
        """Reads which community each of the given nodes belongs to, at one level.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_community_assignments(
                self._graph_stub.GetCommunityAssignments(
                    requests.get_community_assignments(graph_id, level, node_ids),
                    timeout=self._options.call_timeout,
                )
            )
        )

    def global_search(self, graph_id: str, request: GlobalSearchRequest) -> tuple[GlobalSearchResult, ...]:
        """Theme-centric search over community summaries, returning ranked community reports.

        The GraphRAG read: it answers "what themes are in here" rather than "what is near this
        vector".

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_global_search_results(
                self._graph_stub.GlobalSearch(
                    requests.global_search(graph_id, request),
                    timeout=self._options.call_timeout,
                )
            )
        )

    def refresh_communities(self, graph_id: str, request: DetectCommunitiesRequest) -> RefreshCommunitiesResult:
        """Re-detects communities and prunes summaries the new hierarchy orphaned.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_refresh_communities_result(
                self._graph_stub.RefreshCommunities(
                    requests.detect_communities(graph_id, request),
                    timeout=self._options.call_timeout,
                )
            )
        )

    def community_status(self, graph_id: str) -> CommunityStatus:
        """Whether communities have been detected, when, and how stale they are.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_community_status(
                self._graph_stub.CommunityStatus(
                    requests.community_status(graph_id),
                    timeout=self._options.call_timeout,
                )
            )
        )

    def observe(self, graph_id: str, request: ObserveRequest) -> ObserveResult:
        """Stores an observation, auto-linking it to similar existing memories.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_observe_result(
                self._graph_stub.Observe(requests.observe(graph_id, request), timeout=self._options.call_timeout)
            )
        )

    def entity_link(self, graph_id: str, request: EntityLinkRequest) -> tuple[Edge, ...]:
        """Links a node to its nearest neighbours, returning the edges created.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_edges(
                self._graph_stub.EntityLink(requests.entity_link(graph_id, request), timeout=self._options.call_timeout)
            )
        )

    def decay(self, graph_id: str, max_age_hours: int) -> DecayResult:
        """Prunes memories older than the given age.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_decay_result(
                self._graph_stub.Decay(requests.decay(graph_id, max_age_hours), timeout=self._options.call_timeout)
            )
        )

    def nl_search_collection(self, collection_id: str, request: NlSearchRequest) -> NlSearchResult:
        """Searches a collection in plain language, embedding the query server-side.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_nl_search_result(
                self._nl_search_stub.SearchCollection(
                    requests.nl_search_collection(collection_id, request),
                    timeout=self._options.call_timeout,
                )
            )
        )

    def nl_search_graph(self, graph_id: str, request: NlSearchRequest) -> NlSearchResult:
        """Searches a graph in plain language.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: converters.to_nl_search_result(
                self._nl_search_stub.SearchGraph(
                    requests.nl_search_graph(graph_id, request),
                    timeout=self._options.call_timeout,
                )
            )
        )

    def put_community_summary(self, graph_id: str, request: PutCommunitySummaryRequest) -> int:
        """Stores one community's summary, returning its id.

        Goes through the batch RPC with a single entry, as the Java client does. The batch is atomic
        (issue #319), and routing one summary through the same path is one fewer way for the single
        and batch cases to behave differently.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self.put_community_summaries(graph_id, [request])[0]

    def put_community_summaries(
        self, graph_id: str, requests_: Sequence[PutCommunitySummaryRequest]
    ) -> tuple[int, ...]:
        """Stores many community summaries in one atomic call, returning their ids in order.

        :raises CyrockDbClientException: if the server returns an error
        """
        return self._call(
            lambda: tuple(
                self._graph_stub.PutCommunitySummaries(
                    requests.put_community_summaries(graph_id, requests_),
                    timeout=self._options.call_timeout,
                ).ids
            )
        )


    # ─── Change Data Capture ────────────────────────────────────────────────

    def watch_graph(
        self,
        graph_id: str,
        options:  WatchOptions,
        listener: ChangeListener | Callable[[ChangeEvent], None],
    ) -> ChangeStreamSubscription:
        """Opens a resumable change stream over a graph.

        The stream runs on its own daemon thread and reconnects on transient failure, resuming from
        the last delivered LSN. Close the returned handle to stop it, or use it as a context manager.

        Delivery is at-least-once with a resumable ``(resource_id, lsn)`` cursor: checkpoint
        :attr:`~cyrock_db._watch.ChangeStreamSubscription.last_lsn` and de-duplicate on it.

        Watching a **branch** is refused with ``FAILED_PRECONDITION``: a branch is an overlay with no
        retained log of its own.

        :param listener: a :class:`~cyrock_db._watch.ChangeListener`, or a plain callable taking one
            event
        :raises CyrockDbClientException: if the server refuses the subscription permanently
        """
        return ChangeStreamSubscription(
            self._cdc_stub, cdc_pb2.ResourceKind.GRAPH, graph_id, options, listener
        )

    def watch_collection(
        self,
        collection_id: str,
        options:       WatchOptions,
        listener:      ChangeListener | Callable[[ChangeEvent], None],
    ) -> ChangeStreamSubscription:
        """Opens a resumable change stream over a collection. See :meth:`watch_graph`."""
        return ChangeStreamSubscription(
            self._cdc_stub, cdc_pb2.ResourceKind.COLLECTION, collection_id, options, listener
        )

    # ─── Internals ──────────────────────────────────────────────────────────

    @staticmethod
    def _call(operation: Callable[[], _T]) -> _T:
        """Runs one call, translating a gRPC failure into this SDK's exception type.

        A CyrockDbClientException raised inside - NotFoundException from a client-side lookup, say -
        is already the right thing and passes through untouched.
        """
        try:
            return operation()
        except CyrockDbClientException:
            raise
        except grpc.RpcError as error:
            raise from_rpc_error(error) from None
