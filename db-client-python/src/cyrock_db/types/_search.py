"""Search requests and their results.

Mirrors ``SearchRequest``, ``MultiVectorSearchRequest``, ``HybridSearchRequest``, ``RerankOptions``
and ``Match``.

**On precision.** Vectors and fusion weights are 32-bit floats on the wire, while a Python
``float`` is a double. A weight of ``0.7`` therefore reaches the server as ``0.699999988``, and a
vector read back is the float32 rounding of what was sent. This is the wire format rather than a
client choice - the Java client narrows identically, its ``float[]`` being 32-bit already - but it is
worth knowing before comparing a returned vector against the one you sent.

**On ``max_results``.** The proto marks it ``optional`` so that an omitted value can select the
server default while an explicit ``<= 0`` returns nothing (issue #438). These request types make it
required and always send it, which is what the Java client does - its ``maxResults`` is a primitive
``int`` with no unset state. Asking for the server default is therefore not expressible from either
SDK; that is parity, not an oversight, and changing it is a change to both.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ._definitions import Document
from ._enums import FusionStrategy

__all__ = [
    "HybridSearchRequest",
    "Match",
    "MultiVectorSearchRequest",
    "RerankOptions",
    "SearchRequest",
    "TextQuery",
    "VectorQuery",
]

DEFAULT_CANDIDATE_MULTIPLIER = 4
MIN_DEFAULT_CANDIDATES       = 50
MAX_DEFAULT_CANDIDATES       = 200


@dataclass(frozen=True)
class RerankOptions:
    """Second-pass re-ranking over the candidate pool a search returns."""

    enabled:    bool       = False
    model:      str | None = None
    field:      str | None = None
    candidates: int        = 0
    query:      str | None = None

    @staticmethod
    def disabled() -> RerankOptions:
        return RerankOptions()

    def candidate_pool(self, top_n: int) -> int:
        """The pool to fetch before re-ranking: the explicit count, or one derived from ``top_n``."""
        if self.candidates > 0:
            return self.candidates
        derived = max(top_n * DEFAULT_CANDIDATE_MULTIPLIER, MIN_DEFAULT_CANDIDATES)
        return min(derived, MAX_DEFAULT_CANDIDATES)


@dataclass(frozen=True)
class VectorQuery:
    """One vector leg of a multi-vector or hybrid search, with its fusion weight."""

    field_name: str
    vector:     tuple[float, ...]
    weight:     float = 1.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "vector", tuple(float(each) for each in self.vector))


@dataclass(frozen=True)
class TextQuery:
    """One full-text leg of a hybrid search, with its fusion weight."""

    text_field_name: str
    query:           str
    weight:          float = 1.0


@dataclass(frozen=True)
class SearchRequest:
    """Vector similarity search over one field."""

    vector_field: str
    vector:       tuple[float, ...]
    max_results:  int
    filter:       str | None    = None
    rerank:       RerankOptions = field(default_factory=RerankOptions.disabled)

    def __post_init__(self) -> None:
        object.__setattr__(self, "vector", tuple(float(each) for each in self.vector))


@dataclass(frozen=True)
class MultiVectorSearchRequest:
    """Search several vector fields at once, fusing the result lists."""

    queries:     tuple[VectorQuery, ...]
    max_results: int
    fusion:      FusionStrategy = FusionStrategy.RRF
    filter:      str | None     = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "queries", tuple(self.queries))


@dataclass(frozen=True)
class HybridSearchRequest:
    """Search vector fields and full-text fields together, fusing the result lists."""

    vector_queries: tuple[VectorQuery, ...] = ()
    text_queries:   tuple[TextQuery, ...]   = ()
    max_results:    int                     = 10
    fusion:         FusionStrategy          = FusionStrategy.RRF
    filter:         str | None              = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "vector_queries", tuple(self.vector_queries))
        object.__setattr__(self, "text_queries",   tuple(self.text_queries))


@dataclass(frozen=True)
class Match:
    """One search hit: the document, and the score it matched with."""

    score:    float
    document: Document
