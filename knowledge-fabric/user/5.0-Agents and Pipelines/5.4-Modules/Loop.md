# Loop (`LOOP`)

Re-runs a sub-graph (its Body) until a [Validator](Validator.md) inside that Body passes, or a
max-iteration cap is reached.

**Category:** Flow Control · **Deployed:** yes · **Tool-capable:** no

## Ports

| Port | Kind | Purpose |
|---|---|---|
| Input (`in_input`) | Input | The starting value |
| Body (`out_body`) | Output | The sub-graph to repeat — wire the work here |
| Done (`out_done`) | Output | **Give-up signal only** — fires when the loop never succeeded |

## Properties

| Field | Required | Meaning |
|---|---|---|
| Max Iterations (`maxIterations`) | **Yes** | Hard cap on iterations |
| Done Message (`doneMessage`) | No | Included in the Done summary. Auto-generated if omitted |

## How the exit works

This is the part most easily got wrong. **Loop has no exit condition of its own.**

- Put a **Validator inside the Body** and wire its **Pass** output to whatever should run after the loop
  succeeds. Reaching Pass ends the loop immediately.
- The Validator's **Fail** output triggers another iteration. It may be left unconnected; wire it only if
  something should run before retrying.
- **Done is not the success path.** It fires only as a give-up signal — when the Body contains no
  Validator, or Max Iterations was exhausted before one ever passed.

## Use cases

- **Draft-and-check:** Loop → Agent drafts → Validator checks → Pass exits with the good draft.
- **Retry logic:** Loop → API Call → Validator checks the response → Fail retries.
- **Refinement to a quality bar**, with Max Iterations as the cost ceiling.

## Notes

- **A Body with no Validator loops until Max Iterations, every time.** That is what the cap is for.
- Each iteration is a full run of the Body, including model calls. Set the cap deliberately.
- Wiring post-loop work to Done instead of the Validator's Pass is the classic error — it then runs only
  on failure.
