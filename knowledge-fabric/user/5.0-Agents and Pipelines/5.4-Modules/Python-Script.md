# Python Script (`PYTHON_SCRIPT`)

Runs a Python script in a sandboxed container and forwards its JSON output downstream. The escape hatch
for anything no other module covers.

**Category:** Utilities · **Deployed:** yes · **Tool-capable:** **yes**

## Ports

| Port | Kind | Purpose |
|---|---|---|
| Input (`in_input`) | Input | Available to the script as `pipeline_input` |
| Result (`out_result`) | Output | The script's JSON output |
| Tool (`tool_mcp`) | Tool | Wire to an Agent's Tools port so the LLM can invoke it |

## Properties

| Field | Required | Meaning |
|---|---|---|
| Script (`script`) | **Yes** | Python source. The upstream output (or the tool call arguments) is available as `pipeline_input`; **the last printed value must be JSON** |
| Requirements (`requirements`) | No | Pip specifiers, e.g. `requests==2.32.3`. Empty **skips the install step entirely** |
| Timeout (`timeoutSeconds`) | No | Install **and** execution combined. Default 30, maximum 300 |
| Description (`description`) | No, but **required in practice as a tool** | Tells the LLM what the script does and when to call it |

## Use cases

- **Deterministic computation** — maths, date arithmetic, or statistics that a model would get subtly wrong.
- **Reshaping data** between two modules that disagree on format.
- **Custom validation logic**, though [Validator](Validator.md) in `SCRIPT` mode is the better fit for a
  pure Pass/Fail decision.
- **As a tool**, giving an agent a precise calculator instead of letting it do arithmetic in prose.

## Notes

- **Only the standard library is available unless you list requirements.** Importing `requests` without
  declaring it fails at runtime.
- **The timeout covers install plus execution.** A heavy requirements list can consume the whole budget
  before your code runs — leave Requirements empty when you do not need it, which skips installing
  altogether.
- **The last printed value must be JSON.** Printing bare text breaks the downstream contract.
- A model-invoked script runs with arguments the model chose. Validate inputs inside the script rather than
  trusting them.
