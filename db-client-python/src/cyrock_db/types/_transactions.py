"""Transaction operations and their results.

Both transaction surfaces are atomic: every operation commits or none does, applied through an undo
log and one atomic commit. The per-operation results exist so that a partial outcome can be
*reported* precisely even though the transaction as a whole never partially applies - an operation's
``error`` says why the transaction was rolled back, not that this one operation failed alone.

Java models the operations as sealed interfaces with nested records
(``CyrockDbClient.GraphOperation``, ``CyrockDbClient.CollectionOperation``). Python has no sealed
types; these are frozen dataclasses in a shared union, which gives the same closed set for type
checking and reads the same at a call site.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from ._values import VectorInput

__all__ = [
    "AddEdgeOp",
    "AddNodeOp",
    "CollectionOperation",
    "GraphOperation",
    "OperationResult",
    "RemoveDocumentOp",
    "RemoveEdgeOp",
    "RemoveNodeOp",
    "TransactionResult",
    "UpdateEdgeMetadataOp",
    "UpdateNodeMetadataOp",
    "UpdateVectorOp",
    "UpdateWeightOp",
    "UpsertDocumentOp",
    "UpsertKeyOp",
    "UpsertNodeOp",
]

Vectors = Mapping[str, VectorInput | Sequence[float]]


# ─── Collection operations ──────────────────────────────────────────────────


@dataclass(frozen=True)
class UpsertDocumentOp:
    """Insert or replace a document by id. A negative id asks the store to assign one."""

    id:       int
    vectors:  Vectors           = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class UpsertKeyOp:
    """Insert or replace a document by the caller's stable key."""

    external_key: str
    vectors:      Vectors           = field(default_factory=dict)
    metadata:     Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RemoveDocumentOp:
    """Remove a document by id."""

    document_id: int


CollectionOperation = UpsertDocumentOp | UpsertKeyOp | RemoveDocumentOp


# ─── Graph operations ───────────────────────────────────────────────────────


@dataclass(frozen=True)
class AddNodeOp:
    """Add a labelled node."""

    labels:   Sequence[str]     = ()
    vectors:  Vectors           = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AddEdgeOp:
    """Add a weighted, typed edge."""

    source_id: int
    target_id: int
    type:      str
    weight:    float             = 1.0
    metadata:  Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RemoveNodeOp:
    """Remove a node, by id or by external key.

    Java offers ``RemoveNode.byId`` and ``RemoveNode.byKey`` factories over one record with two
    nullable fields; the same shape holds here, and exactly one of the two should be set.
    """

    node_id:      int | None = None
    external_key: str | None = None

    def __post_init__(self) -> None:
        if (self.node_id is None) == (self.external_key is None):
            raise ValueError("RemoveNodeOp takes exactly one of node_id or external_key")

    @staticmethod
    def by_id(node_id: int) -> RemoveNodeOp:
        return RemoveNodeOp(node_id=node_id)

    @staticmethod
    def by_key(external_key: str) -> RemoveNodeOp:
        return RemoveNodeOp(external_key=external_key)


@dataclass(frozen=True)
class RemoveEdgeOp:
    """Remove an edge by id."""

    edge_id: int


@dataclass(frozen=True)
class UpdateVectorOp:
    """Replace one of a node's vectors."""

    node_id:    int
    field_name: str
    vector:     Sequence[float]


@dataclass(frozen=True)
class UpdateWeightOp:
    """Replace an edge's weight."""

    edge_id: int
    weight:  float


@dataclass(frozen=True)
class UpdateNodeMetadataOp:
    """Replace a node's metadata."""

    node_id:  int
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class UpdateEdgeMetadataOp:
    """Replace an edge's metadata."""

    edge_id:  int
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class UpsertNodeOp:
    """Insert or replace a node, addressed by id, by external key, or neither.

    With neither set the store assigns an id, which is what Java's ``UpsertNode.create`` spells.
    """

    node_id:      int | None        = None
    external_key: str | None        = None
    labels:       Sequence[str]     = ()
    vectors:      Vectors           = field(default_factory=dict)
    metadata:     Mapping[str, Any] = field(default_factory=dict)

    @staticmethod
    def by_id(node_id: int, labels: Sequence[str] = (), vectors: Vectors | None = None,
              metadata: Mapping[str, Any] | None = None) -> UpsertNodeOp:
        return UpsertNodeOp(node_id=node_id, labels=labels, vectors=vectors or {}, metadata=metadata or {})

    @staticmethod
    def by_key(external_key: str, labels: Sequence[str] = (), vectors: Vectors | None = None,
               metadata: Mapping[str, Any] | None = None) -> UpsertNodeOp:
        return UpsertNodeOp(external_key=external_key, labels=labels, vectors=vectors or {},
                            metadata=metadata or {})

    @staticmethod
    def create(labels: Sequence[str] = (), vectors: Vectors | None = None,
               metadata: Mapping[str, Any] | None = None) -> UpsertNodeOp:
        return UpsertNodeOp(labels=labels, vectors=vectors or {}, metadata=metadata or {})


GraphOperation = (
    AddNodeOp | AddEdgeOp | RemoveNodeOp | RemoveEdgeOp
    | UpdateVectorOp | UpdateWeightOp | UpdateNodeMetadataOp | UpdateEdgeMetadataOp | UpsertNodeOp
)


# ─── Results ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class OperationResult:
    """One operation's outcome: its position, any id it generated, and any error."""

    index:        int
    generated_id: int        = 0
    error:        str | None = None

    @property
    def success(self) -> bool:
        return self.error is None


@dataclass(frozen=True)
class TransactionResult:
    """Per-operation results, in the order the operations were submitted."""

    results: tuple[OperationResult, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "results", tuple(self.results))

    @property
    def success(self) -> bool:
        """Whether every operation reported success, and so whether the transaction committed."""
        return all(each.success for each in self.results)
