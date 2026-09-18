# Retrieval Strategies — LOCAL, GLOBAL, HYBRID in Detail

[How a prompt is answered](../6.1-Overview/Retrieval-Workflows.md) covers what each strategy *does*.
This page covers what you can actually **tune** about each one — every bound lives on the wizard's
**Retrieval** step (step 4) unless noted otherwise, and every one of them is also editable later from
the Topic's Configuration tab.

---

## Dense vs. dense + keyword search (applies to LOCAL and GLOBAL)

Both LOCAL and GLOBAL search a **BM25 keyword index** alongside the vector (dense) search, by default,
and fuse the two result sets. This is separately switchable for LOCAL and for GLOBAL, on the wizard's
Vector Settings step (step 3).

Keyword search catches what dense/embedding search structurally misses: exact codes, IDs, names, and
short tokens that carry little semantic weight but matter enormously when they are the whole question
("what does error E204 mean"). Leave both on unless you have a specific reason not to — they default to
on for exactly this reason.

---

## LOCAL

| Setting | What it bounds | Why it matters |
|---|---|---|
| **Top-K Nodes** | How many entities the initial dense search picks as "seeds" to start traversal from | Too few seeds means a relevant entity is never reached at all |
| **Hops** | How many relationship-hops the traversal follows outward from the seeds | Higher reaches more distantly related entities, at the cost of pulling in more noise |
| **Max Subgraph Nodes** | A hard cap on the traversal's total result, after Top-K Nodes and Hops have run | Without this, a small increase in hops can explode into a huge subgraph. Left at 0, the image derives a sensible default from Top-K Nodes |
| **Top-K Chunks** | How many source chunks are pulled from the resulting subgraph into the answer prompt | **This is the setting that actually bounds how many source files an answer can cite** — the other bounds above shape the *entity* search, not the citation list directly |
| **Minimum Score** | Discards seed matches below this similarity score (0.0–1.0) | A stricter score trades recall for precision on the seed search specifically |

> **If lowering "Top-K Nodes" doesn't shrink the citation list the way you'd expect, this is why:**
> everything downstream of the seed search (traversal, then chunk gathering) has its own, separate cap.
> **Top-K Chunks** is the one to lower if an answer cites more source files than feels useful.

## GLOBAL

| Setting | What it bounds | Why it matters |
|---|---|---|
| **Top-K Reports** | How many community reports are retrieved for the question | The only size knob GLOBAL has — it returns no chunks and no source files, so there is nothing else to bound |
| **Minimum Score** | Discards community-report matches below this similarity score (0.0–1.0) | Independent of LOCAL's minimum score — a report and a chunk are different kinds of thing to score, so one threshold tuned for one is not automatically right for the other |

## HYBRID

| Setting | What it bounds | Why it matters |
|---|---|---|
| **Max Depth** | How many *rounds* of follow-up questions HYBRID can ask itself | Multiplies with Max Follow-Ups below — their product is the worst-case number of extra LOCAL lookups one chat message can trigger |
| **Max Follow-Ups** | How many follow-up questions per round | See above |
| **Follow-Up Minimum Score** | Discards a follow-up's own retrieved matches below this score | Same idea as LOCAL/GLOBAL's minimum score, scoped to the follow-up loop specifically |
| **Top-K Direct Chunks** | A small, separately bounded chunk search that runs alongside the LOCAL/GLOBAL inputs | Left at 0, the image derives its own default rather than skipping this search |
| **Direct Chunk Minimum Score** | Discards direct-chunk matches below this score | Same idea again, scoped to this one search |

> HYBRID's LOCAL half reuses the same graph-traversal behaviour as a standalone LOCAL query — it is not
> a separate, third traversal implementation.

---

## The router's confidence threshold

One more setting lives here rather than under any single strategy, because it decides *which* strategy
runs at all: the **Router Confidence Threshold** (0.00–1.00). The router always reports how confident it
is in its own LOCAL/GLOBAL classification; below this threshold, the question falls through to HYBRID
instead. There is deliberately no setting for *what* the fallback is — HYBRID is the only sensible
answer to "the router itself isn't sure", so that part is not a choice you get to make.

This threshold is sent to the container even when the Router role itself is left inheriting the
Language Model — routing happens for every question regardless of which model does the classifying, so
gating the threshold on a dedicated router model would silently drop the setting for the common case.

---

## Communities — clustering behind GLOBAL

Configured on the Vector Settings step (step 3), alongside the dense/keyword toggles:

| Setting | Meaning |
|---|---|
| **Community Resolution** | How finely the graph is split into communities. Higher values produce more, smaller communities; lower values merge entities into fewer, larger ones. `1.0` is the standard starting point; the useful range is roughly `0.5`–`2.0` |
| **Refresh Cycle** | A cron expression (with quick presets) controlling how often the whole graph is re-clustered and every community report rewritten |

Communities themselves are not switchable — every GraphRAG Topic clusters its graph and writes reports;
there is no "off" option, because a Topic without reports would still be routed GLOBAL questions by the
router and simply have nothing to answer them from. See
[Recomputing communities](../6.5-Configuration/Configuration.md#recomputing-communities) for running
this on demand rather than waiting for the cycle.

---

## Related

- [How a prompt is answered — LOCAL, GLOBAL, HYBRID](../6.1-Overview/Retrieval-Workflows.md)
- [Models and their roles](Models-and-Roles.md) — the Router, Community Report, and Follow-up models
  these settings shape
- [Glossary of terms](Glossary.md)
- [Creation step by step](../6.4-Creation/Creation-Step-by-Step.md)
