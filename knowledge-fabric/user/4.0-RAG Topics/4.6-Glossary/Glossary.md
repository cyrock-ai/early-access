# Glossary

Every term used elsewhere in this section, in one place. Terms covered in depth on another page link
back to it; this page is where the smaller, easy-to-forget ones live, and where you land when you just
need a quick reminder of what a setting means.

---

### Chunk

A piece of a document's text — a paragraph, a few sentences, a table row — embedded and stored
individually so retrieval can return only the passages relevant to a question, rather than whole
documents. Every retrieved chunk remembers which file it came from, which is what a chat answer's
**Sources** row is built from.

### Chunking Strategy

How a document is split into chunks before embedding — `RECURSIVE` or `SEMANTIC`. Sent with every
upload, so it can be changed on a running Topic and applies from the next upload on. See
[Creation step by step — the two chunking strategies](../4.2-Creation/Creation-Step-by-Step.md#the-two-chunking-strategies).

### Chunk Size / Chunk Overlap

Fixed at Topic creation, unlike the strategy above — changing either later would leave old and new
chunks inconsistent, so both are read-only once the Topic exists. **Chunk Size** is how large one chunk
is (in tokens); **Chunk Overlap** is how much of it repeats in the next chunk, so a sentence spanning a
boundary is not lost.

### Embedding Model

Turns text into the vectors similarity search compares against — for both documents and questions. The
one setting you cannot revise painlessly: changing it later invalidates every vector already stored,
forcing a full re-ingestion. See
[Overview — the building blocks](../4.1-Overview/Overview.md#4-the-building-blocks-you-configure).

### Vector Database

Where embeddings are stored. Either the built-in **embedded** store (EclipseStore, its own volume, zero
configuration) or an external one you register under **Admin → Vector Databases**. Leaving the wizard's
picker empty is a valid, common choice — it means embedded. See
[Connect a Vector DB](../../3.0-Configuration/3.2-Vector-DB%C2%B4s/Connect-Vector-DB.md).

### Retrieval Strategy

`DENSE` (pure vector similarity) or `HYBRID` (adds a BM25 keyword search and fuses both result sets).
Keyword matching helps when exact terms, product codes, or names matter more than semantic similarity.
See [Creation step by step — Step 4](../4.2-Creation/Creation-Step-by-Step.md#step-4--retrieval-strategy).

### Top-K (Results)

How many passages are retrieved and handed to the model for one answer. Higher means more context (and
more tokens spent) per question; too low and an answer can miss content that is clearly in the
documents.

### Reranking

An optional second pass (`LLM` reranking) that re-orders retrieved passages by true relevance before
they reach the answer model — one extra model call per question, reusing the chat model and its
timeout. Improves precision when Top-K pulls in passages that merely resemble the question rather than
answering it.

### Min. Similarity Score

Discards a retrieved passage below this cosine-similarity threshold (0.0–1.0). Empty means no filter.
Set it when answers cite passages that only vaguely relate to the question.

### Context Memory

How many previous messages are fed back into each new request, so a Topic can follow a multi-turn
conversation. Global default of 3, overridable per Topic under **LLM Overrides**. Raise it if the model
seems to forget earlier questions; start a **New Chat** instead of raising it if the conversation has
simply moved to a new subject.

### System Prompt / User System Prompt

Your Topic's own persona and rules, substituted into the global prompt template at the
`{{USER_EDITABLE_PROMPT}}` placeholder — you write only what is specific to this Topic, not general
formatting or safety rules. Assembled once and delivered at container start, **not** sent per chat
request. See [Global LLM Configuration](../../3.0-Configuration/3.3-Global%20LLM%20configuration/Global-LLM-Configuration-and-Prompt-Templates.md).

### RAG Context Template

The instruction, part of the assembled system prompt, telling the model how to use the passages
retrieval handed it — in particular, to prefer that retrieved context over its own general knowledge.
Tighten it if answers seem to ignore the documents in favour of the model's training data.

### No-Answer Response

The fixed text returned when nothing relevant enough was found, instead of letting the model invent an
answer. Configurable per Topic under **LLM Overrides**.

### Source file / citation

A chat answer's list of documents it actually drew on, shown as **Sources** — the mechanism that makes an
answer verifiable rather than merely plausible. Each is a time-limited download link (~10 minutes by
default); an older link greys out and explains itself rather than opening a broken page. See
[Chat window — Sources](../4.4-Chat/Chat-Window.md#3-sources).

### Docling

The service that converts PDF, DOCX, and PPTX into clean text before chunking — required the moment a
Topic accepts **Binary documents**, either as uploads or as chat attachments. Without a reachable
Docling server, such a file is rejected rather than silently skipped.

### Image Describer Model

A dedicated (or inherited) model that turns pictures encountered during ingestion into a text
description, so their content becomes searchable. Independent of whether users may attach an image to a
*chat message* — that is a separate checkbox, and an attached image goes straight to the Topic's own
Language Model instead. See
[Creation step by step — Image handling](../4.2-Creation/Creation-Step-by-Step.md#image-handling).

### Structured Import Strategy

How tabular/record-shaped files (JSON, XML, YAML, TOML, CSV, TSV) are turned into text before chunking —
`FLATTEN` (key/value text, the default) or `NARRATE` (one extra LLM call per record, turning it into
prose). See
[Structured Data Import](../../4.0-RAG%20Topics/4.2-Creation/Creation-Step-by-Step.md#structured-import-optional).

### Storage Mode

`EMBEDDED` (the file's content is stored alongside its vectors — the wizard's only offered option) or
`EXTERNAL` (only a path/URL is stored, requiring a `url` on every ingest call — reachable only through
the [REST interface](../4.5-REST-API/REST-API.md), not the wizard).

### Chat Attachments

Which file types users may attach to a single chat message — configured per Topic, independent of what
that Topic accepts for permanent upload. An attachment is ephemeral: folded into context for that one
reply only, never added to the knowledge base. See
[Chat window — Attachments](../4.4-Chat/Chat-Window.md#5-attachments).

### MCP (Model Context Protocol)

A standard letting a Topic's language model call external tools while answering, instead of relying on
retrieval alone — including calling *another* Topic as a tool. Requires a tool-calling-capable chat
model; without one, connected tools are silently never used. See
[Overview — MCP](../4.1-Overview/Overview.md#5-mcp--giving-a-topic-tools).

### RAG Service Port

The host port a Topic's `rag-service` container listens on, chosen in step 1 of the wizard. What makes
the [REST interface](../4.5-REST-API/REST-API.md) reachable directly, independent of the browser UI.

### memoryId

The REST interface's conversation identifier — there is no separate session endpoint, so reusing the
same `memoryId` across calls *is* what keeps context, and a fresh value starts a new conversation. See
[REST interface — memoryId is the conversation](../4.5-REST-API/REST-API.md#memoryid-is-the-conversation).

---

## Related

- [Overview](../4.1-Overview/Overview.md)
- [Creation step by step](../4.2-Creation/Creation-Step-by-Step.md)
- [Configuration and functions](../4.3-Configuration/Configuration.md)
- [Chat window](../4.4-Chat/Chat-Window.md)
- [REST interface](../4.5-REST-API/REST-API.md)
