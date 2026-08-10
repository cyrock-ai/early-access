# Agents & Pipelines — Overview

Where a **Topic** answers questions from documents, an **Agent** *does things*: it reasons over a task,
calls tools, branches on results, and works through multiple steps to reach an outcome.

Two concepts, and the distinction matters:

| | **Pipeline** | **Agent** |
|---|---|---|
| What it is | A workflow *definition* — a graph of modules built on a canvas | A running server that *executes* pipelines |
| Where it lives | Stored in the platform's database | A container the platform starts |
| Analogy | The program | The machine running it |
| Count | Many pipelines | One Agent can host several pipelines |

You design a Pipeline in the visual editor, assign it to an Agent, and start the Agent. The Agent
registers the pipeline and exposes it for chat or scheduled execution.

---

## 1. Why not just use a Topic?

A Topic is a single round trip: question → retrieve → answer. That covers a large share of real needs
and you should prefer it when it fits.

Reach for an Agent when the task needs *more than one step*, and especially when the steps are not
known in advance:

| Need | Topic | Agent + Pipeline |
|---|---|---|
| Answer from documents | ✅ | possible, but heavier |
| Call an external API mid-answer | via MCP only | ✅ native module |
| Read a database, transform, write a file | ❌ | ✅ |
| Decide between paths based on a result | ❌ | ✅ Validator / Guardrails |
| Repeat until a result is good enough | ❌ | ✅ Loop |
| Run on a schedule with no user present | ❌ | ✅ Scheduler |
| Ask a human for approval mid-run | ❌ | ✅ Human Approval |
| Run untrusted transformation code | ❌ | ✅ Python Script |
| Combine several knowledge bases | via MCP | ✅ AI Topic modules |

Rule of thumb: **if you can describe the job as one question, use a Topic. If you have to describe it
as a procedure, use a Pipeline.**

---

## 2. Use cases

**Report generation on a schedule.** Scheduler fires nightly → SQL Database reads yesterday's figures
→ Agent writes a summary → File Write drops a Markdown report into S3.

**Ticket triage.** Chat Input receives a ticket → Agent classifies it with an AI Topic module holding
the support knowledge base → Validator branches on severity → API Call posts to the ticket system.

**Document enrichment.** File Read loads a document → Text Splitter chunks it → Iterator walks the
chunks → Embedding vectorises each → KV Store Write persists them.

**Guarded assistant.** Chat Input → Guardrails screens the request → Agent answers using MCP tools →
Guardrails screens the answer → Chat Output. Anything failing either gate is routed elsewhere.

**Quality loop.** Loop → Agent drafts → Validator checks the draft against a condition → Pass exits the
loop, Fail runs another iteration up to the cap.

**Human-in-the-loop automation.** Agent proposes an action → Human Approval pauses for a Yes/No →
approved runs the real step, rejected stops.

---

## 3. Architecture

The same orchestration model as Topics: the management application does not execute anything itself,
it generates and controls containers.

```
┌──────────────────────────────────────────────────────────────┐
│  Management application                                      │
│  · Pipeline Designer — stores the graph as JSON               │
│  · Converts the graph to the agent server's wire format       │
│  · Starts / stops the Agent container                         │
│  · Registers pipelines over HTTP                              │
└──────────────┬───────────────────────────────────────────────┘
               │ 1. start container
               ▼
┌──────────────────────────────────────────────────────────────┐
│  Agent container  (one per Agent, own host port)             │
│  · Starts with NO configuration at all                        │
│  · Waits for pipeline registrations                           │
│  · Executes pipeline runs, calls models and tools             │
└──────────────┬───────────────────────────────────────────────┘
               │ 2. POST /pipelines  (after readiness poll)
               │ 3. POST /agent/chat  {pipelineId, sessionId, prompt}
               ▼
   Models · MCP tool servers · Topics · APIs · databases · files
```

### What happens when you press Start

1. A minimal container definition is generated — **no environment variables**, because unlike a Topic
   an Agent carries no configuration in its container spec.
2. The container starts, and the platform **polls it for readiness for up to 30 seconds**.
3. Once ready, **every assigned pipeline is registered** via the agent's HTTP API.
4. The Agent is `RUNNING` and its pipelines are callable.

Two consequences worth internalising:

- **The readiness poll must succeed or nothing is registered.** An Agent that reaches `RUNNING` but has
  no pipelines almost always failed this step.
- **Configuration lives in the pipeline, not the container.** Changing a pipeline does not require
  restarting the Agent — it requires re-registering the pipeline, which the designer offers to do for
  you (*Push Now*).

### From canvas to agent — what gets deployed

The graph you draw is not sent verbatim. A converter translates it, and it **silently drops** anything
it does not recognise:

| Canvas concept | Becomes |
|---|---|
| A module with valid required config | One module in the deployed pipeline |
| A module with **missing required config** | **Dropped** — e.g. a KV Store without a collection name |
| A **Description** note | Always dropped — documentation only, never deployed |
| A normal connection | One connection entry |
| A connection into an Agent's **Tools** port | Folded into that Agent's tool list, not a connection |

> This drop-on-invalid behaviour is the single most common source of "my pipeline does nothing".
> A module missing a required field vanishes from the deployment without an error on the canvas.

---

## 4. The module palette at a glance

28 module types, grouped by role:

| Group | Modules |
|---|---|
| **Input & Output** | Chat Input · Chat Output |
| **Models & Agents** | Agent · Embedding |
| **Flow Control** | Scheduler · Iterator · Loop · Validator · Guardrails |
| **Data Sources** | API Call · SQL Database · Data Faker · KV Store Read · KV Store Write · Structured Output |
| **Files** | File Read · File Write |
| **Utilities** | Template · Text Splitter · Text Format · Python Script · Web Search · Description |
| **Human Interaction** | Human Approval |
| **Integration** | MCP Tool · SSE Tool · AI Topic · Pipeline |

Each has its own reference page under [5.4](../5.4-Modules/README.md).

### Three port kinds

| Port | Meaning |
|---|---|
| **Input** | Receives the previous module's output |
| **Output** | Passes a result to the next module |
| **Tool** | Connects *into an Agent's Tools port*, making the module callable by the LLM |

The Tool port is what makes this more than a flowchart: a module wired as a tool is not executed in
sequence — the language model decides *whether and when* to call it, and with what arguments.

**11 module types can act as tools:** MCP Tool, SSE Tool, API Call, AI Topic, SQL Database, Data Faker,
KV Store Read, KV Store Write, Pipeline, Web Search, Python Script. Anything else wired into a Tools
port is ignored.

---

## 5. Two ways a module runs

The same module can often be used either way, and the difference is fundamental:

| | **As a step** | **As a tool** |
|---|---|---|
| Wired to | Input/Output ports | An Agent's Tools port |
| Runs | Always, in order | Only if the LLM decides to call it |
| Input from | The previous module | Arguments the LLM invents |
| Needs a good `description` | No | **Yes — it is how the LLM knows when to call it** |

An API Call wired as a step fires every run with its configured URL. The same API Call wired as a tool
fires only when the model judges it useful, possibly with a URL or body it chose itself.

> **When using a module as a tool, its Description is not documentation — it is the instruction the
> model reads to decide whether to call it.** A vague description means the tool is never used, or used
> wrongly.

---

## 6. Requirements before you start

| Needed | Where |
|---|---|
| A model endpoint reachable from the Agent container | Each model-bearing module carries its own provider/name/URL |
| Docker or Kubernetes | Same as Topics |
| A free host port per Agent | Set at creation |
| `AGENT_*` and `PIPELINE_*` permissions | **Admin → Roles & Permissions** |
| License headroom | Free tier: **2 Agents, 10 Pipelines** |

> Model configuration in pipelines is **per module**, entered by hand — it does not read the registered
> AI Servers automatically. The designer offers a **Select AI Server & Model** quick-fill that copies
> values from a registered server into the module's fields, which is the practical way to avoid typos.
> Note the URL must be reachable **from inside the Agent container** (`host.docker.internal`, or
> `172.17.0.1` on plain Linux Docker) — not `localhost`.

---

## 7. Typical workflow

1. **Design the pipeline** — [5.3](../5.3-Pipelines/Pipeline-Editor.md)
2. **Create the Agent** and assign the pipeline — [5.2](../5.2-Agent-Server/Agent-Server.md)
3. **Start the Agent** — the pipeline is registered automatically
4. **Chat with it**, selecting the pipeline — [5.6](../5.6-Chat/Agent-Chat.md)
5. **Iterate**: edit the pipeline, save, and accept the *Push Now* prompt to redeploy

---

## Related

- [Agent server creation & configuration](../5.2-Agent-Server/Agent-Server.md)
- [Pipeline editor](../5.3-Pipelines/Pipeline-Editor.md)
- [Module reference](../5.4-Modules/README.md)
- [MCP tools, Topics, and nested pipelines](../5.5-Integration/Integration.md)
- [Agent chat](../5.6-Chat/Agent-Chat.md)
