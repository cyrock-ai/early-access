# Glossary

Every term used elsewhere in this section, in one place. Terms covered in depth on another page link
back to it; this page is where the smaller, easy-to-forget ones live.

---

### Entity

A single "thing" the graph knows about — a person, product, system, error code, organisation, anything
your content actually discusses. Extracted from chunks by the **Extraction model** during ingestion.
Stored as a graph node, and embedded into the vector database so it can be found by a dense (or
keyword) search the same way a chunk can.

### Relationship

A directed connection between two entities, extracted the same way and at the same time as the
entities themselves. Traversal (the core of LOCAL search) works by following relationships outward from
a starting set of entities.

### Node / Edge

The graph-theory names for entity and relationship, respectively — used interchangeably with those
terms in the UI and in this documentation.

### Chunk

Same meaning as in a RAG Topic: a piece of a document's text, embedded and stored for retrieval. In
GraphRAG, a chunk also has a second job — it is what entities and relationships remember as their
**provenance** (which document(s) they were extracted from), which is what makes deleting a document
possible without deleting entities other documents still rely on.

### Seed (entities)

The small set of entities a LOCAL query's traversal starts from — found by a dense search over entity
embeddings, matching the question. See [Retrieval strategies](Retrieval-Strategies.md#local).

### Subgraph

The set of entities and relationships a LOCAL traversal actually collects, starting from the seeds and
expanding outward. Bounded by **Hops** and **Max Subgraph Nodes** — see
[Retrieval strategies](Retrieval-Strategies.md#local).

### Community

A cluster of densely connected entities, produced by periodically re-clustering the whole graph. Every
community with more than one entity gets a written summary (its **community report**) — GLOBAL search
answers entirely from these reports rather than from individual chunks. See
[how a document becomes graph](../6.1-Overview/Ingestion-Workflow.md#communities-are-not-automatic-per-upload)
for when this runs.

### Leiden (clustering algorithm)

The specific graph-clustering algorithm used to detect communities. Not a setting you choose — every
GraphRAG Topic uses it, tuned only by the **Community Resolution** value (see
[Retrieval strategies](Retrieval-Strategies.md#communities--clustering-behind-global)).

### Community Resolution

How finely Leiden splits the graph. Higher → more, smaller communities. Lower → fewer, larger ones.
`1.0` is the standard value.

### BM25 / keyword search

A classic keyword-matching search (as opposed to embedding similarity), run alongside dense search for
both LOCAL and GLOBAL by default, then combined with the dense results. Exists specifically to catch
exact terms, codes, and names that embeddings represent poorly. Its index lives in its own storage
inside the container, entirely separate from whichever vector database you configured — meaning it is
not something an external vector database backs up or migrates for you; it lives and dies with the
container's own volume.

### Dense search

Ordinary embedding-similarity search — the same kind of search a RAG Topic does over chunks, applied
here to chunks, entities, and community reports alike.

### Router

The model call that classifies every incoming question as LOCAL, GLOBAL, or HYBRID before any actual
retrieval happens. See [how a prompt is answered](../6.1-Overview/Retrieval-Workflows.md#the-router--deciding-how-to-answer).

### Router Confidence Threshold

How sure the router has to be in its own classification before it is trusted; below it, the question
falls back to HYBRID. See [Retrieval strategies](Retrieval-Strategies.md#the-routers-confidence-threshold).

### Cypher template (traversal template)

A fragment of Cypher (the query language most graph databases here use) that defines exactly how LOCAL
search traverses the graph from its seed entities. An existing Topic can hold a custom one, but there is
currently no editor for it in the wizard or configuration UI — it can only be set directly on the
underlying data. Leave this alone unless you have a specific reason and a way to write to the field
outside the UI; a broken template fails silently as "no results" rather than as an error.

### Graph database

The external server holding your entities and relationships as real graph structure — Neo4j, Memgraph,
a generic Cypher-compatible server, or CYROCK.DB. **Required** for every GraphRAG Topic; there is no
embedded equivalent to the vector side's built-in EclipseStore. Registered under **Admin → Graph
Databases**.

### Vector database

Same role as in a RAG Topic: stores embeddings for chunks, entity nodes, and community reports. Can be
external (registered under **Admin → Vector Databases**) or left embedded, exactly like a RAG Topic.

### CYROCK.DB

A server registered once but usable in **both** roles at once — as a vector database and as a graph
database — because it is genuinely one product serving both purposes. Its connection settings (gRPC
port, project ID, API-key authentication) are the same regardless of which role you are registering it
for.

### Collection name

The name of the vector-database collection this Topic's chunks, entity nodes, and community reports are
stored under. Unlike a RAG Topic (where this is derived automatically), you type it yourself, and it
must be unique across your GraphRAG Topics on the same database — a collision would mean two Topics
silently sharing (and corrupting) each other's data.

### Source file / citation

An answer's list of documents it drew on, shown under a LOCAL or HYBRID answer (GLOBAL never returns
any — see [how a prompt is answered](../6.1-Overview/Retrieval-Workflows.md#global--broad-thematic-synthesis)).
Each citation is a clickable download link that expires after a short time — asking the same question
again mints a fresh one. Works exactly like a RAG Topic's source citations; see that side's
documentation for the mechanics of the expiry.

### Graph-sync vs. Document

Two different origins a source citation (or a row on the Data Upload tab) can have:

- **Document** — a file you uploaded through this Topic's Data Upload tab. Has real bytes behind it,
  can be downloaded, and can be deleted through the normal flow.
- **Graph-sync** — a database row that arrived through the separate `POST /graphrag/ingest/graph`
  route, used by an external system replicating its own graph data into this Topic. Has no uploaded
  bytes, so it cannot be downloaded, and it is removed through a different route than an uploaded file
  (see [how a document becomes graph](../6.1-Overview/Ingestion-Workflow.md#two-ingestion-routes-not-one)).

### Prompt overrides

Every prompt the container sends to a model can be individually overridden per Topic, on the detail
page's **Prompts** tab — grouped by which model role each one belongs to. Leaving one untouched means
the container uses its own built-in wording; overriding it and later reverting to the exact original
text removes the override rather than freezing a stale copy. See
[Configuration and functions](../6.5-Configuration/Configuration.md#prompts).

### System prompt

Distinct from the prompt overrides above — your Topic's own persona/instructions text, the same idea as
a RAG Topic's system prompt, substituted into a shared template. Applied to exactly one call per
question: LOCAL's answer, GLOBAL's reduce step, or HYBRID's synthesis, whichever handled it. See
[Models and their roles](Models-and-Roles.md#language-model-the-answer-model).

### Expert settings gate

A per-section "Enable expert settings" checkbox on several wizard steps, hiding advanced fields (like
the retrieval bounds on this page) behind a lock so a first-time Topic is not overwhelmed by knobs that
already have sensible defaults. A section unlocks itself automatically if the Topic's stored values are
already different from the defaults, so an already-tuned Topic never looks like it is hiding something
important. See [Creation step by step](../6.4-Creation/Creation-Step-by-Step.md#expert-settings).

### Structured data

Tabular or record-shaped files (JSON, XML, YAML, TOML, CSV, TSV). Unlike a RAG Topic, GraphRAG has no
choice to make here — such files are always flattened into key/value text before chunking, with no
separate "narrate" option and no model call spent on it.

---

## Related

- [How a prompt is answered — LOCAL, GLOBAL, HYBRID](../6.1-Overview/Retrieval-Workflows.md)
- [How a document becomes graph](../6.1-Overview/Ingestion-Workflow.md)
- [Retrieval strategies](Retrieval-Strategies.md)
- [Models and their roles](Models-and-Roles.md)
