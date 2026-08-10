# Module Reference

One page per module in the Pipeline Designer palette. Each page lists the module's ports, its mandatory
and optional properties, whether it can be used as a tool, and what it is for.

## How to read these pages

| Heading | Meaning |
|---|---|
| **Deployed** | Whether the module is sent to the agent server at all. `No` means it exists only on the canvas |
| **Tool-capable** | Whether it can be wired into an Agent's **Tools** port and called by the LLM |
| **Ports** | `Input` receives upstream output · `Output` passes downstream · `Tool` connects to an Agent's Tools port |
| **Required** | A required field left empty causes the whole module to be **silently dropped** at deployment |

> **The universal gotcha:** a module with a missing required field disappears from the deployed pipeline
> without any error on the canvas. If a step never runs, check its required fields first.

## Palette

### Input & Output
- [Chat Input](Chat-Input.md) — entry point, receives the user's message
- [Chat Output](Chat-Output.md) — exit point, returns the result

### Models & Agents
- [Agent](Agent.md) — the reasoning step; the only module with a Tools input
- [Embedding](Embedding.md) — turns text into a vector

### Flow Control
- [Scheduler](Scheduler.md) — cron trigger
- [Iterator](Iterator.md) — walks a JSON collection
- [Loop](Loop.md) — repeats a sub-graph until a Validator passes
- [Validator](Validator.md) — condition / script / LLM check with Pass and Fail
- [Guardrails](Guardrails.md) — safety screening with Pass and Fail

### Data Sources
- [API Call](API-Call.md) — HTTP request
- [SQL Database](SQL-Database.md) — SQL query
- [Data Faker](Data-Faker.md) — synthetic test data
- [KV Store Read](KV-Store-Read.md) — read a key
- [KV Store Write](KV-Store-Write.md) — write a key/value pair
- [Structured Output](Structured-Output.md) — LLM-driven text to JSON array

### Files
- [File Read](File-Read.md) — local, S3, or Azure Blob
- [File Write](File-Write.md) — local, S3, or Azure Blob

### Utilities
- [Template](Template.md) — placeholder substitution
- [Text Splitter](Text-Splitter.md) — chunking
- [Text Format](Text-Format.md) — one text operation
- [Python Script](Python-Script.md) — sandboxed Python
- [Web Search](Web-Search.md) — web search as a tool
- [Description](Description.md) — canvas note, never deployed

### Human Interaction
- [Human Approval](Human-Approval.md) — pauses for a Yes/No

### Integration
- [MCP Tool](MCP-Tool.md) — catalog tool managed by the agent server
- [SSE Tool](SSE-Tool.md) — existing MCP server over HTTP/SSE
- [AI Topic](AI-Topic.md) — a RAG Topic as a tool or step
- [Pipeline](Pipeline.md) — another pipeline as a tool or step

## Tool-capable modules

Only these 13 can be wired into an Agent's Tools port. Anything else connected there is ignored:

MCP Tool · SSE Tool · API Call · AI Topic · SQL Database · Data Faker · KV Store Read ·
KV Store Write · Pipeline · Web Search · Python Script · **File Read** · **File Write**

Notably **not** tool-capable: Human Approval (a paused run cannot hand control back to an LLM's tool
loop), Embedding, Template, Text Splitter, Text Format, Structured Output, and all flow-control modules.

## Step vs. tool

Many modules work either way, and the difference is fundamental:

| | As a step | As a tool |
|---|---|---|
| Wired to | Input/Output ports | An Agent's Tools port |
| Runs | Always, in order | Only when the LLM decides to call it |
| Input | The previous module's output | Arguments the LLM chooses |
| Description field | Optional | **Load-bearing** — it is how the model knows when to call it |
