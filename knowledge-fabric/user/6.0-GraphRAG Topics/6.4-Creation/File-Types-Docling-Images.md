# File Types, Docling, and Image Handling

Step 2 of the wizard asks three closely related questions that are easy to answer carelessly and then
forget about: which file types this Topic accepts, whether Docling is involved, and what happens to
images. This page is the deep dive behind that step — why each choice matters more here than it might
look like it should.

---

## Why defining file types precisely actually matters

It is tempting to tick every box "just in case". Two concrete reasons not to:

**A file type you didn't enable is rejected before it ever reaches the container — with a clear error,
at upload time.** A file type you *did* enable but cannot actually process (Binary documents ticked with
no Docling server reachable, Images ticked with a chat model that cannot see images) is rejected later,
inside the container, as a plain **422** — after the upload has already started, with a less specific
message. Ticking only what you genuinely intend to ingest turns a confusing mid-ingestion failure into
an immediate, obvious one at the point of upload.

**Every ticked type is a standing requirement on the rest of the Topic's configuration.** Binary
documents require a Docling server for the life of the Topic; Images require a vision-capable, non-
Anthropic model for the life of the Topic. Ticking a box you don't need adds a dependency this Topic
must keep satisfying even if you never actually upload that kind of file.

The practical rule: tick exactly the types your real content is made of. If you are certain you will
only ever upload `.txt` and `.md` files, leave Binary documents and Images unticked — there is nothing to
gain from allowing more, and one fewer server this Topic depends on staying reachable.

> Structured data — JSON, XML, YAML, TOML, CSV, TSV — is **not** one of these three checkboxes. It is
> recognised by file extension and parsed into key/value records automatically, regardless of which File
> Types are ticked, with nothing to configure. See
> [the glossary](../6.2-Concepts/Glossary.md#structured-data).

---

## What role Docling plays

**Docling converts PDF, Office documents, and scanned pages into clean text before anything else in the
pipeline runs** — chunking, extraction, embedding, all of it operates on Docling's output, never on the
original binary. Without a reachable Docling server, a binary file is rejected outright; the container
has no fallback conversion path.

Two places a Docling server is required, either one enough to make the picker appear and become
mandatory:

- **Binary documents** ticked among the File Types — uploaded PDFs/Office files need converting.
- **Allow binary documents as chat attachments** ticked — a user attaching a PDF or Office file to a
  chat question needs exactly the same conversion, on the fly, before that message is answered.

Alongside the server picker, a **Timeout (min)** applies **per document, not per chunk** — a long
scanned PDF on a CPU-only Docling server is the case this actually protects against; the default
(120 minutes) is generous precisely because document conversion, unlike a model call, has no natural
upper bound on how long a single file can take.

> If you never intend to ingest binary documents, leaving Binary documents unticked means this Topic has
> **one fewer external server it depends on staying up** — worth doing even if a Docling server happens
> to be available, simply to reduce what can go wrong.

---

## Image handling: ingestion upload vs. chat attachment

These are **two independent settings**, easy to conflate because they are both about images and both sit
near each other on step 2 — but they configure entirely different moments in the Topic's life, and
ticking one does not imply the other.

| | Images found **during ingestion** | Images **attached to a chat message** |
|---|---|---|
| When it applies | A picture inside a converted document, or an image file uploaded on its own | A user attaches an image file to a question in the chat window |
| Setting | **Images found during ingestion**: Ignore, or Describe using a vision model | **Allow images as chat attachments** (its own checkbox) |
| Which model sees it | The **Image Describer Model** (its own role, possibly a dedicated one) | The Topic's own **Language Model**, directly — never the Image Describer Model |
| What happens to the result | A text description is written, embedded, and becomes part of the searchable graph, permanently | The image is handed to the Language Model just for that one turn — nothing about it is stored in the graph |
| Requirement | A vision-capable model in the Image Describer role, which cannot run on an Anthropic server | The Topic's own Language Model must itself be vision-capable — nothing in the UI verifies this automatically |

Concretely: **ticking "Images" among the File Types and choosing "Describe" only makes ingested pictures
searchable.** It says nothing about whether a user can hand the chatbot a photo mid-conversation — that
is the separate **Allow images as chat attachments** checkbox, and it works even if ingestion-time image
handling is set to **Ignore**.

### Why the Image Describer role is the odd one out

Every other optional model role (Extraction, Dedup, Community Report, Router, Follow-up) quietly falls
back to the Language Model's own server when left inherited — there is nothing extra to configure.
**Image description has no such fallback inside the container**: it needs a full chat-completions
endpoint URL, or the feature is switched off entirely. Two consequences:

- Ticking **"Use the topic's Language Model"** for this role only works if that model can genuinely read
  images — nothing checks this for you at save time beyond keeping Anthropic servers out of the picker.
- It **cannot run on an Anthropic server at all**, full stop — the underlying request is shaped for
  OpenAI-compatible chat-completions, which Anthropic's API does not accept. This is why the model picker
  for this one role hides Anthropic servers, unlike every other picker in the wizard.

See [Models and their roles](../6.2-Concepts/Models-and-Roles.md#the-eighth-role-image-describer-a-different-shape-entirely)
for the full picture of how this role differs from the other seven.

---

## Related

- [Creation step by step](Creation-Step-by-Step.md) — where each of these fields lives in the wizard
- [Models and their roles](../6.2-Concepts/Models-and-Roles.md)
- [How a document becomes graph](../6.1-Overview/Ingestion-Workflow.md)
- [Glossary of terms](../6.2-Concepts/Glossary.md)
