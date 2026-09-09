import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
import cyrock_db_value_pb2 as _cyrock_db_value_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class IdRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class Empty(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class OrganizationProto(_message.Message):
    __slots__ = ("id", "name", "created_at", "enabled")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    ENABLED_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    created_at: _timestamp_pb2.Timestamp
    enabled: bool
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., enabled: bool = ...) -> None: ...

class CreateOrganizationRequest(_message.Message):
    __slots__ = ("name",)
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class UpdateOrganizationRequest(_message.Message):
    __slots__ = ("id", "name", "enabled")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    ENABLED_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    enabled: bool
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., enabled: bool = ...) -> None: ...

class OrganizationList(_message.Message):
    __slots__ = ("organizations",)
    ORGANIZATIONS_FIELD_NUMBER: _ClassVar[int]
    organizations: _containers.RepeatedCompositeFieldContainer[OrganizationProto]
    def __init__(self, organizations: _Optional[_Iterable[_Union[OrganizationProto, _Mapping]]] = ...) -> None: ...

class ProjectProto(_message.Message):
    __slots__ = ("id", "organization_id", "name", "created_at", "enabled")
    ID_FIELD_NUMBER: _ClassVar[int]
    ORGANIZATION_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    ENABLED_FIELD_NUMBER: _ClassVar[int]
    id: str
    organization_id: str
    name: str
    created_at: _timestamp_pb2.Timestamp
    enabled: bool
    def __init__(self, id: _Optional[str] = ..., organization_id: _Optional[str] = ..., name: _Optional[str] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., enabled: bool = ...) -> None: ...

class CreateProjectRequest(_message.Message):
    __slots__ = ("organization_id", "name")
    ORGANIZATION_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    organization_id: str
    name: str
    def __init__(self, organization_id: _Optional[str] = ..., name: _Optional[str] = ...) -> None: ...

class UpdateProjectRequest(_message.Message):
    __slots__ = ("id", "name", "enabled")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    ENABLED_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    enabled: bool
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., enabled: bool = ...) -> None: ...

class ProjectList(_message.Message):
    __slots__ = ("projects",)
    PROJECTS_FIELD_NUMBER: _ClassVar[int]
    projects: _containers.RepeatedCompositeFieldContainer[ProjectProto]
    def __init__(self, projects: _Optional[_Iterable[_Union[ProjectProto, _Mapping]]] = ...) -> None: ...

class MetadataFieldDefinitionProto(_message.Message):
    __slots__ = ("name", "type", "cardinality", "fulltext", "unique")
    NAME_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    CARDINALITY_FIELD_NUMBER: _ClassVar[int]
    FULLTEXT_FIELD_NUMBER: _ClassVar[int]
    UNIQUE_FIELD_NUMBER: _ClassVar[int]
    name: str
    type: str
    cardinality: str
    fulltext: bool
    unique: bool
    def __init__(self, name: _Optional[str] = ..., type: _Optional[str] = ..., cardinality: _Optional[str] = ..., fulltext: bool = ..., unique: bool = ...) -> None: ...

class VectorFieldDefinitionProto(_message.Message):
    __slots__ = ("name", "dimension", "similarity_function", "max_degree", "beam_width", "neighbor_overflow", "alpha", "embedding_model", "eventual_indexing")
    NAME_FIELD_NUMBER: _ClassVar[int]
    DIMENSION_FIELD_NUMBER: _ClassVar[int]
    SIMILARITY_FUNCTION_FIELD_NUMBER: _ClassVar[int]
    MAX_DEGREE_FIELD_NUMBER: _ClassVar[int]
    BEAM_WIDTH_FIELD_NUMBER: _ClassVar[int]
    NEIGHBOR_OVERFLOW_FIELD_NUMBER: _ClassVar[int]
    ALPHA_FIELD_NUMBER: _ClassVar[int]
    EMBEDDING_MODEL_FIELD_NUMBER: _ClassVar[int]
    EVENTUAL_INDEXING_FIELD_NUMBER: _ClassVar[int]
    name: str
    dimension: int
    similarity_function: str
    max_degree: int
    beam_width: int
    neighbor_overflow: float
    alpha: float
    embedding_model: str
    eventual_indexing: bool
    def __init__(self, name: _Optional[str] = ..., dimension: _Optional[int] = ..., similarity_function: _Optional[str] = ..., max_degree: _Optional[int] = ..., beam_width: _Optional[int] = ..., neighbor_overflow: _Optional[float] = ..., alpha: _Optional[float] = ..., embedding_model: _Optional[str] = ..., eventual_indexing: bool = ...) -> None: ...

class CollectionDefinitionProto(_message.Message):
    __slots__ = ("id", "name", "vector_fields", "metadata_fields")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    VECTOR_FIELDS_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELDS_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    vector_fields: _containers.RepeatedCompositeFieldContainer[VectorFieldDefinitionProto]
    metadata_fields: _containers.RepeatedCompositeFieldContainer[MetadataFieldDefinitionProto]
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., vector_fields: _Optional[_Iterable[_Union[VectorFieldDefinitionProto, _Mapping]]] = ..., metadata_fields: _Optional[_Iterable[_Union[MetadataFieldDefinitionProto, _Mapping]]] = ...) -> None: ...

class CreateCollectionDefinitionRequest(_message.Message):
    __slots__ = ("project_id", "name", "vector_fields", "metadata_fields")
    PROJECT_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    VECTOR_FIELDS_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELDS_FIELD_NUMBER: _ClassVar[int]
    project_id: str
    name: str
    vector_fields: _containers.RepeatedCompositeFieldContainer[VectorFieldDefinitionProto]
    metadata_fields: _containers.RepeatedCompositeFieldContainer[MetadataFieldDefinitionProto]
    def __init__(self, project_id: _Optional[str] = ..., name: _Optional[str] = ..., vector_fields: _Optional[_Iterable[_Union[VectorFieldDefinitionProto, _Mapping]]] = ..., metadata_fields: _Optional[_Iterable[_Union[MetadataFieldDefinitionProto, _Mapping]]] = ...) -> None: ...

class UpdateCollectionDefinitionRequest(_message.Message):
    __slots__ = ("id", "name")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ...) -> None: ...

class UpdateGraphDefinitionRequest(_message.Message):
    __slots__ = ("id", "name")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ...) -> None: ...

class ProjectIdRequest(_message.Message):
    __slots__ = ("project_id",)
    PROJECT_ID_FIELD_NUMBER: _ClassVar[int]
    project_id: str
    def __init__(self, project_id: _Optional[str] = ...) -> None: ...

class CollectionIdRequest(_message.Message):
    __slots__ = ("project_id", "collection_id")
    PROJECT_ID_FIELD_NUMBER: _ClassVar[int]
    COLLECTION_ID_FIELD_NUMBER: _ClassVar[int]
    project_id: str
    collection_id: str
    def __init__(self, project_id: _Optional[str] = ..., collection_id: _Optional[str] = ...) -> None: ...

class CollectionDefinitionList(_message.Message):
    __slots__ = ("collections",)
    COLLECTIONS_FIELD_NUMBER: _ClassVar[int]
    collections: _containers.RepeatedCompositeFieldContainer[CollectionDefinitionProto]
    def __init__(self, collections: _Optional[_Iterable[_Union[CollectionDefinitionProto, _Mapping]]] = ...) -> None: ...

class OrgIdRequest(_message.Message):
    __slots__ = ("organization_id",)
    ORGANIZATION_ID_FIELD_NUMBER: _ClassVar[int]
    organization_id: str
    def __init__(self, organization_id: _Optional[str] = ...) -> None: ...

class ScopedCollectionDefinitionProto(_message.Message):
    __slots__ = ("collection", "organization_id", "project_id")
    COLLECTION_FIELD_NUMBER: _ClassVar[int]
    ORGANIZATION_ID_FIELD_NUMBER: _ClassVar[int]
    PROJECT_ID_FIELD_NUMBER: _ClassVar[int]
    collection: CollectionDefinitionProto
    organization_id: str
    project_id: str
    def __init__(self, collection: _Optional[_Union[CollectionDefinitionProto, _Mapping]] = ..., organization_id: _Optional[str] = ..., project_id: _Optional[str] = ...) -> None: ...

class ScopedCollectionDefinitionList(_message.Message):
    __slots__ = ("collections",)
    COLLECTIONS_FIELD_NUMBER: _ClassVar[int]
    collections: _containers.RepeatedCompositeFieldContainer[ScopedCollectionDefinitionProto]
    def __init__(self, collections: _Optional[_Iterable[_Union[ScopedCollectionDefinitionProto, _Mapping]]] = ...) -> None: ...

class GraphDefinitionProto(_message.Message):
    __slots__ = ("id", "name", "node_vector_fields", "node_metadata_fields", "edge_metadata_fields", "enable_temporal_tracking", "auto_link_threshold", "parent_graph_id", "forked_at", "branch_name")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    NODE_VECTOR_FIELDS_FIELD_NUMBER: _ClassVar[int]
    NODE_METADATA_FIELDS_FIELD_NUMBER: _ClassVar[int]
    EDGE_METADATA_FIELDS_FIELD_NUMBER: _ClassVar[int]
    ENABLE_TEMPORAL_TRACKING_FIELD_NUMBER: _ClassVar[int]
    AUTO_LINK_THRESHOLD_FIELD_NUMBER: _ClassVar[int]
    PARENT_GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    FORKED_AT_FIELD_NUMBER: _ClassVar[int]
    BRANCH_NAME_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    node_vector_fields: _containers.RepeatedCompositeFieldContainer[VectorFieldDefinitionProto]
    node_metadata_fields: _containers.RepeatedCompositeFieldContainer[MetadataFieldDefinitionProto]
    edge_metadata_fields: _containers.RepeatedCompositeFieldContainer[MetadataFieldDefinitionProto]
    enable_temporal_tracking: bool
    auto_link_threshold: float
    parent_graph_id: str
    forked_at: int
    branch_name: str
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., node_vector_fields: _Optional[_Iterable[_Union[VectorFieldDefinitionProto, _Mapping]]] = ..., node_metadata_fields: _Optional[_Iterable[_Union[MetadataFieldDefinitionProto, _Mapping]]] = ..., edge_metadata_fields: _Optional[_Iterable[_Union[MetadataFieldDefinitionProto, _Mapping]]] = ..., enable_temporal_tracking: bool = ..., auto_link_threshold: _Optional[float] = ..., parent_graph_id: _Optional[str] = ..., forked_at: _Optional[int] = ..., branch_name: _Optional[str] = ...) -> None: ...

class CreateGraphDefinitionRequest(_message.Message):
    __slots__ = ("project_id", "name", "node_vector_fields", "node_metadata_fields", "edge_metadata_fields", "enable_temporal_tracking", "auto_link_threshold")
    PROJECT_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    NODE_VECTOR_FIELDS_FIELD_NUMBER: _ClassVar[int]
    NODE_METADATA_FIELDS_FIELD_NUMBER: _ClassVar[int]
    EDGE_METADATA_FIELDS_FIELD_NUMBER: _ClassVar[int]
    ENABLE_TEMPORAL_TRACKING_FIELD_NUMBER: _ClassVar[int]
    AUTO_LINK_THRESHOLD_FIELD_NUMBER: _ClassVar[int]
    project_id: str
    name: str
    node_vector_fields: _containers.RepeatedCompositeFieldContainer[VectorFieldDefinitionProto]
    node_metadata_fields: _containers.RepeatedCompositeFieldContainer[MetadataFieldDefinitionProto]
    edge_metadata_fields: _containers.RepeatedCompositeFieldContainer[MetadataFieldDefinitionProto]
    enable_temporal_tracking: bool
    auto_link_threshold: float
    def __init__(self, project_id: _Optional[str] = ..., name: _Optional[str] = ..., node_vector_fields: _Optional[_Iterable[_Union[VectorFieldDefinitionProto, _Mapping]]] = ..., node_metadata_fields: _Optional[_Iterable[_Union[MetadataFieldDefinitionProto, _Mapping]]] = ..., edge_metadata_fields: _Optional[_Iterable[_Union[MetadataFieldDefinitionProto, _Mapping]]] = ..., enable_temporal_tracking: bool = ..., auto_link_threshold: _Optional[float] = ...) -> None: ...

class GraphIdRequest(_message.Message):
    __slots__ = ("project_id", "graph_id")
    PROJECT_ID_FIELD_NUMBER: _ClassVar[int]
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    project_id: str
    graph_id: str
    def __init__(self, project_id: _Optional[str] = ..., graph_id: _Optional[str] = ...) -> None: ...

class GraphDefinitionList(_message.Message):
    __slots__ = ("graphs",)
    GRAPHS_FIELD_NUMBER: _ClassVar[int]
    graphs: _containers.RepeatedCompositeFieldContainer[GraphDefinitionProto]
    def __init__(self, graphs: _Optional[_Iterable[_Union[GraphDefinitionProto, _Mapping]]] = ...) -> None: ...

class ScopedGraphDefinitionProto(_message.Message):
    __slots__ = ("graph", "organization_id", "project_id")
    GRAPH_FIELD_NUMBER: _ClassVar[int]
    ORGANIZATION_ID_FIELD_NUMBER: _ClassVar[int]
    PROJECT_ID_FIELD_NUMBER: _ClassVar[int]
    graph: GraphDefinitionProto
    organization_id: str
    project_id: str
    def __init__(self, graph: _Optional[_Union[GraphDefinitionProto, _Mapping]] = ..., organization_id: _Optional[str] = ..., project_id: _Optional[str] = ...) -> None: ...

class ScopedGraphDefinitionList(_message.Message):
    __slots__ = ("graphs",)
    GRAPHS_FIELD_NUMBER: _ClassVar[int]
    graphs: _containers.RepeatedCompositeFieldContainer[ScopedGraphDefinitionProto]
    def __init__(self, graphs: _Optional[_Iterable[_Union[ScopedGraphDefinitionProto, _Mapping]]] = ...) -> None: ...

class ForkGraphRequest(_message.Message):
    __slots__ = ("project_id", "graph_id", "branch_name")
    PROJECT_ID_FIELD_NUMBER: _ClassVar[int]
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    BRANCH_NAME_FIELD_NUMBER: _ClassVar[int]
    project_id: str
    graph_id: str
    branch_name: str
    def __init__(self, project_id: _Optional[str] = ..., graph_id: _Optional[str] = ..., branch_name: _Optional[str] = ...) -> None: ...

class MergeGraphRequest(_message.Message):
    __slots__ = ("project_id", "branch_id")
    PROJECT_ID_FIELD_NUMBER: _ClassVar[int]
    BRANCH_ID_FIELD_NUMBER: _ClassVar[int]
    project_id: str
    branch_id: str
    def __init__(self, project_id: _Optional[str] = ..., branch_id: _Optional[str] = ...) -> None: ...

class MergeGraphResponse(_message.Message):
    __slots__ = ("nodes_added", "nodes_removed", "nodes_updated", "edges_added", "edges_removed", "edges_updated")
    NODES_ADDED_FIELD_NUMBER: _ClassVar[int]
    NODES_REMOVED_FIELD_NUMBER: _ClassVar[int]
    NODES_UPDATED_FIELD_NUMBER: _ClassVar[int]
    EDGES_ADDED_FIELD_NUMBER: _ClassVar[int]
    EDGES_REMOVED_FIELD_NUMBER: _ClassVar[int]
    EDGES_UPDATED_FIELD_NUMBER: _ClassVar[int]
    nodes_added: int
    nodes_removed: int
    nodes_updated: int
    edges_added: int
    edges_removed: int
    edges_updated: int
    def __init__(self, nodes_added: _Optional[int] = ..., nodes_removed: _Optional[int] = ..., nodes_updated: _Optional[int] = ..., edges_added: _Optional[int] = ..., edges_removed: _Optional[int] = ..., edges_updated: _Optional[int] = ...) -> None: ...

class ListBranchesRequest(_message.Message):
    __slots__ = ("project_id", "graph_id")
    PROJECT_ID_FIELD_NUMBER: _ClassVar[int]
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    project_id: str
    graph_id: str
    def __init__(self, project_id: _Optional[str] = ..., graph_id: _Optional[str] = ...) -> None: ...

class ExecuteProjectStatementRequest(_message.Message):
    __slots__ = ("project_id", "statement", "parameters")
    PROJECT_ID_FIELD_NUMBER: _ClassVar[int]
    STATEMENT_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    project_id: str
    statement: str
    parameters: _cyrock_db_value_pb2.CyrockStruct
    def __init__(self, project_id: _Optional[str] = ..., statement: _Optional[str] = ..., parameters: _Optional[_Union[_cyrock_db_value_pb2.CyrockStruct, _Mapping]] = ...) -> None: ...

class StatementRowProto(_message.Message):
    __slots__ = ("values",)
    VALUES_FIELD_NUMBER: _ClassVar[int]
    values: _cyrock_db_value_pb2.CyrockStruct
    def __init__(self, values: _Optional[_Union[_cyrock_db_value_pb2.CyrockStruct, _Mapping]] = ...) -> None: ...

class ProjectStatementResponse(_message.Message):
    __slots__ = ("statement_class", "statement_type", "columns", "rows", "definition")
    STATEMENT_CLASS_FIELD_NUMBER: _ClassVar[int]
    STATEMENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    COLUMNS_FIELD_NUMBER: _ClassVar[int]
    ROWS_FIELD_NUMBER: _ClassVar[int]
    DEFINITION_FIELD_NUMBER: _ClassVar[int]
    statement_class: str
    statement_type: str
    columns: _containers.RepeatedScalarFieldContainer[str]
    rows: _containers.RepeatedCompositeFieldContainer[StatementRowProto]
    definition: GraphDefinitionProto
    def __init__(self, statement_class: _Optional[str] = ..., statement_type: _Optional[str] = ..., columns: _Optional[_Iterable[str]] = ..., rows: _Optional[_Iterable[_Union[StatementRowProto, _Mapping]]] = ..., definition: _Optional[_Union[GraphDefinitionProto, _Mapping]] = ...) -> None: ...

class CollectionCreatedEvent(_message.Message):
    __slots__ = ("collection", "organization_id", "project_id")
    COLLECTION_FIELD_NUMBER: _ClassVar[int]
    ORGANIZATION_ID_FIELD_NUMBER: _ClassVar[int]
    PROJECT_ID_FIELD_NUMBER: _ClassVar[int]
    collection: CollectionDefinitionProto
    organization_id: str
    project_id: str
    def __init__(self, collection: _Optional[_Union[CollectionDefinitionProto, _Mapping]] = ..., organization_id: _Optional[str] = ..., project_id: _Optional[str] = ...) -> None: ...

class CollectionUpdatedEvent(_message.Message):
    __slots__ = ("collection", "organization_id", "project_id")
    COLLECTION_FIELD_NUMBER: _ClassVar[int]
    ORGANIZATION_ID_FIELD_NUMBER: _ClassVar[int]
    PROJECT_ID_FIELD_NUMBER: _ClassVar[int]
    collection: CollectionDefinitionProto
    organization_id: str
    project_id: str
    def __init__(self, collection: _Optional[_Union[CollectionDefinitionProto, _Mapping]] = ..., organization_id: _Optional[str] = ..., project_id: _Optional[str] = ...) -> None: ...

class CollectionDeletedEvent(_message.Message):
    __slots__ = ("collection_id",)
    COLLECTION_ID_FIELD_NUMBER: _ClassVar[int]
    collection_id: str
    def __init__(self, collection_id: _Optional[str] = ...) -> None: ...

class LeaseGrantedEvent(_message.Message):
    __slots__ = ("collection", "organization_id", "project_id", "epoch")
    COLLECTION_FIELD_NUMBER: _ClassVar[int]
    ORGANIZATION_ID_FIELD_NUMBER: _ClassVar[int]
    PROJECT_ID_FIELD_NUMBER: _ClassVar[int]
    EPOCH_FIELD_NUMBER: _ClassVar[int]
    collection: CollectionDefinitionProto
    organization_id: str
    project_id: str
    epoch: int
    def __init__(self, collection: _Optional[_Union[CollectionDefinitionProto, _Mapping]] = ..., organization_id: _Optional[str] = ..., project_id: _Optional[str] = ..., epoch: _Optional[int] = ...) -> None: ...

class LeaseRevokedEvent(_message.Message):
    __slots__ = ("collection_id",)
    COLLECTION_ID_FIELD_NUMBER: _ClassVar[int]
    collection_id: str
    def __init__(self, collection_id: _Optional[str] = ...) -> None: ...

class GraphCreatedEvent(_message.Message):
    __slots__ = ("graph", "organization_id", "project_id")
    GRAPH_FIELD_NUMBER: _ClassVar[int]
    ORGANIZATION_ID_FIELD_NUMBER: _ClassVar[int]
    PROJECT_ID_FIELD_NUMBER: _ClassVar[int]
    graph: GraphDefinitionProto
    organization_id: str
    project_id: str
    def __init__(self, graph: _Optional[_Union[GraphDefinitionProto, _Mapping]] = ..., organization_id: _Optional[str] = ..., project_id: _Optional[str] = ...) -> None: ...

class GraphUpdatedEvent(_message.Message):
    __slots__ = ("graph", "organization_id", "project_id")
    GRAPH_FIELD_NUMBER: _ClassVar[int]
    ORGANIZATION_ID_FIELD_NUMBER: _ClassVar[int]
    PROJECT_ID_FIELD_NUMBER: _ClassVar[int]
    graph: GraphDefinitionProto
    organization_id: str
    project_id: str
    def __init__(self, graph: _Optional[_Union[GraphDefinitionProto, _Mapping]] = ..., organization_id: _Optional[str] = ..., project_id: _Optional[str] = ...) -> None: ...

class GraphDeletedEvent(_message.Message):
    __slots__ = ("graph_id",)
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    graph_id: str
    def __init__(self, graph_id: _Optional[str] = ...) -> None: ...

class GraphLeaseGrantedEvent(_message.Message):
    __slots__ = ("graph", "organization_id", "project_id", "epoch")
    GRAPH_FIELD_NUMBER: _ClassVar[int]
    ORGANIZATION_ID_FIELD_NUMBER: _ClassVar[int]
    PROJECT_ID_FIELD_NUMBER: _ClassVar[int]
    EPOCH_FIELD_NUMBER: _ClassVar[int]
    graph: GraphDefinitionProto
    organization_id: str
    project_id: str
    epoch: int
    def __init__(self, graph: _Optional[_Union[GraphDefinitionProto, _Mapping]] = ..., organization_id: _Optional[str] = ..., project_id: _Optional[str] = ..., epoch: _Optional[int] = ...) -> None: ...

class GraphLeaseRevokedEvent(_message.Message):
    __slots__ = ("graph_id",)
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    graph_id: str
    def __init__(self, graph_id: _Optional[str] = ...) -> None: ...

class GraphForkEvent(_message.Message):
    __slots__ = ("parent_graph_id", "branch", "organization_id", "project_id")
    PARENT_GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    BRANCH_FIELD_NUMBER: _ClassVar[int]
    ORGANIZATION_ID_FIELD_NUMBER: _ClassVar[int]
    PROJECT_ID_FIELD_NUMBER: _ClassVar[int]
    parent_graph_id: str
    branch: GraphDefinitionProto
    organization_id: str
    project_id: str
    def __init__(self, parent_graph_id: _Optional[str] = ..., branch: _Optional[_Union[GraphDefinitionProto, _Mapping]] = ..., organization_id: _Optional[str] = ..., project_id: _Optional[str] = ...) -> None: ...

class GraphMergeEvent(_message.Message):
    __slots__ = ("branch_id", "parent_graph_id", "organization_id", "project_id")
    BRANCH_ID_FIELD_NUMBER: _ClassVar[int]
    PARENT_GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    ORGANIZATION_ID_FIELD_NUMBER: _ClassVar[int]
    PROJECT_ID_FIELD_NUMBER: _ClassVar[int]
    branch_id: str
    parent_graph_id: str
    organization_id: str
    project_id: str
    def __init__(self, branch_id: _Optional[str] = ..., parent_graph_id: _Optional[str] = ..., organization_id: _Optional[str] = ..., project_id: _Optional[str] = ...) -> None: ...

class SinkRegistrationProto(_message.Message):
    __slots__ = ("id", "type", "resource_id", "endpoint", "secret", "include_vectors", "ops", "entity_kinds", "labels", "metadata_predicate", "enabled")
    ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    ENDPOINT_FIELD_NUMBER: _ClassVar[int]
    SECRET_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_VECTORS_FIELD_NUMBER: _ClassVar[int]
    OPS_FIELD_NUMBER: _ClassVar[int]
    ENTITY_KINDS_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    METADATA_PREDICATE_FIELD_NUMBER: _ClassVar[int]
    ENABLED_FIELD_NUMBER: _ClassVar[int]
    id: str
    type: str
    resource_id: str
    endpoint: str
    secret: str
    include_vectors: bool
    ops: _containers.RepeatedScalarFieldContainer[str]
    entity_kinds: _containers.RepeatedScalarFieldContainer[str]
    labels: _containers.RepeatedScalarFieldContainer[str]
    metadata_predicate: str
    enabled: bool
    def __init__(self, id: _Optional[str] = ..., type: _Optional[str] = ..., resource_id: _Optional[str] = ..., endpoint: _Optional[str] = ..., secret: _Optional[str] = ..., include_vectors: bool = ..., ops: _Optional[_Iterable[str]] = ..., entity_kinds: _Optional[_Iterable[str]] = ..., labels: _Optional[_Iterable[str]] = ..., metadata_predicate: _Optional[str] = ..., enabled: bool = ...) -> None: ...

class SinkRegisteredEvent(_message.Message):
    __slots__ = ("registration",)
    REGISTRATION_FIELD_NUMBER: _ClassVar[int]
    registration: SinkRegistrationProto
    def __init__(self, registration: _Optional[_Union[SinkRegistrationProto, _Mapping]] = ...) -> None: ...

class SinkRemovedEvent(_message.Message):
    __slots__ = ("sink_id", "resource_id")
    SINK_ID_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    sink_id: str
    resource_id: str
    def __init__(self, sink_id: _Optional[str] = ..., resource_id: _Optional[str] = ...) -> None: ...

class SinkRegistrationsSnapshot(_message.Message):
    __slots__ = ("registrations",)
    REGISTRATIONS_FIELD_NUMBER: _ClassVar[int]
    registrations: _containers.RepeatedCompositeFieldContainer[SinkRegistrationProto]
    def __init__(self, registrations: _Optional[_Iterable[_Union[SinkRegistrationProto, _Mapping]]] = ...) -> None: ...

class CollectionEvent(_message.Message):
    __slots__ = ("created", "updated", "deleted", "lease_granted", "lease_revoked", "graph_created", "graph_updated", "graph_deleted", "graph_lease_granted", "graph_lease_revoked", "graph_forked", "graph_merged", "sink_registered", "sink_removed", "sink_snapshot")
    CREATED_FIELD_NUMBER: _ClassVar[int]
    UPDATED_FIELD_NUMBER: _ClassVar[int]
    DELETED_FIELD_NUMBER: _ClassVar[int]
    LEASE_GRANTED_FIELD_NUMBER: _ClassVar[int]
    LEASE_REVOKED_FIELD_NUMBER: _ClassVar[int]
    GRAPH_CREATED_FIELD_NUMBER: _ClassVar[int]
    GRAPH_UPDATED_FIELD_NUMBER: _ClassVar[int]
    GRAPH_DELETED_FIELD_NUMBER: _ClassVar[int]
    GRAPH_LEASE_GRANTED_FIELD_NUMBER: _ClassVar[int]
    GRAPH_LEASE_REVOKED_FIELD_NUMBER: _ClassVar[int]
    GRAPH_FORKED_FIELD_NUMBER: _ClassVar[int]
    GRAPH_MERGED_FIELD_NUMBER: _ClassVar[int]
    SINK_REGISTERED_FIELD_NUMBER: _ClassVar[int]
    SINK_REMOVED_FIELD_NUMBER: _ClassVar[int]
    SINK_SNAPSHOT_FIELD_NUMBER: _ClassVar[int]
    created: CollectionCreatedEvent
    updated: CollectionUpdatedEvent
    deleted: CollectionDeletedEvent
    lease_granted: LeaseGrantedEvent
    lease_revoked: LeaseRevokedEvent
    graph_created: GraphCreatedEvent
    graph_updated: GraphUpdatedEvent
    graph_deleted: GraphDeletedEvent
    graph_lease_granted: GraphLeaseGrantedEvent
    graph_lease_revoked: GraphLeaseRevokedEvent
    graph_forked: GraphForkEvent
    graph_merged: GraphMergeEvent
    sink_registered: SinkRegisteredEvent
    sink_removed: SinkRemovedEvent
    sink_snapshot: SinkRegistrationsSnapshot
    def __init__(self, created: _Optional[_Union[CollectionCreatedEvent, _Mapping]] = ..., updated: _Optional[_Union[CollectionUpdatedEvent, _Mapping]] = ..., deleted: _Optional[_Union[CollectionDeletedEvent, _Mapping]] = ..., lease_granted: _Optional[_Union[LeaseGrantedEvent, _Mapping]] = ..., lease_revoked: _Optional[_Union[LeaseRevokedEvent, _Mapping]] = ..., graph_created: _Optional[_Union[GraphCreatedEvent, _Mapping]] = ..., graph_updated: _Optional[_Union[GraphUpdatedEvent, _Mapping]] = ..., graph_deleted: _Optional[_Union[GraphDeletedEvent, _Mapping]] = ..., graph_lease_granted: _Optional[_Union[GraphLeaseGrantedEvent, _Mapping]] = ..., graph_lease_revoked: _Optional[_Union[GraphLeaseRevokedEvent, _Mapping]] = ..., graph_forked: _Optional[_Union[GraphForkEvent, _Mapping]] = ..., graph_merged: _Optional[_Union[GraphMergeEvent, _Mapping]] = ..., sink_registered: _Optional[_Union[SinkRegisteredEvent, _Mapping]] = ..., sink_removed: _Optional[_Union[SinkRemovedEvent, _Mapping]] = ..., sink_snapshot: _Optional[_Union[SinkRegistrationsSnapshot, _Mapping]] = ...) -> None: ...

class StreamEventsRequest(_message.Message):
    __slots__ = ("instance_id",)
    INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    instance_id: str
    def __init__(self, instance_id: _Optional[str] = ...) -> None: ...

class RegisterInstanceRequest(_message.Message):
    __slots__ = ("instance_id", "grpc_address", "http_address")
    INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    GRPC_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    HTTP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    instance_id: str
    grpc_address: str
    http_address: str
    def __init__(self, instance_id: _Optional[str] = ..., grpc_address: _Optional[str] = ..., http_address: _Optional[str] = ...) -> None: ...

class CollectionLease(_message.Message):
    __slots__ = ("collection_id", "epoch", "ttl_seconds")
    COLLECTION_ID_FIELD_NUMBER: _ClassVar[int]
    EPOCH_FIELD_NUMBER: _ClassVar[int]
    TTL_SECONDS_FIELD_NUMBER: _ClassVar[int]
    collection_id: str
    epoch: int
    ttl_seconds: int
    def __init__(self, collection_id: _Optional[str] = ..., epoch: _Optional[int] = ..., ttl_seconds: _Optional[int] = ...) -> None: ...

class RegisterInstanceResponse(_message.Message):
    __slots__ = ("leases",)
    LEASES_FIELD_NUMBER: _ClassVar[int]
    leases: _containers.RepeatedCompositeFieldContainer[CollectionLease]
    def __init__(self, leases: _Optional[_Iterable[_Union[CollectionLease, _Mapping]]] = ...) -> None: ...

class HeartbeatRequest(_message.Message):
    __slots__ = ("instance_id",)
    INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    instance_id: str
    def __init__(self, instance_id: _Optional[str] = ...) -> None: ...

class HeartbeatResponse(_message.Message):
    __slots__ = ("leases",)
    LEASES_FIELD_NUMBER: _ClassVar[int]
    leases: _containers.RepeatedCompositeFieldContainer[CollectionLease]
    def __init__(self, leases: _Optional[_Iterable[_Union[CollectionLease, _Mapping]]] = ...) -> None: ...

class UpdateGraphDefinitionFromInstanceRequest(_message.Message):
    __slots__ = ("instance_id", "graph_id", "definition")
    INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    DEFINITION_FIELD_NUMBER: _ClassVar[int]
    instance_id: str
    graph_id: str
    definition: GraphDefinitionProto
    def __init__(self, instance_id: _Optional[str] = ..., graph_id: _Optional[str] = ..., definition: _Optional[_Union[GraphDefinitionProto, _Mapping]] = ...) -> None: ...

class UpdateCollectionDefinitionFromInstanceRequest(_message.Message):
    __slots__ = ("instance_id", "collection_id", "definition")
    INSTANCE_ID_FIELD_NUMBER: _ClassVar[int]
    COLLECTION_ID_FIELD_NUMBER: _ClassVar[int]
    DEFINITION_FIELD_NUMBER: _ClassVar[int]
    instance_id: str
    collection_id: str
    definition: CollectionDefinitionProto
    def __init__(self, instance_id: _Optional[str] = ..., collection_id: _Optional[str] = ..., definition: _Optional[_Union[CollectionDefinitionProto, _Mapping]] = ...) -> None: ...

class UserProto(_message.Message):
    __slots__ = ("id", "external_id", "issuer", "email", "display_name", "created_at", "enabled")
    ID_FIELD_NUMBER: _ClassVar[int]
    EXTERNAL_ID_FIELD_NUMBER: _ClassVar[int]
    ISSUER_FIELD_NUMBER: _ClassVar[int]
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_NAME_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    ENABLED_FIELD_NUMBER: _ClassVar[int]
    id: str
    external_id: str
    issuer: str
    email: str
    display_name: str
    created_at: _timestamp_pb2.Timestamp
    enabled: bool
    def __init__(self, id: _Optional[str] = ..., external_id: _Optional[str] = ..., issuer: _Optional[str] = ..., email: _Optional[str] = ..., display_name: _Optional[str] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., enabled: bool = ...) -> None: ...

class CreateUserRequest(_message.Message):
    __slots__ = ("external_id", "issuer", "email", "display_name")
    EXTERNAL_ID_FIELD_NUMBER: _ClassVar[int]
    ISSUER_FIELD_NUMBER: _ClassVar[int]
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_NAME_FIELD_NUMBER: _ClassVar[int]
    external_id: str
    issuer: str
    email: str
    display_name: str
    def __init__(self, external_id: _Optional[str] = ..., issuer: _Optional[str] = ..., email: _Optional[str] = ..., display_name: _Optional[str] = ...) -> None: ...

class UpdateUserRequest(_message.Message):
    __slots__ = ("id", "email", "display_name", "enabled")
    ID_FIELD_NUMBER: _ClassVar[int]
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_NAME_FIELD_NUMBER: _ClassVar[int]
    ENABLED_FIELD_NUMBER: _ClassVar[int]
    id: str
    email: str
    display_name: str
    enabled: bool
    def __init__(self, id: _Optional[str] = ..., email: _Optional[str] = ..., display_name: _Optional[str] = ..., enabled: bool = ...) -> None: ...

class ExternalIdentityRequest(_message.Message):
    __slots__ = ("external_id", "issuer")
    EXTERNAL_ID_FIELD_NUMBER: _ClassVar[int]
    ISSUER_FIELD_NUMBER: _ClassVar[int]
    external_id: str
    issuer: str
    def __init__(self, external_id: _Optional[str] = ..., issuer: _Optional[str] = ...) -> None: ...

class UserList(_message.Message):
    __slots__ = ("users",)
    USERS_FIELD_NUMBER: _ClassVar[int]
    users: _containers.RepeatedCompositeFieldContainer[UserProto]
    def __init__(self, users: _Optional[_Iterable[_Union[UserProto, _Mapping]]] = ...) -> None: ...

class MembershipProto(_message.Message):
    __slots__ = ("id", "user_id", "scope", "organization_id", "project_id", "role", "created_at", "organization_name")
    ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    ORGANIZATION_ID_FIELD_NUMBER: _ClassVar[int]
    PROJECT_ID_FIELD_NUMBER: _ClassVar[int]
    ROLE_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    ORGANIZATION_NAME_FIELD_NUMBER: _ClassVar[int]
    id: str
    user_id: str
    scope: str
    organization_id: str
    project_id: str
    role: str
    created_at: _timestamp_pb2.Timestamp
    organization_name: str
    def __init__(self, id: _Optional[str] = ..., user_id: _Optional[str] = ..., scope: _Optional[str] = ..., organization_id: _Optional[str] = ..., project_id: _Optional[str] = ..., role: _Optional[str] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., organization_name: _Optional[str] = ...) -> None: ...

class CreateMembershipRequest(_message.Message):
    __slots__ = ("user_id", "scope", "organization_id", "project_id", "role")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    SCOPE_FIELD_NUMBER: _ClassVar[int]
    ORGANIZATION_ID_FIELD_NUMBER: _ClassVar[int]
    PROJECT_ID_FIELD_NUMBER: _ClassVar[int]
    ROLE_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    scope: str
    organization_id: str
    project_id: str
    role: str
    def __init__(self, user_id: _Optional[str] = ..., scope: _Optional[str] = ..., organization_id: _Optional[str] = ..., project_id: _Optional[str] = ..., role: _Optional[str] = ...) -> None: ...

class UpdateMembershipRequest(_message.Message):
    __slots__ = ("id", "role")
    ID_FIELD_NUMBER: _ClassVar[int]
    ROLE_FIELD_NUMBER: _ClassVar[int]
    id: str
    role: str
    def __init__(self, id: _Optional[str] = ..., role: _Optional[str] = ...) -> None: ...

class UserIdRequest(_message.Message):
    __slots__ = ("user_id",)
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    def __init__(self, user_id: _Optional[str] = ...) -> None: ...

class MembershipList(_message.Message):
    __slots__ = ("memberships",)
    MEMBERSHIPS_FIELD_NUMBER: _ClassVar[int]
    memberships: _containers.RepeatedCompositeFieldContainer[MembershipProto]
    def __init__(self, memberships: _Optional[_Iterable[_Union[MembershipProto, _Mapping]]] = ...) -> None: ...

class ApiKeyProto(_message.Message):
    __slots__ = ("id", "name", "user_id", "organization_id", "project_id", "permissions", "status", "created_at", "expires_at", "last_used_at", "revoked_at")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    ORGANIZATION_ID_FIELD_NUMBER: _ClassVar[int]
    PROJECT_ID_FIELD_NUMBER: _ClassVar[int]
    PERMISSIONS_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_AT_FIELD_NUMBER: _ClassVar[int]
    LAST_USED_AT_FIELD_NUMBER: _ClassVar[int]
    REVOKED_AT_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    user_id: str
    organization_id: str
    project_id: str
    permissions: _containers.RepeatedScalarFieldContainer[str]
    status: str
    created_at: _timestamp_pb2.Timestamp
    expires_at: _timestamp_pb2.Timestamp
    last_used_at: _timestamp_pb2.Timestamp
    revoked_at: _timestamp_pb2.Timestamp
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., user_id: _Optional[str] = ..., organization_id: _Optional[str] = ..., project_id: _Optional[str] = ..., permissions: _Optional[_Iterable[str]] = ..., status: _Optional[str] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., expires_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., last_used_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., revoked_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class CreateApiKeyRequest(_message.Message):
    __slots__ = ("name", "user_id", "organization_id", "project_id", "permissions", "expires_at")
    NAME_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    ORGANIZATION_ID_FIELD_NUMBER: _ClassVar[int]
    PROJECT_ID_FIELD_NUMBER: _ClassVar[int]
    PERMISSIONS_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_AT_FIELD_NUMBER: _ClassVar[int]
    name: str
    user_id: str
    organization_id: str
    project_id: str
    permissions: _containers.RepeatedScalarFieldContainer[str]
    expires_at: _timestamp_pb2.Timestamp
    def __init__(self, name: _Optional[str] = ..., user_id: _Optional[str] = ..., organization_id: _Optional[str] = ..., project_id: _Optional[str] = ..., permissions: _Optional[_Iterable[str]] = ..., expires_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class UpdateApiKeyRequest(_message.Message):
    __slots__ = ("id", "name", "permissions")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    PERMISSIONS_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    permissions: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., permissions: _Optional[_Iterable[str]] = ...) -> None: ...

class ApiKeyCreatedResponse(_message.Message):
    __slots__ = ("api_key", "plaintext_secret")
    API_KEY_FIELD_NUMBER: _ClassVar[int]
    PLAINTEXT_SECRET_FIELD_NUMBER: _ClassVar[int]
    api_key: ApiKeyProto
    plaintext_secret: str
    def __init__(self, api_key: _Optional[_Union[ApiKeyProto, _Mapping]] = ..., plaintext_secret: _Optional[str] = ...) -> None: ...

class ApiKeyList(_message.Message):
    __slots__ = ("api_keys",)
    API_KEYS_FIELD_NUMBER: _ClassVar[int]
    api_keys: _containers.RepeatedCompositeFieldContainer[ApiKeyProto]
    def __init__(self, api_keys: _Optional[_Iterable[_Union[ApiKeyProto, _Mapping]]] = ...) -> None: ...

class ServiceIdentityProto(_message.Message):
    __slots__ = ("id", "organization_id", "project_id", "certificate_fingerprint", "common_name", "name", "permissions", "enabled", "created_at", "expires_at")
    ID_FIELD_NUMBER: _ClassVar[int]
    ORGANIZATION_ID_FIELD_NUMBER: _ClassVar[int]
    PROJECT_ID_FIELD_NUMBER: _ClassVar[int]
    CERTIFICATE_FINGERPRINT_FIELD_NUMBER: _ClassVar[int]
    COMMON_NAME_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    PERMISSIONS_FIELD_NUMBER: _ClassVar[int]
    ENABLED_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_AT_FIELD_NUMBER: _ClassVar[int]
    id: str
    organization_id: str
    project_id: str
    certificate_fingerprint: str
    common_name: str
    name: str
    permissions: _containers.RepeatedScalarFieldContainer[str]
    enabled: bool
    created_at: _timestamp_pb2.Timestamp
    expires_at: _timestamp_pb2.Timestamp
    def __init__(self, id: _Optional[str] = ..., organization_id: _Optional[str] = ..., project_id: _Optional[str] = ..., certificate_fingerprint: _Optional[str] = ..., common_name: _Optional[str] = ..., name: _Optional[str] = ..., permissions: _Optional[_Iterable[str]] = ..., enabled: bool = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., expires_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class CreateServiceIdentityRequest(_message.Message):
    __slots__ = ("organization_id", "project_id", "certificate_fingerprint", "common_name", "name", "permissions", "expires_at")
    ORGANIZATION_ID_FIELD_NUMBER: _ClassVar[int]
    PROJECT_ID_FIELD_NUMBER: _ClassVar[int]
    CERTIFICATE_FINGERPRINT_FIELD_NUMBER: _ClassVar[int]
    COMMON_NAME_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    PERMISSIONS_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_AT_FIELD_NUMBER: _ClassVar[int]
    organization_id: str
    project_id: str
    certificate_fingerprint: str
    common_name: str
    name: str
    permissions: _containers.RepeatedScalarFieldContainer[str]
    expires_at: _timestamp_pb2.Timestamp
    def __init__(self, organization_id: _Optional[str] = ..., project_id: _Optional[str] = ..., certificate_fingerprint: _Optional[str] = ..., common_name: _Optional[str] = ..., name: _Optional[str] = ..., permissions: _Optional[_Iterable[str]] = ..., expires_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class UpdateServiceIdentityRequest(_message.Message):
    __slots__ = ("id", "name", "permissions", "enabled")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    PERMISSIONS_FIELD_NUMBER: _ClassVar[int]
    ENABLED_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    permissions: _containers.RepeatedScalarFieldContainer[str]
    enabled: bool
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., permissions: _Optional[_Iterable[str]] = ..., enabled: bool = ...) -> None: ...

class FingerprintRequest(_message.Message):
    __slots__ = ("fingerprint",)
    FINGERPRINT_FIELD_NUMBER: _ClassVar[int]
    fingerprint: str
    def __init__(self, fingerprint: _Optional[str] = ...) -> None: ...

class ServiceIdentityList(_message.Message):
    __slots__ = ("service_identities",)
    SERVICE_IDENTITIES_FIELD_NUMBER: _ClassVar[int]
    service_identities: _containers.RepeatedCompositeFieldContainer[ServiceIdentityProto]
    def __init__(self, service_identities: _Optional[_Iterable[_Union[ServiceIdentityProto, _Mapping]]] = ...) -> None: ...

class TokenExchangeResponse(_message.Message):
    __slots__ = ("token", "expires_in")
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_IN_FIELD_NUMBER: _ClassVar[int]
    token: str
    expires_in: int
    def __init__(self, token: _Optional[str] = ..., expires_in: _Optional[int] = ...) -> None: ...

class AuditEventProto(_message.Message):
    __slots__ = ("id", "timestamp", "actor_id", "actor_type", "org_id", "project_id", "resource_type", "resource_id", "action", "outcome", "source_ip", "user_agent", "trace_id", "metadata")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    ACTOR_ID_FIELD_NUMBER: _ClassVar[int]
    ACTOR_TYPE_FIELD_NUMBER: _ClassVar[int]
    ORG_ID_FIELD_NUMBER: _ClassVar[int]
    PROJECT_ID_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_TYPE_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    ACTION_FIELD_NUMBER: _ClassVar[int]
    OUTCOME_FIELD_NUMBER: _ClassVar[int]
    SOURCE_IP_FIELD_NUMBER: _ClassVar[int]
    USER_AGENT_FIELD_NUMBER: _ClassVar[int]
    TRACE_ID_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    id: str
    timestamp: _timestamp_pb2.Timestamp
    actor_id: str
    actor_type: str
    org_id: str
    project_id: str
    resource_type: str
    resource_id: str
    action: str
    outcome: str
    source_ip: str
    user_agent: str
    trace_id: str
    metadata: _containers.ScalarMap[str, str]
    def __init__(self, id: _Optional[str] = ..., timestamp: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., actor_id: _Optional[str] = ..., actor_type: _Optional[str] = ..., org_id: _Optional[str] = ..., project_id: _Optional[str] = ..., resource_type: _Optional[str] = ..., resource_id: _Optional[str] = ..., action: _Optional[str] = ..., outcome: _Optional[str] = ..., source_ip: _Optional[str] = ..., user_agent: _Optional[str] = ..., trace_id: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...

class AuditQueryRequest(_message.Message):
    __slots__ = ("org_id", "actor_id", "actor_type", "project_id", "resource_type", "resource_id", "action", "to", "offset", "limit")
    ORG_ID_FIELD_NUMBER: _ClassVar[int]
    ACTOR_ID_FIELD_NUMBER: _ClassVar[int]
    ACTOR_TYPE_FIELD_NUMBER: _ClassVar[int]
    PROJECT_ID_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_TYPE_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    ACTION_FIELD_NUMBER: _ClassVar[int]
    FROM_FIELD_NUMBER: _ClassVar[int]
    TO_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    org_id: str
    actor_id: str
    actor_type: str
    project_id: str
    resource_type: str
    resource_id: str
    action: str
    to: _timestamp_pb2.Timestamp
    offset: int
    limit: int
    def __init__(self, org_id: _Optional[str] = ..., actor_id: _Optional[str] = ..., actor_type: _Optional[str] = ..., project_id: _Optional[str] = ..., resource_type: _Optional[str] = ..., resource_id: _Optional[str] = ..., action: _Optional[str] = ..., to: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., offset: _Optional[int] = ..., limit: _Optional[int] = ..., **kwargs) -> None: ...

class AuditQueryResponse(_message.Message):
    __slots__ = ("events", "total_count", "has_more")
    EVENTS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_COUNT_FIELD_NUMBER: _ClassVar[int]
    HAS_MORE_FIELD_NUMBER: _ClassVar[int]
    events: _containers.RepeatedCompositeFieldContainer[AuditEventProto]
    total_count: int
    has_more: bool
    def __init__(self, events: _Optional[_Iterable[_Union[AuditEventProto, _Mapping]]] = ..., total_count: _Optional[int] = ..., has_more: bool = ...) -> None: ...

class AuditExportRequest(_message.Message):
    __slots__ = ("org_id", "to")
    ORG_ID_FIELD_NUMBER: _ClassVar[int]
    FROM_FIELD_NUMBER: _ClassVar[int]
    TO_FIELD_NUMBER: _ClassVar[int]
    org_id: str
    to: _timestamp_pb2.Timestamp
    def __init__(self, org_id: _Optional[str] = ..., to: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., **kwargs) -> None: ...

class AuditExportChunk(_message.Message):
    __slots__ = ("events",)
    EVENTS_FIELD_NUMBER: _ClassVar[int]
    events: _containers.RepeatedCompositeFieldContainer[AuditEventProto]
    def __init__(self, events: _Optional[_Iterable[_Union[AuditEventProto, _Mapping]]] = ...) -> None: ...

class IngestAuditEventsRequest(_message.Message):
    __slots__ = ("events",)
    EVENTS_FIELD_NUMBER: _ClassVar[int]
    events: _containers.RepeatedCompositeFieldContainer[AuditEventProto]
    def __init__(self, events: _Optional[_Iterable[_Union[AuditEventProto, _Mapping]]] = ...) -> None: ...

class IngestAuditEventsResponse(_message.Message):
    __slots__ = ("ingested_count",)
    INGESTED_COUNT_FIELD_NUMBER: _ClassVar[int]
    ingested_count: int
    def __init__(self, ingested_count: _Optional[int] = ...) -> None: ...

class MeProto(_message.Message):
    __slots__ = ("identity_type", "user", "organization", "project", "system_scoped", "permissions", "memberships")
    IDENTITY_TYPE_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    ORGANIZATION_FIELD_NUMBER: _ClassVar[int]
    PROJECT_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_SCOPED_FIELD_NUMBER: _ClassVar[int]
    PERMISSIONS_FIELD_NUMBER: _ClassVar[int]
    MEMBERSHIPS_FIELD_NUMBER: _ClassVar[int]
    identity_type: str
    user: UserProto
    organization: OrganizationProto
    project: ProjectProto
    system_scoped: bool
    permissions: _containers.RepeatedScalarFieldContainer[str]
    memberships: _containers.RepeatedCompositeFieldContainer[MembershipProto]
    def __init__(self, identity_type: _Optional[str] = ..., user: _Optional[_Union[UserProto, _Mapping]] = ..., organization: _Optional[_Union[OrganizationProto, _Mapping]] = ..., project: _Optional[_Union[ProjectProto, _Mapping]] = ..., system_scoped: bool = ..., permissions: _Optional[_Iterable[str]] = ..., memberships: _Optional[_Iterable[_Union[MembershipProto, _Mapping]]] = ...) -> None: ...
