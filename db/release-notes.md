# Release notes

## 0.9.1 - Early Access

Still one container image. What moved is reach - a Python SDK, connectors for the two JVM AI
frameworks, an asynchronous Java API - and correctness, in a long run of changes to what the APIs
answer when a request is wrong.

### What is new

**Clients**

- A **Python SDK** at parity with the Java client: collections, documents, graphs, CyQL,
  transactions and the community layer, as a blocking client and an asyncio one. See
  [Python SDK](python-sdk.md).
- **Framework connectors** for the JVM AI frameworks: a Spring AI `VectorStore` with Spring Boot
  auto-configuration and a health indicator, and a LangChain4j `EmbeddingStore`, plus retrievers
  that reach the graph traversal and community summaries a plain vector store cannot express. See
  [Framework connectors](framework-connectors.md).
- An **asynchronous Java API**. `client.async()` returns the same operations returning
  `CompletableFuture`, sharing the synchronous client's connection, key exchange and lifecycle, so a
  caller can hold many calls in flight without a thread waiting on each. See
  [Java SDK](java-sdk.md#calling-asynchronously).
- **Renaming a collection** is now available in the SDK, alongside the console and REST.

**Data model**

- **A collection or a graph need not declare a vector field.** Without one you have a document or
  node store with typed metadata filtering and full-text search, and only similarity search is
  unavailable. A vector field added later takes effect immediately, so vectors can arrive after the
  data does.

**New reads**

- `GetNodes` reads a named set of nodes in one call instead of one at a time.
- An **induced subgraph** read: given a set of nodes, get the edges among them without paying for
  the frontier around them.
- **Bounded community reads.** Reading a community's members, the node-to-community assignments and
  the stored summaries are all windowed now, and each says whether more was held back, so reading a
  large graph's community layer no longer means holding all of it at once.
- **Updating an edge's metadata** in place, rather than by replacing the edge.

**Agents**

- One new MCP tool, `cyrock_db_graph_get_community_summaries`, which reads the stored summaries at a
  hierarchy level by name rather than by similarity to a query - the right tool when you already
  know which communities you want. The catalogue is now **40 tools**. See
  [MCP for AI agents](mcp.md).

**Console**

- The **CyQL editor** has syntax highlighting, completion and live validation. Completion offers
  your own fields alongside the language's keywords and functions, and syntax is checked as you type
  rather than on submit.
- A **context-sensitive help panel** that describes the screen you are on, with tooltips on the
  controls that earn them.
- **The console's strings are externalized for translation**, which is the groundwork for shipping
  it in more than one language.
- A pass over the whole console so it **reads as one designed product**: consistent spacing,
  headings, empty states and actions across every tab.
- The console **says which organization and project you are working in**, which starts to matter the
  moment you have more than one.

**Platform**

- **The storage format is versioned.** Storage this build cannot read is detected when it is opened
  at startup and the engine refuses to serve it, naming both format versions and telling you to
  start with an empty storage directory, rather than failing later inside a request. See
  [Operations](operations.md).
- **The tenancy model is enforced across both planes.** Organization and project scoping now
  applies on the platform and data planes alike, so a request cannot reach across a boundary the
  console does not show you.

**Correctness**

- A large pass over the **API contract**, around thirty changes, in three themes. A caller error now
  answers with an honest status code instead of a 500: a wrong vector dimension, a degenerate or
  empty vector, a blank or omitted required field and a number written into a `STRING` field are all
  400s, and a missing graph node or edge is a 404. Input is validated at the boundary rather than
  deep inside a write. And result sets are bounded, so a list or a search cannot be asked for an
  unbounded window, and a zero or negative count means an empty result rather than everything.
- **Graph branching fixes.** An upsert on a branch no longer loses data or leaks into the graph it
  was forked from, a vector field removed on a branch is removed at merge, and `UNIQUE` and
  eventual indexing survive in a branch overlay instead of being silently dropped.

### Upgrading from 0.9.0

- **Start with an empty storage directory.** 0.9.1 will not read 0.9.0's storage: the format is
  versioned now, and a 0.9.0 directory carries no marker, so it is refused at startup with the
  banner described above. Take a backup, then start fresh - [Operations](operations.md) covers
  volumes and backup.
- **Some failures now answer with a different status.** Requests that used to come back as 500 come
  back as 400 or 404 where that is the honest answer, and blank or missing required values are
  refused at the client boundary rather than sent. Code that branched on a 500, or that relied on a
  blank id being accepted, is worth a look. Branch on the SDK's exception subtypes rather than on
  the number - see [Java SDK](java-sdk.md#errors).
- **Unbounded result windows are refused.** A list or a search that asked for everything now has to
  name a window, and a count of zero or less means an empty result.

### Known limitations

These are Early Access boundaries rather than defects. Several are simply the next things we are
building.

- **One container only.** The multi-service topology - separate platform and data servers behind a
  single-port gateway, and horizontally scaled data servers - is not part of this release.
- **Evaluation authentication.** The image seeds three in-memory logins at fixed roles. Identity
  provider integration over OIDC belongs to the deployment topology arriving at general availability.
- **Credentials come from the startup banner.** There is no flow yet for rotating the seeded API key
  from the console; create an additional key in the administration area if you need a second one.
- **A vector field's dimension is fixed once the field exists.** A collection or graph can now be
  created without a vector field at all, and a new field can be added later and takes effect
  immediately - but an existing field's dimension cannot change, so moving to an embedding model of
  a different size still means a new field and a re-embed rather than a migration in place.
- **Single writer per collection.** Consistency for HNSW indices depends on one writer at a time.
  This is invisible in a single container and becomes relevant only in the scaled topology.
- **Visualization suits hundreds of nodes, not tens of thousands.** Start from a query result rather
  than the whole graph.
- **Natural language search needs a language model.** Without one configured the feature is
  unavailable, and the console now says so plainly instead of leaving you to work it out. You write
  CyQL directly, which the new editor makes considerably easier. Everything else works with no
  provider at all.
- **The console is English only for now.** Its strings are externalized for translation, but no
  second language ships in this release.
- **The framework connectors do not create schema.** They read and write a collection or graph that
  already exists; creating it is still your step.

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

Early Access is pre-release software, supported on a best-effort basis through
[issues](https://github.com/cyrock-ai/early-access/issues) and
[discussions](https://github.com/cyrock-ai/early-access/discussions) in the Early Access repository.
We read everything.

Most useful to us, roughly in order: something that does not work, something that was confusing, and
something missing that blocks a real use case.

Storage may not carry over between Early Access releases. When a release changes the on-disk format, the
engine now detects it at startup and refuses to serve the old storage with a clear message telling you to
start with an empty storage directory, rather than failing later with an obscure error. Take a backup before
upgrading, and see [Operations](operations.md).
