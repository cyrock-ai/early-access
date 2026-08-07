# Release notes

## 0.9.0 - Early Access

The first release available outside CYROCK.AI. It ships as a single container image holding the whole
engine, reachable from the web console, REST, the Java SDK and MCP.

### What is in it

**Retrieval**

- Vector search over HNSW indices, with cosine, dot-product and euclidean similarity.
- Hybrid retrieval fusing BM25 full-text scoring with vector similarity.
- Typed, indexed metadata filters applied before ranking, so a narrow filter still returns a full
  result set.
- Multiple vector fields per record, searchable independently - the basis for multi-modal search.
- Optional cross-encoder reranking through Cohere.

**Knowledge graphs**

- Typed, weighted, directed graphs with multi-label nodes.
- CyQL, a Cypher-inspired query language covering matching, traversal, vector similarity, full-text
  search, writes and schema changes.
- Bounded variable-length traversal, one-hop neighbours and context-window construction.
- Graph branching: fork a graph, change the copy, merge or discard.
- Graph RAG - community detection with hierarchical summaries and global search.

**Agentic memory**

- An observe/recall/decay lifecycle with entity linking, for agents that remember across sessions.

**Interfaces**

- A web console for administration, querying and 2D/3D graph visualization.
- REST APIs on two ports, each with an interactive Swagger UI.
- A Java SDK over gRPC that needs no port argument against this image.
- An MCP endpoint exposing 39 tools, with per-request authentication.

**Platform**

- Multi-tenant, role-based access control applied uniformly across console, REST, SDK and MCP.
- Built-in durable storage: every statement is one atomic commit, with multi-operation transactions
  and rollback.
- An in-process ONNX embedder, so vector search works with no provider account and no network.
- Prometheus metrics, OTLP tracing and unauthenticated health endpoints.
- Multi-architecture image - `linux/amd64` and `linux/arm64` both native.

### Known limitations

These are Early Access boundaries rather than defects. Several are simply the next things we are
building.

- **One container only.** The multi-service topology - separate platform and data servers behind a
  single-port gateway, and horizontally scaled data servers - is not part of this release.
- **Evaluation authentication.** The image seeds three in-memory logins at fixed roles. Identity
  provider integration over OIDC belongs to the deployment topology arriving at general availability.
- **Credentials come from the startup banner.** There is no flow yet for rotating the seeded API key
  from the console; create an additional key in the administration area if you need a second one.
- **Vector dimensions are fixed at creation.** Changing the embedding provider or model usually changes
  the dimension, which currently means creating a new field and re-embedding rather than migrating in
  place.
- **Single writer per collection.** Consistency for HNSW indices depends on one writer at a time. This
  is invisible in a single container and becomes relevant only in the scaled topology.
- **Visualization suits hundreds of nodes, not tens of thousands.** Start from a query result rather
  than the whole graph.
- **Natural language search needs a language model.** Without one configured, the feature is
  unavailable and you write CyQL directly. Everything else works with no provider at all.

### Support expectations

Early Access is pre-release software, supported on a best-effort basis through the channel you were
given with your invitation. We read everything.

Most useful to us, roughly in order: something that does not work, something that was confusing,
something missing that blocks a real use case, and performance that surprised you. Do please talk to us
about performance privately - the licence asks you not to publish benchmarks or comparisons without
our written consent, and we would rather have the conversation than have you guess.

Storage carries over between Early Access releases. Take a backup before upgrading anyway; see
[Operations](operations.md).
