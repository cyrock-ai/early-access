import cyrock_db_value_pb2 as _cyrock_db_value_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class VectorFieldProto(_message.Message):
    __slots__ = ("values", "text")
    VALUES_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    values: _containers.RepeatedScalarFieldContainer[float]
    text: str
    def __init__(self, values: _Optional[_Iterable[float]] = ..., text: _Optional[str] = ...) -> None: ...

class DocumentProto(_message.Message):
    __slots__ = ("id", "vectors", "metadata", "external_key")
    class VectorsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: VectorFieldProto
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[VectorFieldProto, _Mapping]] = ...) -> None: ...
    ID_FIELD_NUMBER: _ClassVar[int]
    VECTORS_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    EXTERNAL_KEY_FIELD_NUMBER: _ClassVar[int]
    id: int
    vectors: _containers.MessageMap[str, VectorFieldProto]
    metadata: _cyrock_db_value_pb2.CyrockStruct
    external_key: str
    def __init__(self, id: _Optional[int] = ..., vectors: _Optional[_Mapping[str, VectorFieldProto]] = ..., metadata: _Optional[_Union[_cyrock_db_value_pb2.CyrockStruct, _Mapping]] = ..., external_key: _Optional[str] = ...) -> None: ...

class MatchProto(_message.Message):
    __slots__ = ("score", "document")
    SCORE_FIELD_NUMBER: _ClassVar[int]
    DOCUMENT_FIELD_NUMBER: _ClassVar[int]
    score: float
    document: DocumentProto
    def __init__(self, score: _Optional[float] = ..., document: _Optional[_Union[DocumentProto, _Mapping]] = ...) -> None: ...

class UpsertDocumentRequest(_message.Message):
    __slots__ = ("collection_id", "id", "vectors", "metadata", "external_key")
    class VectorsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: VectorFieldProto
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[VectorFieldProto, _Mapping]] = ...) -> None: ...
    COLLECTION_ID_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    VECTORS_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    EXTERNAL_KEY_FIELD_NUMBER: _ClassVar[int]
    collection_id: str
    id: int
    vectors: _containers.MessageMap[str, VectorFieldProto]
    metadata: _cyrock_db_value_pb2.CyrockStruct
    external_key: str
    def __init__(self, collection_id: _Optional[str] = ..., id: _Optional[int] = ..., vectors: _Optional[_Mapping[str, VectorFieldProto]] = ..., metadata: _Optional[_Union[_cyrock_db_value_pb2.CyrockStruct, _Mapping]] = ..., external_key: _Optional[str] = ...) -> None: ...

class UpsertDocumentResponse(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: int
    def __init__(self, id: _Optional[int] = ...) -> None: ...

class UpsertDocumentsBatchRequest(_message.Message):
    __slots__ = ("collection_id", "documents")
    COLLECTION_ID_FIELD_NUMBER: _ClassVar[int]
    DOCUMENTS_FIELD_NUMBER: _ClassVar[int]
    collection_id: str
    documents: _containers.RepeatedCompositeFieldContainer[UpsertDocumentRequest]
    def __init__(self, collection_id: _Optional[str] = ..., documents: _Optional[_Iterable[_Union[UpsertDocumentRequest, _Mapping]]] = ...) -> None: ...

class UpsertDocumentsBatchResponse(_message.Message):
    __slots__ = ("ids",)
    IDS_FIELD_NUMBER: _ClassVar[int]
    ids: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, ids: _Optional[_Iterable[int]] = ...) -> None: ...

class GetDocumentRequest(_message.Message):
    __slots__ = ("collection_id", "document_id")
    COLLECTION_ID_FIELD_NUMBER: _ClassVar[int]
    DOCUMENT_ID_FIELD_NUMBER: _ClassVar[int]
    collection_id: str
    document_id: int
    def __init__(self, collection_id: _Optional[str] = ..., document_id: _Optional[int] = ...) -> None: ...

class ListDocumentsRequest(_message.Message):
    __slots__ = ("collection_id", "offset", "limit")
    COLLECTION_ID_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    collection_id: str
    offset: int
    limit: int
    def __init__(self, collection_id: _Optional[str] = ..., offset: _Optional[int] = ..., limit: _Optional[int] = ...) -> None: ...

class DocumentList(_message.Message):
    __slots__ = ("documents",)
    DOCUMENTS_FIELD_NUMBER: _ClassVar[int]
    documents: _containers.RepeatedCompositeFieldContainer[DocumentProto]
    def __init__(self, documents: _Optional[_Iterable[_Union[DocumentProto, _Mapping]]] = ...) -> None: ...

class DeleteDocumentRequest(_message.Message):
    __slots__ = ("collection_id", "document_id")
    COLLECTION_ID_FIELD_NUMBER: _ClassVar[int]
    DOCUMENT_ID_FIELD_NUMBER: _ClassVar[int]
    collection_id: str
    document_id: int
    def __init__(self, collection_id: _Optional[str] = ..., document_id: _Optional[int] = ...) -> None: ...

class UpsertByKeyRequest(_message.Message):
    __slots__ = ("collection_id", "external_key", "vectors", "metadata")
    class VectorsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: VectorFieldProto
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[VectorFieldProto, _Mapping]] = ...) -> None: ...
    COLLECTION_ID_FIELD_NUMBER: _ClassVar[int]
    EXTERNAL_KEY_FIELD_NUMBER: _ClassVar[int]
    VECTORS_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    collection_id: str
    external_key: str
    vectors: _containers.MessageMap[str, VectorFieldProto]
    metadata: _cyrock_db_value_pb2.CyrockStruct
    def __init__(self, collection_id: _Optional[str] = ..., external_key: _Optional[str] = ..., vectors: _Optional[_Mapping[str, VectorFieldProto]] = ..., metadata: _Optional[_Union[_cyrock_db_value_pb2.CyrockStruct, _Mapping]] = ...) -> None: ...

class UpsertByKeyResponse(_message.Message):
    __slots__ = ("id", "created")
    ID_FIELD_NUMBER: _ClassVar[int]
    CREATED_FIELD_NUMBER: _ClassVar[int]
    id: int
    created: bool
    def __init__(self, id: _Optional[int] = ..., created: bool = ...) -> None: ...

class GetByKeyRequest(_message.Message):
    __slots__ = ("collection_id", "external_key")
    COLLECTION_ID_FIELD_NUMBER: _ClassVar[int]
    EXTERNAL_KEY_FIELD_NUMBER: _ClassVar[int]
    collection_id: str
    external_key: str
    def __init__(self, collection_id: _Optional[str] = ..., external_key: _Optional[str] = ...) -> None: ...

class RemoveByKeyRequest(_message.Message):
    __slots__ = ("collection_id", "external_key")
    COLLECTION_ID_FIELD_NUMBER: _ClassVar[int]
    EXTERNAL_KEY_FIELD_NUMBER: _ClassVar[int]
    collection_id: str
    external_key: str
    def __init__(self, collection_id: _Optional[str] = ..., external_key: _Optional[str] = ...) -> None: ...

class RerankOptionsProto(_message.Message):
    __slots__ = ("enabled", "model", "field", "candidates", "query")
    ENABLED_FIELD_NUMBER: _ClassVar[int]
    MODEL_FIELD_NUMBER: _ClassVar[int]
    FIELD_FIELD_NUMBER: _ClassVar[int]
    CANDIDATES_FIELD_NUMBER: _ClassVar[int]
    QUERY_FIELD_NUMBER: _ClassVar[int]
    enabled: bool
    model: str
    field: str
    candidates: int
    query: str
    def __init__(self, enabled: bool = ..., model: _Optional[str] = ..., field: _Optional[str] = ..., candidates: _Optional[int] = ..., query: _Optional[str] = ...) -> None: ...

class SearchDocumentsRequest(_message.Message):
    __slots__ = ("collection_id", "vector_field", "vector", "max_results", "filter", "rerank")
    COLLECTION_ID_FIELD_NUMBER: _ClassVar[int]
    VECTOR_FIELD_FIELD_NUMBER: _ClassVar[int]
    VECTOR_FIELD_NUMBER: _ClassVar[int]
    MAX_RESULTS_FIELD_NUMBER: _ClassVar[int]
    FILTER_FIELD_NUMBER: _ClassVar[int]
    RERANK_FIELD_NUMBER: _ClassVar[int]
    collection_id: str
    vector_field: str
    vector: _containers.RepeatedScalarFieldContainer[float]
    max_results: int
    filter: str
    rerank: RerankOptionsProto
    def __init__(self, collection_id: _Optional[str] = ..., vector_field: _Optional[str] = ..., vector: _Optional[_Iterable[float]] = ..., max_results: _Optional[int] = ..., filter: _Optional[str] = ..., rerank: _Optional[_Union[RerankOptionsProto, _Mapping]] = ...) -> None: ...

class SearchDocumentsResponse(_message.Message):
    __slots__ = ("matches",)
    MATCHES_FIELD_NUMBER: _ClassVar[int]
    matches: _containers.RepeatedCompositeFieldContainer[MatchProto]
    def __init__(self, matches: _Optional[_Iterable[_Union[MatchProto, _Mapping]]] = ...) -> None: ...

class VectorQueryProto(_message.Message):
    __slots__ = ("field_name", "vector", "weight")
    FIELD_NAME_FIELD_NUMBER: _ClassVar[int]
    VECTOR_FIELD_NUMBER: _ClassVar[int]
    WEIGHT_FIELD_NUMBER: _ClassVar[int]
    field_name: str
    vector: _containers.RepeatedScalarFieldContainer[float]
    weight: float
    def __init__(self, field_name: _Optional[str] = ..., vector: _Optional[_Iterable[float]] = ..., weight: _Optional[float] = ...) -> None: ...

class MultiSearchDocumentsRequest(_message.Message):
    __slots__ = ("collection_id", "queries", "max_results", "fusion", "filter", "rerank")
    COLLECTION_ID_FIELD_NUMBER: _ClassVar[int]
    QUERIES_FIELD_NUMBER: _ClassVar[int]
    MAX_RESULTS_FIELD_NUMBER: _ClassVar[int]
    FUSION_FIELD_NUMBER: _ClassVar[int]
    FILTER_FIELD_NUMBER: _ClassVar[int]
    RERANK_FIELD_NUMBER: _ClassVar[int]
    collection_id: str
    queries: _containers.RepeatedCompositeFieldContainer[VectorQueryProto]
    max_results: int
    fusion: str
    filter: str
    rerank: RerankOptionsProto
    def __init__(self, collection_id: _Optional[str] = ..., queries: _Optional[_Iterable[_Union[VectorQueryProto, _Mapping]]] = ..., max_results: _Optional[int] = ..., fusion: _Optional[str] = ..., filter: _Optional[str] = ..., rerank: _Optional[_Union[RerankOptionsProto, _Mapping]] = ...) -> None: ...

class TextQueryProto(_message.Message):
    __slots__ = ("text_field", "query", "weight")
    TEXT_FIELD_FIELD_NUMBER: _ClassVar[int]
    QUERY_FIELD_NUMBER: _ClassVar[int]
    WEIGHT_FIELD_NUMBER: _ClassVar[int]
    text_field: str
    query: str
    weight: float
    def __init__(self, text_field: _Optional[str] = ..., query: _Optional[str] = ..., weight: _Optional[float] = ...) -> None: ...

class HybridSearchDocumentsRequest(_message.Message):
    __slots__ = ("collection_id", "vector_queries", "text_queries", "max_results", "fusion", "filter", "rerank")
    COLLECTION_ID_FIELD_NUMBER: _ClassVar[int]
    VECTOR_QUERIES_FIELD_NUMBER: _ClassVar[int]
    TEXT_QUERIES_FIELD_NUMBER: _ClassVar[int]
    MAX_RESULTS_FIELD_NUMBER: _ClassVar[int]
    FUSION_FIELD_NUMBER: _ClassVar[int]
    FILTER_FIELD_NUMBER: _ClassVar[int]
    RERANK_FIELD_NUMBER: _ClassVar[int]
    collection_id: str
    vector_queries: _containers.RepeatedCompositeFieldContainer[VectorQueryProto]
    text_queries: _containers.RepeatedCompositeFieldContainer[TextQueryProto]
    max_results: int
    fusion: str
    filter: str
    rerank: RerankOptionsProto
    def __init__(self, collection_id: _Optional[str] = ..., vector_queries: _Optional[_Iterable[_Union[VectorQueryProto, _Mapping]]] = ..., text_queries: _Optional[_Iterable[_Union[TextQueryProto, _Mapping]]] = ..., max_results: _Optional[int] = ..., fusion: _Optional[str] = ..., filter: _Optional[str] = ..., rerank: _Optional[_Union[RerankOptionsProto, _Mapping]] = ...) -> None: ...

class ExecuteDocumentTransactionRequest(_message.Message):
    __slots__ = ("collection_id", "operations")
    COLLECTION_ID_FIELD_NUMBER: _ClassVar[int]
    OPERATIONS_FIELD_NUMBER: _ClassVar[int]
    collection_id: str
    operations: _containers.RepeatedCompositeFieldContainer[DocumentOperationProto]
    def __init__(self, collection_id: _Optional[str] = ..., operations: _Optional[_Iterable[_Union[DocumentOperationProto, _Mapping]]] = ...) -> None: ...

class DocumentOperationProto(_message.Message):
    __slots__ = ("upsert", "remove", "upsert_by_key")
    UPSERT_FIELD_NUMBER: _ClassVar[int]
    REMOVE_FIELD_NUMBER: _ClassVar[int]
    UPSERT_BY_KEY_FIELD_NUMBER: _ClassVar[int]
    upsert: UpsertDocumentOp
    remove: RemoveDocumentOp
    upsert_by_key: UpsertByKeyOp
    def __init__(self, upsert: _Optional[_Union[UpsertDocumentOp, _Mapping]] = ..., remove: _Optional[_Union[RemoveDocumentOp, _Mapping]] = ..., upsert_by_key: _Optional[_Union[UpsertByKeyOp, _Mapping]] = ...) -> None: ...

class UpsertDocumentOp(_message.Message):
    __slots__ = ("id", "vectors", "metadata")
    class VectorsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: VectorFieldProto
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[VectorFieldProto, _Mapping]] = ...) -> None: ...
    ID_FIELD_NUMBER: _ClassVar[int]
    VECTORS_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    id: int
    vectors: _containers.MessageMap[str, VectorFieldProto]
    metadata: _cyrock_db_value_pb2.CyrockStruct
    def __init__(self, id: _Optional[int] = ..., vectors: _Optional[_Mapping[str, VectorFieldProto]] = ..., metadata: _Optional[_Union[_cyrock_db_value_pb2.CyrockStruct, _Mapping]] = ...) -> None: ...

class RemoveDocumentOp(_message.Message):
    __slots__ = ("document_id",)
    DOCUMENT_ID_FIELD_NUMBER: _ClassVar[int]
    document_id: int
    def __init__(self, document_id: _Optional[int] = ...) -> None: ...

class UpsertByKeyOp(_message.Message):
    __slots__ = ("external_key", "vectors", "metadata")
    class VectorsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: VectorFieldProto
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[VectorFieldProto, _Mapping]] = ...) -> None: ...
    EXTERNAL_KEY_FIELD_NUMBER: _ClassVar[int]
    VECTORS_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    external_key: str
    vectors: _containers.MessageMap[str, VectorFieldProto]
    metadata: _cyrock_db_value_pb2.CyrockStruct
    def __init__(self, external_key: _Optional[str] = ..., vectors: _Optional[_Mapping[str, VectorFieldProto]] = ..., metadata: _Optional[_Union[_cyrock_db_value_pb2.CyrockStruct, _Mapping]] = ...) -> None: ...

class DocumentOperationResultProto(_message.Message):
    __slots__ = ("index", "generated_id", "error")
    INDEX_FIELD_NUMBER: _ClassVar[int]
    GENERATED_ID_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    index: int
    generated_id: int
    error: str
    def __init__(self, index: _Optional[int] = ..., generated_id: _Optional[int] = ..., error: _Optional[str] = ...) -> None: ...

class ExecuteDocumentTransactionResponse(_message.Message):
    __slots__ = ("results",)
    RESULTS_FIELD_NUMBER: _ClassVar[int]
    results: _containers.RepeatedCompositeFieldContainer[DocumentOperationResultProto]
    def __init__(self, results: _Optional[_Iterable[_Union[DocumentOperationResultProto, _Mapping]]] = ...) -> None: ...

class ExecuteCollectionStatementRequest(_message.Message):
    __slots__ = ("collection_id", "statement", "vectors", "parameters", "unrestricted")
    class VectorsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: VectorFieldProto
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[VectorFieldProto, _Mapping]] = ...) -> None: ...
    COLLECTION_ID_FIELD_NUMBER: _ClassVar[int]
    STATEMENT_FIELD_NUMBER: _ClassVar[int]
    VECTORS_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    UNRESTRICTED_FIELD_NUMBER: _ClassVar[int]
    collection_id: str
    statement: str
    vectors: _containers.MessageMap[str, VectorFieldProto]
    parameters: _cyrock_db_value_pb2.CyrockStruct
    unrestricted: bool
    def __init__(self, collection_id: _Optional[str] = ..., statement: _Optional[str] = ..., vectors: _Optional[_Mapping[str, VectorFieldProto]] = ..., parameters: _Optional[_Union[_cyrock_db_value_pb2.CyrockStruct, _Mapping]] = ..., unrestricted: bool = ...) -> None: ...

class CollectionQueryRow(_message.Message):
    __slots__ = ("values",)
    VALUES_FIELD_NUMBER: _ClassVar[int]
    values: _cyrock_db_value_pb2.CyrockStruct
    def __init__(self, values: _Optional[_Union[_cyrock_db_value_pb2.CyrockStruct, _Mapping]] = ...) -> None: ...

class CollectionWriteSummaryProto(_message.Message):
    __slots__ = ("documents_created", "documents_deleted", "properties_set", "created_document_ids")
    DOCUMENTS_CREATED_FIELD_NUMBER: _ClassVar[int]
    DOCUMENTS_DELETED_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_SET_FIELD_NUMBER: _ClassVar[int]
    CREATED_DOCUMENT_IDS_FIELD_NUMBER: _ClassVar[int]
    documents_created: int
    documents_deleted: int
    properties_set: int
    created_document_ids: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, documents_created: _Optional[int] = ..., documents_deleted: _Optional[int] = ..., properties_set: _Optional[int] = ..., created_document_ids: _Optional[_Iterable[int]] = ...) -> None: ...

class CollectionStatementResponse(_message.Message):
    __slots__ = ("statement_class", "statement_type", "columns", "rows", "summary")
    STATEMENT_CLASS_FIELD_NUMBER: _ClassVar[int]
    STATEMENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    COLUMNS_FIELD_NUMBER: _ClassVar[int]
    ROWS_FIELD_NUMBER: _ClassVar[int]
    SUMMARY_FIELD_NUMBER: _ClassVar[int]
    statement_class: str
    statement_type: str
    columns: _containers.RepeatedScalarFieldContainer[str]
    rows: _containers.RepeatedCompositeFieldContainer[CollectionQueryRow]
    summary: CollectionWriteSummaryProto
    def __init__(self, statement_class: _Optional[str] = ..., statement_type: _Optional[str] = ..., columns: _Optional[_Iterable[str]] = ..., rows: _Optional[_Iterable[_Union[CollectionQueryRow, _Mapping]]] = ..., summary: _Optional[_Union[CollectionWriteSummaryProto, _Mapping]] = ...) -> None: ...
