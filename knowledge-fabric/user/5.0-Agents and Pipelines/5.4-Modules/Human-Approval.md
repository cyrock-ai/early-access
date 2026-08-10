# Human Approval (`HUMAN_APPROVAL`)

Pauses the pipeline run to ask the user for Yes/No — or free-text — approval before continuing.

**Category:** Human Interaction · **Deployed:** yes · **Tool-capable:** **no, deliberately**

## Ports

| Port | Kind | Purpose |
|---|---|---|
| Input (`in_input`) | Input | The value the user is asked to approve |
| Output (`out_output`) | Output | A single JSON result carrying the decision and any comment |

## Properties

| Field | Required | Meaning |
|---|---|---|
| Prompt (`promptTemplate`) | No | Shown to the user. Supports a `{{input}}` placeholder for the upstream value. Auto-generated if empty |
| Allow Free-Text Response (`allowFreeTextResponse`) | No | Lets the user type a custom judgment instead of only Yes/No. On by default — the box starts **checked**; clear it to offer Yes/No only |

## Use cases

- **Gating a real side effect:** Agent drafts an email → Human Approval → API Call actually sends it.
- **Approving a destructive step** before a File Write overwrites something or a SQL statement runs.
- **Spot-checking automation** while you build confidence in a new pipeline.

## Notes

- **It returns one JSON result, it does not branch.** Unlike [Validator](Validator.md) and
  [Guardrails](Guardrails.md) there are no Pass/Fail ports — chain a **Validator** after it to branch on
  the decision.
- **Not tool-callable, by design.** A paused run cannot hand control back to a model's own tool-calling
  loop and resume later. For "only ask when it matters", put an **Agent + Validator** branch *in front* of
  the approval so it is reached only in the cases that warrant it.
- **An Agent does not need this module to ask a question.** Its reply *is* the question and the user's next
  message *is* the answer, carried by ordinary session history. This module earns its place only when it
  gates a real non-LLM step downstream.
- The run genuinely waits. A scheduled pipeline with nobody watching will sit paused.
