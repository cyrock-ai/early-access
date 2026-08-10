# Creating an AI Server for LM Studio models

This guide describes how to register a running **LM Studio** instance as an AI Server in
AI Knowledge Fabric, so its models become selectable for Topics, GraphRAG Topics, and Agent
Pipelines.

**Prerequisite:** LM Studio is installed, the models are downloaded, and the local server is
running with **Serve on Local Network** enabled. If that is not yet the case, work through
[Getting started local model](Getting_Started_Local_AIModel.md) first.

---

## 1. Background: Managed vs. External

Every AI Server has a type that determines whether the platform controls its container:

| Server Type | Meaning |
|---|---|
| **Managed (deployed by this app)** | The platform generates a Compose file and starts/stops an **Ollama** container itself. Locked to the Ollama provider — this is the only provider it knows how to deploy. |
| **External (existing instance)** | The platform only *talks* to an already-running endpoint. Start/Stop do nothing; only reachability is checked. |

**LM Studio is always registered as External.** The platform cannot start or stop LM Studio — you
control that on your desktop.

---

## 2. Create the AI Server

Navigate to **Admin → AI Servers** and click **Add AI Server**.

### Fill in the form

| Field | Value | Notes |
|---|---|---|
| **Server Type** | `External (existing instance)` | Required — Managed would lock the provider to Ollama |
| **Provider** | `OpenAI-compatible` | LM Studio serves the OpenAI protocol |
| **Name** | e.g. `LM_Studio` | Must be unique. Letters only — spaces are converted to underscores automatically |
| **Host** | see the table below | Must be resolvable **from inside the Topic containers** |
| **Port** | `1234` | LM Studio's default server port |
| **Default Model ID** | `qwen2.5-coder-7b-instruct` | Pre-fills the model picker in the Topic wizard; the user can still choose another model |

Fields that stay **empty** for LM Studio: *API Key* and *Management API Key Env Var* — these appear
only for cloud providers (OpenAI, Anthropic) and are hidden for `OpenAI-compatible`. LM Studio
requires no authentication by default.

The **Enable WSL2 GPU passthrough** checkbox applies only to managed Ollama servers and is ignored
here.

### Choosing the Host value

This is the field that most often goes wrong. The value must be reachable from the **Topic
container**, not from your browser:

| Your setup | Host value |
|---|---|
| Management app in Docker, Docker Desktop (Windows/macOS) | `host.docker.internal` |
| Management app in Docker, plain Linux Docker | `172.17.0.1` |
| Management app started directly from the IDE / JAR, on the same machine as LM Studio | `localhost` |
| LM Studio on a different machine in the network | That machine's IP or hostname, e.g. `192.168.1.42` |

> **Do not enter a protocol or a path.** Only the bare host belongs in this field — no `http://`,
> no `/v1`. The platform builds the final URL itself and appends the `/v1` prefix automatically for
> OpenAI-compatible providers. Entering `/v1` manually produces `/v1/v1/embeddings`, and embedding
> calls fail with an empty result.

Click **Save**.

---

## 3. Verify the connection

The server detail page has three tabs:

| Tab | Contents |
|---|---|
| **Configuration** | The values you entered — editable |
| **Models** | The models the endpoint reports. For OpenAI-compatible servers this is the result of `GET /v1/models` |
| **Actions** | Reachability check and deletion. Start/Stop do nothing for an external server |

Open the **Models** tab. Both models should be listed:

- `qwen2.5-coder-7b-instruct`
- `text-embedding-nomic-embed-text-v1.5`

If the list is empty, the endpoint is not reachable — see [Troubleshooting](#5-troubleshooting).

> **Pull New Model** is only offered for Ollama servers. LM Studio models are downloaded in
> LM Studio itself, not from this UI.

---

## 4. Use the server

Once the server is saved and reachable, its models appear in every model picker:

| Where | What to select |
|---|---|
| **Topic wizard**, model step | Chat model: `LM_Studio` → `qwen2.5-coder-7b-instruct` · Embedding model: `LM_Studio` → `text-embedding-nomic-embed-text-v1.5` |
| **Topic detail → Configuration** | Per-topic override of the chat/embedding model |
| **Pipeline Designer**, AGENT node | Provider `OpenAI-compatible`, model name, and the server URL |

Notes for local inference:

- Set a **timeout** that suits local hardware. A 7B model on CPU is far slower than a cloud API —
  5 minutes or more is realistic. Never leave the timeout empty.
- Keep the **embedding model stable**. Changing it invalidates all existing vectors in a Topic and
  the documents have to be ingested again.
- The same server can be used simultaneously by several Topics and Agents. LM Studio processes the
  requests sequentially, so parallel load increases response times noticeably.

---

## 5. Troubleshooting

| Symptom | Cause and fix |
|---|---|
| Models tab is empty, server shown as unreachable | LM Studio server not running, or **Serve on Local Network** disabled. LM Studio binds to `localhost` only by default, which containers cannot reach |
| "Cannot resolve hostname" | Wrong Host value — see [Choosing the Host value](#choosing-the-host-value). On plain Linux Docker use `172.17.0.1` |
| "Connection refused" | Host resolves but nothing is listening on port 1234. Check LM Studio's port setting |
| Model list shows only one model | The other model is not loaded in LM Studio and Just-In-Time loading is disabled |
| Chat works, document upload fails | Wrong model selected as the embedding model, or the embedding model is not loaded |
| Embedding fails with an empty result | `/v1` was entered in the Host field. Remove it — the platform appends it automatically |
| A name is rejected | An AI server with that name already exists, or the name contains unsupported characters |

---

## Related

- [Getting started local model](Getting_Started_Local_AIModel.md) — installing LM Studio and loading the models
- [Creating an AI Server for Claude](Connect%20External%20Claude%20AI%20Sever.md) — the same procedure for a cloud provider
