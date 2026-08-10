# Template (`TEMPLATE`)

Substitutes placeholders into a template string — the standard way to turn a raw upstream value into a
well-formed prompt.

**Category:** Utilities · **Deployed:** yes · **Tool-capable:** no

## Ports

| Port | Kind | Purpose |
|---|---|---|
| Input (`in_input`) | Input | The upstream value |
| Output (`out_output`) | Output | The rendered text |

## Properties

| Field | Required | Meaning |
|---|---|---|
| Template (`template`) | **Yes** | Multi-line text. `{{input}}` inserts the upstream module's raw output; `{{fieldName}}` pulls a key out of it when it is a JSON object. Unresolved placeholders are left as literal text |

## Use cases

- **Framing data as a prompt:** a SQL Database result becomes *"Summarise these figures for a manager:
  {{input}}"* before reaching an Agent.
- **Picking fields out of JSON:** `{{customerName}} ordered {{productName}}` from a structured upstream
  result.
- **Adding fixed instructions** around a variable payload, without hard-coding them into the Agent's
  system instruction.

## Notes

- **Unresolved placeholders are left as literal text, not blanked.** A typo in `{{fieldname}}` reaches the
  model verbatim — which is a useful debugging signal: if you see the braces in the output, the field name
  did not match.
- `{{fieldName}}` requires the upstream output to be a JSON object. Against plain text, only `{{input}}`
  works.
- Cheap and deterministic. Prefer it over asking a model to reformat something.
