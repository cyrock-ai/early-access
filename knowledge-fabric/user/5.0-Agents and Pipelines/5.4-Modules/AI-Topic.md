# AI Topic (`AI_TOPIC`)

Uses an existing RAG **Topic** from this installation — either as a tool an Agent can consult, or wired
into the flow as a step.

**Category:** Integration · **Deployed:** yes · **Tool-capable:** **yes**

## Ports

| Port | Kind | Purpose |
|---|---|---|
| Query (`in_query`) | Input | The question to put to the Topic |
| Answer (`out_answer`) | Output | The Topic's answer |
| Tool (`tool_mcp`) | Tool | Wire to an Agent's Tools port so the LLM consults the Topic on demand |

## Properties

| Field | Required | Meaning |
|---|---|---|
| Topic (`topicId`) | **Yes** | Select an existing AI Topic |
| Tool Filter (`toolFilter`) | No | Exact tool names to expose to the agent. Empty allows all |

## Use cases

- **Give an agent your documents** without rebuilding retrieval in the pipeline. This is the single most
  valuable integration module.
- **Several knowledge bases in one agent** — wire an HR Topic and a technical Topic into the same Agent and
  let the model pick the right one per question.
- **As a step**, when the pipeline always needs the Topic consulted: Chat Input → AI Topic → Agent
  post-processes the answer.
- **Combine internal and external knowledge** by pairing it with [Web Search](Web-Search.md) on the same
  Agent.

## Notes

- **The Topic must be `RUNNING`.** A stopped Topic makes the tool fail at call time, not at deployment.
- **The topic ID does not survive an export/import to another installation** — the UUID will not exist
  there. Re-select the Topic after importing.
- As a tool, the model decides when to consult it. Give the Agent an instruction that mentions what the
  Topic knows, so it reaches for it in the right cases.
- The Topic's own model does the retrieval and answering, so its configuration — retrieval strategy,
  prompt, no-answer response — still applies.
