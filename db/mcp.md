# MCP for AI agents

The engine speaks the [Model Context Protocol](https://modelcontextprotocol.io/), so an AI agent can
search, query and write through **39 tools** rather than through code you write and maintain.

The endpoint is streamable HTTP at **`http://localhost:8085/mcp`**.

## Connecting Claude Code

```bash
claude mcp add --transport http cyrock-db http://localhost:8085/mcp \
  --header "Authorization: Bearer <the key from the startup banner>"
```

## Connecting Claude Desktop

Add the server to your Claude Desktop configuration file:

```json
{
  "mcpServers": {
    "cyrock-db": {
      "type": "http",
      "url": "http://localhost:8085/mcp",
      "headers": {
        "Authorization": "Bearer <the key from the startup banner>"
      }
    }
  }
}
```

Restart Claude Desktop. The CYROCK.AI DB tools appear in the tool list.

## Authentication

Every request carries its own credential:

```
Authorization: Bearer <api-key>
```

`X-API-Key: <api-key>` works too, if your client makes that easier to set.

The key is authenticated per request rather than configured once on the server. That is what allows
one endpoint to serve several users and agents at different permission levels: an agent can only do
what its key's role allows, exactly as in the console. There is no ambient identity to fall back on,
so a request without a credential fails rather than being treated as trusted.

Tools also default to the project from the startup banner, so an agent need not be told a project ID
for ordinary work.

## The tool catalogue

39 tools in four groups. Every name is prefixed `cyrock_db_`.

### Collections (4)

| Tool | Purpose |
|---|---|
| `cyrock_db_list_collections` | List collections in a project |
| `cyrock_db_get_collection` | Get a collection definition |
| `cyrock_db_collection_query` | Run a read-only CyQL query against a collection |
| `cyrock_db_collection_statement` | Run any CyQL statement, including writes and schema changes |

### Documents (9)

Reading, writing and searching documents: get by id or external key, list, upsert, delete, and vector
or filtered similarity search.

### Knowledge graphs (22)

The largest group, covering graph and schema management, node and edge reads and writes, similarity
search over node fields, one-hop neighbours, bounded traversal, context windows, graph branching, and
the Graph RAG community tools - community detection, summaries, global search, refresh and status.

### Agentic memory (4)

The observe/recall/decay lifecycle plus entity linking, for agents that need to remember across
sessions.

For the exact signature of any tool, ask the agent to list its tools - the descriptions the server
publishes are the authoritative reference, and they are what the model actually reads.

## Read-only against read-write

The split between `cyrock_db_collection_query` and `cyrock_db_collection_statement` is deliberate, and
graph tools split the same way. A query tool rejects writes.

This is how you give an agent useful access without granting it destructive power. If an agent's job
is to answer questions, the read-only tools are enough - and then no amount of confused reasoning or
prompt injection turns into deleted data. Reach for the statement tools only when the agent's job
genuinely includes writing.

Role permissions apply on top: a key with a read-only role cannot write even through a statement tool.

## What works well

A few patterns worth knowing, from using this ourselves:

- **Let the agent search semantically, then traverse.** Vector search finds the entry point; the graph
  supplies the surrounding context. An agent that does both gives far better answers than one doing
  keyword lookup.
- **Give it the schema first.** `get_collection` and the graph schema tools are cheap, and an agent
  that knows the field names writes correct CyQL instead of guessing.
- **Prefer one CyQL statement to several tool calls.** A single query with a traversal costs one round
  trip and keeps the reasoning simpler than five sequential lookups.

## Troubleshooting

**Tools do not appear.** Check the container is healthy (`docker ps`) and the endpoint responds:

```bash
curl -sS -X POST http://localhost:8085/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"curl","version":"1"}}}'
```

A JSON result with `serverInfo` means the endpoint is fine and the problem is in the client
configuration.

**Calls fail with a permission error.** The key's role is too narrow for that tool. Try the
`superadmin` key from the banner to confirm, then decide which role the agent should really have.

**Port 8085 is taken.** Publish it elsewhere - `-p 8090:8085` - and use the new port in the client
configuration. See [Troubleshooting](troubleshooting.md).
