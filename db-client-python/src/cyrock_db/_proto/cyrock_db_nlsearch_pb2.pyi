import cyrock_db_data_pb2 as _cyrock_db_data_pb2
import cyrock_db_value_pb2 as _cyrock_db_value_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class NlSearchCollectionRequest(_message.Message):
    __slots__ = ("collection_id", "query", "vector_field", "max_results", "rerank")
    COLLECTION_ID_FIELD_NUMBER: _ClassVar[int]
    QUERY_FIELD_NUMBER: _ClassVar[int]
    VECTOR_FIELD_FIELD_NUMBER: _ClassVar[int]
    MAX_RESULTS_FIELD_NUMBER: _ClassVar[int]
    RERANK_FIELD_NUMBER: _ClassVar[int]
    collection_id: str
    query: str
    vector_field: str
    max_results: int
    rerank: _cyrock_db_data_pb2.RerankOptionsProto
    def __init__(self, collection_id: _Optional[str] = ..., query: _Optional[str] = ..., vector_field: _Optional[str] = ..., max_results: _Optional[int] = ..., rerank: _Optional[_Union[_cyrock_db_data_pb2.RerankOptionsProto, _Mapping]] = ...) -> None: ...

class NlSearchGraphRequest(_message.Message):
    __slots__ = ("graph_id", "query", "vector_field", "max_results", "rerank")
    GRAPH_ID_FIELD_NUMBER: _ClassVar[int]
    QUERY_FIELD_NUMBER: _ClassVar[int]
    VECTOR_FIELD_FIELD_NUMBER: _ClassVar[int]
    MAX_RESULTS_FIELD_NUMBER: _ClassVar[int]
    RERANK_FIELD_NUMBER: _ClassVar[int]
    graph_id: str
    query: str
    vector_field: str
    max_results: int
    rerank: _cyrock_db_data_pb2.RerankOptionsProto
    def __init__(self, graph_id: _Optional[str] = ..., query: _Optional[str] = ..., vector_field: _Optional[str] = ..., max_results: _Optional[int] = ..., rerank: _Optional[_Union[_cyrock_db_data_pb2.RerankOptionsProto, _Mapping]] = ...) -> None: ...

class NlSearchMatchProto(_message.Message):
    __slots__ = ("id", "score", "metadata")
    ID_FIELD_NUMBER: _ClassVar[int]
    SCORE_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    id: int
    score: float
    metadata: _cyrock_db_value_pb2.CyrockStruct
    def __init__(self, id: _Optional[int] = ..., score: _Optional[float] = ..., metadata: _Optional[_Union[_cyrock_db_value_pb2.CyrockStruct, _Mapping]] = ...) -> None: ...

class NlSearchResponseProto(_message.Message):
    __slots__ = ("matches", "translated_query", "query_type")
    MATCHES_FIELD_NUMBER: _ClassVar[int]
    TRANSLATED_QUERY_FIELD_NUMBER: _ClassVar[int]
    QUERY_TYPE_FIELD_NUMBER: _ClassVar[int]
    matches: _containers.RepeatedCompositeFieldContainer[NlSearchMatchProto]
    translated_query: str
    query_type: str
    def __init__(self, matches: _Optional[_Iterable[_Union[NlSearchMatchProto, _Mapping]]] = ..., translated_query: _Optional[str] = ..., query_type: _Optional[str] = ...) -> None: ...
