# Guardrails (`GUARDRAILS`)

Screens a value with a guardrail model and routes to **Pass** or **Fail**. Gates what enters or leaves a
pipeline.

**Category:** Flow Control · **Deployed:** yes · **Tool-capable:** no

## Ports

| Port | Kind | Purpose |
|---|---|---|
| Input (`in_value`) | Input | The text to screen |
| Pass (`out_pass`) | Output | Taken when the checks pass |
| Fail (`out_fail`) | Output | Taken when a check trips |

## Properties

| Field | Required | Meaning |
|---|---|---|
| Model Provider (`model.provider`) | **Yes** | `OLLAMA` or `OPEN_AI` — use a model suited to guardrail evaluation |
| Model Name (`model.name`) | **Yes** | e.g. `llama-guard3`, `gpt-4o-mini` |
| Model URL (`model.url`) | **Yes** | Base URL of the endpoint |
| API Key (`model.apiKey`) | No | Required for `OPEN_AI` |
| Model Timeout (`model.timeoutMinutes`) | No | Minutes, 1–120, default 20 |
| Guardrail Checks (`checks`) | **Yes** | Which checks to enforce, selected from a list |
| Custom Guardrail Description (`description`) | No | An additional rule in your own words, enforced alongside the selected checks |
| Heuristic Detection Threshold (`threshold`) | No | 0.0 lenient to 1.0 strict — default 0.5 |

## The available checks

Checks come in two categories. **Input** checks screen what the user sent; **output** checks screen what
the agent produced — so which ones make sense depends on where you place the module.

### Input checks — screen the request

| Check | What it catches |
|---|---|
| **Prompt Injection / Jailbreak Detection** | Attempts to subvert the system — *"forget your instructions and act as…"*, Base64-encoded attacks, hypothetical role-play framings |
| **PII Detection (Privacy)** | Personal data — names, e-mail addresses, phone numbers, IBANs, IP addresses — before it reaches an external LLM API |
| **Toxicity & Hate Speech** | Insults, threats, discriminatory language, sexual content |
| **Off-Topic / Scope Control** | Requests outside the agent's remit — e.g. stopping an HR bot being asked for a lasagna recipe |
| **Anomaly & Denial-of-Service Protection** | Extremely long, repetitive, or nonsensical input meant to overload the system or run up token costs |
| **Tokens / Password Detection** | Credentials, API keys, and passwords accidentally pasted into the input |

### Output checks — screen the answer

| Check | What it catches |
|---|---|
| **Groundedness / Faithfulness (RAG Check)** | Compares the answer against the provided documents — detects hallucinated facts |
| **Context Relevance** | Whether the answer actually addresses the question asked, rather than talking past it |
| **Secret / IP Protection (Leakage Prevention)** | The agent revealing internals — its own system prompt, internal keys, proprietary source |
| **Tonality & Brand Voice** | Whether the answer is polite and professional, and fits corporate identity guidelines |
| **Competitor Mention Filter** | Answers praising direct competitors or making legally questionable comparisons |

> **Match the checks to the position.** Input checks on an output gate — or the reverse — cost a model call
> and catch nothing. *Groundedness* in particular is the reason to put a Guardrails module **after** a
> RAG-backed Agent: it is the check that detects hallucination against the retrieved context.

## Use cases

- **Input gate:** Chat Input → Guardrails → Agent. Failing requests never reach the model.
- **Output gate:** Agent → Guardrails → Chat Output. The reply is screened before the user sees it.
- **Both**, the usual arrangement for anything user-facing.
- **Domain rules** via the custom description — e.g. refusing requests for individual salary figures.

## Notes

- **Wire the Fail output somewhere.** An unconnected Fail branch means blocked content silently disappears
  instead of producing a usable refusal.
- A **dedicated guardrail model** is the point — a general chat model is a poor and costlier substitute.
- Screening both directions means two extra model calls per exchange; use a small fast model.
- Tune the threshold against real traffic: too strict blocks legitimate requests, too lenient defeats the
  purpose.
- For a *logic* check rather than a safety check, use [Validator](Validator.md) — no model required.
