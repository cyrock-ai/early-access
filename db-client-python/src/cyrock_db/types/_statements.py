"""Results of an executed CyQL statement.

Three domain-tailored response messages share one row encoding on the wire - a collection has
documents, a graph has nodes and edges, a project statement is DDL - and they decode into the one
:class:`StatementResult` here, as they do in Java.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ._definitions import GraphDefinition
from ._enums import StatementClass, StatementType

__all__ = ["QueryResult", "StatementResult", "WriteSummary"]


@dataclass(frozen=True)
class WriteSummary:
    """What a write statement changed, and the ids it generated."""

    nodes_created:    int                = 0
    nodes_deleted:    int                = 0
    edges_created:    int                = 0
    edges_deleted:    int                = 0
    properties_set:   int                = 0
    created_node_ids: tuple[int, ...]    = ()
    created_edge_ids: tuple[int, ...]    = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "created_node_ids", tuple(self.created_node_ids))
        object.__setattr__(self, "created_edge_ids", tuple(self.created_edge_ids))


@dataclass(frozen=True)
class QueryResult:
    """The rows a read query returned, and the columns it bound."""

    columns: tuple[str, ...]                     = ()
    rows:    tuple[Mapping[str, Any], ...]       = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "columns", tuple(self.columns))
        object.__setattr__(self, "rows", tuple(dict(row) for row in self.rows))


@dataclass(frozen=True)
class StatementResult:
    """An executed statement's outcome.

    Reads carry ``columns`` and ``rows``; writes carry a ``summary``; schema statements echo the
    ``definition`` they evolved.
    """

    statement_class: StatementClass
    statement_type:  StatementType
    columns:         tuple[str, ...]                = ()
    rows:            tuple[Mapping[str, Any], ...]  = ()
    summary:         WriteSummary | None            = None
    definition:      GraphDefinition | None         = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "columns", tuple(self.columns))
        object.__setattr__(self, "rows", tuple(dict(row) for row in self.rows))

    def to_query_result(self) -> QueryResult:
        """The read-only view of this result, as ``query`` returns."""
        return QueryResult(columns=self.columns, rows=self.rows)
