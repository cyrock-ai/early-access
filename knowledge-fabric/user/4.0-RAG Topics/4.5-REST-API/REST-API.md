# REST Interface — File Upload and Chat

A Topic can be driven programmatically: upload documents and ask questions from a script, without a
browser session. This is how you automate ingestion or embed a Topic into another application.

Two hosts are involved, and confusing them is the main source of trouble:

| Host | Port | Used for |
|---|---|---|
| **Management application** | `8080` (or `APP_PORT`) | Obtaining a token — `POST /api/auth/token` |
| **The Topic itself** | Its own **RAG Service Port** | Chat, upload, file listing |

The token is issued by the management app; every other call goes **directly to the Topic's port**.
This works because the same JWT signing secret is passed into each Topic container, so the Topic
validates the token the management app issued.

---

## 1. Prerequisites

| Requirement | Notes |
|---|---|
| A user with the **`API_ACCESS`** permission | Grant it under **Admin → Roles & Permissions**. Without it the token endpoint returns `403` |
| That user's role has access to the Topic | The token's resource list is filtered by role, exactly as the UI is |
| The Topic is **`RUNNING`** | A stopped Topic has nothing listening |
| The Topic has a **RAG Service Port** | Set in step 1 of the wizard. Without it the API is not exposed on the host |

---

## 2. Obtain a token

```bash
curl -s -X POST http://localhost:8080/api/auth/token \
  -H 'Content-Type: application/json' \
  -d '{"username": "api-user", "password": "your-password"}'
```

Response:

```json
{
  "token": "eyJhbGciOiJIUzI1NiJ9...",
  "tokenType": "Bearer",
  "expiresIn": 28800,
  "username": "api-user",
  "roles": ["API"],
  "permissions": ["API_ACCESS", "TOPIC_CHAT", "TOPIC_UPLOAD", "TOPIC_VIEW"],
  "topics": [
    { "id": "3f8b2c1a-...", "name": "HR_Assistant", "status": "RUNNING" }
  ],
  "agents": [],
  "pipelines": []
}
```

The response doubles as a discovery call: `topics` lists exactly the Topics this user may use, with
their IDs and current status — so a script can find its Topic instead of hard-coding a UUID.

`expiresIn` is seconds (8 hours by default, `JWT_EXPIRY_HOURS`). Cache the token and re-request it when
it expires.

Status codes: `400` malformed body · `401` unknown user or wrong password · `403` account disabled or
locked, or missing `API_ACCESS`.

```bash
TOKEN=$(curl -s -X POST http://localhost:8080/api/auth/token \
  -H 'Content-Type: application/json' \
  -d '{"username":"api-user","password":"your-password"}' | jq -r .token)
```

---

## 3. The Topic's endpoints

All calls go to `http://<host>:<RAG Service Port>` with `Authorization: Bearer <token>`. The examples
below assume the Topic is on port `8081`.

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/chatbot/chat` | Ask a question (multipart) |
| `POST` | `/chatbot/chat/abort?memoryId=…` | Cancel an in-flight request |
| `POST` | `/embeddings/embed` | Upload and index a document (multipart) |
| `GET` | `/embeddings/file/list` | List indexed filenames |
| `GET` | `/embeddings/file/download?fileName=…` | Download an indexed file |
| `GET` | `/embeddings/chunk/list` | List all stored chunks |
| `DELETE` | `/embeddings/file?fileName=…` | Remove a file and its chunks |

---

## 4. Chat

`POST /chatbot/chat` as `multipart/form-data`:

| Part | Type | Notes |
|---|---|---|
| `memoryId` | text | Conversation identifier. Reuse it across calls to keep context; use a fresh one to start over |
| `prompt` | text | The question |
| `files` | file, repeatable | Optional ephemeral attachments |

```bash
curl -s -X POST http://localhost:8081/chatbot/chat \
  -H "Authorization: Bearer $TOKEN" \
  -F 'memoryId=session-42' \
  -F 'prompt=How many vacation days do I get after five years?'
```

```json
{
  "answer": "After five years of service you are entitled to 30 days.",
  "sourceFiles": [
    { "fileName": "hr-policy.pdf", "downloadToken": "eyJhbGciOiJIUzI1NiJ9..." }
  ]
}
```

`sourceFiles` lists the documents the answer drew on — the same information the chat UI shows as
**Sources**. Each entry pairs the filename with a `downloadToken`: a single-file key, valid for about
**10 minutes**, that stands in for the `Authorization` header on the download endpoint. Scripts that
already hold a token do not need it (see [6a](#6a-downloading-a-source-file)); it exists so a browser
can follow a plain link.

> Older Topic images return `"sourceFiles": ["hr-policy.pdf"]` — bare strings, no token. The
> management app reads both shapes; a script parsing this field should too.

### With an attachment

```bash
curl -s -X POST http://localhost:8081/chatbot/chat \
  -H "Authorization: Bearer $TOKEN" \
  -F 'memoryId=session-42' \
  -F 'prompt=Summarise the attached report.' \
  -F 'files=@quarterly-report.pdf'
```

Attachments are **ephemeral** — folded into the context for this one reply, never added to the
knowledge base. The allowed types are the Topic's configured **Chat Attachments**; a disallowed type
returns `422`.

### `memoryId` is the conversation

There is no session endpoint: the `memoryId` *is* the conversation. Reuse the same value and the Topic
keeps context (bounded by the Context Memory setting); change it and you start fresh. Use one value per
end user or per task, and make it unique enough not to collide with another script's.

### Aborting

```bash
curl -s -X POST "http://localhost:8081/chatbot/chat/abort?memoryId=session-42" \
  -H "Authorization: Bearer $TOKEN"
```

Best-effort cancellation of whatever is in flight for that `memoryId`.

### Status codes

| Code | Meaning |
|---|---|
| `200` | Answer returned |
| `401` / `403` | Token missing, expired, or lacking permission |
| `422` | Attachment rejected — type not enabled, or a binary document without Docling |
| `503` | A downstream service is unreachable (model server, vector database, Docling). **Retryable as-is** — the body explains which |

---

## 5. Upload a document

`POST /embeddings/embed` as `multipart/form-data` with a single `file` part. Unlike chat attachments,
this **permanently indexes** the document.

```bash
curl -s -X POST http://localhost:8081/embeddings/embed \
  -H "Authorization: Bearer $TOKEN" \
  -F 'file=@hr-policy.pdf'
```

Returns an empty body on success. The call is **synchronous and can take a long time** — conversion,
chunking, embedding, and optional enrichment all happen before it returns. Set a generous client
timeout; a large PDF against a local embedding model can take minutes.

Three optional query parameters go with it:

| Parameter | Default | Meaning |
|---|---|---|
| `strategy` | `RECURSIVE` | `RECURSIVE` or `SEMANTIC`. `SEMANTIC` adds one LLM call per chunk to prepend a context sentence — far slower, and it runs on the chat model |
| `url` | — | Where the file lives. **Required** when the Topic runs in `EXTERNAL` storage mode; the call returns `400` without it |
| `renamedFrom` | — | Previous filename, so the old chunks are deleted before re-embedding. The filename is the document identifier: uploading the same name again replaces it |

```bash
curl -s -X POST "http://localhost:8081/embeddings/embed?strategy=SEMANTIC" \
  -H "Authorization: Bearer $TOKEN" \
  -F 'file=@hr-policy.pdf'
```

The management app sends `strategy` from the Topic's configured chunking strategy on every upload.

`503` means a required service was unreachable — Docling, the embedding model, or an enrichment model.
Retrying the same file is safe.

### Ingesting a directory

```bash
for f in ./docs/*.pdf; do
  echo "Ingesting $f"
  curl -s -f -X POST http://localhost:8081/embeddings/embed \
    -H "Authorization: Bearer $TOKEN" \
    -F "file=@$f" \
    || echo "FAILED: $f"
done
```

Upload **sequentially**, not in parallel: each file occupies the embedding model, and concurrent
requests mostly produce timeouts. This is also what the UI does.

---

## 6. Inspecting and removing content

```bash
# Which files are indexed?
curl -s http://localhost:8081/embeddings/file/list -H "Authorization: Bearer $TOKEN"
```

```json
["hr-policy.pdf", "onboarding.md"]
```

```bash
# What can actually be retrieved? (chunk text + metadata)
curl -s http://localhost:8081/embeddings/chunk/list -H "Authorization: Bearer $TOKEN" | jq '.[0]'

# Remove a file and all its chunks
curl -s -X DELETE "http://localhost:8081/embeddings/file?fileName=hr-policy.pdf" \
  -H "Authorization: Bearer $TOKEN"
```

The delete returns `true` / `false`. The chunk list is the same diagnostic as the UI's **Chunks** tab —
the fastest way to confirm from a script that a document really is retrievable.

### 6a. Downloading a source file

```bash
# With your normal token — the usual case for a script
curl -s -o hr-policy.pdf \
  "http://localhost:8081/embeddings/file/download?fileName=hr-policy.pdf" \
  -H "Authorization: Bearer $TOKEN"

# With the downloadToken from a chat answer — no header, so this URL also works in a browser
curl -s -o hr-policy.pdf \
  "http://localhost:8081/embeddings/file/download?fileName=hr-policy.pdf&token=$DOWNLOAD_TOKEN"
```

Both parameters are URL-encoded. `200` returns the file, `302` redirects to an externally hosted one,
`404` means the filename is not indexed, and `401` means the `downloadToken` is missing, expired, or
was issued for a different file — ask the question again to mint a new one.

> A file removed here disappears from the rag-service but may still be listed in the management app's
> own **Database** tab, which tracks what was submitted rather than what is currently indexed.

---

## 7. A complete example

```bash
#!/usr/bin/env bash
set -euo pipefail

APP="http://localhost:8080"
TOPIC="http://localhost:8081"

TOKEN=$(curl -s -X POST "$APP/api/auth/token" \
  -H 'Content-Type: application/json' \
  -d '{"username":"api-user","password":"your-password"}' | jq -r .token)

# Ingest
curl -s -f -X POST "$TOPIC/embeddings/embed" \
  -H "Authorization: Bearer $TOKEN" \
  -F 'file=@hr-policy.pdf'

# Verify it is retrievable
curl -s "$TOPIC/embeddings/file/list" -H "Authorization: Bearer $TOKEN" | jq .

# Ask
curl -s -X POST "$TOPIC/chatbot/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -F 'memoryId=script-run-1' \
  -F 'prompt=How many vacation days after five years?' | jq -r '.answer, .sourceFiles[].fileName'
```

### Python

```python
import requests

APP, TOPIC = "http://localhost:8080", "http://localhost:8081"

token = requests.post(f"{APP}/api/auth/token",
                      json={"username": "api-user", "password": "your-password"},
                      timeout=30).json()["token"]
headers = {"Authorization": f"Bearer {token}"}

# Upload — allow plenty of time; embedding is synchronous
with open("hr-policy.pdf", "rb") as fh:
    requests.post(f"{TOPIC}/embeddings/embed", headers=headers,
                  files={"file": ("hr-policy.pdf", fh)}, timeout=600).raise_for_status()

# Ask
r = requests.post(f"{TOPIC}/chatbot/chat", headers=headers,
                  data={"memoryId": "py-1", "prompt": "How many vacation days after five years?"},
                  timeout=300)
r.raise_for_status()
answer = r.json()
print(answer["answer"], [s["fileName"] for s in answer["sourceFiles"]])
```

Note that `prompt` and `memoryId` are form fields, not JSON — the endpoint is multipart.

---

## 8. Reaching the Topic from elsewhere

| Caller | Base URL |
|---|---|
| Script on the Docker host | `http://localhost:<port>` |
| Another container, Docker Desktop | `http://host.docker.internal:<port>` |
| Another container, plain Linux Docker | `http://172.17.0.1:<port>` |
| Elsewhere on the network | `http://<host>:<port>` — the port must be open in the firewall |
| Inside Kubernetes | `http://topic-<topicId>.<namespace>.svc.cluster.local:8080` |

---

## 9. Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `403` from `/api/auth/token` | The user lacks `API_ACCESS`, or is disabled/locked |
| `401` from the token endpoint | Unknown username or wrong password |
| Token works, Topic calls return `401` | The token expired (8 h by default) — request a new one |
| `401` from `/embeddings/file/download` | The `downloadToken` is older than ~10 minutes or belongs to another file. Re-run the chat call, or send your normal `Authorization` header instead |
| `topics` list is empty in the token response | The user's role has no access to any Topic. Grant it under **Roles & Permissions → Resource Access** |
| Connection refused on the Topic port | The Topic is not `RUNNING`, or no RAG Service Port was configured |
| `422` on chat with an attachment | The type is not enabled for the Topic, or a binary document was sent without Docling |
| `503` | A downstream service is down — the body names it. Retryable |
| Upload times out client-side | Embedding is synchronous. Raise the client timeout (minutes for large files on local models) |
| Parallel uploads mostly fail | Upload sequentially — the embedding model handles one at a time |
| Answers ignore an uploaded file | Check `/embeddings/chunk/list`; if it is absent, ingestion failed |
| Every answer is the no-answer text | Nothing indexed, or the minimum similarity score filters everything out |
| Context is not retained between calls | Send the same `memoryId`. A new value starts a new conversation |

---

## Related

- [Chat window](../4.4-Chat/Chat-Window.md) — the same operations in the UI
- [Configuration and functions](../4.3-Configuration/Configuration.md) — attachment types, timeouts, chunk inspection
- [Roles & Permissions](../../3.0-Configuration/3.5-Users-Roles-and-Authentication/Roles-and-Permissions.md) — granting `API_ACCESS`
