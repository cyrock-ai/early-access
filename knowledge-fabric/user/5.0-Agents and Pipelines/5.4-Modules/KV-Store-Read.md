# KV Store Read (`KV_STORE_READ`)

Reads a value by key from an EclipseStore storage map.

**Category:** Data Sources · **Deployed:** yes · **Tool-capable:** **yes**

## Ports

| Port | Kind | Purpose |
|---|---|---|
| Key (`in_key`) | Input | The key to look up |
| Value (`out_value`) | Output | The stored value |
| Tool (`tool_mcp`) | Tool | Wire to an Agent's Tools port so the LLM can look keys up itself |

## Properties

| Field | Required | Meaning |
|---|---|---|
| Collection Name (`collectionName`) | **Yes** | The storage map to read from |
| Static Key (fallback) (`key`) | No | Used only as a pipeline step, and only when the incoming JSON has no `key` field |

### Runtime input

| Input field | Meaning |
|---|---|
| `key` | The key to look up — overrides any static key, or is supplied by the LLM when used as a tool |

## Use cases

- **Persistent agent memory** — read state written on a previous run, which a `NEW_EACH_RUN` scheduled
  pipeline otherwise has no way to carry forward.
- **Caching** — check for a previously computed result before doing expensive work.
- **As a tool**, letting the agent retrieve stored context on demand.
- **Pairs with [KV Store Write](KV-Store-Write.md)** as the read half of a store.

## Notes

- **Collection Name is required.** Empty means the module is dropped from the deployment, and if it was an
  Agent's tool it is removed from that tool list too.
- **The static key does nothing in tool mode.** When this module is wired to an Agent's Tools port, the
  calling LLM always supplies the key — the configured value is never consulted. A pipeline step with
  neither an incoming `key` nor a static key fails with an explicit error.
- The collection is a plain key/value map — no querying, no scanning. Design keys you can reconstruct.
