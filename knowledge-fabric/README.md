<p align="center">
  <img src="assets/cyrock-ai-mark-azure.svg" alt="CYROCK.AI" width="104" height="116">
</p>

<h1 align="center">AI Knowledge Fabric</h1>

<p align="center">
  Documentation for building RAG chatbots, agents, and visual pipelines —<br>
  with container orchestration handled for you, on Docker or Kubernetes.
</p>

<a href="assets/screenshots/topic-list.jpg"><img src="assets/screenshots/topic-list.jpg" alt="The Topic list — the screen you land on after logging in" width="50%"></a>

---

## Early Access scope

Please read this first — it shapes what you may do with the software.

- **Not for production.** Early Access is licensed for evaluation and internal, non-production
  development only.
- **Do not redistribute or embed.** The software may not be embedded in anything you ship or expose
  outside your own organization.
- **Run it on a host you control.** The management app orchestrates container stacks through the
  host's Docker socket, which is equivalent to root access on that host. It is not built for shared
  multi-tenant infrastructure, and port 8080 should not face the internet directly — see
  [the installation guide](user/2.0-Installation/docker-compose-installation.md) for the reverse-proxy
  setup.
- **GraphRAG Topics are not part of this release.** The navigation menu and the feature list mention
  them, and they are described in these pages, but the feature is still in development and does not
  yet work end to end. Build with RAG Topics, Agents and Pipelines.

The full terms are in the
[CYROCK.AI Early Access End-User License Agreement](https://github.com/cyrock-ai/early-access/blob/main/LICENSE).

---

## Start here

New to the platform? **[Getting Started](user/1.0-Overview/Getting-Started.md)** is the one page that
walks the whole path — install, model provider, Docling, Topic wizard, document upload, first chat —
linking out to the detail pages at each step. Allow 30–60 minutes.

Prefer to pick the pieces yourself:

| | Page | What you get |
|---|---|---|
| 1 | [What the platform does](user/1.0-Overview/overview.md) | The concepts — Topics, Agents, Pipelines — and how they relate |
| 2 | [Install with Docker Compose](user/2.0-Installation/docker-compose-installation.md) | A running instance on a single host |
| 3 | [Getting started with a local model](user/3.0-Configuration/3.1-AI-Server/Getting_Started_Local_AIModel.md) | A chat and an embedding model the platform can reach |
| 4 | [Create your first RAG Topic](user/4.0-RAG%20Topics/4.2-Creation/Creation-Step-by-Step.md) | A document-grounded chatbot you can talk to |

---

## 1 · Overview

| Page | Contents |
|---|---|
| [Getting Started](user/1.0-Overview/Getting-Started.md) | The end-to-end walkthrough: install → models, Docling, vector DB → Topic wizard → upload and chunking → chat |
| [User Guide](user/1.0-Overview/overview.md) | The three building blocks (Topics, Agents, Pipelines), MCP tools, logs, roles, and a getting-started checklist |
| [Feature list](user/1.0-Overview/AI-Knowledge-Fabric-Features.md) | What the platform supports: RAG, agent pipelines, orchestration targets — plus GraphRAG, which is [not part of this release](#early-access-scope) |

## 2 · Installation

| Page | Contents |
|---|---|
| [Docker Compose installation](user/2.0-Installation/docker-compose-installation.md) | Single-host install: prerequisites, compose file, first login, upgrades |

## 3 · Configuration

Admin-side setup. Everything here lives under **Admin** in the navigation menu and is gated by
permissions — see [Roles & Permissions](user/3.0-Configuration/3.5-Users-Roles-and-Authentication/Roles-and-Permissions.md).

### 3.1 AI Servers — where the models come from

| Page | Contents |
|---|---|
| [Getting started with a local model](user/3.0-Configuration/3.1-AI-Server/Getting_Started_Local_AIModel.md) | A managed Ollama server the platform starts for you — the quickest path to a working model |
| [Connect LM Studio](user/3.0-Configuration/3.1-AI-Server/Connect%20LM%20Studio%20AI%20Server.md) | Registering an OpenAI-compatible endpoint you run yourself |
| [Connect Claude (Anthropic)](user/3.0-Configuration/3.1-AI-Server/Connect%20External%20Claude%20AI%20Sever.md) | Registering a cloud model provider with an API key |

### 3.2 Vector databases — where embeddings are stored

| Page | Contents |
|---|---|
| [Connect a Vector DB](user/3.0-Configuration/3.2-Vector-DB%C2%B4s/Connect-Vector-DB.md) | Qdrant, Milvus, Weaviate, CYROCK.DB — host/port/TLS, the connection test, collection naming, and when the built-in embedded store is enough |

### 3.3 – 3.6 Platform settings

| Page | Contents |
|---|---|
| [Global LLM configuration & prompt templates](user/3.0-Configuration/3.3-Global%20LLM%20configuration/Global-LLM-Configuration-and-Prompt-Templates.md) | The global system-prompt template and how each Topic's own prompt is substituted into it |
| [License](user/3.0-Configuration/3.4-License/License.md) | Free-tier limits, entering a key, and checking current usage |
| [User management](user/3.0-Configuration/3.5-Users-Roles-and-Authentication/User-Management.md) | Creating users, assigning roles, resetting passwords |
| [Roles & permissions](user/3.0-Configuration/3.5-Users-Roles-and-Authentication/Roles-and-Permissions.md) | The permission catalogue and how roles are composed from it |
| [OIDC / Single Sign-On](user/3.0-Configuration/3.5-Users-Roles-and-Authentication/OIDC-Settings.md) | SSO setup, auto-provisioning on first login, mapping OIDC groups to roles |
| [Metrics](user/3.0-Configuration/3.6-Metrics/Metrics.md) | The usage dashboard: token counts, durations, per-model and per-user breakdowns |

## 4 · RAG Topics

A **Topic** is one self-contained chatbot that answers from documents you upload.

| Page | Contents |
|---|---|
| [Overview](user/4.0-RAG%20Topics/4.1-Overview/Overview.md) | What a Topic is, its lifecycle, and what the platform provisions per Topic |
| [Creation step by step](user/4.0-RAG%20Topics/4.2-Creation/Creation-Step-by-Step.md) | The five-step wizard, field by field |
| [Configuration and functions](user/4.0-RAG%20Topics/4.3-Configuration/Configuration.md) | The detail view's tabs: configuration, data upload, MCP connections, actions and logs |
| [Chat window](user/4.0-RAG%20Topics/4.4-Chat/Chat-Window.md) | Multi-tab chat, source citations, attachments, session handling |
| [REST API](user/4.0-RAG%20Topics/4.5-REST-API/REST-API.md) | Calling upload and chat programmatically, with JWT authentication |

## 5 · Agents & Pipelines

An **Agent** executes multi-step tasks; a **Pipeline** is the visual definition of how it does so.

| Page | Contents |
|---|---|
| [Overview](user/5.0-Agents%20and%20Pipelines/5.1-Overview/Overview.md) | How Agents, Pipelines, and modules fit together |
| [Agent Server](user/5.0-Agents%20and%20Pipelines/5.2-Agent-Server/Agent-Server.md) | Creating an Agent, assigning Pipelines, start/stop lifecycle |
| [Pipeline editor](user/5.0-Agents%20and%20Pipelines/5.3-Pipelines/Pipeline-Editor.md) | The drag-and-drop canvas, wiring ports, import/export, deployment |
| [Module reference](user/5.0-Agents%20and%20Pipelines/5.4-Modules/README.md) | **All 28 palette modules**, one page each — see below |
| [Integration](user/5.0-Agents%20and%20Pipelines/5.5-Integration/Integration.md) | MCP tools, calling Topics, nested pipelines, SSE tool servers |
| [Agent chat](user/5.0-Agents%20and%20Pipelines/5.6-Chat/Agent-Chat.md) | Selecting a Pipeline per conversation and running it |

<details>
<summary><b>All 28 modules</b> — click to expand</summary>

Read [the module reference intro](user/5.0-Agents%20and%20Pipelines/5.4-Modules/README.md) first: it
explains ports, tool-capability, and the universal gotcha that a module with a missing required field
is **silently dropped** from the deployed pipeline.

**Input & Output**
[Chat Input](user/5.0-Agents%20and%20Pipelines/5.4-Modules/Chat-Input.md) ·
[Chat Output](user/5.0-Agents%20and%20Pipelines/5.4-Modules/Chat-Output.md)

**Models & Agents**
[Agent](user/5.0-Agents%20and%20Pipelines/5.4-Modules/Agent.md) ·
[Embedding](user/5.0-Agents%20and%20Pipelines/5.4-Modules/Embedding.md)

**Flow Control**
[Scheduler](user/5.0-Agents%20and%20Pipelines/5.4-Modules/Scheduler.md) ·
[Iterator](user/5.0-Agents%20and%20Pipelines/5.4-Modules/Iterator.md) ·
[Loop](user/5.0-Agents%20and%20Pipelines/5.4-Modules/Loop.md) ·
[Validator](user/5.0-Agents%20and%20Pipelines/5.4-Modules/Validator.md) ·
[Guardrails](user/5.0-Agents%20and%20Pipelines/5.4-Modules/Guardrails.md)

**Data Sources**
[API Call](user/5.0-Agents%20and%20Pipelines/5.4-Modules/API-Call.md) ·
[SQL Database](user/5.0-Agents%20and%20Pipelines/5.4-Modules/SQL-Database.md) ·
[Data Faker](user/5.0-Agents%20and%20Pipelines/5.4-Modules/Data-Faker.md) ·
[KV Store Read](user/5.0-Agents%20and%20Pipelines/5.4-Modules/KV-Store-Read.md) ·
[KV Store Write](user/5.0-Agents%20and%20Pipelines/5.4-Modules/KV-Store-Write.md) ·
[Structured Output](user/5.0-Agents%20and%20Pipelines/5.4-Modules/Structured-Output.md)

**Files**
[File Read](user/5.0-Agents%20and%20Pipelines/5.4-Modules/File-Read.md) ·
[File Write](user/5.0-Agents%20and%20Pipelines/5.4-Modules/File-Write.md)

**Utilities**
[Template](user/5.0-Agents%20and%20Pipelines/5.4-Modules/Template.md) ·
[Text Splitter](user/5.0-Agents%20and%20Pipelines/5.4-Modules/Text-Splitter.md) ·
[Text Format](user/5.0-Agents%20and%20Pipelines/5.4-Modules/Text-Format.md) ·
[Python Script](user/5.0-Agents%20and%20Pipelines/5.4-Modules/Python-Script.md) ·
[Web Search](user/5.0-Agents%20and%20Pipelines/5.4-Modules/Web-Search.md) ·
[Description](user/5.0-Agents%20and%20Pipelines/5.4-Modules/Description.md)

**Human Interaction**
[Human Approval](user/5.0-Agents%20and%20Pipelines/5.4-Modules/Human-Approval.md)

**Integration**
[MCP Tool](user/5.0-Agents%20and%20Pipelines/5.4-Modules/MCP-Tool.md) ·
[SSE Tool](user/5.0-Agents%20and%20Pipelines/5.4-Modules/SSE-Tool.md) ·
[AI Topic](user/5.0-Agents%20and%20Pipelines/5.4-Modules/AI-Topic.md) ·
[Pipeline](user/5.0-Agents%20and%20Pipelines/5.4-Modules/Pipeline.md)

</details>

---

## Finding your way around

- **Numbered folders follow the order you would set things up in** — install (2), configure the
  infrastructure (3), then build Topics (4) or Agents (5).
- **Most section pages end with a Related section** linking sideways to what you are likely to need
  next. The per-module pages mostly do not — come back to the
  [module reference](user/5.0-Agents%20and%20Pipelines/5.4-Modules/README.md) to move between those.
- **Something in the UI missing?** It is almost always a permission, not a bug — check
  [Roles & Permissions](user/3.0-Configuration/3.5-Users-Roles-and-Authentication/Roles-and-Permissions.md).

---

## Support and feedback

Early Access exists so we can hear what does and does not work for you. Bug reports, rough edges,
missing capabilities and "this was confusing" are all equally welcome.

Both channels live in the Early Access repository:

- **[Issues](https://github.com/cyrock-ai/early-access/issues)** — something is broken, or behaves
  differently from what these pages say.
- **[Discussions](https://github.com/cyrock-ai/early-access/discussions)** — questions, ideas, "how
  would I model this", and anything you are not sure is a bug.

One thing worth knowing: under the Early Access agreement, feedback you send us becomes ours to act
on freely. Both channels are also public, so please keep anything confidential to your organization
out of a report — and out of the logs you attach to one.
