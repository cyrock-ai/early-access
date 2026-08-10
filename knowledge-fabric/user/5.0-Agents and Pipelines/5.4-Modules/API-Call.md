# API Call (`API_CALL`)

Makes an HTTP request and forwards the response downstream. One of the most useful modules, and one that
works equally well as a step or as a tool.

**Category:** Data Sources · **Deployed:** yes · **Tool-capable:** **yes**

## Ports

| Port | Kind | Purpose |
|---|---|---|
| Input (`in_input`) | Input | Optional JSON that can override the configuration at runtime |
| Response (`out_response`) | Output | The response body, or the extracted field |
| Tool (`tool_mcp`) | Tool | Wire to an Agent's Tools port to let the LLM call the API itself |

## Properties

| Field | Required | Meaning |
|---|---|---|
| URL (`url`) | **Yes** | Endpoint URL |
| Method (`method`) | **Yes** | `GET` / `POST` / `PUT` / `PATCH` / `DELETE` |
| Description (`description`) | No, but **required in practice when used as a tool** | Tells the LLM what this API does and when to call it |
| Headers (`headers`) | No | JSON object of custom headers |
| Body (`body`) | No | Request body |
| Auth Type (`authType`) | No | `NONE` (default) / `BEARER` / `BASIC`. For an arbitrary API-key header, add it to Headers instead |
| Auth Value (`authValue`) | No | Bearer: the token. Basic: `username:password` in **plain text** — base64-encoded automatically, do not pre-encode |
| Response JSONPath (`responseJsonPath`) | No | Extract one field, e.g. `$.choices[0].message.content` |
| Timeout (`timeoutSeconds`) | No | Default 30 |

### Runtime overrides

When wired as a step, incoming JSON can override the configuration:

| Input field | Overrides |
|---|---|
| `url` | The configured endpoint |
| `method` | The HTTP method |
| `body` | The request body |
| `headers` | Merged as additional headers |

## Use cases

- **Fetch data mid-pipeline:** Scheduler → API Call → Agent summarises the response.
- **As a tool**, letting the agent look things up on demand — the model supplies the URL or body itself.
- **Push a result outward:** Agent → API Call posting to a webhook or ticket system.
- **Chained calls** where the first response feeds the next request via the input overrides.

## Notes

- **Do not base64-encode Basic credentials yourself** — enter `username:password` and let the module do it.
- Use **Response JSONPath** to hand the model one clean value instead of a whole JSON document; it markedly
  improves answer quality and cuts tokens.
- As a tool, the **Description is load-bearing** — a vague one means the model never calls it, or calls it
  wrongly.
- The URL must be reachable **from inside the Agent container**.
