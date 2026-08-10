# Agent (`AGENT`)

The reasoning step: an LLM with instructions and optional tool access. **The only module with a Tools
input port**, which makes it the hub of every tool-using pipeline.

**Category:** Models & Agents · **Deployed:** yes · **Tool-capable:** no (it *consumes* tools)

## Ports

| Port | Kind | Purpose |
|---|---|---|
| Prompt (`in_prompt`) | Input | The task or question |
| Tools (`tool_in`) | Input | Connect tool modules here — this is what gives the LLM callable tools |
| Response (`out_response`) | Output | The model's reply |

## Properties

| Field | Required | Meaning |
|---|---|---|
| Model Provider (`model.provider`) | **Yes** | `OLLAMA` or `OPEN_AI` |
| Model Name (`model.name`) | **Yes** | e.g. `qwen3:latest`, `gpt-4o` |
| Model URL (`model.url`) | **Yes** | Base URL of the model endpoint |
| API Key (`model.apiKey`) | No | Required for `OPEN_AI`, leave empty for `OLLAMA` |
| Model Timeout (`model.timeoutMinutes`) | No | Minutes, 1–120, defaults to 20 |
| Instruction (`instruction`) | No | System-level instruction — the agent's role and rules |
| Description (`description`) | No | Human-readable note on this agent's purpose |

**Select AI Server & Model** fills the model fields from a registered AI Server instead of typing them.

## Use cases

- **The answering step** of any conversational pipeline.
- **A tool-using worker** — wire API Call, SQL Database, Web Search, or AI Topic into its Tools port and
  let it choose.
- **Several Agents in one pipeline**, each with a different model: a cheap fast one to classify, a strong
  one for the final answer.
- **Asking the user something** — an Agent's reply *is* the question and the next user message *is* the
  answer, carried by ordinary session history. No dedicated module needed.

## Notes

- **The Model URL must resolve from inside the Agent container.** `localhost` is the container itself —
  use `host.docker.internal`, or `172.17.0.1` on plain Linux Docker.
- **Tool calling requires a capable model.** A model without tool-calling support ignores everything
  wired into its Tools port, with no error.
- Missing any of the three required model fields drops the whole module from the deployment.
- Tool connections are folded into this Agent's tool list rather than appearing as normal connections.
