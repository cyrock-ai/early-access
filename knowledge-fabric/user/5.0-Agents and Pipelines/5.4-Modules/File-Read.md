# File Read (`FILE_READ`)

Reads a file from the local filesystem, AWS S3, or Azure Blob Storage.

**Category:** Files · **Deployed:** yes · **Tool-capable:** yes

## Ports

| Port | Kind | Purpose |
|---|---|---|
| Trigger (`in_trigger`) | Input | Anything arriving here triggers the read |
| Tool (`tool_mcp`) | Tool | Wire to an Agent's Tools port to let the model read on demand |
| Content (`out_content`) | Output | The file's content |

## Properties

| Field | Required | Meaning |
|---|---|---|
| Default Filename (`filename`) | No | Name including extension, used when nothing else supplies one. A tool argument overrides it. **Leave it empty** when the model always names the file — see [As a tool](#as-a-tool) |
| File Type (`fileType`) | No | MIME type or format hint, e.g. `text/plain`, `application/json` |
| Description (tool use) (`description`) | No | Only used when wired as a tool — see [As a tool](#as-a-tool). Ignored as a pipeline step |

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
| S3 Prefix (`aws.s3Prefix`) | No | Object key prefix / folder path, e.g. `uploads/` |

### Azure Blob Storage

| Field | Required | Meaning |
|---|---|---|
| Connection String (`azure.connectionString`) | **Yes** | Azure Storage connection string |
| Container Name (`azure.containerName`) | **Yes** | Blob container |
| Account Name (`azure.accountName`) | No | Storage account name — derived from the connection string when omitted |
| Blob Prefix (`azure.blobPrefix`) | No | Blob name prefix / folder path, e.g. `reports/`. Include the trailing slash. The Azure counterpart of `aws.s3Prefix` |

## As a tool

Wired to an Agent's **Tools** port instead of its Trigger input, the module becomes a function the model
can call — `file_read_<filename>` — with one optional argument:

| Argument | Required | Meaning |
|---|---|---|
| `filename` | No | Defaults to the configured Filename, so the tool is callable with **no arguments at all**. A plain name, no path separators |

**You do not write the tool description.** It is generated from the node's own configuration — the
storage backend, the resolved target, and how text versus binary content comes back — so it cannot drift
out of sync with the settings. The optional **Description (tool use)** property is appended on top, for
the one thing the config cannot express: what the file *means*, e.g. *"the current price list"*. That is
what makes the model reach for it at the right moment; without it the model knows *how* to call the tool
but not *why*.

Because `filename` is optional, one node covers both shapes: a fixed reference document (model calls
with no arguments) and a directory the model can pick from (model supplies the name).

## Use cases

- **Ingestion chain:** File Read → Text Splitter → Iterator → Embedding.
- **A prompt template from S3** — Storage Type `AWS S3`, filename `system-prompt.txt`, wired from a
  Scheduler trigger. The prompt becomes editable without touching the pipeline.
- **Local reference data:** Base Path `/data/reference`, filename `product-catalog.csv`, Content wired to an
  Agent that answers product questions — full catalog as context, no database needed.
- **Picking up a dropped file** on a schedule: Scheduler → File Read → Agent.

## Notes

- **Pick the Storage Type first** — the path and credential fields do not exist until you do.
- **Local Filesystem means inside the Agent container**, not your workstation. The path must exist in the
  container, which usually means a mounted volume.
- The Trigger input is a trigger, not the filename — the filename comes from the property.
- Not tool-callable. An agent cannot decide to read a file; the read is always a fixed step.
