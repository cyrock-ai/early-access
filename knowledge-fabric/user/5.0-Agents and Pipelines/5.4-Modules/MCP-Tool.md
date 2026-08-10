# MCP Tool (`MCP_TOOL`)

A tool from the Docker MCP catalog, started and managed by the agent server itself.

**Category:** Integration · **Deployed:** yes · **Tool-capable:** **yes (only)**

## Ports

| Port | Kind | Purpose |
|---|---|---|
| Tool (`tool_mcp`) | Tool | Wire to an Agent's Tools port |

## Properties

| Field | Required | Meaning |
|---|---|---|
| Name (`name`) | **Yes** | Tool name **as the agent server expects it** |
| URL (`url`) | No | MCP SSE endpoint — only for manual SSE tools |
| Tool Filter (`toolFilter`) | No | Exact tool names to expose to the agent. Empty allows all |

### Secrets — rendered dynamically per tool

Beyond the fields above, the properties panel shows a **Secrets** section whose contents depend on the tool
you picked from the catalog. Each catalog entry declares which credentials it needs (an API token, an
account ID), and the panel renders one field per declared secret — with the tool's own example value as
helper text where it provides one.

There is therefore no fixed list here: a filesystem tool may need none, while a hosted API tool needs
several. Add the tool from the catalog first, then fill in whatever secrets appear.

> Secret values are stored in the pipeline definition, which means they are included in an **exported
> pipeline JSON in plain text**. Scrub exports before sharing them.

## Use cases

- **Standard capabilities** from the catalog — filesystem access, web fetch, developer tooling — without
  running a server yourself.
- **Narrowing a broad server** with Tool Filter: expose only the read operations of a server that also
  offers writes.

## Notes

- **Name must match what the agent server expects** — this is not a free-text label. A wrong name means the
  tool never resolves.
- For an MCP server **you already run**, use [SSE Tool](SSE-Tool.md) instead; that is what it is for.
- **Tool Filter is the safety control.** An unfiltered server exposes every tool it has to the model,
  including destructive ones.
- The Agent's model must support tool calling, or nothing here is ever invoked.
