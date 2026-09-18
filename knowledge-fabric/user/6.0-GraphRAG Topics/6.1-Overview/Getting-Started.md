# GraphRAG — Getting Started

> **Before you read this:** GraphRAG assumes you already understand ordinary RAG — embeddings, a
> vector database, chunking, a chat model answering from retrieved passages. That is the whole content
> of [RAG Topics](../../4.0-RAG%20Topics/4.1-Overview/Overview.md). This section only covers what is
> *different* about GraphRAG.

A **GraphRAG Topic** is the graph-based sibling of a [RAG Topic](../../4.0-RAG%20Topics/4.1-Overview/Overview.md).
Where a RAG Topic only ever embeds chunks into a vector store, a GraphRAG Topic *also* extracts the
entities and relationships those chunks describe into a real graph database, clusters that graph into
topical **communities**, and answers a question with whichever of three retrieval strategies fits it
best — a precise entity lookup, a broad thematic summary, or both combined.

It is a **separate resource type** from a RAG Topic — its own list, its own wizard, its own detail
page, its own chat, and its own permissions (`GRAPHRAG_*` instead of `TOPIC_*`). Creating one does not
touch your existing RAG Topics, and the two can coexist for different purposes.

> **Current status.** GraphRAG is younger than RAG Topics and still under active development. The
> wizard, ingestion, chat, and community recompute all reach a real backend today, but expect rougher
> edges than the RAG side — this is not yet a feature you should stake a production rollout on without
> testing it against your own content first.

---

## What you need before you start

Everything a RAG Topic needs, **plus a graph database**:

| Needed | Where it comes from | Notes |
|---|---|---|
| An AI server with a **chat model** | **Admin → AI Servers** | Doubles as the answer model and the fallback for every optional model role |
| An AI server with an **embedding model** | Same | Chunks, entities, and community reports are all embedded with it |
| A registered **graph database** | **Admin → Graph Databases** | Neo4j, Memgraph, a generic Cypher-compatible server, or CYROCK.DB — **required**, there is no embedded graph store |
| A **vector database**, if you don't want the embedded one | **Admin → Vector Databases** | Same picker and same embedded fallback as RAG Topics |
| A **Docling server**, if you will upload PDF/DOCX/PPTX | **Admin → Docling Servers** | Only needed once you tick Binary documents |
| A free **host port** for the Topic | Anything unused on the host | Same idea as a RAG Topic's port |

The graph database is the one genuinely new prerequisite. See
[Connect a Graph Database](../../3.0-Configuration/3.2-Vector-DB%C2%B4s/Connect-Vector-DB.md) for the
vector-side connection dialog and the **Admin → Graph Databases** page for the graph-side equivalent —
registering one is the same shape of dialog: host/port, credentials, a connection test.

---

## The path from zero to a working GraphRAG Topic

1. **Read [Why GraphRAG](Overview.md)** — five minutes to understand what a graph buys you over plain
   RAG, and whether your content actually benefits from it.
2. **Register a graph database** under **Admin → Graph Databases** (Neo4j is the easiest to try
   locally — a single `docker run` gives you one).
3. **Run the four-step wizard** — [Creation step by step](../../6.0-GraphRAG%20Topics/6.4-Creation/Creation-Step-by-Step.md)
   walks through it field by field.
4. **Start the Topic** and upload documents on its **Data Upload** tab — ingestion runs LLM extraction
   over each document, so it is slower than plain RAG ingestion. See
   [the ingestion workflow](Ingestion-Workflow.md) for what happens underneath.
5. **Wait for communities.** A GraphRAG Topic is not fully ready the instant ingestion finishes —
   community reports (what makes broad, thematic questions answerable) are built on the refresh cycle
   configured in the wizard, or on demand from the **Actions** tab. See
   [Recomputing communities](../../6.0-GraphRAG%20Topics/6.5-Configuration/Configuration.md#recomputing-communities).
6. **Chat.** Ask a narrow, fact-shaped question and a broad, thematic one, and notice they are answered
   differently — that difference is the whole point of the three retrieval strategies. See
   [Retrieval workflows](Retrieval-Workflows.md) and the
   [GraphRAG Chat Window](../6.6-Chat/Chat-Window.md) for what the chat interface shows you about each.

---

## Related

- [Why GraphRAG, and the architecture behind it](Overview.md)
- [How a prompt is answered — LOCAL, GLOBAL, HYBRID](Retrieval-Workflows.md)
- [How a document becomes graph](Ingestion-Workflow.md)
- [Glossary of terms](../6.2-Concepts/Glossary.md)
- [Creation step by step](../6.4-Creation/Creation-Step-by-Step.md)
- [GraphRAG Chat Window](../6.6-Chat/Chat-Window.md)
