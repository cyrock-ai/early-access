# Models and Their Roles

A RAG Topic needs two models: one to embed, one to answer. A GraphRAG Topic needs those same two, plus
up to **five more roles** for the graph-specific parts of the pipeline (extraction, deduplication,
community reports, routing, and HYBRID's follow-up reasoning) — seven in total — and a separate,
eighth, image-description role for ingesting pictures. This page describes what each one actually does,
so you can decide where a dedicated model is worth the extra setup and where reusing your answer model
is perfectly fine.

Every optional role works the same way in the wizard: pick a model for it, **or** tick "use the
Language Model" and let it reuse your answer model. Nothing forces you to decide immediately — every
optional role defaults to inheriting the answer model until you deliberately assign one — but you
cannot leave a role in limbo either way; picking neither is not a state the form allows for these
roles. Five of the seven quietly fall back to the answer model's own server field by field when
inherited, which is why inheriting one costs nothing extra to configure — see
[Creation step by step](../6.4-Creation/Creation-Step-by-Step.md) for exactly where each picker lives.

---

## The two required roles

### Language Model (the "answer model")

The model that actually writes what you read in chat. It is the **only** model with a real fallback
inside the container if left unconfigured (a built-in default that is not reachable from this
platform's own network, which is why the wizard makes you choose one explicitly). Every optional role
that inherits rather than getting its own model, inherits **this one**.

It does more than just answer, though — your system prompt is applied to exactly one call in the whole
pipeline, and it is always this model's: LOCAL's final answer, GLOBAL's reduce step, or HYBRID's final
synthesis, whichever strategy handled the question. The router, GLOBAL's map step, extraction, and
dedup never see your system prompt — their replies are parsed against a fixed format a persona
instruction would only break.

### Embedding Model

Turns text into vectors — for chunks (as in a RAG Topic), and additionally for **entity nodes** and
**community reports**, which is new here. Like a RAG Topic, this is the one choice you cannot revise
without consequences: changing it later leaves old and new vectors incomparable, effectively resetting
retrieval quality until everything is re-ingested and communities are recomputed.

---

## The five optional pipeline roles

### Extraction model

Reads each chunk during ingestion and pulls out the entities and relationships it describes — this is
the model call that turns "text" into "graph". Runs once per chunk, so its cost scales directly with
how much you ingest. See [how a document becomes graph](../6.1-Overview/Ingestion-Workflow.md).

### Deduplication model ("Dedup")

Also runs during ingestion, right after extraction: decides whether an entity just extracted is the
same real-world thing as one already sitting in the graph (from this document or an earlier one), and
merges them if so. This is what keeps "Acme Corp" mentioned in three different documents from becoming
three unrelated nodes — and, less obviously, what turns a merged entity into a small hub that later
traversal can reach from multiple documents at once.

### Community Report model

Writes the summary for each **community** — a cluster of densely connected entities — once graph
clustering runs. GLOBAL search answers entirely from these summaries, so this role effectively decides
how good every broad, thematic question's answer can be. Since communities are always on for every
GraphRAG Topic (there is no switch to turn them off any more), this role always matters, even if you
never explicitly think about GLOBAL questions when setting a Topic up.

### Router model

Classifies every incoming question as LOCAL, GLOBAL, or HYBRID before anything else happens. Its
**confidence threshold** — how sure it has to be before its classification is trusted — is a separate
setting you tune directly (see [Retrieval strategies](Retrieval-Strategies.md)), and that threshold
applies even when the router itself is left on the inherited answer model, since routing happens for
every Topic regardless of which model does it.

### Follow-up model

The model behind HYBRID's extra reasoning step: deciding whether to ask itself follow-up questions to
fill a gap between what LOCAL and GLOBAL each returned, and then writing the final synthesised answer.
Your system prompt applies to that final synthesis, the same way it applies to LOCAL's answer and
GLOBAL's reduce step.

---

## The eighth role: Image Describer (a different shape entirely)

Describes images encountered **during ingestion** so their content becomes searchable — configured
under **Image Handling**, not listed alongside the seven roles above, because it behaves differently in
one important way: **it has no fallback inside the container.** Every other optional role, left
inherited, quietly resolves against the answer model's own server. Image description instead needs a
full chat-completions endpoint URL or the feature is switched off entirely — there is nothing to fall
back to.

Practical consequences:

- Inheriting the Language Model for this role only works if that model is genuinely **vision-capable**.
- It cannot run on an **Anthropic** server at all — the underlying call is shaped for OpenAI-compatible
  chat-completions, and Anthropic's API does not fit it. The model picker keeps Anthropic servers out of
  this role's list for that reason, and the wizard will not let you save a topic where the inherited
  answer model is an Anthropic one.

See [File types, Docling, and image handling](../6.4-Creation/File-Types-Docling-Images.md) for how this
interacts with Docling and with chat attachments (a separate, independent setting).

---

## Where each role is configured

| Role | Wizard step | Required, or inherits Language Model? |
|---|---|---|
| Language Model | 1 — Basic Information | Required |
| Embedding Model | 1 — Basic Information | Required |
| Extraction | 2 — Data Ingestion | Inherits by default |
| Dedup | 2 — Data Ingestion | Inherits by default |
| Image Describer | 2 — Data Ingestion (Image Handling) | Off by default; no silent fallback if turned on |
| Community Report | 3 — Vector Settings | Inherits by default, but always resolved (communities cannot be turned off) |
| Router | 4 — Retrieval | Inherits by default |
| Follow-up | 4 — Retrieval | Inherits by default |

---

## Related

- [How a prompt is answered — LOCAL, GLOBAL, HYBRID](../6.1-Overview/Retrieval-Workflows.md) — the
  router, community-report, and follow-up roles in action
- [How a document becomes graph](../6.1-Overview/Ingestion-Workflow.md) — extraction and dedup in
  action
- [Retrieval strategies](Retrieval-Strategies.md) — the router's confidence threshold and every other
  tunable bound
- [Creation step by step](../6.4-Creation/Creation-Step-by-Step.md) — exactly where each picker lives
  in the wizard
