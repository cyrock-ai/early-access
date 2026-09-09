"""Enumerations mirroring ``ai.cyrock.db.data``.

Every member name matches the Java constant exactly, because several of these cross the wire as
strings: ``StatementClass`` and ``StatementType`` are parsed back from a string field by name, and
``SimilarityFunction``, ``FusionStrategy`` and ``Direction`` are sent as one. A rename here is a
wire-compatibility break, not a local tidy-up.
"""

from __future__ import annotations

from enum import Enum

__all__ = [
    "Cardinality",
    "Direction",
    "FusionStrategy",
    "MetadataFieldType",
    "SimilarityFunction",
    "StatementClass",
    "StatementType",
]


class StatementClass(Enum):
    """Routing classification of a CyQL statement.

    Read queries, data writes and resource-scoped DDL execute on the data server holding the
    resource's write lease; project-scoped DDL executes on the platform server, which owns the
    resource definitions.
    """

    READ_QUERY            = "READ_QUERY"
    DATA_WRITE            = "DATA_WRITE"
    GRAPH_SCOPED_DDL      = "GRAPH_SCOPED_DDL"
    COLLECTION_SCOPED_DDL = "COLLECTION_SCOPED_DDL"
    PROJECT_SCOPED_DDL    = "PROJECT_SCOPED_DDL"


class StatementType(Enum):
    """The specific CyQL statement, as the server reports it."""

    MATCH               = "MATCH"
    INSERT              = "INSERT"
    MERGE               = "MERGE"
    SET                 = "SET"
    DELETE              = "DELETE"
    REMOVE              = "REMOVE"
    LOAD_CSV            = "LOAD_CSV"
    ALTER_GRAPH         = "ALTER_GRAPH"
    ALTER_COLLECTION    = "ALTER_COLLECTION"
    SHOW_GRAPHS         = "SHOW_GRAPHS"
    DESCRIBE_GRAPH      = "DESCRIBE_GRAPH"
    CREATE_GRAPH        = "CREATE_GRAPH"
    DROP_GRAPH          = "DROP_GRAPH"
    CREATE_COLLECTION   = "CREATE_COLLECTION"
    DROP_COLLECTION     = "DROP_COLLECTION"
    SHOW_COLLECTIONS    = "SHOW_COLLECTIONS"
    DESCRIBE_COLLECTION = "DESCRIBE_COLLECTION"


class SimilarityFunction(Enum):
    """How vector distance is measured on a vector field."""

    EUCLIDEAN   = "EUCLIDEAN"
    DOT_PRODUCT = "DOT_PRODUCT"
    COSINE      = "COSINE"


class FusionStrategy(Enum):
    """How the result lists of a multi-vector or hybrid search are combined."""

    RRF            = "RRF"
    WEIGHTED_SCORE = "WEIGHTED_SCORE"


class Direction(Enum):
    """Edge direction for neighbour and traversal reads."""

    OUTGOING = "OUTGOING"
    INCOMING = "INCOMING"
    BOTH     = "BOTH"


class Cardinality(Enum):
    """The expected distinct-value count of an indexed metadata field."""

    HIGH = "HIGH"
    LOW  = "LOW"


class MetadataFieldType(Enum):
    """The declared type of a metadata field.

    The scalar members map to the Java types named in ``MetadataFieldType``; the ``*_LIST`` members
    are homogeneous lists of the corresponding scalar.
    """

    STRING   = "STRING"
    BYTE     = "BYTE"
    SHORT    = "SHORT"
    INTEGER  = "INTEGER"
    LONG     = "LONG"
    FLOAT    = "FLOAT"
    DOUBLE   = "DOUBLE"
    BOOLEAN  = "BOOLEAN"
    DATE     = "DATE"
    TIME     = "TIME"
    DATETIME = "DATETIME"
    INSTANT  = "INSTANT"
    BYTES    = "BYTES"

    STRING_LIST   = "STRING_LIST"
    BYTE_LIST     = "BYTE_LIST"
    SHORT_LIST    = "SHORT_LIST"
    INTEGER_LIST  = "INTEGER_LIST"
    LONG_LIST     = "LONG_LIST"
    FLOAT_LIST    = "FLOAT_LIST"
    DOUBLE_LIST   = "DOUBLE_LIST"
    BOOLEAN_LIST  = "BOOLEAN_LIST"
    DATE_LIST     = "DATE_LIST"
    TIME_LIST     = "TIME_LIST"
    DATETIME_LIST = "DATETIME_LIST"
    INSTANT_LIST  = "INSTANT_LIST"

    def is_list_type(self) -> bool:
        """Whether this is one of the homogeneous list types."""
        return self.name.endswith("_LIST")

    def element_type(self) -> MetadataFieldType:
        """The scalar type a list type holds.

        :raises ValueError: if this is not a list type
        """
        if not self.is_list_type():
            raise ValueError(f"{self.name} is not a list type")
        return MetadataFieldType[self.name.removesuffix("_LIST")]
