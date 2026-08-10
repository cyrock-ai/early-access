# Chat Input (`CHAT_INPUT`)

Entry point of a pipeline — provides the user's prompt as input to the flow.

**Category:** Input & Output · **Deployed:** yes · **Tool-capable:** no

## Ports

| Port | Kind | Purpose |
|---|---|---|
| Prompt (`out_prompt`) | Output | The incoming user message |

No input port — this is where a run begins.

## Properties

| Field | Required | Meaning |
|---|---|---|
| Default Prompt (`promptValue`) | No | Value sent through the output port when no prompt is supplied at runtime |

## Use cases

- **Any chat-driven pipeline.** Wire it to the first Agent or Guardrails module.
- **Testing without a user** — set a Default Prompt so the flow has something to work with.

## Notes

- A chat-driven pipeline needs this module; without it the user's message has nowhere to enter.
- A scheduled pipeline uses [Scheduler](Scheduler.md) instead, which carries its own prompt.
