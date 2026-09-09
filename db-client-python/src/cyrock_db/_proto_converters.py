"""Proto response -> domain type. Pure, no I/O.

One of the two layers both client facades share, matching ``client-java``'s ``ProtoConverters``.
Keeping it free of transport means the synchronous and asynchronous clients differ only in how they
issue the call, never in what a response means.
"""

from __future__ import annotations

from typing import Any

from ._values_codec import from_struct
from .types import (
    Cardinality,
    ChangeEvent,
    ChangeOp,
    ChangeSource,
    CollectionDefinition,
    CommunityAssignments,
    CommunityHierarchy,
    CommunityMemberSet,
    CommunityRef,
    CommunityResult,
    CommunityStatus,
    CommunitySummaries,
    CommunitySummary,
    DecayResult,
    Document,
    Edge,
    EdgeInfo,
    EntityKind,
    GlobalSearchResult,
    GraphDefinition,
    GraphWindow,
    Match,
    MergeResult,
    MetadataFieldDefinition,
    MetadataFieldType,
    NeighborsWindow,
    NlMatch,
    NlSearchResult,
    Node,
    NodeMatch,
    ObserveResult,
    OperationResult,
    RefreshCommunitiesResult,
    SchemaChange,
    SimilarityFunction,
    StatementClass,
    StatementResult,
    StatementType,
    TransactionResult,
    WriteSummary,
)

__all__ = [
    "to_collection_definition",
    "to_document",
    "to_documents",
    "to_edge",
    "to_graph_window",
    "to_neighbors_window",
    "to_matches",
    "to_node",
    "to_node_matches",
    "to_statement_result",
    "to_transaction_result",
    "to_nodes",
    "to_collection_definitions",
    "to_graph_definition",
    "to_graph_definitions",
    "to_statement_class",
    "to_statement_type",
]


def to_statement_class(name: str) -> StatementClass:
    """Parses the wire's ``statement_class`` string.

    ``statement_class`` and ``statement_type`` are declared ``string`` in the proto, not enums, and
    the Java converter parses them with ``StatementClass.valueOf`` - which throws on a name it does
    not know. This matches that strictness deliberately: a name we cannot parse means the server is
    newer than this client, and failing loudly beats quietly reporting the wrong statement class to
    a caller routing on it.

    :raises ValueError: if the name is not one this client knows
    """
    try:
        return StatementClass[name]
    except KeyError as unknown:
        raise ValueError(
            f"Unknown statement class '{name}'. The server is likely newer than this client; "
            f"upgrade cyrock-db."
        ) from unknown


def to_statement_type(name: str) -> StatementType:
    """Parses the wire's ``statement_type`` string. See :func:`to_statement_class`.

    :raises ValueError: if the name is not one this client knows
    """
    try:
        return StatementType[name]
    except KeyError as unknown:
        raise ValueError(
            f"Unknown statement type '{name}'. The server is likely newer than this client; "
            f"upgrade cyrock-db."
        ) from unknown


def _to_vector_field(proto: Any) -> Any:
    from .types._definitions import VectorFieldDefinition

    return VectorFieldDefinition(
        name                = proto.name,
        dimension           = proto.dimension,
        similarity_function = SimilarityFunction[proto.similarity_function]
                              if proto.similarity_function else None,  # type: ignore[arg-type]
        max_degree          = proto.max_degree,
        beam_width          = proto.beam_width,
        neighbor_overflow   = proto.neighbor_overflow,
        alpha               = proto.alpha,
        embedding_model     = proto.embedding_model or None,
        eventual_indexing   = proto.eventual_indexing,
    )


def _to_metadata_field(proto: Any) -> MetadataFieldDefinition:
    return MetadataFieldDefinition(
        name        = proto.name,
        type        = MetadataFieldType[proto.type],
        # A definition that came off the wire always names one; HIGH is the read-side fallback for a
        # server that somehow sent none, chosen because it is what an indexed field wants and because
        # refusing to decode a stored definition would be worse than assuming.
        cardinality = Cardinality[proto.cardinality] if proto.cardinality else Cardinality.HIGH,
        fulltext    = proto.fulltext,
        # MetadataFieldDefinitionProto carries no `unique` field, so a unique constraint cannot come
        # back off the wire and is left at its default here. That is issue #227, not an omission in
        # this converter: UNIQUE is unreachable over gRPC on the Java side too, and fixing it is a
        # proto change both SDKs pick up together.
    )


def to_collection_definition(proto: Any) -> CollectionDefinition:
    return CollectionDefinition(
        id              = proto.id or None,
        name            = proto.name or None,
        vector_fields   = tuple(_to_vector_field(each)   for each in proto.vector_fields),
        metadata_fields = tuple(_to_metadata_field(each) for each in proto.metadata_fields),
    )


def to_collection_definitions(proto: Any) -> tuple[CollectionDefinition, ...]:
    return tuple(to_collection_definition(each) for each in proto.collections)


def to_graph_definition(proto: Any) -> GraphDefinition:
    return GraphDefinition(
        id                       = proto.id or None,
        name                     = proto.name or None,
        node_vector_fields       = tuple(_to_vector_field(each)   for each in proto.node_vector_fields),
        node_metadata_fields     = tuple(_to_metadata_field(each) for each in proto.node_metadata_fields),
        edge_metadata_fields     = tuple(_to_metadata_field(each) for each in proto.edge_metadata_fields),
        enable_temporal_tracking = proto.enable_temporal_tracking,
        auto_link_threshold      = proto.auto_link_threshold,
        parent_graph_id          = proto.parent_graph_id or None,
        forked_at                = proto.forked_at,
        branch_name              = proto.branch_name or None,
    )


def to_graph_definitions(proto: Any) -> tuple[GraphDefinition, ...]:
    return tuple(to_graph_definition(each) for each in proto.graphs)


def to_document(proto: Any) -> Document:
    """Decodes a ``DocumentProto``.

    Only the ``values`` half of each vector field is read: ``text`` is an *input*, asking the server
    to embed, and a stored document carries the embedding rather than the phrase that produced it.
    """
    return Document(
        id           = proto.id,
        vectors      = {
            name: tuple(field.values) for name, field in proto.vectors.items()
        },
        metadata     = from_struct(proto.metadata) if proto.HasField("metadata") else {},
        external_key = proto.external_key if proto.HasField("external_key") else None,
    )


def to_documents(proto: Any) -> tuple[Document, ...]:
    return tuple(to_document(each) for each in proto.documents)


def to_matches(proto: Any) -> tuple[Match, ...]:
    """Decodes a list of search hits."""
    return tuple(Match(score=each.score, document=to_document(each.document)) for each in proto.matches)


def to_node(proto: Any) -> Node:
    """Decodes a ``NodeProto``.

    ``vectors`` is empty when the read did not ask for them - which is the default on the listing and
    keyed-read paths - so an empty mapping means "not requested" as often as it means "none stored".
    """
    return Node(
        id           = proto.id,
        labels       = tuple(proto.labels),
        external_key = proto.external_key if proto.HasField("external_key") else None,
        vectors      = {name: tuple(field.values) for name, field in proto.vectors.items()},
        metadata     = from_struct(proto.metadata) if proto.HasField("metadata") else {},
        created_at   = proto.created_at,
    )


def to_nodes(proto: Any) -> tuple[Node, ...]:
    return tuple(to_node(each) for each in proto.nodes)


def to_edge(proto: Any) -> Edge:
    return Edge(
        id         = proto.id,
        type       = proto.type,
        source_id  = proto.source_id,
        target_id  = proto.target_id,
        weight     = proto.weight,
        metadata   = from_struct(proto.metadata) if proto.HasField("metadata") else {},
        created_at = proto.created_at,
    )


def to_graph_window(proto: Any) -> GraphWindow:
    return GraphWindow(
        nodes=tuple(to_node(each) for each in proto.nodes),
        edges=tuple(to_edge(each) for each in proto.edges),
    )


def to_neighbors_window(proto: Any) -> NeighborsWindow:
    return NeighborsWindow(
        nodes=tuple(to_node(each) for each in proto.nodes),
        edges=tuple(to_edge(each) for each in proto.edges),
        truncated=proto.truncated,
    )


def to_node_matches(proto: Any) -> tuple[NodeMatch, ...]:
    """Decodes a list of similarity hits."""
    return tuple(NodeMatch(score=each.score, node=to_node(each.node)) for each in proto.matches)


def to_transaction_result(proto: Any) -> TransactionResult:
    """Decodes per-operation transaction results.

    An operation's ``error`` explains why the transaction rolled back, not that this one operation
    failed while the others stood: the surface is all-or-nothing.
    """
    return TransactionResult(
        results=tuple(
            OperationResult(
                index=each.index, generated_id=each.generated_id, error=each.error or None
            )
            for each in proto.results
        )
    )


def _to_write_summary(proto: Any) -> WriteSummary:
    return WriteSummary(
        nodes_created    = proto.nodes_created,
        nodes_deleted    = proto.nodes_deleted,
        edges_created    = proto.edges_created,
        edges_deleted    = proto.edges_deleted,
        properties_set   = proto.properties_set,
        created_node_ids = tuple(proto.created_node_ids),
        created_edge_ids = tuple(proto.created_edge_ids),
    )


def to_statement_result(proto: Any) -> StatementResult:
    """Decodes any of the three statement responses.

    They are deliberately separate messages - a collection has documents, a graph has nodes and
    edges, a project statement is DDL - but share one row encoding and these five field names, so one
    converter reads all three, as the Java one does.

    ``statement_class`` and ``statement_type`` are strings on the wire and are parsed strictly: an
    unrecognised name means the server is newer than this client, and failing loudly beats reporting
    the wrong class to a caller routing on it.
    """
    # hasattr first, then HasField: HasField raises on a message that has no such field, and
    # ProjectStatementResponse genuinely has no `summary` - a project statement is DDL and writes no
    # rows. The order matters, and the wrong one only fails on that one response type.
    summary = (
        _to_write_summary(proto.summary)
        if hasattr(proto, "summary") and proto.HasField("summary")
        else None
    )
    definition = (
        to_graph_definition(proto.definition)
        if hasattr(proto, "definition") and proto.HasField("definition")
        else None
    )
    return StatementResult(
        statement_class = to_statement_class(proto.statement_class),
        statement_type  = to_statement_type(proto.statement_type),
        columns         = tuple(proto.columns),
        rows            = tuple(from_struct(row.values) for row in proto.rows),
        summary         = summary,
        definition      = definition,
    )


# ─── Branching ──────────────────────────────────────────────────────────────


def to_merge_result(proto: Any) -> MergeResult:
    return MergeResult(
        nodes_added   = proto.nodes_added,
        nodes_removed = proto.nodes_removed,
        nodes_updated = proto.nodes_updated,
        edges_added   = proto.edges_added,
        edges_removed = proto.edges_removed,
        edges_updated = proto.edges_updated,
    )


# ─── Communities ────────────────────────────────────────────────────────────


def _to_community_ref(proto: Any) -> CommunityRef:
    return CommunityRef(level=proto.level, community_id=proto.community_id)


def to_community_hierarchy(proto: Any) -> CommunityHierarchy:
    """Decodes a ``DetectCommunitiesResponse``, which both detection and the stored read return."""
    return CommunityHierarchy(
        communities = tuple(
            CommunityResult(
                id=each.id, level=each.level, parent_id=each.parent_id, size=each.size,
                member_node_ids=tuple(each.member_node_ids),
            )
            for each in proto.communities
        ),
        levels      = proto.levels,
        algorithm   = proto.algorithm,
        detected_at = proto.detected_at,
        stale_communities = tuple(
            _to_community_ref(each) for each in getattr(proto, "stale_communities", ())
        ),
    )


def to_community_summaries(proto: Any) -> CommunitySummaries:
    return CommunitySummaries(
        summaries=tuple(
            CommunitySummary(
                level=each.level, community_id=each.community_id, summary_text=each.summary_text
            )
            for each in proto.summaries
        ),
        truncated=proto.truncated,
    )


def to_community_member_sets(proto: Any) -> tuple[CommunityMemberSet, ...]:
    return tuple(
        CommunityMemberSet(
            level=each.level, community_id=each.community_id,
            member_node_ids=tuple(each.member_node_ids), truncated=each.truncated,
        )
        for each in proto.communities
    )


def to_community_assignments(proto: Any) -> CommunityAssignments:
    return CommunityAssignments(
        by_node={each.node_id: each.community_id for each in proto.assignments},
        levels=proto.levels,
    )


def to_community_status(proto: Any) -> CommunityStatus:
    return CommunityStatus(
        detected        = proto.detected,
        detected_at     = proto.detected_at,
        stale           = proto.stale,
        levels          = proto.levels,
        community_count = proto.community_count,
        summary_count   = proto.summary_count,
    )


def to_global_search_results(proto: Any) -> tuple[GlobalSearchResult, ...]:
    return tuple(
        GlobalSearchResult(
            community_id=each.community_id, level=each.level, score=each.score,
            summary_text=each.summary_text, parent_community_id=each.parent_community_id,
            member_node_ids=tuple(each.member_node_ids),
        )
        for each in proto.results
    )


def to_refresh_communities_result(proto: Any) -> RefreshCommunitiesResult:
    return RefreshCommunitiesResult(
        hierarchy=to_community_hierarchy(proto.hierarchy),
        pruned_summaries=proto.pruned_summaries,
        stale_communities=tuple(_to_community_ref(each) for each in proto.stale_communities),
    )


# ─── Agentic memory ─────────────────────────────────────────────────────────


def to_observe_result(proto: Any) -> ObserveResult:
    """Decodes an ``ObserveResponse``.

    The wire field is ``linked_ids`` and the domain name is ``linked_edge_ids``, as in Java: they are
    edge ids, and the shorter wire name has been read as node ids before.
    """
    return ObserveResult(node_id=proto.node_id, linked_edge_ids=tuple(proto.linked_ids))


def to_decay_result(proto: Any) -> DecayResult:
    return DecayResult(pruned_nodes=proto.pruned_nodes, pruned_edges=proto.pruned_edges)


def to_edges(proto: Any) -> tuple[Edge, ...]:
    return tuple(to_edge(each) for each in proto.edges)


# ─── Natural-language search ────────────────────────────────────────────────


def to_nl_search_result(proto: Any) -> NlSearchResult:
    return NlSearchResult(
        matches=tuple(
            NlMatch(id=each.id, score=each.score, metadata=from_struct(each.metadata))
            for each in proto.matches
        ),
        translated_query=proto.translated_query,
        query_type=proto.query_type,
    )


# ─── Change Data Capture ────────────────────────────────────────────────────


def _enum_or_unspecified(enum_type: Any, name: str) -> Any:
    """Reads a wire enum by name, falling back to UNSPECIFIED for one this build does not know.

    Unlike the statement enums, an unknown value here is not worth failing the stream over: a change
    of a kind this client cannot name is still a change at an LSN the consumer must checkpoint, and
    dropping the whole subscription would cost it every other event too.
    """
    try:
        return enum_type(name)
    except ValueError:
        return enum_type.UNSPECIFIED


def to_change_event(proto: Any) -> ChangeEvent:
    """Decodes a ``ChangeEvent``."""
    source = ChangeSource(
        resource_kind = proto.source.resource_kind,
        resource_id   = proto.source.resource_id,
        lsn           = proto.source.lsn,
        tx_id         = proto.source.tx_id,
        ts_ms         = proto.source.ts_ms,
    )
    if proto.snapshot_complete:
        # Every other field is unset on the marker; decoding them would invent defaults that read as
        # real values - an entity_id of 0, which is a valid id.
        return ChangeEvent(source=source, snapshot_complete=True)

    from ._proto import cyrock_db_cdc_pb2 as cdc_pb2

    return ChangeEvent(
        source       = source,
        op           = _enum_or_unspecified(ChangeOp, cdc_pb2.ChangeOp.Name(proto.op)),
        entity_kind  = _enum_or_unspecified(EntityKind, cdc_pb2.EntityKind.Name(proto.entity_kind)),
        entity_id    = proto.entity_id,
        external_key = proto.external_key if proto.HasField("external_key") else None,
        labels       = tuple(proto.labels),
        metadata     = from_struct(proto.metadata) if proto.HasField("metadata") else {},
        vectors      = {name: tuple(v.values) for name, v in proto.vectors.items()},
        edge         = (
            EdgeInfo(
                source_id=proto.edge.source_id, target_id=proto.edge.target_id,
                type=proto.edge.type, weight=proto.edge.weight,
            )
            if proto.HasField("edge") else None
        ),
        schema       = (
            SchemaChange(
                added_fields=tuple(proto.schema.added_fields),
                dropped_fields=tuple(proto.schema.dropped_fields),
            )
            if proto.HasField("schema") else None
        ),
    )
