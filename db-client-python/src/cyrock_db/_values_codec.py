"""The ``CyrockValue`` wire codec: Python values to and from the shared value type.

The Python counterpart of ``CyrockValues`` (``proto/src/main/java/ai/cyrock/db/proto/value``). This
is the encoding for everything a caller supplies - node, edge and document metadata, CyQL row values
and query parameters - so it is worth stating why the wire type is not
``google.protobuf.Value``: that type inherits JSON's single numeric kind, a double, and this system
offers a ``LONG`` distinct from ``INTEGER``. A LONG past 2^53 does not survive a double, and used to
be rounded silently, with no exception and no warning. That is issue #121, and this codec exists to
make it impossible.

**Two ordering traps, both load-bearing.**

``bool`` is checked before ``int`` because in Python ``bool`` *is* a subclass of ``int``:
``isinstance(True, int)`` is ``True``. Check ints first and ``True`` goes out as ``int_value=1`` and
comes back as ``1``. The Java codec puts ``Boolean`` ahead of its ``Number`` branch for a different
reason - a ``Boolean`` is not a ``Number`` there - but the consequence of getting it wrong is the
same silent type change this whole type exists to prevent.

``str`` and ``bytes`` are checked before the sequence branch because both are sequences in Python. A
string would otherwise be encoded as a list of one-character strings.

**Integers wider than int64.** Python integers are arbitrary precision, so this is routine here
rather than exotic: an ``int`` that does not fit a signed 64-bit field is encoded as its exact
decimal text, matching what the Java codec does with a large ``BigInteger``. Text keeps every digit;
a double would drop most of them. The value reads back as a string, which is lossy in type but not
in magnitude - the alternative is to be wrong about the number itself.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any

from ._proto import cyrock_db_value_pb2 as value_pb2

__all__ = ["from_struct", "from_value", "to_struct", "to_value"]

INT64_MIN = -(2**63)
INT64_MAX = 2**63 - 1


def to_value(value: Any) -> Any:
    """Encodes one Python value as a ``CyrockValue``."""
    encoded = value_pb2.CyrockValue()

    if value is None:
        # Presence-only: the payload is never read, only the field being set means anything.
        encoded.null_value = True
    elif isinstance(value, bool):
        # Before int. See the module docstring.
        encoded.bool_value = value
    elif isinstance(value, int):
        if INT64_MIN <= value <= INT64_MAX:
            encoded.int_value = value
        else:
            # Wider than int64. Exact text rather than a double that would lose digits.
            encoded.string_value = str(value)
    elif isinstance(value, float):
        encoded.double_value = value
    elif isinstance(value, str):
        # Before the sequence branch: a str is a Sequence.
        encoded.string_value = value
    elif isinstance(value, bytes | bytearray | memoryview):
        # Carried as bytes, not as a base64 string.
        encoded.bytes_value = bytes(value)
    elif isinstance(value, Decimal):
        # Arbitrary precision by definition: neither int64 nor double can be relied on to hold one,
        # so the exact text is the only encoding that does not quietly change the value. "f" is
        # Python's plain-string format - no exponent - matching BigDecimal.toPlainString.
        encoded.string_value = format(value, "f")
    elif isinstance(value, Mapping):
        encoded.struct_value.CopyFrom(to_struct(value))
    elif isinstance(value, Sequence | set | frozenset):
        encoded.list_value.CopyFrom(_to_list(value))
    else:
        # Anything else, as the Java codec's default arm does: something a caller wrote, or a type
        # neither side models. Its text is better than dropping the field.
        encoded.string_value = str(value)

    return encoded


def _to_list(values: Any) -> Any:
    encoded = value_pb2.CyrockList()
    for element in values:
        encoded.values.append(to_value(element))
    return encoded


def to_struct(mapping: Mapping[Any, Any] | None) -> Any:
    """Encodes a mapping as a ``CyrockStruct``. Keys are stringified, as on the Java side."""
    encoded = value_pb2.CyrockStruct()
    if mapping:
        for key, value in mapping.items():
            encoded.fields[str(key)].CopyFrom(to_value(value))
    return encoded


def from_value(value: Any) -> Any:
    """Decodes a ``CyrockValue``."""
    if value is None:
        return None

    kind = value.WhichOneof("kind")
    if kind is None or kind == "null_value":
        # `None` covers both the explicit null and a kind this build does not know, which is what a
        # newer peer sending a new kind looks like. Not an exception: one unreadable field should not
        # cost the caller the whole message.
        return None
    if kind == "string_value":
        return value.string_value
    if kind == "int_value":
        return value.int_value
    if kind == "double_value":
        return value.double_value
    if kind == "bool_value":
        return value.bool_value
    if kind == "bytes_value":
        return value.bytes_value
    if kind == "list_value":
        return [from_value(element) for element in value.list_value.values]
    if kind == "struct_value":
        return from_struct(value.struct_value)
    return None


def from_struct(struct: Any) -> dict[str, Any]:
    """Decodes a ``CyrockStruct`` into a plain dict."""
    if struct is None:
        return {}
    return {key: from_value(value) for key, value in struct.fields.items()}
