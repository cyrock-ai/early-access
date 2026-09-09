from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CyrockValue(_message.Message):
    __slots__ = ("null_value", "string_value", "int_value", "double_value", "bool_value", "bytes_value", "list_value", "struct_value")
    NULL_VALUE_FIELD_NUMBER: _ClassVar[int]
    STRING_VALUE_FIELD_NUMBER: _ClassVar[int]
    INT_VALUE_FIELD_NUMBER: _ClassVar[int]
    DOUBLE_VALUE_FIELD_NUMBER: _ClassVar[int]
    BOOL_VALUE_FIELD_NUMBER: _ClassVar[int]
    BYTES_VALUE_FIELD_NUMBER: _ClassVar[int]
    LIST_VALUE_FIELD_NUMBER: _ClassVar[int]
    STRUCT_VALUE_FIELD_NUMBER: _ClassVar[int]
    null_value: bool
    string_value: str
    int_value: int
    double_value: float
    bool_value: bool
    bytes_value: bytes
    list_value: CyrockList
    struct_value: CyrockStruct
    def __init__(self, null_value: bool = ..., string_value: _Optional[str] = ..., int_value: _Optional[int] = ..., double_value: _Optional[float] = ..., bool_value: bool = ..., bytes_value: _Optional[bytes] = ..., list_value: _Optional[_Union[CyrockList, _Mapping]] = ..., struct_value: _Optional[_Union[CyrockStruct, _Mapping]] = ...) -> None: ...

class CyrockList(_message.Message):
    __slots__ = ("values",)
    VALUES_FIELD_NUMBER: _ClassVar[int]
    values: _containers.RepeatedCompositeFieldContainer[CyrockValue]
    def __init__(self, values: _Optional[_Iterable[_Union[CyrockValue, _Mapping]]] = ...) -> None: ...

class CyrockStruct(_message.Message):
    __slots__ = ("fields",)
    class FieldsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: CyrockValue
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[CyrockValue, _Mapping]] = ...) -> None: ...
    FIELDS_FIELD_NUMBER: _ClassVar[int]
    fields: _containers.MessageMap[str, CyrockValue]
    def __init__(self, fields: _Optional[_Mapping[str, CyrockValue]] = ...) -> None: ...
