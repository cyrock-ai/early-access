# File Write (`FILE_WRITE`)

Writes content to a file on the local filesystem, AWS S3, or Azure Blob Storage.

**Category:** Files · **Deployed:** yes · **Tool-capable:** yes

## Ports

| Port | Kind | Purpose |
|---|---|---|
| Content (`in_content`) | Input | The content to write |
| Tool (`tool_mcp`) | Tool | Wire to an Agent's Tools port to let the model write on demand |
| Result (`out_result`) | Output | Write outcome |

## Properties

| Field | Required | Meaning |
|---|---|---|
| Default Filename (`filename`) | No | Name including extension, used when nothing else supplies one. A tool argument or a `{"filename": …}` envelope overrides it. **Leave it empty** when the name always arrives at runtime — see [Writing a different file per run](#writing-a-different-file-per-run) |
| File Type (`fileType`) | No | MIME type or format hint |
| Description (tool use) (`description`) | No | Only used when wired as a tool — see [As a tool](#as-a-tool). Ignored as a pipeline step |
| Write Mode (`writeMode`) | No | `OVERWRITE` (default) · `APPEND` · `FAIL_IF_EXISTS` |
| Allow empty content (`allowEmptyContent`) | No | Write a zero-byte file instead of failing when the incoming content is empty. Off by default |

Plus a **selector-driven** storage section — choose **Storage Type** first, and that backend's fields
appear.

### Local Filesystem

| Field | Required | Meaning |
|---|---|---|
| Base Path (`local.basePath`) | No | Base directory, e.g. `/data/files`. The filename is appended automatically |

### AWS S3

| Field | Required | Meaning |
|---|---|---|
| Access Key ID (`aws.accessKey`) | **Yes** | AWS access key ID |
| Secret Access Key (`aws.secretKey`) | **Yes** | AWS secret access key |
| Bucket Name (`aws.bucketName`) | **Yes** | S3 bucket |
| Region (`aws.region`) | No | e.g. `eu-central-1` |
| S3 Prefix (`aws.s3Prefix`) | No | Object key prefix / folder path, e.g. `reports/` |

### Azure Blob Storage

| Field | Required | Meaning |
|---|---|---|
| Connection String (`azure.connectionString`) | **Yes** | Azure Storage connection string |
| Container Name (`azure.containerName`) | **Yes** | Blob container |
| Account Name (`azure.accountName`) | No | Storage account name — derived from the connection string when omitted |
| Blob Prefix (`azure.blobPrefix`) | No | Blob name prefix / folder path, e.g. `reports/`. Include the trailing slash. The Azure counterpart of `aws.s3Prefix` |

## Writing a different file per run

By default the incoming text **is** the content and the configured Filename is the target — so a node
inside an Iterator writes the same path every time and you keep only the last item.

To vary the target, send the module a JSON **envelope** instead of plain text:

```json
{ "filename": "chunk-3.txt", "content": "…the text to write…" }
```

A `TEMPLATE` upstream is the usual way to build it. Either key may be omitted: without `filename` the
configured one is used, without `content` an empty file is written (subject to **Allow empty content**).

| Incoming value | What happens |
|---|---|
| Plain text | Written as UTF-8 to the configured Filename — the original behaviour |
| `{"encoding":"base64","data":…}` | Decoded and written as binary — matches [File Read](File-Read.md)'s output |
| `{"filename":…,"content":…}` | `content` written to `filename`, overriding the configured one |
| Any other JSON object | Written verbatim, as before |

**The envelope filename is validated, not trusted.** Path separators and `..` are rejected, because the
name usually comes from model output. Directories stay with `local.basePath` / `aws.s3Prefix` /
`azure.blobPrefix`.

**Leave Default Filename empty** when the name always comes from the envelope. Nothing forces you to
invent a placeholder that never gets written. The trade-off is that this cannot be checked when you save
the pipeline — the graph does not reveal whether an upstream module will actually produce a `filename`.
If none does, the step fails at runtime with a message naming all three ways you could have supplied one.

## As a tool

Wired to an Agent's **Tools** port instead of its Content input, the module becomes a function the model
can call — `file_write_<filename>` — with two arguments:

| Argument | Required | Meaning |
|---|---|---|
| `content` | **Yes** | The text to write. There is no upstream output to fall back on in a tool call |
| `filename` | No | Defaults to the configured Filename. A plain name, no path separators |

**You do not write the tool description.** It is generated from the node's own configuration — the
storage backend, the resolved target, the active write mode, and which arguments are optional — so it
cannot drift out of sync with the settings. The optional **Description (tool use)** property is appended
on top, for the one thing the config cannot express: what the file *means*, e.g. *"the outbox the
operator picks up each morning"*. Leave it empty and the tool still describes itself correctly.

> **Write mode matters more here.** A model can call the tool several times in one turn. With the default
> `OVERWRITE` a second call using the same filename silently replaces the first call's output. Either
> instruct the model to vary `filename`, or set `FAIL_IF_EXISTS` so a collision surfaces as an error.

## Use cases

- **Scheduled report output:** Scheduler → SQL Database → Agent → File Write drops a Markdown report in S3.
- **Letting an agent save its own work** — wired as a tool, the model decides when a result is worth
  persisting and under which name.
- **Persisting a generated artifact** for a person or another system to pick up.
- **Audit trail** — write each run's result to a timestamped object.

## Notes

- **Pick the Storage Type first.**
- **Local Filesystem writes inside the container.** Without a mounted volume the file disappears when the
  container is replaced — for anything you need to keep, use S3 or Azure.
- **`OVERWRITE` is still the default**, so a node without a Write Mode behaves exactly as before — repeated
  runs replace the same object. Use `FAIL_IF_EXISTS` when a second write would mean something went wrong.
- **`APPEND` is only a true append on the local filesystem.** S3 objects and Azure block blobs are
  immutable, so there it is a download-concatenate-reupload: not atomic, and it transfers the whole object
  every time. For per-item output prefer a varying filename over appending in a loop.
- Cloud credentials entered here are included in an exported pipeline JSON. Scrub exports.
