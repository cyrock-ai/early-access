# KV Store Write (`KV_STORE_WRITE`)

Writes a key/value pair into an EclipseStore storage map.

**Category:** Data Sources · **Deployed:** yes · **Tool-capable:** **yes**

## Ports

| Port | Kind | Purpose |
|---|---|---|
| Entry (`in_entry`) | Input | The key/value pair to store |
| Result (`out_result`) | Output | Write outcome |
| Tool (`tool_mcp`) | Tool | Wire to an Agent's Tools port so the LLM can store values itself |

## Properties

| Field | Required | Meaning |
|---|---|---|
| Collection Name (`collectionName`) | **Yes** | The storage map to write into |
| Static Key (fallback) (`key`) | No | Used only as a pipeline step, and only when the incoming JSON has no `key` field |
| Static Value (fallback) (`value`) | No | Used only as a pipeline step, and only when the incoming JSON has no `value` field. Stored as plain text |

### Runtime input

| Input field | Meaning |
|---|---|
| `key` | The key to store — via the input connection or the tool call. Overrides the static key |
| `value` | The value to store — likewise |

## Use cases

- **Persisting a vector index:** Text Splitter → Iterator → Embedding → KV Store Write.
- **Cross-run state** for scheduled pipelines — record what was processed so the next run can skip it.
- **Caching expensive results** keyed on the input.
- **As a tool**, letting the agent remember something the user told it.

## Notes

- **Collection Name is required** — an empty one drops the module silently.
- `key` and `value` normally come from the input or the tool call. The two static fields are *fallbacks*,
  applied per field: whatever the incoming JSON supplies wins, and whatever it omits falls back. Wiring a
  bare string to Entry, with neither an input field nor a static fallback for a part, fails the step.
- **The static fields do nothing in tool mode.** When this module is wired to an Agent's Tools port, the
  calling LLM always supplies both — the configured values are never consulted.
- Writes overwrite. There is no versioning — keep the previous value yourself if you need it.
