import cyrock_db_platform_pb2 as _cyrock_db_platform_pb2
import cyrock_db_data_pb2 as _cyrock_db_data_pb2
import cyrock_db_value_pb2 as _cyrock_db_value_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class GraphVectorFieldProto(_message.Message):
    __slots__ = ("values", "text")
    VALUES_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    values: _containers.RepeatedScalarFieldContainer[float]
    text: str
    def __init__(self, values: _Optional[_Iterable[float]] = ..., text: _Optional[str] = ...) -> None: ...

class NodeProto(_message.Message):
    __slots__ = ("id", "labels", "vectors", "metadata", "created_at", "external_key")
    class VectorsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: GraphVectorFieldProto
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[GraphVectorFieldProto, _Mapping]] = ...) -> None: ...
    ID_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    VECTORS_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    EXTERNAL_KEY_FIELD_NUMBER: _ClassVar[int]
    id: int
    labels: _containers.RepeatedScalarFieldContainer[str]
    vectors: _containers.MessageMap[str, GraphVectorFieldProto]
    metadata: _cyrock_db_value_pb2.CyrockStruct
    created_at: int
    external_key: str
    def __init__(self, id: _Optional[int] = ..., labels: _Optional[_Iterable[str]] = ..., vectors: _Optional[_Mapping[str, GraphVectorFieldProto]] = ..., metadata: _Optional[_Union[_cyrock_db_value_pb2.CyrockStruct, _Mapping]] = ..., created_at: _Optional[int] = ..., external_key: _Optional[str] = ...) -> None: ...

class EdgeProto(_message.Message):
    __slots__ = ("id", "type", "source_id", "target_id", "weight", "metadata", "created_at")
    ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    SOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    TARGET_ID_FIELD_NUMBER: _ClassVar[int]
    WEIGHT_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    id: int
    type: str
    source_id: int
    target_id: int
    weight: float
    metadata: _cyrock_db_value_pb2.CyrockStruct
    created_at: int
    def __init__(self, id: _Optional[int] = ..., type: _Optional[str] = ..., source_id: _Optional[int] = ..., target_id: _Optional[int] = ..., weight: _Optional[float] = ..., metadata: _Optional[_Union[_cyrock_db_value_pb2.CyrockStruct, _Mapping]] = ..., created_at: _Optional[int] = ...) -> None: ...

class NodeMatchProto(_message.Message):
    __slots__ = ("score", "node")
    SCORE_FIELD_NUMBER: _ClassVar[int]
    NODE_FIELD_NUMBER: _ClassVar[int]
    score: float
    node: NodeProto
    def __init__(self, score: _Optional[float] = ..., node: _Optional[_Union[NodeProto, _Mapping]] = ...) -> None: ...

class LabelExpressionProto(_message.Message):
    __slots__ = ("label",)
    LABEL_FIELD_NUMBER: _ClassVar[int]
    AND_FIELD_NUMBER: _ClassVar[int]
    OR_FIELD_NUMBER: _ClassVar[int]
    NOT_FIELD_NUMBER: _ClassVar[int]
    label: str
    def __init__(self, label: _Optional[str] = ..., **kwargs) -> None: ...

class LabelBinaryProto(_message.Message):
    __slots__ = ("left", "right")
    LEFT_FIELD_NUMBER: _ClassVar[int]
    RIGHT_FIELD_NUMBER: _ClassVar[int]
    left: LabelExpressionProto
    right: LabelExpressionProto
    def __init__(self, left: _Optional[_Union[LabelExpressionProto, _Mapping]] = ..., right: _Optional[_Union[LabelExpressionProto, _Mapping]] = ...) -> None: ...

class AddNodeRequest(_message.Message):
    __slots__ = ("graph_id", "labels", "vectors", "metadata")
    class VectorsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: GraphVectorFieldProto
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[GraphVectorFieldProto, _Mapping]] = ...) -> None: ...
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    VECTORS_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    graph_id: str
    labels: _containers.RepeatedScalarFieldContainer[str]
    vectors: _containers.MessageMap[str, GraphVectorFieldProto]
    metadata: _cyrock_db_value_pb2.CyrockStruct
    def __init__(self, graph_id: _Optional[str] = ..., labels: _Optional[_Iterable[str]] = ..., vectors: _Optional[_Mapping[str, GraphVectorFieldProto]] = ..., metadata: _Optional[_Union[_cyrock_db_value_pb2.CyrockStruct, _Mapping]] = ...) -> None: ...

class AddNodeResponse(_message.Message):
    __slots__ = ("node_id",)
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    node_id: int
    def __init__(self, node_id: _Optional[int] = ...) -> None: ...

class AddEdgeRequest(_message.Message):
    __slots__ = ("graph_id", "source_id", "target_id", "type", "weight", "metadata")
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    SOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    TARGET_ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    WEIGHT_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    graph_id: str
    source_id: int
    target_id: int
    type: str
    weight: float
    metadata: _cyrock_db_value_pb2.CyrockStruct
    def __init__(self, graph_id: _Optional[str] = ..., source_id: _Optional[int] = ..., target_id: _Optional[int] = ..., type: _Optional[str] = ..., weight: _Optional[float] = ..., metadata: _Optional[_Union[_cyrock_db_value_pb2.CyrockStruct, _Mapping]] = ...) -> None: ...

class AddEdgeResponse(_message.Message):
    __slots__ = ("edge_id",)
    EDGE_ID_FIELD_NUMBER: _ClassVar[int]
    edge_id: int
    def __init__(self, edge_id: _Optional[int] = ...) -> None: ...

class GetNodeRequest(_message.Message):
    __slots__ = ("graph_id", "node_id")
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    graph_id: str
    node_id: int
    def __init__(self, graph_id: _Optional[str] = ..., node_id: _Optional[int] = ...) -> None: ...

class GetNodeResponse(_message.Message):
    __slots__ = ("node",)
    NODE_FIELD_NUMBER: _ClassVar[int]
    node: NodeProto
    def __init__(self, node: _Optional[_Union[NodeProto, _Mapping]] = ...) -> None: ...

class GetEdgeRequest(_message.Message):
    __slots__ = ("graph_id", "edge_id")
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    EDGE_ID_FIELD_NUMBER: _ClassVar[int]
    graph_id: str
    edge_id: int
    def __init__(self, graph_id: _Optional[str] = ..., edge_id: _Optional[int] = ...) -> None: ...

class GetEdgeResponse(_message.Message):
    __slots__ = ("edge",)
    EDGE_FIELD_NUMBER: _ClassVar[int]
    edge: EdgeProto
    def __init__(self, edge: _Optional[_Union[EdgeProto, _Mapping]] = ...) -> None: ...

class RemoveNodeRequest(_message.Message):
    __slots__ = ("graph_id", "node_id")
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    graph_id: str
    node_id: int
    def __init__(self, graph_id: _Optional[str] = ..., node_id: _Optional[int] = ...) -> None: ...

class RemoveEdgeRequest(_message.Message):
    __slots__ = ("graph_id", "edge_id")
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    EDGE_ID_FIELD_NUMBER: _ClassVar[int]
    graph_id: str
    edge_id: int
    def __init__(self, graph_id: _Optional[str] = ..., edge_id: _Optional[int] = ...) -> None: ...

class UpdateVectorRequest(_message.Message):
    __slots__ = ("graph_id", "node_id", "field_name", "vector")
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    FIELD_NAME_FIELD_NUMBER: _ClassVar[int]
    VECTOR_FIELD_NUMBER: _ClassVar[int]
    graph_id: str
    node_id: int
    field_name: str
    vector: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, graph_id: _Optional[str] = ..., node_id: _Optional[int] = ..., field_name: _Optional[str] = ..., vector: _Optional[_Iterable[float]] = ...) -> None: ...

class UpdateWeightRequest(_message.Message):
    __slots__ = ("graph_id", "edge_id", "weight")
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    EDGE_ID_FIELD_NUMBER: _ClassVar[int]
    WEIGHT_FIELD_NUMBER: _ClassVar[int]
    graph_id: str
    edge_id: int
    weight: float
    def __init__(self, graph_id: _Optional[str] = ..., edge_id: _Optional[int] = ..., weight: _Optional[float] = ...) -> None: ...

class UpdateNodeMetadataRequest(_message.Message):
    __slots__ = ("graph_id", "node_id", "metadata")
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    graph_id: str
    node_id: int
    metadata: _cyrock_db_value_pb2.CyrockStruct
    def __init__(self, graph_id: _Optional[str] = ..., node_id: _Optional[int] = ..., metadata: _Optional[_Union[_cyrock_db_value_pb2.CyrockStruct, _Mapping]] = ...) -> None: ...

class UpdateEdgeMetadataRequest(_message.Message):
    __slots__ = ("graph_id", "edge_id", "metadata")
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    EDGE_ID_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    graph_id: str
    edge_id: int
    metadata: _cyrock_db_value_pb2.CyrockStruct
    def __init__(self, graph_id: _Optional[str] = ..., edge_id: _Optional[int] = ..., metadata: _Optional[_Union[_cyrock_db_value_pb2.CyrockStruct, _Mapping]] = ...) -> None: ...

class UpsertNodeRequest(_message.Message):
    __slots__ = ("graph_id", "external_key", "labels", "vectors", "metadata", "node_id")
    class VectorsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: GraphVectorFieldProto
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[GraphVectorFieldProto, _Mapping]] = ...) -> None: ...
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    EXTERNAL_KEY_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    VECTORS_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    graph_id: str
    external_key: str
    labels: _containers.RepeatedScalarFieldContainer[str]
    vectors: _containers.MessageMap[str, GraphVectorFieldProto]
    metadata: _cyrock_db_value_pb2.CyrockStruct
    node_id: int
    def __init__(self, graph_id: _Optional[str] = ..., external_key: _Optional[str] = ..., labels: _Optional[_Iterable[str]] = ..., vectors: _Optional[_Mapping[str, GraphVectorFieldProto]] = ..., metadata: _Optional[_Union[_cyrock_db_value_pb2.CyrockStruct, _Mapping]] = ..., node_id: _Optional[int] = ...) -> None: ...

class UpsertNodeResponse(_message.Message):
    __slots__ = ("node_id", "created")
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    CREATED_FIELD_NUMBER: _ClassVar[int]
    node_id: int
    created: bool
    def __init__(self, node_id: _Optional[int] = ..., created: bool = ...) -> None: ...

class GetNodeByKeyRequest(_message.Message):
    __slots__ = ("graph_id", "external_key")
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    EXTERNAL_KEY_FIELD_NUMBER: _ClassVar[int]
    graph_id: str
    external_key: str
    def __init__(self, graph_id: _Optional[str] = ..., external_key: _Optional[str] = ...) -> None: ...

class RemoveNodeByKeyRequest(_message.Message):
    __slots__ = ("graph_id", "external_key")
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    EXTERNAL_KEY_FIELD_NUMBER: _ClassVar[int]
    graph_id: str
    external_key: str
    def __init__(self, graph_id: _Optional[str] = ..., external_key: _Optional[str] = ...) -> None: ...

class ListNodesRequest(_message.Message):
    __slots__ = ("graph_id", "offset", "limit", "filter", "label_expression", "include_vectors", "sample_seed")
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    FILTER_FIELD_NUMBER: _ClassVar[int]
    LABEL_EXPRESSION_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_VECTORS_FIELD_NUMBER: _ClassVar[int]
    SAMPLE_SEED_FIELD_NUMBER: _ClassVar[int]
    graph_id: str
    offset: int
    limit: int
    filter: str
    label_expression: LabelExpressionProto
    include_vectors: bool
    sample_seed: int
    def __init__(self, graph_id: _Optional[str] = ..., offset: _Optional[int] = ..., limit: _Optional[int] = ..., filter: _Optional[str] = ..., label_expression: _Optional[_Union[LabelExpressionProto, _Mapping]] = ..., include_vectors: bool = ..., sample_seed: _Optional[int] = ...) -> None: ...

class ListNodesResponse(_message.Message):
    __slots__ = ("nodes",)
    NODES_FIELD_NUMBER: _ClassVar[int]
    nodes: _containers.RepeatedCompositeFieldContainer[NodeProto]
    def __init__(self, nodes: _Optional[_Iterable[_Union[NodeProto, _Mapping]]] = ...) -> None: ...

class GetNodesRequest(_message.Message):
    __slots__ = ("graph_id", "node_ids", "include_vectors")
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    NODE_IDS_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_VECTORS_FIELD_NUMBER: _ClassVar[int]
    graph_id: str
    node_ids: _containers.RepeatedScalarFieldContainer[int]
    include_vectors: bool
    def __init__(self, graph_id: _Optional[str] = ..., node_ids: _Optional[_Iterable[int]] = ..., include_vectors: bool = ...) -> None: ...

class GetNodesResponse(_message.Message):
    __slots__ = ("nodes",)
    NODES_FIELD_NUMBER: _ClassVar[int]
    nodes: _containers.RepeatedCompositeFieldContainer[NodeProto]
    def __init__(self, nodes: _Optional[_Iterable[_Union[NodeProto, _Mapping]]] = ...) -> None: ...

class InducedSubgraphRequest(_message.Message):
    __slots__ = ("graph_id", "node_ids", "include_vectors")
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    NODE_IDS_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_VECTORS_FIELD_NUMBER: _ClassVar[int]
    graph_id: str
    node_ids: _containers.RepeatedScalarFieldContainer[int]
    include_vectors: bool
    def __init__(self, graph_id: _Optional[str] = ..., node_ids: _Optional[_Iterable[int]] = ..., include_vectors: bool = ...) -> None: ...

class InducedSubgraphResponse(_message.Message):
    __slots__ = ("nodes", "edges")
    NODES_FIELD_NUMBER: _ClassVar[int]
    EDGES_FIELD_NUMBER: _ClassVar[int]
    nodes: _containers.RepeatedCompositeFieldContainer[NodeProto]
    edges: _containers.RepeatedCompositeFieldContainer[EdgeProto]
    def __init__(self, nodes: _Optional[_Iterable[_Union[NodeProto, _Mapping]]] = ..., edges: _Optional[_Iterable[_Union[EdgeProto, _Mapping]]] = ...) -> None: ...

class ListLabelsRequest(_message.Message):
    __slots__ = ("graph_id", "include_counts")
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_COUNTS_FIELD_NUMBER: _ClassVar[int]
    graph_id: str
    include_counts: bool
    def __init__(self, graph_id: _Optional[str] = ..., include_counts: bool = ...) -> None: ...

class LabelStatProto(_message.Message):
    __slots__ = ("label", "count")
    LABEL_FIELD_NUMBER: _ClassVar[int]
    COUNT_FIELD_NUMBER: _ClassVar[int]
    label: str
    count: int
    def __init__(self, label: _Optional[str] = ..., count: _Optional[int] = ...) -> None: ...

class ListLabelsResponse(_message.Message):
    __slots__ = ("labels",)
    LABELS_FIELD_NUMBER: _ClassVar[int]
    labels: _containers.RepeatedCompositeFieldContainer[LabelStatProto]
    def __init__(self, labels: _Optional[_Iterable[_Union[LabelStatProto, _Mapping]]] = ...) -> None: ...

class SearchSimilarRequest(_message.Message):
    __slots__ = ("graph_id", "field_name", "vector", "max_results", "diversity_seed", "filter", "label_expression")
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    FIELD_NAME_FIELD_NUMBER: _ClassVar[int]
    VECTOR_FIELD_NUMBER: _ClassVar[int]
    MAX_RESULTS_FIELD_NUMBER: _ClassVar[int]
    DIVERSITY_SEED_FIELD_NUMBER: _ClassVar[int]
    FILTER_FIELD_NUMBER: _ClassVar[int]
    LABEL_EXPRESSION_FIELD_NUMBER: _ClassVar[int]
    graph_id: str
    field_name: str
    vector: _containers.RepeatedScalarFieldContainer[float]
    max_results: int
    diversity_seed: int
    filter: str
    label_expression: LabelExpressionProto
    def __init__(self, graph_id: _Optional[str] = ..., field_name: _Optional[str] = ..., vector: _Optional[_Iterable[float]] = ..., max_results: _Optional[int] = ..., diversity_seed: _Optional[int] = ..., filter: _Optional[str] = ..., label_expression: _Optional[_Union[LabelExpressionProto, _Mapping]] = ...) -> None: ...

class SearchSimilarResponse(_message.Message):
    __slots__ = ("matches",)
    MATCHES_FIELD_NUMBER: _ClassVar[int]
    matches: _containers.RepeatedCompositeFieldContainer[NodeMatchProto]
    def __init__(self, matches: _Optional[_Iterable[_Union[NodeMatchProto, _Mapping]]] = ...) -> None: ...

class NeighborsRequest(_message.Message):
    __slots__ = ("graph_id", "node_id", "direction", "edge_type", "diversity_seed", "limit", "include_vectors")
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    DIRECTION_FIELD_NUMBER: _ClassVar[int]
    EDGE_TYPE_FIELD_NUMBER: _ClassVar[int]
    DIVERSITY_SEED_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_VECTORS_FIELD_NUMBER: _ClassVar[int]
    graph_id: str
    node_id: int
    direction: str
    edge_type: str
    diversity_seed: int
    limit: int
    include_vectors: bool
    def __init__(self, graph_id: _Optional[str] = ..., node_id: _Optional[int] = ..., direction: _Optional[str] = ..., edge_type: _Optional[str] = ..., diversity_seed: _Optional[int] = ..., limit: _Optional[int] = ..., include_vectors: bool = ...) -> None: ...

class NeighborsResponse(_message.Message):
    __slots__ = ("nodes", "edges", "truncated")
    NODES_FIELD_NUMBER: _ClassVar[int]
    EDGES_FIELD_NUMBER: _ClassVar[int]
    TRUNCATED_FIELD_NUMBER: _ClassVar[int]
    nodes: _containers.RepeatedCompositeFieldContainer[NodeProto]
    edges: _containers.RepeatedCompositeFieldContainer[EdgeProto]
    truncated: bool
    def __init__(self, nodes: _Optional[_Iterable[_Union[NodeProto, _Mapping]]] = ..., edges: _Optional[_Iterable[_Union[EdgeProto, _Mapping]]] = ..., truncated: bool = ...) -> None: ...

class BatchNeighborsRequest(_message.Message):
    __slots__ = ("graph_id", "node_ids", "direction", "edge_type", "limit", "include_vectors")
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    NODE_IDS_FIELD_NUMBER: _ClassVar[int]
    DIRECTION_FIELD_NUMBER: _ClassVar[int]
    EDGE_TYPE_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_VECTORS_FIELD_NUMBER: _ClassVar[int]
    graph_id: str
    node_ids: _containers.RepeatedScalarFieldContainer[int]
    direction: str
    edge_type: str
    limit: int
    include_vectors: bool
    def __init__(self, graph_id: _Optional[str] = ..., node_ids: _Optional[_Iterable[int]] = ..., direction: _Optional[str] = ..., edge_type: _Optional[str] = ..., limit: _Optional[int] = ..., include_vectors: bool = ...) -> None: ...

class BatchNeighborsResponse(_message.Message):
    __slots__ = ("nodes", "edges", "truncated")
    NODES_FIELD_NUMBER: _ClassVar[int]
    EDGES_FIELD_NUMBER: _ClassVar[int]
    TRUNCATED_FIELD_NUMBER: _ClassVar[int]
    nodes: _containers.RepeatedCompositeFieldContainer[NodeProto]
    edges: _containers.RepeatedCompositeFieldContainer[EdgeProto]
    truncated: bool
    def __init__(self, nodes: _Optional[_Iterable[_Union[NodeProto, _Mapping]]] = ..., edges: _Optional[_Iterable[_Union[EdgeProto, _Mapping]]] = ..., truncated: bool = ...) -> None: ...

class TraverseRequest(_message.Message):
    __slots__ = ("graph_id", "start_id", "max_depth", "direction", "edge_type")
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    START_ID_FIELD_NUMBER: _ClassVar[int]
    MAX_DEPTH_FIELD_NUMBER: _ClassVar[int]
    DIRECTION_FIELD_NUMBER: _ClassVar[int]
    EDGE_TYPE_FIELD_NUMBER: _ClassVar[int]
    graph_id: str
    start_id: int
    max_depth: int
    direction: str
    edge_type: str
    def __init__(self, graph_id: _Optional[str] = ..., start_id: _Optional[int] = ..., max_depth: _Optional[int] = ..., direction: _Optional[str] = ..., edge_type: _Optional[str] = ...) -> None: ...

class TraverseResponse(_message.Message):
    __slots__ = ("nodes",)
    NODES_FIELD_NUMBER: _ClassVar[int]
    nodes: _containers.RepeatedCompositeFieldContainer[NodeProto]
    def __init__(self, nodes: _Optional[_Iterable[_Union[NodeProto, _Mapping]]] = ...) -> None: ...

class ContextWindowRequest(_message.Message):
    __slots__ = ("graph_id", "field_name", "vector", "max_results", "depth", "diversity_seed")
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    FIELD_NAME_FIELD_NUMBER: _ClassVar[int]
    VECTOR_FIELD_NUMBER: _ClassVar[int]
    MAX_RESULTS_FIELD_NUMBER: _ClassVar[int]
    DEPTH_FIELD_NUMBER: _ClassVar[int]
    DIVERSITY_SEED_FIELD_NUMBER: _ClassVar[int]
    graph_id: str
    field_name: str
    vector: _containers.RepeatedScalarFieldContainer[float]
    max_results: int
    depth: int
    diversity_seed: int
    def __init__(self, graph_id: _Optional[str] = ..., field_name: _Optional[str] = ..., vector: _Optional[_Iterable[float]] = ..., max_results: _Optional[int] = ..., depth: _Optional[int] = ..., diversity_seed: _Optional[int] = ...) -> None: ...

class ContextWindowResponse(_message.Message):
    __slots__ = ("nodes", "edges")
    NODES_FIELD_NUMBER: _ClassVar[int]
    EDGES_FIELD_NUMBER: _ClassVar[int]
    nodes: _containers.RepeatedCompositeFieldContainer[NodeProto]
    edges: _containers.RepeatedCompositeFieldContainer[EdgeProto]
    def __init__(self, nodes: _Optional[_Iterable[_Union[NodeProto, _Mapping]]] = ..., edges: _Optional[_Iterable[_Union[EdgeProto, _Mapping]]] = ...) -> None: ...

class ReasoningChainRequest(_message.Message):
    __slots__ = ("graph_id", "from_id", "to_id", "max_depth")
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    FROM_ID_FIELD_NUMBER: _ClassVar[int]
    TO_ID_FIELD_NUMBER: _ClassVar[int]
    MAX_DEPTH_FIELD_NUMBER: _ClassVar[int]
    graph_id: str
    from_id: int
    to_id: int
    max_depth: int
    def __init__(self, graph_id: _Optional[str] = ..., from_id: _Optional[int] = ..., to_id: _Optional[int] = ..., max_depth: _Optional[int] = ...) -> None: ...

class ReasoningChainResponse(_message.Message):
    __slots__ = ("nodes", "edges")
    NODES_FIELD_NUMBER: _ClassVar[int]
    EDGES_FIELD_NUMBER: _ClassVar[int]
    nodes: _containers.RepeatedCompositeFieldContainer[NodeProto]
    edges: _containers.RepeatedCompositeFieldContainer[EdgeProto]
    def __init__(self, nodes: _Optional[_Iterable[_Union[NodeProto, _Mapping]]] = ..., edges: _Optional[_Iterable[_Union[EdgeProto, _Mapping]]] = ...) -> None: ...

class DetectCommunitiesRequest(_message.Message):
    __slots__ = ("graph_id", "algorithm", "resolution", "edge_weight_field", "edge_types", "max_levels", "seed")
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    ALGORITHM_FIELD_NUMBER: _ClassVar[int]
    RESOLUTION_FIELD_NUMBER: _ClassVar[int]
    EDGE_WEIGHT_FIELD_FIELD_NUMBER: _ClassVar[int]
    EDGE_TYPES_FIELD_NUMBER: _ClassVar[int]
    MAX_LEVELS_FIELD_NUMBER: _ClassVar[int]
    SEED_FIELD_NUMBER: _ClassVar[int]
    graph_id: str
    algorithm: str
    resolution: float
    edge_weight_field: str
    edge_types: _containers.RepeatedScalarFieldContainer[str]
    max_levels: int
    seed: int
    def __init__(self, graph_id: _Optional[str] = ..., algorithm: _Optional[str] = ..., resolution: _Optional[float] = ..., edge_weight_field: _Optional[str] = ..., edge_types: _Optional[_Iterable[str]] = ..., max_levels: _Optional[int] = ..., seed: _Optional[int] = ...) -> None: ...

class CommunityProto(_message.Message):
    __slots__ = ("id", "level", "parent_id", "size", "member_node_ids")
    ID_FIELD_NUMBER: _ClassVar[int]
    LEVEL_FIELD_NUMBER: _ClassVar[int]
    PARENT_ID_FIELD_NUMBER: _ClassVar[int]
    SIZE_FIELD_NUMBER: _ClassVar[int]
    MEMBER_NODE_IDS_FIELD_NUMBER: _ClassVar[int]
    id: int
    level: int
    parent_id: int
    size: int
    member_node_ids: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, id: _Optional[int] = ..., level: _Optional[int] = ..., parent_id: _Optional[int] = ..., size: _Optional[int] = ..., member_node_ids: _Optional[_Iterable[int]] = ...) -> None: ...

class DetectCommunitiesResponse(_message.Message):
    __slots__ = ("communities", "levels", "algorithm", "detected_at")
    COMMUNITIES_FIELD_NUMBER: _ClassVar[int]
    LEVELS_FIELD_NUMBER: _ClassVar[int]
    ALGORITHM_FIELD_NUMBER: _ClassVar[int]
    DETECTED_AT_FIELD_NUMBER: _ClassVar[int]
    communities: _containers.RepeatedCompositeFieldContainer[CommunityProto]
    levels: int
    algorithm: str
    detected_at: int
    def __init__(self, communities: _Optional[_Iterable[_Union[CommunityProto, _Mapping]]] = ..., levels: _Optional[int] = ..., algorithm: _Optional[str] = ..., detected_at: _Optional[int] = ...) -> None: ...

class CommunitySummaryProto(_message.Message):
    __slots__ = ("level", "community_id", "summary_text", "vectors")
    class VectorsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: GraphVectorFieldProto
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[GraphVectorFieldProto, _Mapping]] = ...) -> None: ...
    LEVEL_FIELD_NUMBER: _ClassVar[int]
    COMMUNITY_ID_FIELD_NUMBER: _ClassVar[int]
    SUMMARY_TEXT_FIELD_NUMBER: _ClassVar[int]
    VECTORS_FIELD_NUMBER: _ClassVar[int]
    level: int
    community_id: int
    summary_text: str
    vectors: _containers.MessageMap[str, GraphVectorFieldProto]
    def __init__(self, level: _Optional[int] = ..., community_id: _Optional[int] = ..., summary_text: _Optional[str] = ..., vectors: _Optional[_Mapping[str, GraphVectorFieldProto]] = ...) -> None: ...

class PutCommunitySummariesRequest(_message.Message):
    __slots__ = ("graph_id", "summaries")
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    SUMMARIES_FIELD_NUMBER: _ClassVar[int]
    graph_id: str
    summaries: _containers.RepeatedCompositeFieldContainer[CommunitySummaryProto]
    def __init__(self, graph_id: _Optional[str] = ..., summaries: _Optional[_Iterable[_Union[CommunitySummaryProto, _Mapping]]] = ...) -> None: ...

class PutCommunitySummariesResponse(_message.Message):
    __slots__ = ("ids",)
    IDS_FIELD_NUMBER: _ClassVar[int]
    ids: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, ids: _Optional[_Iterable[int]] = ...) -> None: ...

class GetCommunitySummariesRequest(_message.Message):
    __slots__ = ("graph_id", "level", "community_ids", "limit")
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    LEVEL_FIELD_NUMBER: _ClassVar[int]
    COMMUNITY_IDS_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    graph_id: str
    level: int
    community_ids: _containers.RepeatedScalarFieldContainer[int]
    limit: int
    def __init__(self, graph_id: _Optional[str] = ..., level: _Optional[int] = ..., community_ids: _Optional[_Iterable[int]] = ..., limit: _Optional[int] = ...) -> None: ...

class CommunitySummaryEntryProto(_message.Message):
    __slots__ = ("level", "community_id", "summary_text")
    LEVEL_FIELD_NUMBER: _ClassVar[int]
    COMMUNITY_ID_FIELD_NUMBER: _ClassVar[int]
    SUMMARY_TEXT_FIELD_NUMBER: _ClassVar[int]
    level: int
    community_id: int
    summary_text: str
    def __init__(self, level: _Optional[int] = ..., community_id: _Optional[int] = ..., summary_text: _Optional[str] = ...) -> None: ...

class GetCommunitySummariesResponse(_message.Message):
    __slots__ = ("summaries", "truncated")
    SUMMARIES_FIELD_NUMBER: _ClassVar[int]
    TRUNCATED_FIELD_NUMBER: _ClassVar[int]
    summaries: _containers.RepeatedCompositeFieldContainer[CommunitySummaryEntryProto]
    truncated: bool
    def __init__(self, summaries: _Optional[_Iterable[_Union[CommunitySummaryEntryProto, _Mapping]]] = ..., truncated: bool = ...) -> None: ...

class GlobalSearchRequest(_message.Message):
    __slots__ = ("graph_id", "query", "query_vector", "level", "top_k", "vector_field", "include_members", "max_members_per_community", "expand", "expand_depth", "rerank")
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    QUERY_FIELD_NUMBER: _ClassVar[int]
    QUERY_VECTOR_FIELD_NUMBER: _ClassVar[int]
    LEVEL_FIELD_NUMBER: _ClassVar[int]
    TOP_K_FIELD_NUMBER: _ClassVar[int]
    VECTOR_FIELD_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_MEMBERS_FIELD_NUMBER: _ClassVar[int]
    MAX_MEMBERS_PER_COMMUNITY_FIELD_NUMBER: _ClassVar[int]
    EXPAND_FIELD_NUMBER: _ClassVar[int]
    EXPAND_DEPTH_FIELD_NUMBER: _ClassVar[int]
    RERANK_FIELD_NUMBER: _ClassVar[int]
    graph_id: str
    query: str
    query_vector: _containers.RepeatedScalarFieldContainer[float]
    level: int
    top_k: int
    vector_field: str
    include_members: bool
    max_members_per_community: int
    expand: bool
    expand_depth: int
    rerank: _cyrock_db_data_pb2.RerankOptionsProto
    def __init__(self, graph_id: _Optional[str] = ..., query: _Optional[str] = ..., query_vector: _Optional[_Iterable[float]] = ..., level: _Optional[int] = ..., top_k: _Optional[int] = ..., vector_field: _Optional[str] = ..., include_members: bool = ..., max_members_per_community: _Optional[int] = ..., expand: bool = ..., expand_depth: _Optional[int] = ..., rerank: _Optional[_Union[_cyrock_db_data_pb2.RerankOptionsProto, _Mapping]] = ...) -> None: ...

class GlobalSearchResultProto(_message.Message):
    __slots__ = ("community_id", "level", "score", "summary_text", "member_node_ids", "parent_community_id")
    COMMUNITY_ID_FIELD_NUMBER: _ClassVar[int]
    LEVEL_FIELD_NUMBER: _ClassVar[int]
    SCORE_FIELD_NUMBER: _ClassVar[int]
    SUMMARY_TEXT_FIELD_NUMBER: _ClassVar[int]
    MEMBER_NODE_IDS_FIELD_NUMBER: _ClassVar[int]
    PARENT_COMMUNITY_ID_FIELD_NUMBER: _ClassVar[int]
    community_id: int
    level: int
    score: float
    summary_text: str
    member_node_ids: _containers.RepeatedScalarFieldContainer[int]
    parent_community_id: int
    def __init__(self, community_id: _Optional[int] = ..., level: _Optional[int] = ..., score: _Optional[float] = ..., summary_text: _Optional[str] = ..., member_node_ids: _Optional[_Iterable[int]] = ..., parent_community_id: _Optional[int] = ...) -> None: ...

class GlobalSearchResponse(_message.Message):
    __slots__ = ("results",)
    RESULTS_FIELD_NUMBER: _ClassVar[int]
    results: _containers.RepeatedCompositeFieldContainer[GlobalSearchResultProto]
    def __init__(self, results: _Optional[_Iterable[_Union[GlobalSearchResultProto, _Mapping]]] = ...) -> None: ...

class CommunityRefProto(_message.Message):
    __slots__ = ("level", "community_id")
    LEVEL_FIELD_NUMBER: _ClassVar[int]
    COMMUNITY_ID_FIELD_NUMBER: _ClassVar[int]
    level: int
    community_id: int
    def __init__(self, level: _Optional[int] = ..., community_id: _Optional[int] = ...) -> None: ...

class RefreshCommunitiesResponse(_message.Message):
    __slots__ = ("hierarchy", "pruned_summaries", "stale_communities")
    HIERARCHY_FIELD_NUMBER: _ClassVar[int]
    PRUNED_SUMMARIES_FIELD_NUMBER: _ClassVar[int]
    STALE_COMMUNITIES_FIELD_NUMBER: _ClassVar[int]
    hierarchy: DetectCommunitiesResponse
    pruned_summaries: int
    stale_communities: _containers.RepeatedCompositeFieldContainer[CommunityRefProto]
    def __init__(self, hierarchy: _Optional[_Union[DetectCommunitiesResponse, _Mapping]] = ..., pruned_summaries: _Optional[int] = ..., stale_communities: _Optional[_Iterable[_Union[CommunityRefProto, _Mapping]]] = ...) -> None: ...

class CommunityStatusRequest(_message.Message):
    __slots__ = ("graph_id",)
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    graph_id: str
    def __init__(self, graph_id: _Optional[str] = ...) -> None: ...

class GetCommunitiesRequest(_message.Message):
    __slots__ = ("graph_id", "max_level", "include_members")
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    MAX_LEVEL_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_MEMBERS_FIELD_NUMBER: _ClassVar[int]
    graph_id: str
    max_level: int
    include_members: bool
    def __init__(self, graph_id: _Optional[str] = ..., max_level: _Optional[int] = ..., include_members: bool = ...) -> None: ...

class GetCommunityMembersRequest(_message.Message):
    __slots__ = ("graph_id", "level", "community_ids", "limit")
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    LEVEL_FIELD_NUMBER: _ClassVar[int]
    COMMUNITY_IDS_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    graph_id: str
    level: int
    community_ids: _containers.RepeatedScalarFieldContainer[int]
    limit: int
    def __init__(self, graph_id: _Optional[str] = ..., level: _Optional[int] = ..., community_ids: _Optional[_Iterable[int]] = ..., limit: _Optional[int] = ...) -> None: ...

class CommunityMembersProto(_message.Message):
    __slots__ = ("level", "community_id", "member_node_ids", "truncated")
    LEVEL_FIELD_NUMBER: _ClassVar[int]
    COMMUNITY_ID_FIELD_NUMBER: _ClassVar[int]
    MEMBER_NODE_IDS_FIELD_NUMBER: _ClassVar[int]
    TRUNCATED_FIELD_NUMBER: _ClassVar[int]
    level: int
    community_id: int
    member_node_ids: _containers.RepeatedScalarFieldContainer[int]
    truncated: bool
    def __init__(self, level: _Optional[int] = ..., community_id: _Optional[int] = ..., member_node_ids: _Optional[_Iterable[int]] = ..., truncated: bool = ...) -> None: ...

class GetCommunityMembersResponse(_message.Message):
    __slots__ = ("communities",)
    COMMUNITIES_FIELD_NUMBER: _ClassVar[int]
    communities: _containers.RepeatedCompositeFieldContainer[CommunityMembersProto]
    def __init__(self, communities: _Optional[_Iterable[_Union[CommunityMembersProto, _Mapping]]] = ...) -> None: ...

class GetCommunityAssignmentsRequest(_message.Message):
    __slots__ = ("graph_id", "level", "node_ids")
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    LEVEL_FIELD_NUMBER: _ClassVar[int]
    NODE_IDS_FIELD_NUMBER: _ClassVar[int]
    graph_id: str
    level: int
    node_ids: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, graph_id: _Optional[str] = ..., level: _Optional[int] = ..., node_ids: _Optional[_Iterable[int]] = ...) -> None: ...

class CommunityAssignmentProto(_message.Message):
    __slots__ = ("node_id", "community_id")
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    COMMUNITY_ID_FIELD_NUMBER: _ClassVar[int]
    node_id: int
    community_id: int
    def __init__(self, node_id: _Optional[int] = ..., community_id: _Optional[int] = ...) -> None: ...

class GetCommunityAssignmentsResponse(_message.Message):
    __slots__ = ("assignments", "levels")
    ASSIGNMENTS_FIELD_NUMBER: _ClassVar[int]
    LEVELS_FIELD_NUMBER: _ClassVar[int]
    assignments: _containers.RepeatedCompositeFieldContainer[CommunityAssignmentProto]
    levels: int
    def __init__(self, assignments: _Optional[_Iterable[_Union[CommunityAssignmentProto, _Mapping]]] = ..., levels: _Optional[int] = ...) -> None: ...

class CommunityStatusResponse(_message.Message):
    __slots__ = ("detected", "detected_at", "stale", "levels", "community_count", "summary_count")
    DETECTED_FIELD_NUMBER: _ClassVar[int]
    DETECTED_AT_FIELD_NUMBER: _ClassVar[int]
    STALE_FIELD_NUMBER: _ClassVar[int]
    LEVELS_FIELD_NUMBER: _ClassVar[int]
    COMMUNITY_COUNT_FIELD_NUMBER: _ClassVar[int]
    SUMMARY_COUNT_FIELD_NUMBER: _ClassVar[int]
    detected: bool
    detected_at: int
    stale: bool
    levels: int
    community_count: int
    summary_count: int
    def __init__(self, detected: bool = ..., detected_at: _Optional[int] = ..., stale: bool = ..., levels: _Optional[int] = ..., community_count: _Optional[int] = ..., summary_count: _Optional[int] = ...) -> None: ...

class EntityLinkRequest(_message.Message):
    __slots__ = ("graph_id", "field_name", "node_id", "threshold", "max_links")
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    FIELD_NAME_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    THRESHOLD_FIELD_NUMBER: _ClassVar[int]
    MAX_LINKS_FIELD_NUMBER: _ClassVar[int]
    graph_id: str
    field_name: str
    node_id: int
    threshold: float
    max_links: int
    def __init__(self, graph_id: _Optional[str] = ..., field_name: _Optional[str] = ..., node_id: _Optional[int] = ..., threshold: _Optional[float] = ..., max_links: _Optional[int] = ...) -> None: ...

class EntityLinkResponse(_message.Message):
    __slots__ = ("edges",)
    EDGES_FIELD_NUMBER: _ClassVar[int]
    edges: _containers.RepeatedCompositeFieldContainer[EdgeProto]
    def __init__(self, edges: _Optional[_Iterable[_Union[EdgeProto, _Mapping]]] = ...) -> None: ...

class ObserveRequest(_message.Message):
    __slots__ = ("graph_id", "labels", "vectors", "metadata", "link_field", "threshold", "max_links")
    class VectorsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: GraphVectorFieldProto
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[GraphVectorFieldProto, _Mapping]] = ...) -> None: ...
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    VECTORS_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    LINK_FIELD_FIELD_NUMBER: _ClassVar[int]
    THRESHOLD_FIELD_NUMBER: _ClassVar[int]
    MAX_LINKS_FIELD_NUMBER: _ClassVar[int]
    graph_id: str
    labels: _containers.RepeatedScalarFieldContainer[str]
    vectors: _containers.MessageMap[str, GraphVectorFieldProto]
    metadata: _cyrock_db_value_pb2.CyrockStruct
    link_field: str
    threshold: float
    max_links: int
    def __init__(self, graph_id: _Optional[str] = ..., labels: _Optional[_Iterable[str]] = ..., vectors: _Optional[_Mapping[str, GraphVectorFieldProto]] = ..., metadata: _Optional[_Union[_cyrock_db_value_pb2.CyrockStruct, _Mapping]] = ..., link_field: _Optional[str] = ..., threshold: _Optional[float] = ..., max_links: _Optional[int] = ...) -> None: ...

class ObserveResponse(_message.Message):
    __slots__ = ("node_id", "linked_ids")
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    LINKED_IDS_FIELD_NUMBER: _ClassVar[int]
    node_id: int
    linked_ids: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, node_id: _Optional[int] = ..., linked_ids: _Optional[_Iterable[int]] = ...) -> None: ...

class RecallRequest(_message.Message):
    __slots__ = ("graph_id", "field_name", "vector", "max_results", "recency_hours", "diversity_seed")
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    FIELD_NAME_FIELD_NUMBER: _ClassVar[int]
    VECTOR_FIELD_NUMBER: _ClassVar[int]
    MAX_RESULTS_FIELD_NUMBER: _ClassVar[int]
    RECENCY_HOURS_FIELD_NUMBER: _ClassVar[int]
    DIVERSITY_SEED_FIELD_NUMBER: _ClassVar[int]
    graph_id: str
    field_name: str
    vector: _containers.RepeatedScalarFieldContainer[float]
    max_results: int
    recency_hours: int
    diversity_seed: int
    def __init__(self, graph_id: _Optional[str] = ..., field_name: _Optional[str] = ..., vector: _Optional[_Iterable[float]] = ..., max_results: _Optional[int] = ..., recency_hours: _Optional[int] = ..., diversity_seed: _Optional[int] = ...) -> None: ...

class RecallResponse(_message.Message):
    __slots__ = ("nodes", "edges")
    NODES_FIELD_NUMBER: _ClassVar[int]
    EDGES_FIELD_NUMBER: _ClassVar[int]
    nodes: _containers.RepeatedCompositeFieldContainer[NodeProto]
    edges: _containers.RepeatedCompositeFieldContainer[EdgeProto]
    def __init__(self, nodes: _Optional[_Iterable[_Union[NodeProto, _Mapping]]] = ..., edges: _Optional[_Iterable[_Union[EdgeProto, _Mapping]]] = ...) -> None: ...

class DecayRequest(_message.Message):
    __slots__ = ("graph_id", "max_age_hours")
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    MAX_AGE_HOURS_FIELD_NUMBER: _ClassVar[int]
    graph_id: str
    max_age_hours: int
    def __init__(self, graph_id: _Optional[str] = ..., max_age_hours: _Optional[int] = ...) -> None: ...

class DecayResponse(_message.Message):
    __slots__ = ("pruned_nodes", "pruned_edges")
    PRUNED_NODES_FIELD_NUMBER: _ClassVar[int]
    PRUNED_EDGES_FIELD_NUMBER: _ClassVar[int]
    pruned_nodes: int
    pruned_edges: int
    def __init__(self, pruned_nodes: _Optional[int] = ..., pruned_edges: _Optional[int] = ...) -> None: ...

class ExecuteStatementRequest(_message.Message):
    __slots__ = ("graph_id", "statement", "vectors", "parameters", "unrestricted")
    class VectorsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: GraphVectorFieldProto
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[GraphVectorFieldProto, _Mapping]] = ...) -> None: ...
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    STATEMENT_FIELD_NUMBER: _ClassVar[int]
    VECTORS_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    UNRESTRICTED_FIELD_NUMBER: _ClassVar[int]
    graph_id: str
    statement: str
    vectors: _containers.MessageMap[str, GraphVectorFieldProto]
    parameters: _cyrock_db_value_pb2.CyrockStruct
    unrestricted: bool
    def __init__(self, graph_id: _Optional[str] = ..., statement: _Optional[str] = ..., vectors: _Optional[_Mapping[str, GraphVectorFieldProto]] = ..., parameters: _Optional[_Union[_cyrock_db_value_pb2.CyrockStruct, _Mapping]] = ..., unrestricted: bool = ...) -> None: ...

class GraphQueryRow(_message.Message):
    __slots__ = ("values",)
    VALUES_FIELD_NUMBER: _ClassVar[int]
    values: _cyrock_db_value_pb2.CyrockStruct
    def __init__(self, values: _Optional[_Union[_cyrock_db_value_pb2.CyrockStruct, _Mapping]] = ...) -> None: ...

class WriteSummaryProto(_message.Message):
    __slots__ = ("nodes_created", "nodes_deleted", "edges_created", "edges_deleted", "properties_set", "created_node_ids", "created_edge_ids")
    NODES_CREATED_FIELD_NUMBER: _ClassVar[int]
    NODES_DELETED_FIELD_NUMBER: _ClassVar[int]
    EDGES_CREATED_FIELD_NUMBER: _ClassVar[int]
    EDGES_DELETED_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_SET_FIELD_NUMBER: _ClassVar[int]
    CREATED_NODE_IDS_FIELD_NUMBER: _ClassVar[int]
    CREATED_EDGE_IDS_FIELD_NUMBER: _ClassVar[int]
    nodes_created: int
    nodes_deleted: int
    edges_created: int
    edges_deleted: int
    properties_set: int
    created_node_ids: _containers.RepeatedScalarFieldContainer[int]
    created_edge_ids: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, nodes_created: _Optional[int] = ..., nodes_deleted: _Optional[int] = ..., edges_created: _Optional[int] = ..., edges_deleted: _Optional[int] = ..., properties_set: _Optional[int] = ..., created_node_ids: _Optional[_Iterable[int]] = ..., created_edge_ids: _Optional[_Iterable[int]] = ...) -> None: ...

class StatementResponse(_message.Message):
    __slots__ = ("statement_class", "statement_type", "columns", "rows", "summary", "definition")
    STATEMENT_CLASS_FIELD_NUMBER: _ClassVar[int]
    STATEMENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    COLUMNS_FIELD_NUMBER: _ClassVar[int]
    ROWS_FIELD_NUMBER: _ClassVar[int]
    SUMMARY_FIELD_NUMBER: _ClassVar[int]
    DEFINITION_FIELD_NUMBER: _ClassVar[int]
    statement_class: str
    statement_type: str
    columns: _containers.RepeatedScalarFieldContainer[str]
    rows: _containers.RepeatedCompositeFieldContainer[GraphQueryRow]
    summary: WriteSummaryProto
    definition: _cyrock_db_platform_pb2.GraphDefinitionProto
    def __init__(self, statement_class: _Optional[str] = ..., statement_type: _Optional[str] = ..., columns: _Optional[_Iterable[str]] = ..., rows: _Optional[_Iterable[_Union[GraphQueryRow, _Mapping]]] = ..., summary: _Optional[_Union[WriteSummaryProto, _Mapping]] = ..., definition: _Optional[_Union[_cyrock_db_platform_pb2.GraphDefinitionProto, _Mapping]] = ...) -> None: ...

class MergeGraphDataRequest(_message.Message):
    __slots__ = ("branch_graph_id", "parent_graph_id")
    BRANCH_GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    PARENT_GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    branch_graph_id: str
    parent_graph_id: str
    def __init__(self, branch_graph_id: _Optional[str] = ..., parent_graph_id: _Optional[str] = ...) -> None: ...

class MergeGraphDataResponse(_message.Message):
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

class ExecuteTransactionRequest(_message.Message):
    __slots__ = ("graph_id", "operations")
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    OPERATIONS_FIELD_NUMBER: _ClassVar[int]
    graph_id: str
    operations: _containers.RepeatedCompositeFieldContainer[GraphOperationProto]
    def __init__(self, graph_id: _Optional[str] = ..., operations: _Optional[_Iterable[_Union[GraphOperationProto, _Mapping]]] = ...) -> None: ...

class GraphOperationProto(_message.Message):
    __slots__ = ("add_node", "add_edge", "remove_node", "remove_edge", "update_vector", "update_weight", "update_node_metadata", "upsert_node", "remove_node_by_key", "update_edge_metadata")
    ADD_NODE_FIELD_NUMBER: _ClassVar[int]
    ADD_EDGE_FIELD_NUMBER: _ClassVar[int]
    REMOVE_NODE_FIELD_NUMBER: _ClassVar[int]
    REMOVE_EDGE_FIELD_NUMBER: _ClassVar[int]
    UPDATE_VECTOR_FIELD_NUMBER: _ClassVar[int]
    UPDATE_WEIGHT_FIELD_NUMBER: _ClassVar[int]
    UPDATE_NODE_METADATA_FIELD_NUMBER: _ClassVar[int]
    UPSERT_NODE_FIELD_NUMBER: _ClassVar[int]
    REMOVE_NODE_BY_KEY_FIELD_NUMBER: _ClassVar[int]
    UPDATE_EDGE_METADATA_FIELD_NUMBER: _ClassVar[int]
    add_node: AddNodeOp
    add_edge: AddEdgeOp
    remove_node: RemoveNodeOp
    remove_edge: RemoveEdgeOp
    update_vector: UpdateVectorOp
    update_weight: UpdateWeightOp
    update_node_metadata: UpdateNodeMetadataOp
    upsert_node: UpsertNodeOp
    remove_node_by_key: RemoveNodeByKeyOp
    update_edge_metadata: UpdateEdgeMetadataOp
    def __init__(self, add_node: _Optional[_Union[AddNodeOp, _Mapping]] = ..., add_edge: _Optional[_Union[AddEdgeOp, _Mapping]] = ..., remove_node: _Optional[_Union[RemoveNodeOp, _Mapping]] = ..., remove_edge: _Optional[_Union[RemoveEdgeOp, _Mapping]] = ..., update_vector: _Optional[_Union[UpdateVectorOp, _Mapping]] = ..., update_weight: _Optional[_Union[UpdateWeightOp, _Mapping]] = ..., update_node_metadata: _Optional[_Union[UpdateNodeMetadataOp, _Mapping]] = ..., upsert_node: _Optional[_Union[UpsertNodeOp, _Mapping]] = ..., remove_node_by_key: _Optional[_Union[RemoveNodeByKeyOp, _Mapping]] = ..., update_edge_metadata: _Optional[_Union[UpdateEdgeMetadataOp, _Mapping]] = ...) -> None: ...

class AddNodeOp(_message.Message):
    __slots__ = ("labels", "vectors", "metadata")
    class VectorsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: GraphVectorFieldProto
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[GraphVectorFieldProto, _Mapping]] = ...) -> None: ...
    LABELS_FIELD_NUMBER: _ClassVar[int]
    VECTORS_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    labels: _containers.RepeatedScalarFieldContainer[str]
    vectors: _containers.MessageMap[str, GraphVectorFieldProto]
    metadata: _cyrock_db_value_pb2.CyrockStruct
    def __init__(self, labels: _Optional[_Iterable[str]] = ..., vectors: _Optional[_Mapping[str, GraphVectorFieldProto]] = ..., metadata: _Optional[_Union[_cyrock_db_value_pb2.CyrockStruct, _Mapping]] = ...) -> None: ...

class AddEdgeOp(_message.Message):
    __slots__ = ("source_id", "target_id", "type", "weight", "metadata")
    SOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    TARGET_ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    WEIGHT_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    source_id: int
    target_id: int
    type: str
    weight: float
    metadata: _cyrock_db_value_pb2.CyrockStruct
    def __init__(self, source_id: _Optional[int] = ..., target_id: _Optional[int] = ..., type: _Optional[str] = ..., weight: _Optional[float] = ..., metadata: _Optional[_Union[_cyrock_db_value_pb2.CyrockStruct, _Mapping]] = ...) -> None: ...

class RemoveNodeOp(_message.Message):
    __slots__ = ("node_id",)
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    node_id: int
    def __init__(self, node_id: _Optional[int] = ...) -> None: ...

class RemoveNodeByKeyOp(_message.Message):
    __slots__ = ("external_key",)
    EXTERNAL_KEY_FIELD_NUMBER: _ClassVar[int]
    external_key: str
    def __init__(self, external_key: _Optional[str] = ...) -> None: ...

class RemoveEdgeOp(_message.Message):
    __slots__ = ("edge_id",)
    EDGE_ID_FIELD_NUMBER: _ClassVar[int]
    edge_id: int
    def __init__(self, edge_id: _Optional[int] = ...) -> None: ...

class UpdateVectorOp(_message.Message):
    __slots__ = ("node_id", "field_name", "vector")
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    FIELD_NAME_FIELD_NUMBER: _ClassVar[int]
    VECTOR_FIELD_NUMBER: _ClassVar[int]
    node_id: int
    field_name: str
    vector: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, node_id: _Optional[int] = ..., field_name: _Optional[str] = ..., vector: _Optional[_Iterable[float]] = ...) -> None: ...

class UpdateWeightOp(_message.Message):
    __slots__ = ("edge_id", "weight")
    EDGE_ID_FIELD_NUMBER: _ClassVar[int]
    WEIGHT_FIELD_NUMBER: _ClassVar[int]
    edge_id: int
    weight: float
    def __init__(self, edge_id: _Optional[int] = ..., weight: _Optional[float] = ...) -> None: ...

class UpdateNodeMetadataOp(_message.Message):
    __slots__ = ("node_id", "metadata")
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    node_id: int
    metadata: _cyrock_db_value_pb2.CyrockStruct
    def __init__(self, node_id: _Optional[int] = ..., metadata: _Optional[_Union[_cyrock_db_value_pb2.CyrockStruct, _Mapping]] = ...) -> None: ...

class UpdateEdgeMetadataOp(_message.Message):
    __slots__ = ("edge_id", "metadata")
    EDGE_ID_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    edge_id: int
    metadata: _cyrock_db_value_pb2.CyrockStruct
    def __init__(self, edge_id: _Optional[int] = ..., metadata: _Optional[_Union[_cyrock_db_value_pb2.CyrockStruct, _Mapping]] = ...) -> None: ...

class UpsertNodeOp(_message.Message):
    __slots__ = ("external_key", "labels", "vectors", "metadata", "node_id")
    class VectorsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: GraphVectorFieldProto
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[GraphVectorFieldProto, _Mapping]] = ...) -> None: ...
    EXTERNAL_KEY_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    VECTORS_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    external_key: str
    labels: _containers.RepeatedScalarFieldContainer[str]
    vectors: _containers.MessageMap[str, GraphVectorFieldProto]
    metadata: _cyrock_db_value_pb2.CyrockStruct
    node_id: int
    def __init__(self, external_key: _Optional[str] = ..., labels: _Optional[_Iterable[str]] = ..., vectors: _Optional[_Mapping[str, GraphVectorFieldProto]] = ..., metadata: _Optional[_Union[_cyrock_db_value_pb2.CyrockStruct, _Mapping]] = ..., node_id: _Optional[int] = ...) -> None: ...

class OperationResultProto(_message.Message):
    __slots__ = ("index", "generated_id", "error")
    INDEX_FIELD_NUMBER: _ClassVar[int]
    GENERATED_ID_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    index: int
    generated_id: int
    error: str
    def __init__(self, index: _Optional[int] = ..., generated_id: _Optional[int] = ..., error: _Optional[str] = ...) -> None: ...

class ExecuteTransactionResponse(_message.Message):
    __slots__ = ("results",)
    RESULTS_FIELD_NUMBER: _ClassVar[int]
    results: _containers.RepeatedCompositeFieldContainer[OperationResultProto]
    def __init__(self, results: _Optional[_Iterable[_Union[OperationResultProto, _Mapping]]] = ...) -> None: ...

class GraphEmpty(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...
