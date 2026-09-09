"""Value types a caller supplies: vectors and statement parameters.

The validation here is not decoration. Issue #352 was filed because a null or empty vector bound to
a statement parameter was marshalled as a zero-length vector field, reached a ``SIMILAR TO $v``
clause as a dimensionless vector, and produced a confusing result far from its cause with nothing
having said the parameter was never set. The Java client pushed the guards down into the value types
(#383); these are the same guards, at the same place, so the Python client cannot put that on the
wire either.

An explicitly empty vector is rejected alongside ``None``: it is not a meaningful vector for any
dimensioned field.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

__all__ = ["QueryParameters", "Text", "Vector", "VectorInput", "vector_input"]


@dataclass(frozen=True)
class Vector:
    """A pre-computed embedding."""

    values: tuple[float, ...]

    def __init__(self, values: Sequence[float]) -> None:
        if values is None or len(values) == 0:
            raise ValueError("vector values must not be None or empty")
        object.__setattr__(self, "values", tuple(float(value) for value in values))


@dataclass(frozen=True)
class Text:
    """Text to be embedded server-side. See the Inference reference."""

    text: str


VectorInput = Vector | Text
"""Either a pre-computed embedding or text for the server to embed."""


def vector_input(value: Sequence[float] | str) -> VectorInput:
    """Builds a :data:`VectorInput` from an embedding or from text.

    The counterpart of Java's overloaded ``VectorInput.of``. ``Vector`` and ``Text`` can also be
    constructed directly, which reads better when the kind is not in question.
    """
    return Text(value) if isinstance(value, str) else Vector(value)


@dataclass(frozen=True)
class QueryParameters:
    """Vector and scalar parameters bound to a CyQL statement.

    Build with :meth:`builder`, or construct directly from two mappings. Both are copied, so a later
    mutation of the caller's map cannot reintroduce a value past the guards.
    """

    vectors: Mapping[str, tuple[float, ...]] = field(default_factory=dict)
    scalars: Mapping[str, Any]               = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "vectors", dict(self.vectors))
        object.__setattr__(self, "scalars", dict(self.scalars))

    @staticmethod
    def builder() -> QueryParametersBuilder:
        return QueryParametersBuilder()

    def get_vector(self, name: str) -> tuple[float, ...]:
        """:raises KeyError: if no vector parameter of that name was bound."""
        if name not in self.vectors:
            raise KeyError(f"Vector parameter not found: ${name}")
        return self.vectors[name]

    def get_scalar(self, name: str) -> Any:
        """:raises KeyError: if no scalar parameter of that name was bound."""
        if name not in self.scalars:
            raise KeyError(f"Scalar parameter not found: ${name}")
        return self.scalars[name]


class QueryParametersBuilder:
    """Accumulates parameters, validating each at the point the caller binds it."""

    def __init__(self) -> None:
        self._vectors: dict[str, tuple[float, ...]] = {}
        self._scalars: dict[str, Any]               = {}

    def vector(self, name: str, values: Sequence[float]) -> QueryParametersBuilder:
        """Binds a vector parameter.

        :raises ValueError: if the name is blank, or the vector is ``None`` or empty. Both are
            rejected here rather than at build time so the failure names the parameter.
        """
        if not name or not name.strip():
            raise ValueError("vector parameter name must not be None or blank")
        if values is None or len(values) == 0:
            raise ValueError(f"vector parameter '{name}' must not be None or empty")
        self._vectors[name] = tuple(float(value) for value in values)
        return self

    def param(self, name: str, value: Any) -> QueryParametersBuilder:
        """Binds a scalar parameter.

        :raises ValueError: if the name is blank. The value is deliberately unconstrained - ``None``
            is a legitimate scalar, unlike an absent vector.
        """
        if not name or not name.strip():
            raise ValueError("scalar parameter name must not be None or blank")
        self._scalars[name] = value
        return self

    def build(self) -> QueryParameters:
        return QueryParameters(vectors=self._vectors, scalars=self._scalars)
