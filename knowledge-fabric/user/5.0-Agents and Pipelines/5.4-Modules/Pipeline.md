# Pipeline (`WORKFLOW`)

Runs another pipeline — as a callable tool an Agent can invoke, or as an ordinary step in the flow. This is
how pipelines compose.

**Category:** Integration · **Deployed:** yes · **Tool-capable:** **yes**

## Ports

| Port | Kind | Purpose |
|---|---|---|
| Input (`in_input`) | Input | As a step: the previous module's output becomes the nested pipeline's input |
| Output (`out_output`) | Output | The nested pipeline's result, passed downstream |
| Tool (`tool_mcp`) | Tool | Wire to an Agent's Tools port so the LLM can invoke the pipeline |

## Properties

| Field | Required | Meaning |
|---|---|---|
| Pipeline (`workflowId`) | **Yes** | Select an existing pipeline to run |

Name and description are taken from the selected pipeline — there is nothing else to configure.

## Use cases

- **Reuse instead of duplication** — a shared "look up and format a customer record" pipeline called from
  several places. Fix it once, and every caller benefits.
- **Keeping a large pipeline readable** — extract a self-contained section into its own pipeline and call it.
- **As a tool**, giving an agent a complex multi-step capability behind a single callable name.
- **Layered design:** a thin front pipeline that routes to specialised ones.

## Notes

- **The pipeline ID does not survive an export/import to another installation.** Re-select it after
  importing.
- **Watch for cycles.** A pipeline that calls itself, directly or through a chain, will not terminate
  sensibly — nothing prevents you from wiring it.
- Changes to the nested pipeline take effect for callers once it is **pushed to the running Agent** —
  saving alone is not enough, same as any other pipeline change.
- As a step, the connection is plain data flow. As a tool, the model chooses when to invoke it and with what
  input.
