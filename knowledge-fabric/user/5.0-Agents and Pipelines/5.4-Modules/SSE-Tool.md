# SSE Tool (`MCP_SSE`)

Connects to an **existing** MCP server over an HTTP/SSE URL.

**Category:** Integration · **Deployed:** yes · **Tool-capable:** **yes (only)**

## Ports

| Port | Kind | Purpose |
|---|---|---|
| Tool (`tool_mcp`) | Tool | Wire to an Agent's Tools port |

## Properties

| Field | Required | Meaning |
|---|---|---|
| Name (`name`) | **Yes** | Display name for this connection |
| URL (`url`) | **Yes** | SSE endpoint, e.g. `http://my-server:3000/sse` |
| Description (`description`) | No | What tools this server provides — read by the LLM |
| Tool Filter (`toolFilter`) | No | Exact tool names to expose. Empty allows all |

## Use cases

- **Your own MCP server** — an internal service wrapped as MCP and shared across pipelines.
- **A third-party hosted MCP server** you have a URL for.
- **A running Topic as a tool** — every running Topic exposes an MCP endpoint. Using
  [AI Topic](AI-Topic.md) is more convenient, but this works when you have the URL.
- **Restricting a shared server** per pipeline via different Tool Filters.

## Notes

- **The URL must be reachable from inside the Agent container.** `localhost` refers to the container —
  use `host.docker.internal`, or `172.17.0.1` on plain Linux Docker.
- **Unlike [MCP Tool](MCP-Tool.md), the Name is a free label** here — the URL identifies the server. The
  Description is what guides the model.
- **Tool Filter is the control that matters** on a server exposing write or delete operations.
- Both Name and URL are required; either one empty drops the module.
