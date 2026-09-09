"""The community layer: detection, summaries, and theme-centric global search.

Mirrors the ``Community*`` records, ``DetectCommunitiesRequest``, ``GlobalSearch*``,
``RefreshCommunitiesResult`` and the memory and natural-language types. This is the GraphRAG surface:
communities are detected over the graph, summarised, and then searched by theme rather than by
similarity to one node.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from ._search import RerankOptions

__all__ = [
    "CommunityAssignments",
    "CommunityHierarchy",
    "CommunityMemberSet",
    "CommunityRef",
    "CommunityResult",
    "CommunityStatus",
    "CommunitySummaries",
    "CommunitySummary",
    "DecayResult",
    "DetectCommunitiesRequest",
    "EntityLinkRequest",
    "GetCommunityMembersRequest",
    "GetCommunitySummariesRequest",
    "GlobalSearchRequest",
    "GlobalSearchResult",
    "NlMatch",
    "NlSearchRequest",
    "NlSearchResult",
    "ObserveRequest",
    "ObserveResult",
    "PutCommunitySummaryRequest",
    "RefreshCommunitiesResult",
]


@dataclass(frozen=True)
class CommunityRef:
    """A community, addressed by the level it lives on and its id within that level."""

    level:        int
    community_id: int


@dataclass(frozen=True)
class CommunityResult:
    """One detected community: where it sits in the hierarchy, and optionally who is in it.

    ``member_node_ids`` is empty when the read asked to leave members out (issue #320) - which is the
    default on :meth:`~cyrock_db.client.CyrockDbClient.get_communities` - so empty means "not asked
    for" as often as it means "none".
    """

    id:              int
    level:           int
    parent_id:       int             = 0
    size:            int             = 0
    member_node_ids: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "member_node_ids", tuple(self.member_node_ids))


@dataclass(frozen=True)
class CommunityHierarchy:
    """Every detected community, the levels they span, and which are stale."""

    communities:       tuple[CommunityResult, ...] = ()
    levels:            int                         = 0
    algorithm:         str                         = ""
    detected_at:       int                         = 0
    stale_communities: tuple[CommunityRef, ...]    = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "communities", tuple(self.communities))
        object.__setattr__(self, "stale_communities", tuple(self.stale_communities))


@dataclass(frozen=True)
class CommunityStatus:
    """Whether communities have been detected, when, and how stale they are."""

    detected:        bool = False
    detected_at:     int  = 0
    stale:           bool = False
    levels:          int  = 0
    community_count: int  = 0
    summary_count:   int  = 0


@dataclass(frozen=True)
class CommunitySummary:
    """A stored summary for one community."""

    level:        int
    community_id: int
    summary_text: str


@dataclass(frozen=True)
class CommunitySummaries:
    """Stored summaries, and whether the read was cut short by its limit."""

    summaries: tuple[CommunitySummary, ...] = ()
    truncated: bool                         = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "summaries", tuple(self.summaries))


@dataclass(frozen=True)
class CommunityMemberSet:
    """The members of one community, and whether the read was cut short by its limit."""

    level:           int
    community_id:    int
    member_node_ids: tuple[int, ...] = ()
    truncated:       bool            = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "member_node_ids", tuple(self.member_node_ids))


@dataclass(frozen=True)
class CommunityAssignments:
    """Which community each queried node belongs to, at one level."""

    by_node: Mapping[int, int] = field(default_factory=dict)
    levels:  int               = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "by_node", dict(self.by_node))


@dataclass(frozen=True)
class GetCommunitySummariesRequest:
    """Which summaries to read: a level, optionally specific communities, and a cap."""

    level:         int
    community_ids: Sequence[int] = ()
    limit:         int           = 0


@dataclass(frozen=True)
class GetCommunityMembersRequest:
    """Which communities' members to read, and how many to return per community."""

    level:         int
    community_ids: Sequence[int] = ()
    limit:         int           = 0


@dataclass(frozen=True)
class DetectCommunitiesRequest:
    """How to run community detection.

    Also the request type for :meth:`~cyrock_db.client.CyrockDbClient.refresh_communities`, which
    re-detects and prunes summaries orphaned by the new hierarchy.
    """

    algorithm:         str           = ""
    resolution:        float         = 0.0
    edge_weight_field: str | None    = None
    edge_types:        Sequence[str] = ()
    max_levels:        int           = 0
    seed:              int           = 0


@dataclass(frozen=True)
class PutCommunitySummaryRequest:
    """A summary to store for one community, with optional precomputed vectors.

    ``vectors`` values are rejected when empty, and keys when blank - the same guard
    :class:`~cyrock_db.types.QueryParameters` carries, and for the same reason (issue #383).
    """

    level:        int
    community_id: int
    summary_text: str
    vectors:      Mapping[str, tuple[float, ...]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        checked: dict[str, tuple[float, ...]] = {}
        for name, values in (self.vectors or {}).items():
            if not name or not str(name).strip():
                raise ValueError("community summary vector field name must not be None or blank")
            if values is None or len(values) == 0:
                raise ValueError(f"community summary vector '{name}' must not be None or empty")
            checked[name] = tuple(float(each) for each in values)
        object.__setattr__(self, "vectors", checked)


@dataclass(frozen=True)
class GlobalSearchRequest:
    """Theme-centric search over community summaries at one level."""

    query:                     str
    query_vector:              tuple[float, ...] = ()
    level:                     int               = 0
    top_k:                     int               = 10
    vector_field:              str | None        = None
    include_members:           bool              = False
    max_members_per_community: int               = 0
    expand:                    bool              = False
    expand_depth:              int               = 0
    rerank:                    RerankOptions     = field(default_factory=RerankOptions.disabled)

    def __post_init__(self) -> None:
        object.__setattr__(self, "query_vector", tuple(float(each) for each in self.query_vector))


@dataclass(frozen=True)
class GlobalSearchResult:
    """One ranked community report."""

    community_id:        int
    level:               int             = 0
    score:               float           = 0.0
    summary_text:        str             = ""
    parent_community_id: int             = 0
    member_node_ids:     tuple[int, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "member_node_ids", tuple(self.member_node_ids))


@dataclass(frozen=True)
class RefreshCommunitiesResult:
    """The re-detected hierarchy, and how many orphaned summaries were pruned."""

    hierarchy:         CommunityHierarchy       = field(default_factory=CommunityHierarchy)
    pruned_summaries:  int                      = 0
    stale_communities: tuple[CommunityRef, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "stale_communities", tuple(self.stale_communities))


# ─── Agentic memory ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ObserveRequest:
    """An observation to store, with automatic linking to similar existing memories."""

    labels:    Sequence[str]                       = ()
    vectors:   Mapping[str, Any]                   = field(default_factory=dict)
    link_field: str | None                         = None
    threshold: float                               = 0.0
    max_links: int                                 = 0
    metadata:  Mapping[str, Any]                   = field(default_factory=dict)


@dataclass(frozen=True)
class ObserveResult:
    """The stored node, and the edges auto-linking created."""

    node_id:         int
    linked_edge_ids: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "linked_edge_ids", tuple(self.linked_edge_ids))


@dataclass(frozen=True)
class EntityLinkRequest:
    """Link one node to its nearest neighbours above a similarity threshold."""

    field_name: str
    node_id:    int
    threshold:  float
    max_links:  int


@dataclass(frozen=True)
class DecayResult:
    """What pruning stale memories removed."""

    pruned_nodes: int = 0
    pruned_edges: int = 0


# ─── Natural-language search ────────────────────────────────────────────────


@dataclass(frozen=True)
class NlSearchRequest:
    """A plain-language query, embedded server-side."""

    query:        str
    vector_field: str
    max_results:  int
    rerank:       RerankOptions = field(default_factory=RerankOptions.disabled)


@dataclass(frozen=True)
class NlMatch:
    """One natural-language search hit."""

    id:       int
    score:    float
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", dict(self.metadata))


@dataclass(frozen=True)
class NlSearchResult:
    """The hits, plus what the query was translated into and how it was classified."""

    matches:          tuple[NlMatch, ...] = ()
    translated_query: str                 = ""
    query_type:       str                 = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "matches", tuple(self.matches))
