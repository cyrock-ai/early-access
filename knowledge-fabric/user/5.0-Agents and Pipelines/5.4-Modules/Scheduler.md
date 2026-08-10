# Scheduler (`SCHEDULER`)

Triggers a connected agent on a cron schedule — the way a pipeline runs with no user present.

**Category:** Flow Control · **Deployed:** yes · **Tool-capable:** no

## Ports

| Port | Kind | Purpose |
|---|---|---|
| Trigger (`out_trigger`) | Output | Fires on each scheduled tick |

No input port — the schedule is the trigger.

## Properties

| Field | Required | Meaning |
|---|---|---|
| Cron Expression (`cronExpression`) | **Yes** | Standard **6-field** cron: `sec min hour day month weekday`. `0 */5 * * * *` = every 5 minutes |
| Prompt (`prompt`) | **Yes** | The instruction sent to the agent on every trigger |
| Session Mode (`sessionMode`) | No | `NEW_EACH_RUN` (default) — fresh context each run · `PERSISTENT` — the agent keeps memory across runs |

## Use cases

- **Nightly report:** Scheduler → SQL Database → Agent → File Write.
- **Periodic monitoring:** Scheduler → API Call → Validator → Agent alerts only when a threshold is
  breached.
- **Recurring digest** with `PERSISTENT` mode, so the agent remembers what it already reported.

## Notes

- **Six fields, not five.** A five-field expression copied from crontab documentation will not behave as
  expected — the leading field here is seconds.
- `NEW_EACH_RUN` is the safer default: `PERSISTENT` grows context indefinitely and eventually costs more
  per run than the work is worth.
- The Prompt is fixed. For varying input, have the pipeline fetch it (API Call, SQL Database) rather than
  trying to parameterise the trigger.
- A scheduled pipeline needs no [Chat Input](Chat-Input.md).
