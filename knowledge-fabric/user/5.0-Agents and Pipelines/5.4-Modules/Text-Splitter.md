# Text Splitter (`TEXT_SPLITTER`)

Splits text into overlapping chunks.

**Category:** Utilities · **Deployed:** yes · **Tool-capable:** no

## Ports

| Port | Kind | Purpose |
|---|---|---|
| Text (`in_text`) | Input | The text to split |
| Chunks (`out_chunks`) | Output | The resulting chunks |

## Properties

| Field | Required | Meaning |
|---|---|---|
| Chunk Size (`chunkSize`) | **Yes** | Maximum characters per chunk |
| Chunk Overlap (`chunkOverlap`) | No | Characters each chunk repeats from the end of the previous one — default 0 |

## Use cases

- **Custom ingestion:** File Read → Text Splitter → Iterator → Embedding → KV Store Write.
- **Working around a context limit** — split a long document, process each part, then combine.

## Notes

- **Set an overlap when the chunks will be embedded.** With 0 overlap a sentence spanning a boundary is
  split across two chunks and retrieval finds neither cleanly. A modest overlap is the standard remedy.
- Chunk size is in **characters**, not tokens.
- Feeds [Iterator](Iterator.md) naturally — Splitter produces the collection, Iterator walks it.
- For ordinary document Q&A, a RAG **Topic** already chunks for you. This is for custom flows.
