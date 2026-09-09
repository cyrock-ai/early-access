import cyrock_db_value_pb2 as _cyrock_db_value_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ResourceKind(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    RESOURCE_KIND_UNSPECIFIED: _ClassVar[ResourceKind]
    GRAPH: _ClassVar[ResourceKind]
    COLLECTION: _ClassVar[ResourceKind]

class ChangeOp(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CHANGE_OP_UNSPECIFIED: _ClassVar[ChangeOp]
    CREATE: _ClassVar[ChangeOp]
    UPDATE: _ClassVar[ChangeOp]
    UPSERT: _ClassVar[ChangeOp]
    DELETE: _ClassVar[ChangeOp]
    SCHEMA: _ClassVar[ChangeOp]
    SNAPSHOT: _ClassVar[ChangeOp]
    DISCONTINUITY: _ClassVar[ChangeOp]

class EntityKind(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ENTITY_KIND_UNSPECIFIED: _ClassVar[EntityKind]
    NODE: _ClassVar[EntityKind]
    EDGE: _ClassVar[EntityKind]
    DOCUMENT: _ClassVar[EntityKind]
    SCHEMA_ENTITY: _ClassVar[EntityKind]
RESOURCE_KIND_UNSPECIFIED: ResourceKind
GRAPH: ResourceKind
COLLECTION: ResourceKind
CHANGE_OP_UNSPECIFIED: ChangeOp
CREATE: ChangeOp
UPDATE: ChangeOp
UPSERT: ChangeOp
DELETE: ChangeOp
SCHEMA: ChangeOp
SNAPSHOT: ChangeOp
DISCONTINUITY: ChangeOp
ENTITY_KIND_UNSPECIFIED: EntityKind
NODE: EntityKind
EDGE: EntityKind
DOCUMENT: EntityKind
SCHEMA_ENTITY: EntityKind

class WatchRequest(_message.Message):
    __slots__ = ("resource_kind", "resource_id", "from_lsn", "from_now", "with_snapshot", "include_vectors", "filter")
    RESOURCE_KIND_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    FROM_LSN_FIELD_NUMBER: _ClassVar[int]
    FROM_NOW_FIELD_NUMBER: _ClassVar[int]
    WITH_SNAPSHOT_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_VECTORS_FIELD_NUMBER: _ClassVar[int]
    FILTER_FIELD_NUMBER: _ClassVar[int]
    resource_kind: ResourceKind
    resource_id: str
    from_lsn: int
    from_now: bool
    with_snapshot: bool
    include_vectors: bool
    filter: ChangeFilter
    def __init__(self, resource_kind: _Optional[_Union[ResourceKind, str]] = ..., resource_id: _Optional[str] = ..., from_lsn: _Optional[int] = ..., from_now: bool = ..., with_snapshot: bool = ..., include_vectors: bool = ..., filter: _Optional[_Union[ChangeFilter, _Mapping]] = ...) -> None: ...

class ChangeFilter(_message.Message):
    __slots__ = ("ops", "entity_kinds", "labels", "metadata_predicate")
    OPS_FIELD_NUMBER: _ClassVar[int]
    ENTITY_KINDS_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    METADATA_PREDICATE_FIELD_NUMBER: _ClassVar[int]
    ops: _containers.RepeatedScalarFieldContainer[ChangeOp]
    entity_kinds: _containers.RepeatedScalarFieldContainer[EntityKind]
    labels: _containers.RepeatedScalarFieldContainer[str]
    metadata_predicate: str
    def __init__(self, ops: _Optional[_Iterable[_Union[ChangeOp, str]]] = ..., entity_kinds: _Optional[_Iterable[_Union[EntityKind, str]]] = ..., labels: _Optional[_Iterable[str]] = ..., metadata_predicate: _Optional[str] = ...) -> None: ...

class VectorValue(_message.Message):
    __slots__ = ("values",)
    VALUES_FIELD_NUMBER: _ClassVar[int]
    values: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, values: _Optional[_Iterable[float]] = ...) -> None: ...

class ChangeSource(_message.Message):
    __slots__ = ("resource_kind", "resource_id", "lsn", "tx_id", "ts_ms")
    RESOURCE_KIND_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    LSN_FIELD_NUMBER: _ClassVar[int]
    TX_ID_FIELD_NUMBER: _ClassVar[int]
    TS_MS_FIELD_NUMBER: _ClassVar[int]
    resource_kind: ResourceKind
    resource_id: str
    lsn: int
    tx_id: int
    ts_ms: int
    def __init__(self, resource_kind: _Optional[_Union[ResourceKind, str]] = ..., resource_id: _Optional[str] = ..., lsn: _Optional[int] = ..., tx_id: _Optional[int] = ..., ts_ms: _Optional[int] = ...) -> None: ...

class EdgeInfo(_message.Message):
    __slots__ = ("source_id", "target_id", "type", "weight")
    SOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    TARGET_ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    WEIGHT_FIELD_NUMBER: _ClassVar[int]
    source_id: int
    target_id: int
    type: str
    weight: float
    def __init__(self, source_id: _Optional[int] = ..., target_id: _Optional[int] = ..., type: _Optional[str] = ..., weight: _Optional[float] = ...) -> None: ...

class SchemaChange(_message.Message):
    __slots__ = ("added_fields", "dropped_fields")
    ADDED_FIELDS_FIELD_NUMBER: _ClassVar[int]
    DROPPED_FIELDS_FIELD_NUMBER: _ClassVar[int]
    added_fields: _containers.RepeatedScalarFieldContainer[str]
    dropped_fields: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, added_fields: _Optional[_Iterable[str]] = ..., dropped_fields: _Optional[_Iterable[str]] = ...) -> None: ...

class ChangeEvent(_message.Message):
    __slots__ = ("source", "op", "entity_kind", "entity_id", "external_key", "labels", "metadata", "vectors", "edge", "schema", "snapshot_complete")
    class VectorsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: VectorValue
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[VectorValue, _Mapping]] = ...) -> None: ...
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    OP_FIELD_NUMBER: _ClassVar[int]
    ENTITY_KIND_FIELD_NUMBER: _ClassVar[int]
    ENTITY_ID_FIELD_NUMBER: _ClassVar[int]
    EXTERNAL_KEY_FIELD_NUMBER: _ClassVar[int]
    LABELS_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    VECTORS_FIELD_NUMBER: _ClassVar[int]
    EDGE_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_FIELD_NUMBER: _ClassVar[int]
    SNAPSHOT_COMPLETE_FIELD_NUMBER: _ClassVar[int]
    source: ChangeSource
    op: ChangeOp
    entity_kind: EntityKind
    entity_id: int
    external_key: str
    labels: _containers.RepeatedScalarFieldContainer[str]
    metadata: _cyrock_db_value_pb2.CyrockStruct
    vectors: _containers.MessageMap[str, VectorValue]
    edge: EdgeInfo
    schema: SchemaChange
    snapshot_complete: bool
    def __init__(self, source: _Optional[_Union[ChangeSource, _Mapping]] = ..., op: _Optional[_Union[ChangeOp, str]] = ..., entity_kind: _Optional[_Union[EntityKind, str]] = ..., entity_id: _Optional[int] = ..., external_key: _Optional[str] = ..., labels: _Optional[_Iterable[str]] = ..., metadata: _Optional[_Union[_cyrock_db_value_pb2.CyrockStruct, _Mapping]] = ..., vectors: _Optional[_Mapping[str, VectorValue]] = ..., edge: _Optional[_Union[EdgeInfo, _Mapping]] = ..., schema: _Optional[_Union[SchemaChange, _Mapping]] = ..., snapshot_complete: bool = ...) -> None: ...
