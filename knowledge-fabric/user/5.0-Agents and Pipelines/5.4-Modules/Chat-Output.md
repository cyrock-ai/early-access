# Chat Output (`CHAT_OUTPUT`)

Exit point — whatever reaches it is returned to the caller as the pipeline's result.

**Category:** Input & Output · **Deployed:** yes · **Tool-capable:** no

## Ports

| Port | Kind | Purpose |
|---|---|---|
| Output Value (`in_output_value`) | Input | The value to return |

## Properties

| Field | Required | Meaning |
|---|---|---|
| Output Value (`outputValue`) | No | Pre-filled value, overridden at runtime by whatever arrives on the input port |

## Use cases

- **Ending any chat-facing pipeline** — the last module in the visible chain.
- **Returning a fixed confirmation** for a pipeline whose real work is a side effect (a file written, a
  record updated) and whose reply is only an acknowledgement.

## Notes

- **If chat shows nothing, check this module first**: either it is missing, or the chain leading to it is
  broken upstream.
- Only what reaches Chat Output is returned. Intermediate results appear in the Agent's log, not to the
  caller.
