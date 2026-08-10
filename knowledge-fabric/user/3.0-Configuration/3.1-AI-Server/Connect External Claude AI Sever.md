# Creating an AI Server for Claude (Anthropic)

This guide describes how to connect **Anthropic's Claude API** as an AI Server in AI Knowledge
Fabric, so Claude models become selectable for Topics, GraphRAG Topics, and Agent Pipelines.

Unlike a local LM Studio or Ollama server, Claude is a **cloud provider**: there is no container to
start, no port to configure, and an API key is mandatory.

---

## 1. Prerequisites

1. An **Anthropic account** with API access — [console.anthropic.com](https://console.anthropic.com).
2. An **API key**, created under **Settings → API Keys** in the Anthropic Console. It starts with
   `sk-ant-api03-…`.
3. Credit or an active billing plan on the account. Without it, requests are rejected with a
   `credit balance too low` error.

> **Handle the key like a password.** It grants full access to your Anthropic account's API usage
> at your expense. Do not commit it to a repository and do not paste it into a chat.

---

## 2. Create the AI Server

Navigate to **Admin → AI Servers** and click **Add AI Server**.

### Fill in the form

| Field | Value | Notes |
|---|---|---|
| **Server Type** | `External (existing instance)` | Required. `Managed` is locked to Ollama and cannot deploy a cloud API |
| **Provider** | `Anthropic` | Selecting it auto-fills the host and switches the form to cloud mode |
| **Name** | e.g. `Anthropic_Claude` | Must be unique. Letters only — spaces become underscores |
| **Host** | `api.anthropic.com` | Pre-filled when you select the provider |
| **Port** | *(hidden)* | Cloud providers always use HTTPS on port 443. Any port value is ignored |
| **Default Model ID** | e.g. `claude-opus-5` | Pre-fills the model picker in the Topic wizard |
| **API Key** | `sk-ant-api03-…` | Written into the generated container configuration. This is the key the Topic and Agent containers use |
| **Management API Key Env Var** | e.g. `ANTHROPIC_API_KEY` | Optional. Name of an environment variable **on the management host** — used only by this app for reachability checks and model listing |

Click **Save**.

### The two key fields, and why there are two

This is the part most easily misunderstood:

| Field | Who uses it | What happens without it |
|---|---|---|
| **API Key** | The Topic and Agent **containers**, for the actual chat and embedding requests | Chat fails with an authentication error |
| **Management API Key Env Var** | The **management app itself**, for the reachability check and the model list | The status indicator and the Models tab do not work; chat is unaffected |

The management app resolves its key in this order: the named environment variable first, and if that
variable is unset it **falls back to the stored API Key**. So in a simple setup filling in only the
**API Key** is sufficient — reachability checks then use the stored key too.

Use the environment variable when you do not want the key readable in the app at all: set
`ANTHROPIC_API_KEY` on the management host (in the `app` service's environment in
`docker-compose.yml`, for instance) and enter only its *name* here.

### Kubernetes mode: the env var name becomes a Secret key

In Kubernetes mode the generated container environment does not contain the literal key. Instead the
value is turned into a `SecretKeyRef` against one shared Secret (`kubernetes.api-keys-secret`,
default `aiknowledgefabric-api-keys`), using the **Management API Key Env Var** name as the key
inside that Secret. Two consequences:

- Both fields must be filled in Kubernetes mode — the API Key field decides *whether* a key is
  passed at all, and the env-var name decides *which Secret key* is looked up.
- The Secret must already exist in the target namespace, or Topic and Agent pods fail to start with
  a missing-secret error that looks unrelated to the app:

```bash
kubectl create secret generic aiknowledgefabric-api-keys \
  --from-literal=ANTHROPIC_API_KEY=sk-ant-api03-...
```

In Docker mode this does not apply — the real key value is written into the generated Compose file.

---

## 3. Choosing a model

Enter the model ID as **Default Model ID**. Current Claude models:

| Model | Model ID | Context | Best for |
|---|---|---|---|
| Claude Opus 5 | `claude-opus-5` | 1M | The most capable model — complex agent tasks, tool calling, long documents |
| Claude Sonnet 5 | `claude-sonnet-5` | 1M | Best balance of speed, quality, and cost — a good default |
| Claude Haiku 4.5 | `claude-haiku-4-5` | 200K | Fastest and cheapest — simple classification and summarisation |

Notes:

- **Use the exact ID strings** — no date suffix. `claude-sonnet-5`, not `claude-sonnet-5-20260101`.
- The **Default Model ID** is only a pre-selection. Each Topic and each Pipeline node can use a
  different model.
- The placeholder text in the form shows an older example ID; use one of the IDs above instead.
- **Anthropic does not provide embedding models.** A Topic always needs an embedding model as well —
  use a local server (LM Studio, Ollama) or an OpenAI-compatible endpoint for that. See
  [Creating an AI Server for LM Studio models](Connect%20LM%20Studio%20AI%20Server.md).

---

## 4. Verify the connection

Open the new server's detail page. It has three tabs:

| Tab | Contents |
|---|---|
| **Configuration** | The values you entered — editable |
| **Models** | The models the Anthropic API reports for your account |
| **Actions** | Reachability check and deletion. Start/Stop do nothing for a cloud provider |

The reachability check performs an authenticated request against `api.anthropic.com`. Success means
the host is reachable **and** the key was accepted.

> **Pull New Model** is not offered — cloud models are not downloaded. That section only exists for
> Ollama servers.

---

## 5. Use Claude in a Topic or Pipeline

**In a Topic** (**Topics → New Topic**, model step):

- **Chat model:** `Anthropic_Claude` → `claude-opus-5` (or another ID from the table above)
- **Embedding model:** a *different* server — Anthropic offers no embedding models

**In a Pipeline** (Pipeline Designer, AGENT node): set the provider to Anthropic and enter the model
ID. Claude models handle tool calling well, which makes them a good fit for Agents with MCP tools.

Notes:

- **Every request costs money.** Unlike a local model, each chat message and each ingested document
  is billed against your Anthropic account. Watch usage under **Admin → Metrics** and in the
  Anthropic Console.
- Set a **timeout** with a real value. Cloud requests are much faster than local inference, but long
  documents and deep reasoning still take time — leaving it empty is not an option.
- The **system prompt** is assembled from the global template and the per-topic prompt and delivered
  to the container as an environment variable — identically for all providers.

---

## 6. Troubleshooting

| Symptom | Cause and fix |
|---|---|
| Server shown as unreachable, Models tab empty | No key available to the management app. Fill in the **API Key**, or set the environment variable named in **Management API Key Env Var** on the management host |
| "authentication_error" / 401 | Key wrong, revoked, or truncated when pasted. Create a new key in the Anthropic Console |
| "credit balance is too low" | No credit on the Anthropic account. Top up in the Console |
| Reachability check succeeds, but Topic chat fails with an auth error | The **API Key** field is empty — the app used the env-var key for its own check, but the container got no key. Fill in the API Key field |
| "not_found_error" naming the model | Invalid or retired model ID. Use one of the IDs in [Choosing a model](#3-choosing-a-model) — without a date suffix |
| "rate_limit_error" / 429 | Account rate limit reached. Reduce parallel Topics/Agents or request a higher tier |
| Kubernetes: Topic pods fail with a missing-secret error | The Secret named in `kubernetes.api-keys-secret` does not exist, or has no key matching the configured env-var name. See [Kubernetes mode](#kubernetes-mode-the-env-var-name-becomes-a-secret-key) |
| Document upload fails, chat works | Claude is set as the embedding model. Anthropic provides no embedding models — configure a separate server for embeddings |

---

## Related

- [Creating an AI Server for LM Studio models](Connect%20LM%20Studio%20AI%20Server.md) — a local server, and the source of the embedding model
- [Getting started local model](Getting_Started_Local_AIModel.md) — a fully local setup with no cloud costs
