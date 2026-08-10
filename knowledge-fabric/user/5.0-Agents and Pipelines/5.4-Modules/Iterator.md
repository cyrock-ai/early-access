# Iterator (`ITERATOR`)

Walks a JSON collection, forwarding each item in turn, then emits a static message when finished.

**Category:** Flow Control · **Deployed:** yes · **Tool-capable:** no

## Ports

| Port | Kind | Purpose |
|---|---|---|
| Collection (`in_collection`) | Input | A JSON collection to iterate |
| Item (`out_item`) | Output | Fires once **per item** |
| Done (`out_done`) | Output | Fires **once**, after every item has been forwarded |

## Properties

| Field | Required | Meaning |
|---|---|---|
| Done Message (`doneMessage`) | **Yes** | Static message emitted on the Done output when iteration completes |

## Use cases

- **Per-chunk processing:** Text Splitter → Iterator → Embedding → KV Store Write.
- **Batch over query results:** SQL Database → Iterator → Agent, one row at a time.
- **Fan-out then summarise** — per-item work on Item, the closing summary on Done.

## Notes

- Two outputs with different cardinality: **Item fires N times, Done fires once.** Wiring per-item work to
  Done (or the reverse) is the usual mistake.
- The input must be a JSON collection. A plain string is not iterable.
- Distinct from [Loop](Loop.md): Iterator walks a *known* collection once; Loop *repeats* a sub-graph
  until a condition is met.
