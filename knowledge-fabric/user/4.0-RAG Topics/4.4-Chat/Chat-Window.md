# Chat Window

The chat interface (`/chat_client?id=…`) is where you actually talk to a Topic. Open it by clicking the
Topic's name in the Topic list — the name is clickable once the Topic is `RUNNING`.

Requires the `TOPIC_CHAT` permission, plus access to that specific Topic through your role.

---

## 1. Layout

<a href="../../../assets/screenshots/topic-chat.jpg"><img src="../../../assets/screenshots/topic-chat.jpg" alt="The chat window: an answer with a code block, the Sources row beneath it, and the input bar" width="50%"></a>

The **Sources** row under each answer lists the documents the passages came from — that is how you
check an answer is grounded rather than invented. The paperclip below the input bar attaches a file to
a single question.

```
┌──────────────────────────────────────────────────────────┐
│ ← Topics    HR_Assistant                                 │  header
├──────────────────────────────────────────────────────────┤
│                              [History]  [+ New Chat]     │  session bar
├──────────────────────────────────────────────────────────┤
│                                                          │
│   You:  How many vacation days after five years?         │
│                                                          │
│   AI:   After five years you are entitled to 30 days.    │  conversation
│         Sources: hr-policy.pdf                           │
│                                                          │
├──────────────────────────────────────────────────────────┤
│  [Ask a question...                    ]  [Send]  [Stop] │  input
│  📎                                                      │  attachments
└──────────────────────────────────────────────────────────┘
```

---

## 2. Sending a question

Type in the input field and press **Enter** or click **Send**.

While the model works, a **Stop** button appears — click it, or press **Esc**, to abort a reply that is
going nowhere. The abort is best-effort: it asks the rag-service to cancel the in-flight request.

Local models are slow. A reply taking a minute or more on a CPU-only model is normal; if it aborts
itself, the Chat Timeout is too low (see
[LLM Overrides](../4.3-Configuration/Configuration.md#2-llm-overrides)).

---

## 3. Sources

Every answer that used retrieved documents lists **Sources:** below it, with one badge per file. The
badges are **download links** to the actual documents on the rag-service.

This is the feature that makes answers verifiable, and it is worth using: if an answer looks wrong,
open the cited file and check. No sources listed means the model answered without retrieval — either
nothing matched, or the question did not need the knowledge base.

When nothing relevant is found, you get the **No-Answer Response** configured for the Topic instead of
an invented answer.

### Download links expire

Each badge carries a one-off key to the file, good for about **10 minutes** after the answer appeared.
That is what lets the link open in a new tab without a login. Once it lapses the badge turns grey and
clicking it says so rather than opening a broken page — the same is true for sources on an older
answer you reopen from **History**, which never had a live key.

Ask the question again to get fresh links. Nothing is lost: the documents are still there, only the
short-lived key to them is gone.

---

## 4. Sessions and history

Conversations are persistent and **per user** — you see only your own.

| Control | Effect |
|---|---|
| **+ New Chat** | Starts a fresh conversation with empty context |
| **History** | Lists your previous conversations for this Topic; open one to continue it |

Opening the chat resumes your most recent session automatically.

**Start a new chat when you change subject.** Context memory feeds the last few messages back into
every request, so a long conversation that has wandered makes the model answer in terms of the earlier
topic — and costs more tokens per question. How many messages are kept is the Context Memory setting
(global default 3, overridable per Topic).

> **Closing a chat tab deletes that conversation** — its messages and the session record are removed.
> This is by design, not a bug: use History to keep conversations, and close only what you no longer
> need.

---

## 5. Attachments

The **📎** button below the input attaches files to a *single* question. Up to 10 files per message.

> **Attachments are ephemeral.** They are folded into the context for that one reply and are **never
> added to the knowledge base**. The next question no longer knows them. To add a document
> permanently, upload it on the Topic's **Data Upload** tab.

This is the right tool for "here is a document, what does it say about X?" — and the wrong tool for
building up knowledge.

Which types are accepted depends on the Topic's **Chat Attachments** setting:

| Type | Requirement |
|---|---|
| Plain text — txt, md, json, yaml, csv, source code | None |
| Binary documents — PDF, DOCX, XLSX, PPTX | Docling configured for the Topic |
| Images — JPG, PNG, GIF, WEBP, BMP, TIFF | A vision-capable chat model, confirmed in the Topic's settings |

The file picker filters by these types, but that is only a convenience — the rag-service is the real
gatekeeper and rejects a disallowed attachment with a clear message.

Attached files appear as chips before sending; **✕** removes one. After sending, the message shows the
files it carried.

### Paste and drag & drop

- **Paste** longer text directly into the input — it becomes an attachment chip rather than flooding the
  field. Handy for logs and stack traces.
- **Drag files onto the input field** to attach them.

---

## 6. Errors and retrying

When a dependency is unreachable — the model server, Docling, the vector database — the failure is
shown **in place** with a **↻ Retry this message** action. Your question is not lost: fix the cause (or
just wait, if a container was restarting) and retry the same message.

| Message | Meaning |
|---|---|
| Service unavailable / retryable error | A downstream service is down. Retry once it is back |
| Attachment rejected | The type is not enabled for this Topic, or Docling is missing for a binary document |
| Timeout | The model took longer than the Chat Timeout. Raise it, or use a faster model |

---

## 7. Getting better answers

| Symptom | What to do |
|---|---|
| Answer ignores a document you uploaded | Check the **Chunks** tab — if it is not there, it was never indexed |
| Answer is vague or generic | Ask more specifically, using terms that appear in the documents. Consider raising Top-K |
| Answer cites irrelevant files | Set a **Min. Similarity Score**, or enable **LLM reranking** |
| Answer contradicts a document | Open the cited source and check. If the chunk is garbled, conversion failed |
| Model answers from general knowledge instead of the documents | Tighten the **RAG Context Template** — that is the instruction telling it to prefer retrieved context |
| Wrong tone or too verbose | Adjust the Topic's system prompt |
| Model forgets earlier questions | Raise **Context Memory** |
| Model brings up an unrelated earlier subject | Start a **New Chat** |

---

## 8. Troubleshooting

| Symptom | Cause and fix |
|---|---|
| Topic name not clickable in the list | The Topic is not `RUNNING`. Start it first |
| "No topic found. Please open via the topic list." | The chat was opened without a valid Topic ID |
| No chat access at all | Missing `TOPIC_CHAT`, or your role lacks access to this Topic |
| Every question returns the no-answer text | Nothing is indexed, or retrieval finds nothing above the minimum score |
| A source badge is grey and says the link expired | Normal after ~10 minutes, and always so in **History**. Ask the question again |
| Sources listed but the download fails | The rag-service is no longer reachable — check the Topic's status and Logs tab |
| The 📎 button rejects everything | No attachment types are enabled in the Topic's configuration |
| Images rejected despite being enabled | The vision-capable checkbox is unticked, or the model cannot actually see images |
| A conversation disappeared | Closing a chat tab deletes it. Use **History** to keep conversations |
| Reply never arrives, Stop does nothing | The rag-service is wedged. Check the Logs tab; restart the Topic if needed |

---

## Related

- [Overview](../4.1-Overview/Overview.md)
- [Configuration and functions](../4.3-Configuration/Configuration.md) — attachments, timeouts, retrieval tuning
- [REST interface](../4.5-REST-API/REST-API.md) — the same chat from a script
