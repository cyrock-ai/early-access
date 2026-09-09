"""Collection and graph schema definitions.

Mirrors ``VectorFieldDefinition``, ``MetadataFieldDefinition``, ``CollectionDefinition`` and
``GraphDefinition``. The defaulting in :class:`VectorFieldDefinition` is not cosmetic: the Java
constructor resolves the field name first because it names the field in every validation message,
and because an unset name would otherwise reach the server's index-path resolution as a null. Zero
is treated as "unset" for the tuning parameters, matching Java's ``orDefault`` - a proto3 scalar
carries 0 when the sender left it out, so a definition that came off the wire and one built by hand
default alike.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import Any

from ._enums import Cardinality, MetadataFieldType, SimilarityFunction

__all__ = [
    "AUTO_ASSIGN_ID",
    "CollectionDefinition",
    "Document",
    "GraphDefinition",
    "MetadataFieldDefinition",
    "UpsertResult",
    "VectorFieldDefinition",
]

DEFAULT_FIELD_NAME         = "vector"
DEFAULT_SIMILARITY_FUNCTION = SimilarityFunction.COSINE
DEFAULT_MAX_DEGREE         = 32
DEFAULT_BEAM_WIDTH         = 200
DEFAULT_NEIGHBOR_OVERFLOW  = 1.2
DEFAULT_ALPHA              = 1.0


def _describe(parameter: str, requirement: str, value: Any, field_name: str) -> str:
    return f"{parameter} must be {requirement} for vector field '{field_name}', but was {value}"


def _or_default(value: float | None, default: float, parameter: str, field_name: str) -> float:
    """Java's ``orDefault``: None and 0 both mean "unset"; a negative is an error."""
    if value is None or value == 0:
        return default
    if value < 0:
        raise ValueError(_describe(parameter, "positive", value, field_name))
    return value


@dataclass(frozen=True)
class VectorFieldDefinition:
    """One vector field: its dimension, metric, and HNSW tuning."""

    name:                str               = DEFAULT_FIELD_NAME
    dimension:           int               = 0
    similarity_function: SimilarityFunction = DEFAULT_SIMILARITY_FUNCTION
    max_degree:          int               = DEFAULT_MAX_DEGREE
    beam_width:          int               = DEFAULT_BEAM_WIDTH
    neighbor_overflow:   float             = DEFAULT_NEIGHBOR_OVERFLOW
    alpha:               float             = DEFAULT_ALPHA
    embedding_model:     str | None        = None
    eventual_indexing:   bool              = False

    def __post_init__(self) -> None:
        # Resolved first: it names the field in every message below.
        name = self.name if self.name and self.name.strip() else DEFAULT_FIELD_NAME
        object.__setattr__(self, "name", name)

        if self.dimension is None or self.dimension <= 0:
            raise ValueError(_describe("dimension", "positive", self.dimension, name))

        object.__setattr__(self, "similarity_function", self.similarity_function or DEFAULT_SIMILARITY_FUNCTION)
        object.__setattr__(
            self, "max_degree", int(_or_default(self.max_degree, DEFAULT_MAX_DEGREE, "max_degree", name))
        )
        object.__setattr__(
            self, "beam_width", int(_or_default(self.beam_width, DEFAULT_BEAM_WIDTH, "beam_width", name))
        )
        object.__setattr__(
            self,
            "neighbor_overflow",
            _or_default(self.neighbor_overflow, DEFAULT_NEIGHBOR_OVERFLOW, "neighbor_overflow", name),
        )
        object.__setattr__(self, "alpha", _or_default(self.alpha, DEFAULT_ALPHA, "alpha", name))
        object.__setattr__(self, "eventual_indexing", bool(self.eventual_indexing))


@dataclass(frozen=True)
class MetadataFieldDefinition:
    """One metadata field: its type, index cardinality, and whether it is full-text or unique.

    ``cardinality`` is **required**, and that is a small, deliberate divergence. Java declares it
    nullable and then encodes it with ``cardinality().name()``, which throws on null - so it is
    required there too, just later and less clearly. Sending an absent one as the empty string is
    what a proto3 string does by default, and the server answers
    ``No enum constant ai.cyrock.db.data.Cardinality.`` - a message that says nothing about which
    field or why.

    There is no sensible default to pick on the caller's behalf: cardinality chooses the index, HIGH
    giving a binary index for range and equality lookups and LOW a bitmap. Guessing would quietly
    decide the performance characteristics of somebody's field.
    """

    name:        str
    type:        MetadataFieldType
    cardinality: Cardinality
    fulltext:    bool = False
    unique:      bool = False

    def __post_init__(self) -> None:
        if self.cardinality is None:
            raise ValueError(
                f"cardinality is required for metadata field '{self.name}': HIGH indexes for range "
                f"and equality lookups, LOW uses a bitmap"
            )
        object.__setattr__(self, "fulltext", bool(self.fulltext))
        object.__setattr__(self, "unique",   bool(self.unique))


@dataclass(frozen=True)
class CollectionDefinition:
    """A collection's schema: its vector fields and its metadata fields."""

    id:              str | None                          = None
    name:            str | None                          = None
    vector_fields:   tuple[VectorFieldDefinition, ...]   = ()
    metadata_fields: tuple[MetadataFieldDefinition, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "vector_fields",   tuple(self.vector_fields or ()))
        object.__setattr__(self, "metadata_fields", tuple(self.metadata_fields or ()))

    def default_vector_field(self) -> VectorFieldDefinition | None:
        """The field named ``vector``, or the only field if there is exactly one. Otherwise None."""
        if not self.vector_fields:
            return None
        for candidate in self.vector_fields:
            if candidate.name == DEFAULT_FIELD_NAME:
                return candidate
        return self.vector_fields[0] if len(self.vector_fields) == 1 else None

    def fulltext_fields(self) -> tuple[MetadataFieldDefinition, ...]:
        return tuple(candidate for candidate in self.metadata_fields if candidate.fulltext)

    def evolve(self, **changes: Any) -> CollectionDefinition:
        """A copy with the named fields changed.

        The counterpart of Java's ``Builder.from(definition)``, which exists so that rebuilding a
        definition to change one field cannot silently drop a field added to the type later. A
        dataclass gets that for free; this names it so the two SDKs read alike.
        """
        return replace(self, **changes)


@dataclass(frozen=True)
class GraphDefinition:
    """A graph's schema, plus its branch lineage when it is a fork."""

    id:                       str | None                          = None
    name:                     str | None                          = None
    node_vector_fields:       tuple[VectorFieldDefinition, ...]   = ()
    node_metadata_fields:     tuple[MetadataFieldDefinition, ...] = ()
    edge_metadata_fields:     tuple[MetadataFieldDefinition, ...] = ()
    enable_temporal_tracking: bool                                = False
    auto_link_threshold:      float                               = 0.0
    parent_graph_id:          str | None                          = None
    forked_at:                int                                 = 0
    branch_name:              str | None                          = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "node_vector_fields",   tuple(self.node_vector_fields or ()))
        object.__setattr__(self, "node_metadata_fields", tuple(self.node_metadata_fields or ()))
        object.__setattr__(self, "edge_metadata_fields", tuple(self.edge_metadata_fields or ()))

    def is_branch(self) -> bool:
        return bool(self.parent_graph_id)

    def evolve(self, **changes: Any) -> GraphDefinition:
        """A copy with the named fields changed. See :meth:`CollectionDefinition.evolve`."""
        return replace(self, **changes)



AUTO_ASSIGN_ID = -1
"""Passed as a document or node id to ask the store to assign one."""


@dataclass(frozen=True)
class Document:
    """A document: its id, optional application key, vectors and metadata.

    ``id`` is :data:`AUTO_ASSIGN_ID` to let the store choose one. Note that ``0`` is a real id -
    GigaMap numbers from zero, so document 0 is the first document of every store - which is why the
    sentinel is -1 and not 0, and why the request protos mark the id ``optional`` rather than reading
    an absent value as zero.
    """

    id:           int                              = AUTO_ASSIGN_ID
    vectors:      Mapping[str, tuple[float, ...]]  = field(default_factory=dict)
    metadata:     Mapping[str, Any]                = field(default_factory=dict)
    external_key: str | None                       = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "vectors", {
            name: tuple(float(each) for each in values) for name, values in (self.vectors or {}).items()
        })
        object.__setattr__(self, "metadata", dict(self.metadata or {}))

    @staticmethod
    def with_vector(
        vector:   Sequence[float],
        metadata: Mapping[str, Any] | None = None,
        id:       int = AUTO_ASSIGN_ID,  # noqa: A002 - mirrors the Java parameter name
    ) -> Document:
        """A document with a single vector on the default field, the common case.

        The counterpart of Java's ``Document(long, float[], Map)`` convenience constructor.
        """
        return Document(id=id, vectors={DEFAULT_FIELD_NAME: tuple(vector)}, metadata=metadata or {})


@dataclass(frozen=True)
class UpsertResult:
    """The outcome of an upsert addressed by external key: the id, and whether it was created.

    ``created`` is ``False`` when an existing document was updated, which is what makes re-ingest by
    a stable key idempotent and observably so.

    Java declares this as a record nested inside ``CyrockDbClient``. Python has no equivalent idiom
    and both facades need it, so it lives here with the other domain records - a difference of
    location, not of surface.
    """

    id:      int
    created: bool
