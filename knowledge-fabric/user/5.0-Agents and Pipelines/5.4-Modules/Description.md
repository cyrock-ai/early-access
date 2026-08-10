# Description (`DESCRIPTION`)

A free-form Markdown note rendered directly on the canvas. Pure documentation.

**Category:** Utilities · **Deployed:** **no — never sent to the agent server** · **Tool-capable:** no

## Ports

None. It connects to nothing.

## Properties

| Field | Required | Meaning |
|---|---|---|
| Content (`content`) | No | Markdown text, rendered on the canvas node |

## Use cases

- **Explaining the intent** of a non-obvious pipeline to whoever opens it next — including you, later.
- **Documenting a branch:** what the Fail path of a Guardrails module is for, and why.
- **Recording decisions** — why this model, why this iteration cap.
- **Leaving a TODO** on an unfinished section.

## Notes

- **Deliberately dropped at deployment.** The converter has no case for it, so it never reaches the agent
  server and costs nothing at runtime.
- Because it is free, use it liberally. A pipeline with a dozen modules and branching flow control is hard
  to read cold.
- No ports means it cannot accidentally affect execution.
