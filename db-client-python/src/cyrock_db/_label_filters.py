"""Builds the label expression a node listing filters on.

The Python counterpart of ``LabelFilters``. ``ListNodesRequest`` offers included labels with an
ALL/ANY match and a separate exclusion list; the wire carries a single boolean expression tree, so
the three have to be folded into one.

One asymmetry is worth stating because it is easy to read as a bug: **exclusions are always ANDed**,
even when the inclusion match is ANY. ``labels=[A, B], match=ANY, exclude=[C]`` means "A or B, and
not C" - not "A or B or not C", which would match almost everything. Java folds them the same way.

The oneof arms are named ``and``, ``or`` and ``not`` in the proto, and protobuf's Python codegen
keeps those names verbatim. All three are Python keywords, so the generated attributes exist but are
unreachable by ordinary attribute syntax - ``expression.and`` is a syntax error and ``expression.and_``
does not exist. ``getattr`` is the only way to reach them, and is not a workaround for anything.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from ._proto import cyrock_db_graph_pb2 as graph_pb2
from .types import LabelMatch

__all__ = ["to_label_expression"]


def _leaf(label: str) -> Any:
    return graph_pb2.LabelExpressionProto(label=label)


def _combine(left: Any, right: Any, disjunction: bool) -> Any:
    binary = graph_pb2.LabelBinaryProto(left=left, right=right)
    expression = graph_pb2.LabelExpressionProto()
    getattr(expression, "or" if disjunction else "and").CopyFrom(binary)
    return expression


def _checked(labels: Sequence[str] | None) -> list[str]:
    values = list(labels or ())
    if any(label is None for label in values):
        raise ValueError("label filters must not contain None")
    return values


def to_label_expression(
    labels:         Sequence[str] | None,
    match:          LabelMatch,
    exclude_labels: Sequence[str] | None,
) -> Any | None:
    """Folds the three filter inputs into one expression, or ``None`` for no label constraint."""
    included = _checked(labels)
    excluded = _checked(exclude_labels)
    if not included and not excluded:
        return None

    expression: Any | None = None
    for label in included:
        leaf = _leaf(label)
        expression = leaf if expression is None else _combine(expression, leaf, match is LabelMatch.ANY)
    for label in excluded:
        negated = graph_pb2.LabelExpressionProto()
        getattr(negated, "not").CopyFrom(_leaf(label))
        # Always a conjunction, whatever the inclusion match. See the module docstring.
        expression = negated if expression is None else _combine(expression, negated, False)
    return expression
