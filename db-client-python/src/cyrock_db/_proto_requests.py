"""Domain type -> proto request message. Pure, no I/O.

The other layer both facades share, matching ``client-java``'s ``ProtoRequests``. Every request the
client sends is built here, so the two facades cannot disagree about what a call looks like on the
wire - only about how they wait for the answer.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from ._label_filters import to_label_expression
from ._proto import cyrock_db_data_pb2 as data_pb2
from ._proto import cyrock_db_graph_pb2 as graph_pb2
from ._proto import cyrock_db_nlsearch_pb2 as nlsearch_pb2
from ._proto import cyrock_db_platform_pb2 as platform_pb2
from ._values_codec import to_struct
from .types import (
    AddEdgeOp,
    AddEdgeRequest,
    AddNodeOp,
    CollectionDefinition,
    CollectionOperation,
    DetectCommunitiesRequest,
    Document,
    EntityLinkRequest,
    GetCommunityMembersRequest,
    GetCommunitySummariesRequest,
    GlobalSearchRequest,
    GraphDefinition,
    GraphOperation,
    GraphRecallRequest,
    GraphSearchExpansionRequest,
    HybridSearchRequest,
    ListNodesRequest,
    MetadataFieldDefinition,
    MultiVectorSearchRequest,
    NeighborsRequest,
    NlSearchRequest,
    ObserveRequest,
    PutCommunitySummaryRequest,
    QueryParameters,
    ReasoningChainRequest,
    RemoveDocumentOp,
    RemoveEdgeOp,
    RemoveNodeOp,
    RerankOptions,
    SearchRequest,
    SearchSimilarRequest,
    Text,
    TraverseRequest,
    UpdateEdgeMetadataOp,
    UpdateNodeMetadataOp,
    UpdateVectorOp,
    UpdateWeightOp,
    UpsertDocumentOp,
    UpsertKeyOp,
    UpsertNodeOp,
    UpsertNodeRequest,
    Vector,
    VectorFieldDefinition,
    VectorInput,
)

__all__ = [
    "collection_id_request",
    "create_collection",
    "create_graph",
    "delete_document",
    "get_document_by_id",
    "get_document_by_key",
    "graph_id_request",
    "list_documents",
    "project_id_request",
    "remove_document_by_key",
    "upsert_document",
    "upsert_document_by_key",
    "hybrid_search",
    "multi_search",
    "search",
    "upsert_documents_batch",
    "vector_field_proto",
]


def vector_field_proto(value: VectorInput | Sequence[float]) -> Any:
    """Encodes one vector field: a precomputed embedding, or text for the server to embed.

    ``VectorFieldProto`` carries either ``values`` or ``text``, which is exactly the
    ``Vector | Text`` split. A bare sequence of floats is accepted too, because ``Document.vectors``
    holds plain embeddings rather than ``VectorInput``.
    """
    if isinstance(value, Text):
        return data_pb2.VectorFieldProto(text=value.text)
    if isinstance(value, Vector):
        return data_pb2.VectorFieldProto(values=list(value.values))
    return data_pb2.VectorFieldProto(values=[float(each) for each in value])


def _vector_map(vectors: Mapping[str, Any] | None) -> dict[str, Any]:
    return {name: vector_field_proto(value) for name, value in (vectors or {}).items()}


def upsert_document(
    collection_id: str,
    document_id:   int,
    vectors:       Mapping[str, VectorInput | Sequence[float]] | None,
    metadata:      Mapping[str, Any] | None,
    external_key:  str | None = None,
) -> Any:
    """Builds a single-document upsert.

    The id is sent as given, negative values included. The server reads any negative id as
    "assign me one" and a non-negative one as the document to replace; the field carries presence so
    that an absent id is distinguishable from an explicit ``0``, which addresses document 0 - GigaMap
    numbers from zero, so that is a real document. Sending -1 rather than omitting the field is what
    the Java client does, and the two spellings mean the same thing to the server.
    """
    request = data_pb2.UpsertDocumentRequest(collection_id=collection_id, id=document_id)
    for name, value in _vector_map(vectors).items():
        request.vectors[name].CopyFrom(value)
    if metadata is not None:
        request.metadata.CopyFrom(to_struct(metadata))
    if external_key is not None:
        request.external_key = external_key
    return request


def upsert_documents_batch(collection_id: str, documents: Sequence[Document]) -> Any:
    """Builds a batch upsert, one ``UpsertDocumentRequest`` per document."""
    batch = data_pb2.UpsertDocumentsBatchRequest(collection_id=collection_id)
    for document in documents:
        batch.documents.append(
            upsert_document(
                collection_id,
                document.id,
                document.vectors,
                document.metadata,
                document.external_key,
            )
        )
    return batch


def get_document_by_id(collection_id: str, document_id: int) -> Any:
    return data_pb2.GetDocumentRequest(collection_id=collection_id, document_id=document_id)


def list_documents(collection_id: str, offset: int, limit: int) -> Any:
    return data_pb2.ListDocumentsRequest(collection_id=collection_id, offset=offset, limit=limit)


def delete_document(collection_id: str, document_id: int) -> Any:
    return data_pb2.DeleteDocumentRequest(collection_id=collection_id, document_id=document_id)


def upsert_document_by_key(
    collection_id: str,
    external_key:  str,
    vectors:       Mapping[str, VectorInput | Sequence[float]] | None,
    metadata:      Mapping[str, Any] | None,
) -> Any:
    """Builds an upsert addressed by the caller's own stable key, for idempotent ingest."""
    request = data_pb2.UpsertByKeyRequest(collection_id=collection_id, external_key=external_key)
    for name, value in _vector_map(vectors).items():
        request.vectors[name].CopyFrom(value)
    if metadata is not None:
        request.metadata.CopyFrom(to_struct(metadata))
    return request


def get_document_by_key(collection_id: str, external_key: str) -> Any:
    return data_pb2.GetByKeyRequest(collection_id=collection_id, external_key=external_key)


def remove_document_by_key(collection_id: str, external_key: str) -> Any:
    return data_pb2.RemoveByKeyRequest(collection_id=collection_id, external_key=external_key)


def _vector_field_proto(definition: VectorFieldDefinition) -> Any:
    return platform_pb2.VectorFieldDefinitionProto(
        name                = definition.name,
        dimension           = definition.dimension,
        similarity_function = definition.similarity_function.value,
        max_degree          = definition.max_degree,
        beam_width          = definition.beam_width,
        neighbor_overflow   = definition.neighbor_overflow,
        alpha               = definition.alpha,
        embedding_model     = definition.embedding_model or "",
        eventual_indexing   = definition.eventual_indexing,
    )


def _metadata_field_proto(definition: MetadataFieldDefinition) -> Any:
    # `unique` is deliberately not sent: MetadataFieldDefinitionProto has no such field (issue #227),
    # so a unique constraint declared here is dropped on the way to the server, exactly as it is from
    # the Java client. Sending it silently is not possible; saying so here is the next best thing.
    return platform_pb2.MetadataFieldDefinitionProto(
        name        = definition.name,
        type        = definition.type.value,
        cardinality = definition.cardinality.value,
        fulltext    = definition.fulltext,
    )


def create_collection(project_id: str, definition: CollectionDefinition) -> Any:
    return platform_pb2.CreateCollectionDefinitionRequest(
        project_id      = project_id,
        name            = definition.name or "",
        vector_fields   = [_vector_field_proto(each)   for each in definition.vector_fields],
        metadata_fields = [_metadata_field_proto(each) for each in definition.metadata_fields],
    )


def update_collection(collection_id: str, new_name: str) -> Any:
    return platform_pb2.UpdateCollectionDefinitionRequest(id=collection_id, name=new_name or "")


def create_graph(project_id: str, definition: GraphDefinition) -> Any:
    return platform_pb2.CreateGraphDefinitionRequest(
        project_id               = project_id,
        name                     = definition.name or "",
        node_vector_fields       = [_vector_field_proto(each)   for each in definition.node_vector_fields],
        node_metadata_fields     = [_metadata_field_proto(each) for each in definition.node_metadata_fields],
        edge_metadata_fields     = [_metadata_field_proto(each) for each in definition.edge_metadata_fields],
        enable_temporal_tracking = definition.enable_temporal_tracking,
        auto_link_threshold      = definition.auto_link_threshold,
    )


def project_id_request(project_id: str) -> Any:
    return platform_pb2.ProjectIdRequest(project_id=project_id)


def collection_id_request(project_id: str, collection_id: str) -> Any:
    return platform_pb2.CollectionIdRequest(project_id=project_id, collection_id=collection_id)


def graph_id_request(project_id: str, graph_id: str) -> Any:
    return platform_pb2.GraphIdRequest(project_id=project_id, graph_id=graph_id)


def _rerank_proto(rerank: RerankOptions | None) -> Any | None:
    """Encodes re-rank options, or ``None`` when they are off.

    Disabled options are left off the request entirely rather than sent with ``enabled=False``, which
    is what the Java builder does: an absent message and a disabled one mean the same thing, and not
    sending it keeps the request honest about what was asked for.
    """
    if rerank is None or not rerank.enabled:
        return None
    return data_pb2.RerankOptionsProto(
        enabled    = True,
        model      = rerank.model or "",
        field      = rerank.field or "",
        candidates = rerank.candidates,
        query      = rerank.query or "",
    )


def _vector_query_proto(query: Any) -> Any:
    return data_pb2.VectorQueryProto(
        field_name=query.field_name, vector=list(query.vector), weight=query.weight
    )


def _text_query_proto(query: Any) -> Any:
    return data_pb2.TextQueryProto(
        text_field=query.text_field_name, query=query.query, weight=query.weight
    )


def search(collection_id: str, request: SearchRequest) -> Any:
    """Builds a single-field vector search.

    ``max_results`` is always sent. The field is ``optional`` on the wire so an omitted value can
    select the server default (issue #438), but neither SDK's request type has an unset state, so
    neither can ask for it.
    """
    built = data_pb2.SearchDocumentsRequest(
        collection_id = collection_id,
        vector_field  = request.vector_field,
        vector        = list(request.vector),
        max_results   = request.max_results,
    )
    if request.filter is not None:
        built.filter = request.filter
    rerank = _rerank_proto(request.rerank)
    if rerank is not None:
        built.rerank.CopyFrom(rerank)
    return built


def multi_search(collection_id: str, request: MultiVectorSearchRequest) -> Any:
    """Builds a multi-vector search with fusion."""
    built = data_pb2.MultiSearchDocumentsRequest(
        collection_id = collection_id,
        queries       = [_vector_query_proto(each) for each in request.queries],
        max_results   = request.max_results,
        fusion        = request.fusion.value,
    )
    if request.filter is not None:
        built.filter = request.filter
    return built


def hybrid_search(collection_id: str, request: HybridSearchRequest) -> Any:
    """Builds a combined vector and full-text search with fusion."""
    built = data_pb2.HybridSearchDocumentsRequest(
        collection_id  = collection_id,
        vector_queries = [_vector_query_proto(each) for each in request.vector_queries],
        text_queries   = [_text_query_proto(each)   for each in request.text_queries],
        max_results    = request.max_results,
        fusion         = request.fusion.value,
    )
    if request.filter is not None:
        built.filter = request.filter
    return built


# ─── Graph nodes and edges ──────────────────────────────────────────────────


def add_node(
    graph_id: str,
    labels:   Sequence[str] | None,
    vectors:  Mapping[str, VectorInput | Sequence[float]] | None,
    metadata: Mapping[str, Any] | None,
) -> Any:
    request = graph_pb2.AddNodeRequest(graph_id=graph_id, labels=list(labels or ()))
    for name, value in _vector_map(vectors).items():
        request.vectors[name].CopyFrom(_graph_vector(value))
    if metadata is not None:
        request.metadata.CopyFrom(to_struct(metadata))
    return request


def _graph_vector(field: Any) -> Any:
    """Re-encodes a data-plane VectorFieldProto as the graph plane's own message.

    The two protos are structurally identical - ``values`` or ``text`` - but they are distinct
    generated types in distinct modules, so one cannot be assigned where the other is expected.
    """
    return graph_pb2.GraphVectorFieldProto(values=list(field.values), text=field.text)


def add_edge(graph_id: str, request: AddEdgeRequest) -> Any:
    built = graph_pb2.AddEdgeRequest(
        graph_id  = graph_id,
        source_id = request.source_id,
        target_id = request.target_id,
        type      = request.type,
        weight    = request.weight,
    )
    if request.metadata:
        built.metadata.CopyFrom(to_struct(request.metadata))
    return built


def get_node(graph_id: str, node_id: int) -> Any:
    return graph_pb2.GetNodeRequest(graph_id=graph_id, node_id=node_id)


def get_node_by_key(graph_id: str, external_key: str) -> Any:
    return graph_pb2.GetNodeByKeyRequest(graph_id=graph_id, external_key=external_key)


def get_edge(graph_id: str, edge_id: int) -> Any:
    return graph_pb2.GetEdgeRequest(graph_id=graph_id, edge_id=edge_id)


def remove_node(graph_id: str, node_id: int) -> Any:
    return graph_pb2.RemoveNodeRequest(graph_id=graph_id, node_id=node_id)


def remove_node_by_key(graph_id: str, external_key: str) -> Any:
    return graph_pb2.RemoveNodeByKeyRequest(graph_id=graph_id, external_key=external_key)


def remove_edge(graph_id: str, edge_id: int) -> Any:
    return graph_pb2.RemoveEdgeRequest(graph_id=graph_id, edge_id=edge_id)


def update_vector(graph_id: str, node_id: int, field_name: str, vector: Sequence[float]) -> Any:
    return graph_pb2.UpdateVectorRequest(
        graph_id=graph_id, node_id=node_id, field_name=field_name,
        vector=[float(each) for each in vector],
    )


def update_weight(graph_id: str, edge_id: int, weight: float) -> Any:
    return graph_pb2.UpdateWeightRequest(graph_id=graph_id, edge_id=edge_id, weight=weight)


def update_node_metadata(graph_id: str, node_id: int, metadata: Mapping[str, Any] | None) -> Any:
    request = graph_pb2.UpdateNodeMetadataRequest(graph_id=graph_id, node_id=node_id)
    if metadata is not None:
        request.metadata.CopyFrom(to_struct(metadata))
    return request


def update_edge_metadata(graph_id: str, edge_id: int, metadata: Mapping[str, Any] | None) -> Any:
    request = graph_pb2.UpdateEdgeMetadataRequest(graph_id=graph_id, edge_id=edge_id)
    if metadata is not None:
        request.metadata.CopyFrom(to_struct(metadata))
    return request


def list_nodes(graph_id: str, request: ListNodesRequest) -> Any:
    built = graph_pb2.ListNodesRequest(
        graph_id        = graph_id,
        offset          = request.offset,
        limit           = request.limit,
        include_vectors = request.include_vectors,
    )
    if request.filter is not None:
        built.filter = request.filter
    if request.sample_seed is not None:
        built.sample_seed = request.sample_seed
    expression = to_label_expression(request.labels, request.label_match, request.exclude_labels)
    if expression is not None:
        built.label_expression.CopyFrom(expression)
    return built


def get_nodes(graph_id: str, node_ids: Sequence[int], include_vectors: bool = False) -> Any:
    return graph_pb2.GetNodesRequest(
        graph_id=graph_id, node_ids=list(node_ids), include_vectors=include_vectors
    )


def induced_subgraph(graph_id: str, node_ids: Sequence[int], include_vectors: bool = False) -> Any:
    return graph_pb2.InducedSubgraphRequest(
        graph_id=graph_id, node_ids=list(node_ids), include_vectors=include_vectors
    )


def upsert_node(graph_id: str, request: UpsertNodeRequest) -> Any:
    built = graph_pb2.UpsertNodeRequest(
        graph_id     = graph_id,
        external_key = request.external_key or "",
        labels       = list(request.labels or ()),
    )
    for name, value in _vector_map(request.vectors).items():
        built.vectors[name].CopyFrom(_graph_vector(value))
    if request.metadata:
        built.metadata.CopyFrom(to_struct(request.metadata))
    if request.node_id is not None:
        built.node_id = request.node_id
    return built


# ─── Graph reads ────────────────────────────────────────────────────────────


def search_similar(graph_id: str, request: SearchSimilarRequest) -> Any:
    built = graph_pb2.SearchSimilarRequest(
        graph_id    = graph_id,
        field_name  = request.field_name,
        vector      = list(request.vector),
        max_results = request.max_results,
    )
    if request.filter is not None:
        built.filter = request.filter
    expression = to_label_expression(request.labels, request.label_match, request.exclude_labels)
    if expression is not None:
        built.label_expression.CopyFrom(expression)
    return built


def neighbors(graph_id: str, request: NeighborsRequest) -> Any:
    built = graph_pb2.NeighborsRequest(
        graph_id        = graph_id,
        node_id         = request.node_id,
        direction       = request.direction.value,
        edge_type       = request.edge_type or "",
        include_vectors = request.include_vectors,
        limit           = request.limit,
    )
    if request.diversity_seed is not None:
        built.diversity_seed = request.diversity_seed
    return built


def traverse(graph_id: str, request: TraverseRequest) -> Any:
    return graph_pb2.TraverseRequest(
        graph_id  = graph_id,
        start_id  = request.start_id,
        max_depth = request.max_depth,
        direction = request.direction.value,
        edge_type = request.edge_type or "",
    )


def context_window(graph_id: str, request: GraphSearchExpansionRequest) -> Any:
    """Builds a vector-search-plus-expansion request. ``depth`` here is a hop count."""
    built = graph_pb2.ContextWindowRequest(
        graph_id    = graph_id,
        field_name  = request.field_name,
        vector      = list(request.vector),
        max_results = request.max_results,
        depth       = request.depth,
    )
    if request.diversity_seed is not None:
        built.diversity_seed = request.diversity_seed
    return built


def recall(graph_id: str, request: GraphRecallRequest) -> Any:
    """Builds a memory-recall request. ``recency_hours`` here is a time window, not a hop count.

    The proto field kept its number when it was renamed from ``depth`` (issue #230, #400), and the
    old name is reserved so it cannot come back meaning something else.
    """
    built = graph_pb2.RecallRequest(
        graph_id      = graph_id,
        field_name    = request.field_name,
        vector        = list(request.vector),
        max_results   = request.max_results,
        recency_hours = request.recency_hours,
    )
    if request.diversity_seed is not None:
        built.diversity_seed = request.diversity_seed
    return built


def reasoning_chain(graph_id: str, request: ReasoningChainRequest) -> Any:
    return graph_pb2.ReasoningChainRequest(
        graph_id=graph_id, from_id=request.from_id, to_id=request.to_id, max_depth=request.max_depth
    )


# ─── Transactions ───────────────────────────────────────────────────────────


def _graph_vector_map(vectors: Any) -> dict[str, Any]:
    return {name: _graph_vector(value) for name, value in _vector_map(vectors).items()}


def _collection_operation_proto(operation: CollectionOperation) -> Any:
    """Encodes one document-transaction operation.

    The match is exhaustive over ``CollectionOperation``; the final ``raise`` is what makes a member
    added to that union without a branch here fail loudly rather than be silently dropped from a
    transaction - which, in a surface whose whole promise is all-or-nothing, would be the worst kind
    of bug to ship.
    """
    encoded = data_pb2.DocumentOperationProto()
    if isinstance(operation, UpsertDocumentOp):
        encoded.upsert.CopyFrom(
            data_pb2.UpsertDocumentOp(
                id=operation.id,
                vectors=_vector_map(operation.vectors),
                metadata=to_struct(operation.metadata),
            )
        )
    elif isinstance(operation, UpsertKeyOp):
        encoded.upsert_by_key.CopyFrom(
            data_pb2.UpsertByKeyOp(
                external_key=operation.external_key,
                vectors=_vector_map(operation.vectors),
                metadata=to_struct(operation.metadata),
            )
        )
    elif isinstance(operation, RemoveDocumentOp):
        encoded.remove.CopyFrom(data_pb2.RemoveDocumentOp(document_id=operation.document_id))
    else:
        raise TypeError(f"Unsupported collection operation: {type(operation).__name__}")
    return encoded


def _graph_operation_proto(operation: GraphOperation) -> Any:
    """Encodes one graph-transaction operation. Exhaustive; see :func:`_collection_operation_proto`."""
    encoded = graph_pb2.GraphOperationProto()
    if isinstance(operation, AddNodeOp):
        encoded.add_node.CopyFrom(
            graph_pb2.AddNodeOp(
                labels=list(operation.labels),
                vectors=_graph_vector_map(operation.vectors),
                metadata=to_struct(operation.metadata),
            )
        )
    elif isinstance(operation, AddEdgeOp):
        encoded.add_edge.CopyFrom(
            graph_pb2.AddEdgeOp(
                source_id=operation.source_id,
                target_id=operation.target_id,
                type=operation.type,
                weight=operation.weight,
                metadata=to_struct(operation.metadata),
            )
        )
    elif isinstance(operation, RemoveNodeOp):
        if operation.external_key is not None:
            encoded.remove_node_by_key.CopyFrom(
                graph_pb2.RemoveNodeByKeyOp(external_key=operation.external_key)
            )
        else:
            encoded.remove_node.CopyFrom(graph_pb2.RemoveNodeOp(node_id=operation.node_id))
    elif isinstance(operation, RemoveEdgeOp):
        encoded.remove_edge.CopyFrom(graph_pb2.RemoveEdgeOp(edge_id=operation.edge_id))
    elif isinstance(operation, UpdateVectorOp):
        encoded.update_vector.CopyFrom(
            graph_pb2.UpdateVectorOp(
                node_id=operation.node_id,
                field_name=operation.field_name,
                vector=[float(each) for each in operation.vector],
            )
        )
    elif isinstance(operation, UpdateWeightOp):
        encoded.update_weight.CopyFrom(
            graph_pb2.UpdateWeightOp(edge_id=operation.edge_id, weight=operation.weight)
        )
    elif isinstance(operation, UpdateNodeMetadataOp):
        encoded.update_node_metadata.CopyFrom(
            graph_pb2.UpdateNodeMetadataOp(
                node_id=operation.node_id, metadata=to_struct(operation.metadata)
            )
        )
    elif isinstance(operation, UpdateEdgeMetadataOp):
        encoded.update_edge_metadata.CopyFrom(
            graph_pb2.UpdateEdgeMetadataOp(
                edge_id=operation.edge_id, metadata=to_struct(operation.metadata)
            )
        )
    elif isinstance(operation, UpsertNodeOp):
        upsert = graph_pb2.UpsertNodeOp(
            external_key=operation.external_key or "",
            labels=list(operation.labels),
            vectors=_graph_vector_map(operation.vectors),
            metadata=to_struct(operation.metadata),
        )
        if operation.node_id is not None:
            upsert.node_id = operation.node_id
        encoded.upsert_node.CopyFrom(upsert)
    else:
        raise TypeError(f"Unsupported graph operation: {type(operation).__name__}")
    return encoded


def execute_document_transaction(
    collection_id: str, operations: Sequence[CollectionOperation]
) -> Any:
    return data_pb2.ExecuteDocumentTransactionRequest(
        collection_id=collection_id,
        operations=[_collection_operation_proto(each) for each in operations],
    )


def execute_transaction(graph_id: str, operations: Sequence[GraphOperation]) -> Any:
    return graph_pb2.ExecuteTransactionRequest(
        graph_id=graph_id, operations=[_graph_operation_proto(each) for each in operations]
    )


# ─── CyQL statements ────────────────────────────────────────────────────────


def _statement_parameters(params: QueryParameters | None) -> tuple[dict[str, Any], Any]:
    """Splits bound parameters into the vector map and the scalar struct the requests carry."""
    if params is None:
        return {}, to_struct({})
    vectors = {
        name: data_pb2.VectorFieldProto(values=list(values))
        for name, values in params.vectors.items()
    }
    return vectors, to_struct(params.scalars)


def execute_statement(graph_id: str, statement: str, params: QueryParameters | None) -> Any:
    vectors, scalars = _statement_parameters(params)
    built = graph_pb2.ExecuteStatementRequest(
        graph_id=graph_id, statement=statement, parameters=scalars
    )
    for name, value in vectors.items():
        built.vectors[name].CopyFrom(_graph_vector(value))
    return built


def execute_collection_statement(
    collection_id: str, statement: str, params: QueryParameters | None
) -> Any:
    vectors, scalars = _statement_parameters(params)
    built = data_pb2.ExecuteCollectionStatementRequest(
        collection_id=collection_id, statement=statement, parameters=scalars
    )
    for name, value in vectors.items():
        built.vectors[name].CopyFrom(value)
    return built


def execute_project_statement(project_id: str, statement: str, params: QueryParameters | None) -> Any:
    _, scalars = _statement_parameters(params)
    return platform_pb2.ExecuteProjectStatementRequest(
        project_id=project_id, statement=statement, parameters=scalars
    )


# ─── Branching ──────────────────────────────────────────────────────────────


def fork_graph(project_id: str, graph_id: str, branch_name: str) -> Any:
    return platform_pb2.ForkGraphRequest(
        project_id=project_id, graph_id=graph_id, branch_name=branch_name
    )


def merge_graph(project_id: str, branch_id: str) -> Any:
    return platform_pb2.MergeGraphRequest(project_id=project_id, branch_id=branch_id)


def list_branches(project_id: str, graph_id: str) -> Any:
    return platform_pb2.ListBranchesRequest(project_id=project_id, graph_id=graph_id)


# ─── Communities ────────────────────────────────────────────────────────────


def detect_communities(graph_id: str, request: DetectCommunitiesRequest) -> Any:
    return graph_pb2.DetectCommunitiesRequest(
        graph_id          = graph_id,
        algorithm         = request.algorithm,
        resolution        = request.resolution,
        edge_weight_field = request.edge_weight_field or "",
        edge_types        = list(request.edge_types),
        max_levels        = request.max_levels,
        seed              = request.seed,
    )


def get_communities(graph_id: str, max_level: int, include_members: bool = False) -> Any:
    """Reads the stored hierarchy.

    ``include_members`` is off by default: a hierarchy read used to load every node id whether the
    caller wanted them or not (issue #320), which on a large graph is most of the response.
    """
    return graph_pb2.GetCommunitiesRequest(
        graph_id=graph_id, max_level=max_level, include_members=include_members
    )


def get_community_summaries(graph_id: str, request: GetCommunitySummariesRequest) -> Any:
    return graph_pb2.GetCommunitySummariesRequest(
        graph_id=graph_id, level=request.level,
        community_ids=list(request.community_ids), limit=request.limit,
    )


def get_community_members(graph_id: str, request: GetCommunityMembersRequest) -> Any:
    return graph_pb2.GetCommunityMembersRequest(
        graph_id=graph_id, level=request.level,
        community_ids=list(request.community_ids), limit=request.limit,
    )


def get_community_assignments(graph_id: str, level: int, node_ids: Sequence[int]) -> Any:
    return graph_pb2.GetCommunityAssignmentsRequest(
        graph_id=graph_id, level=level, node_ids=list(node_ids)
    )


def put_community_summaries(
    graph_id: str, summaries: Sequence[PutCommunitySummaryRequest]
) -> Any:
    """Builds a batch summary write.

    One call for one summary as well as for many: the batch is atomic (issue #319), and a
    single-summary write going through the same path is one fewer way for the two to diverge.
    """
    request = graph_pb2.PutCommunitySummariesRequest(graph_id=graph_id)
    for summary in summaries:
        entry = graph_pb2.CommunitySummaryProto(
            level=summary.level, community_id=summary.community_id, summary_text=summary.summary_text
        )
        for name, values in summary.vectors.items():
            entry.vectors[name].CopyFrom(graph_pb2.GraphVectorFieldProto(values=list(values)))
        request.summaries.append(entry)
    return request


def global_search(graph_id: str, request: GlobalSearchRequest) -> Any:
    built = graph_pb2.GlobalSearchRequest(
        graph_id                  = graph_id,
        query                     = request.query,
        query_vector              = list(request.query_vector),
        level                     = request.level,
        top_k                     = request.top_k,
        vector_field              = request.vector_field or "",
        include_members           = request.include_members,
        max_members_per_community = request.max_members_per_community,
        expand                    = request.expand,
        expand_depth              = request.expand_depth,
    )
    # The graph and nlsearch protos both import RerankOptionsProto from the data package rather than
    # declaring their own, so one encoder serves all three search surfaces.
    rerank = _rerank_proto(request.rerank)
    if rerank is not None:
        built.rerank.CopyFrom(rerank)
    return built


def community_status(graph_id: str) -> Any:
    return graph_pb2.CommunityStatusRequest(graph_id=graph_id)


# ─── Agentic memory ─────────────────────────────────────────────────────────


def observe(graph_id: str, request: ObserveRequest) -> Any:
    built = graph_pb2.ObserveRequest(
        graph_id   = graph_id,
        labels     = list(request.labels),
        link_field = request.link_field or "",
        threshold  = request.threshold,
        max_links  = request.max_links,
    )
    for name, value in _vector_map(request.vectors).items():
        built.vectors[name].CopyFrom(_graph_vector(value))
    if request.metadata:
        built.metadata.CopyFrom(to_struct(request.metadata))
    return built


def entity_link(graph_id: str, request: EntityLinkRequest) -> Any:
    return graph_pb2.EntityLinkRequest(
        graph_id=graph_id, field_name=request.field_name, node_id=request.node_id,
        threshold=request.threshold, max_links=request.max_links,
    )


def decay(graph_id: str, max_age_hours: int) -> Any:
    return graph_pb2.DecayRequest(graph_id=graph_id, max_age_hours=max_age_hours)


# ─── Natural-language search ────────────────────────────────────────────────


def nl_search_collection(collection_id: str, request: NlSearchRequest) -> Any:
    built = nlsearch_pb2.NlSearchCollectionRequest(
        collection_id=collection_id, query=request.query,
        vector_field=request.vector_field, max_results=request.max_results,
    )
    rerank = _rerank_proto(request.rerank)
    if rerank is not None:
        built.rerank.CopyFrom(rerank)
    return built


def nl_search_graph(graph_id: str, request: NlSearchRequest) -> Any:
    built = nlsearch_pb2.NlSearchGraphRequest(
        graph_id=graph_id, query=request.query,
        vector_field=request.vector_field, max_results=request.max_results,
    )
    rerank = _rerank_proto(request.rerank)
    if rerank is not None:
        built.rerank.CopyFrom(rerank)
    return built
