"""Change Data Capture: the events a stream delivers, and how to ask for them.

**A domain type where Java hands over the protobuf.** ``ChangeListener.onChange`` in the Java client
takes ``ai.cyrock.db.proto.cdc.ChangeEvent`` - the generated message itself. This client decodes into
:class:`ChangeEvent` below instead, for two reasons: every other response in this SDK arrives as a
frozen dataclass, and ``cyrock_db._proto`` is private precisely so generated names never become the
public API. Handing a caller a protobuf here would make ``_proto`` load-bearing for one method out of
seventy. The fields carry the same names and meanings.

**Delivery is at-least-once**, with a resumable ``(resource_id, lsn)`` cursor. A consumer that
checkpoints the last LSN it processed and de-duplicates on it can resume exactly where it left off;
one that does not may see an event twice after a reconnect.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

__all__ = [
    "ChangeEvent",
    "ChangeFilter",
    "ChangeOp",
    "ChangeSource",
    "EdgeInfo",
    "EntityKind",
    "SchemaChange",
    "WatchOptions",
    "WatchStart",
]


class ChangeOp(Enum):
    """What happened to the entity."""

    UNSPECIFIED = "CHANGE_OP_UNSPECIFIED"
    CREATE      = "CREATE"
    UPDATE      = "UPDATE"
    UPSERT      = "UPSERT"
    DELETE      = "DELETE"
    SCHEMA      = "SCHEMA"
    SNAPSHOT    = "SNAPSHOT"

    DISCONTINUITY = "DISCONTINUITY"
    """Not a change: **changes are missing**.

    Everything between the consumer's cursor and this event's LSN was committed by the store but
    never reached the change log - records are appended after the commit, so a crash between the two
    loses the record. A consumer that receives this has a hole and must re-snapshot; reading on would
    leave it silently wrong. Never suppressed by a filter, because the filter cannot know the
    consumer needs it.
    """


class EntityKind(Enum):
    """What kind of entity the change is about."""

    UNSPECIFIED   = "ENTITY_KIND_UNSPECIFIED"
    NODE          = "NODE"
    EDGE          = "EDGE"
    DOCUMENT      = "DOCUMENT"
    SCHEMA_ENTITY = "SCHEMA_ENTITY"


class WatchStart(Enum):
    """Where a stream begins."""

    FROM_NOW      = "FROM_NOW"
    """Only changes committed after the stream opens."""

    WITH_SNAPSHOT = "WITH_SNAPSHOT"
    """A consistent snapshot of current state, then the live tail."""

    FROM_LSN      = "FROM_LSN"
    """Resume: only changes with an LSN strictly greater than the given one."""


@dataclass(frozen=True)
class ChangeSource:
    """Where the change came from, and its position in the log."""

    resource_kind: str = ""
    resource_id:   str = ""
    lsn:           int = 0
    tx_id:         int = 0
    ts_ms:         int = 0


@dataclass(frozen=True)
class EdgeInfo:
    """The endpoints of a changed edge."""

    source_id: int   = 0
    target_id: int   = 0
    type:      str   = ""
    weight:    float = 0.0


@dataclass(frozen=True)
class SchemaChange:
    """Fields added or dropped by a schema change."""

    added_fields:   tuple[str, ...] = ()
    dropped_fields: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "added_fields", tuple(self.added_fields))
        object.__setattr__(self, "dropped_fields", tuple(self.dropped_fields))


@dataclass(frozen=True)
class ChangeEvent:
    """One change, or a marker.

    ``snapshot_complete`` marks the single event emitted after the initial snapshot and before the
    live tail; when it is set, every field except :attr:`source` is unset.
    """

    source:            ChangeSource                    = field(default_factory=ChangeSource)
    op:                ChangeOp                        = ChangeOp.UNSPECIFIED
    entity_kind:       EntityKind                      = EntityKind.UNSPECIFIED
    entity_id:         int                             = 0
    external_key:      str | None                      = None
    labels:            tuple[str, ...]                 = ()
    metadata:          Mapping[str, Any]               = field(default_factory=dict)
    vectors:           Mapping[str, tuple[float, ...]] = field(default_factory=dict)
    edge:              EdgeInfo | None                 = None
    schema:            SchemaChange | None             = None
    snapshot_complete: bool                            = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "labels", tuple(self.labels))
        object.__setattr__(self, "metadata", dict(self.metadata))
        object.__setattr__(self, "vectors", {
            name: tuple(values) for name, values in (self.vectors or {}).items()
        })

    @property
    def lsn(self) -> int:
        """The event's position in the log - the value to checkpoint for a resumable cursor."""
        return self.source.lsn


@dataclass(frozen=True)
class ChangeFilter:
    """Server-side filtering. Everything unset means no constraint.

    ``DISCONTINUITY`` is never filtered out, whatever ``ops`` says: a consumer that has lost changes
    needs to be told regardless of what it asked for.
    """

    ops:                Sequence[ChangeOp]   = ()
    entity_kinds:       Sequence[EntityKind] = ()
    labels:             Sequence[str]        = ()
    metadata_predicate: str | None           = None
    """A CyQL filter expression evaluated against the change's after-image metadata."""


@dataclass(frozen=True)
class WatchOptions:
    """Where a stream starts, and what it carries.

    Java builds these fluently (``WatchOptions.create().withSnapshot().includeVectors(true)``) and
    takes the filter's ops and entity kinds as strings, validating them up front. Here they are
    enums, so an invalid value cannot be constructed in the first place.
    """

    start:           WatchStart   = WatchStart.FROM_NOW
    from_lsn:        int          = 0
    include_vectors: bool         = False
    filter:          ChangeFilter = field(default_factory=ChangeFilter)

    def __post_init__(self) -> None:
        if self.start is WatchStart.FROM_LSN and self.from_lsn < 0:
            raise ValueError(f"from_lsn must not be negative, was {self.from_lsn}")

    @staticmethod
    def from_now() -> WatchOptions:
        return WatchOptions(start=WatchStart.FROM_NOW)

    @staticmethod
    def with_snapshot() -> WatchOptions:
        return WatchOptions(start=WatchStart.WITH_SNAPSHOT)

    @staticmethod
    def resume_from(lsn: int) -> WatchOptions:
        """Resume after a known LSN. The usual way to restart a checkpointed consumer."""
        return WatchOptions(start=WatchStart.FROM_LSN, from_lsn=lsn)
