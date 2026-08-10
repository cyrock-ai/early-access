# SQL Database (`SQL_DATABASE`)

Executes a SQL query and returns the result as JSON.

**Category:** Data Sources · **Deployed:** yes · **Tool-capable:** **yes**

## Ports

| Port | Kind | Purpose |
|---|---|---|
| Input (`in_input`) | Input | Optional JSON that can override the query |
| Result (`out_result`) | Output | Query result as JSON |
| Tool (`tool_mcp`) | Tool | Wire to an Agent's Tools port to let the LLM query on demand |

## Properties

| Field | Required | Meaning |
|---|---|---|
| Connection String (`connectionString`) | **Yes** | JDBC URL, e.g. `jdbc:postgresql://host:5432/db?user=u&password=p` |
| SQL Query (`sqlQuery`) | **Yes** | The query to execute |
| Description (`description`) | No, but **required in practice as a tool** | Tells the LLM what this query returns |

### Runtime override

| Input field | Overrides |
|---|---|
| `sqlQuery` | The configured query |

## Use cases

- **Scheduled reporting:** Scheduler → SQL Database → Agent writes the narrative → File Write.
- **As a tool**, so the agent can look up a record when the conversation calls for it.
- **Feeding an Iterator** — query rows, then process each one.

## Notes

- **The connection string contains credentials in plain text**, and it is included in an exported
  pipeline JSON. Scrub exports before sharing them.
- **Prefer a fixed query with a read-only database user.** The `sqlQuery` override exists, and a
  tool-wired module lets the model influence what runs — grant only the privileges the job needs.
- The database must be reachable **from inside the Agent container**, so `localhost` will not work.
- Large result sets go straight into the model's context. Constrain with `LIMIT` rather than filtering
  afterwards.
