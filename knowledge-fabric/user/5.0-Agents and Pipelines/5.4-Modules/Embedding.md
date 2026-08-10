# Embedding (`EMBEDDING`)

Creates a vector embedding for a chunk of text.

**Category:** Models & Agents · **Deployed:** yes · **Tool-capable:** no

## Ports

| Port | Kind | Purpose |
|---|---|---|
| Text (`in_text`) | Input | The text to embed |
| Vector (`out_vector`) | Output | The resulting vector |

## Properties

| Field | Required | Meaning |
|---|---|---|
| Model Provider (`model.provider`) | **Yes** | `OLLAMA` or `OPEN_AI` |
| Model Name (`model.name`) | **Yes** | e.g. `nomic-embed-text`, `text-embedding-3-small` |
| Model URL (`model.url`) | **Yes** | Base URL of the endpoint |
| API Key (`model.apiKey`) | No | Required for `OPEN_AI` |
| Model Timeout (`model.timeoutMinutes`) | No | Minutes, 1–120, defaults to 20 |

## Use cases

- **Custom ingestion chain:** File Read → Text Splitter → Iterator → Embedding → KV Store Write. This is
  the canonical use, and the reason Embedding pairs naturally with Iterator.
- **Semantic comparison** — embed two texts and compare the vectors in a Python Script module.

## Notes

- Use an **embedding** model, not a chat model — different model families; a chat model does not produce
  usable vectors.
- For ordinary document Q&A a RAG **Topic** already does all of this. Reach for this module only when you
  need a custom vector workflow.
