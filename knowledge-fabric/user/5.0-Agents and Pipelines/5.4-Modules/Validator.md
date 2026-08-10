# Validator (`VALIDATOR`)

Screens a value and routes it to **Pass** or **Fail**. Three modes: a field condition, a Python script, or
an LLM check.

**Category:** Flow Control · **Deployed:** yes · **Tool-capable:** no

## Ports

| Port | Kind | Purpose |
|---|---|---|
| Input (`in_value`) | Input | The value to check |
| Pass (`out_pass`) | Output | Taken when the check passes |
| Fail (`out_fail`) | Output | Taken when it does not |

## Properties

The panel is **selector-driven**: choose **Validation Type** first and the remaining fields appear.

### `CONDITION` — a field comparison

| Field | Required | Meaning |
|---|---|---|
| Condition Field (`conditionField`) | **Yes** | JSON field name read from the upstream output |
| Condition Operator (`conditionOperator`) | **Yes** | `EQUALS` · `NOT_EQUALS` · `CONTAINS` · `GREATER_THAN` · `LESS_THAN` · `EXISTS` · `NOT_EXISTS` |
| Condition Value (`conditionValue`) | **Yes** | The comparison value. **Hidden for `EXISTS` / `NOT_EXISTS`**, which take no operand |

### `SCRIPT` — a Python predicate

| Field | Required | Meaning |
|---|---|---|
| Script (`script`) | **Yes** | Upstream output is available as `pipeline_input`; must print a bare boolean or a JSON object with a `pass` key |
| Requirements (`requirements`) | No | Pip specifiers. Empty skips the install step entirely |
| Timeout (`timeoutSeconds`) | No | Install + execution combined. Default 30, max 300 |

### `LLM` — a model judges

| Field | Required | Meaning |
|---|---|---|
| Model Provider / Name / URL | **Yes** | The judging model — a small fast one is usually right |
| API Key | No | Required for `OPEN_AI` |
| Model Timeout | No | Minutes, 1–120, default 20 |

## Use cases

- **The exit condition of a [Loop](Loop.md)** — its primary role. Place it inside the Body, wire Pass onward.
- **Branching on data:** `CONDITION` with `GREATER_THAN` to alert only above a threshold.
- **Quality gate:** `LLM` mode asking whether a draft meets a stated standard.
- **Anything computable:** `SCRIPT` mode for checks a simple condition cannot express.

## Notes

- **Inside a Loop, Pass is the loop's real success exit.** See [Loop](Loop.md).
- `CONDITION` reads a **JSON field**, so the upstream module must emit JSON rather than prose.
- Prefer `CONDITION` where it suffices — it costs nothing, while `LLM` mode adds a model call per check.
