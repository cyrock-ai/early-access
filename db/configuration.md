# Configuration

Everything is configured with environment variables passed to `docker run`. The defaults are chosen so
the container works with no configuration at all; this chapter covers what is worth changing.

## Storage and memory

| Variable | Default | Purpose |
|---|---|---|
| `CYROCK_DB_BOOTSTRAP_STORAGE_PATH` | `/data` | Where storage and seed state live. Mount a volume here to persist across restarts. |
| `JAVA_OPTS` | *(unset)* | JVM options, most usefully the heap ceiling. |

Three servers and the vector indices share one JVM in this image, so the heap matters more than it
would for a single service:

```bash
docker run --rm --name cyrock-db -p 8080:8080 -v cyrock-db-data:/data \
  -e JAVA_OPTS="-Xmx6g" \
  cyrockai/db:0.9.0
```

Guidance: 3 GB is fine for exploring with sample data. Give it 6-8 GB before loading hundreds of
thousands of vectors. HNSW indices are held in memory for search, so vector count and dimension drive
the requirement more than document count does. Also raise Docker's own memory limit - a `-Xmx` above
what Docker will grant just moves the failure.

## Embedding providers

Vector search needs embeddings. Either supply vectors yourself, or configure a provider and let the
engine compute them on write.

### In-process ONNX - no account, no network

**The image enables this one by default**, so vector search works out of the box: the embedding model
runs inside the container, needing no API key, no provider account and no outbound network access at
all. There is nothing to set to get it.

**It takes precedence over every other embedding provider.** That is what makes the default safe - but
it also means configuring a provider of your own is not enough on its own. To be served by another
provider, turn ONNX off in the same command:

```bash
docker run --rm --name cyrock-db -p 8080:8080 -v cyrock-db-data:/data \
  -e CYROCK_DB_EMBEDDING_ONNX_ENABLED=false \
  -e CYROCK_DB_EMBEDDING_OPENAI_API_KEY=sk-... \
  cyrockai/db:0.9.0
```

Leave ONNX on and set an OpenAI key, and ONNX still wins while the key is ignored - worth knowing
before you spend an afternoon wondering which one produced a vector.

### Hosted and self-hosted providers

| Provider | Enabled by | Default model |
|---|---|---|
| OpenAI | `CYROCK_DB_EMBEDDING_OPENAI_API_KEY` | `text-embedding-3-small` |
| Gemini | `CYROCK_DB_EMBEDDING_GEMINI_API_KEY` | `text-embedding-004` |
| Ollama | `CYROCK_DB_EMBEDDING_OLLAMA_MODEL` | *(no default - the model name is required)* |

Each also accepts `..._MODEL` and `..._TIMEOUT`. Providing the key - or, for Ollama, the model name -
is what activates the provider; there is no separate enable flag.

For Ollama, set `CYROCK_DB_EMBEDDING_OLLAMA_BASE_URL` to your Ollama host. Inside a container
`localhost` means the container itself, so reach an Ollama on your own machine as
`http://host.docker.internal:11434`.

Embedding dimensions must match the vector field's declared dimensions. The in-process ONNX model is
fixed at 384. Changing provider or model usually changes the dimension, which means re-embedding
rather than just reconfiguring.

## Language model providers

Natural-language search and the console's schema wizards use a language model. All are optional; the
engine works without one, you simply write CyQL yourself.

| Provider | Variables |
|---|---|
| Anthropic | `CYROCK_DB_INFERENCE_LLM_ANTHROPIC_API_KEY`, `..._MODEL`, `..._TEMPERATURE`, `..._TIMEOUT` |
| OpenAI | `CYROCK_DB_INFERENCE_LLM_OPENAI_API_KEY`, `..._MODEL`, `..._TEMPERATURE`, `..._TIMEOUT` |
| Gemini | `CYROCK_DB_INFERENCE_LLM_GEMINI_API_KEY`, `..._MODEL`, `..._TEMPERATURE`, `..._TIMEOUT` |
| Ollama | `CYROCK_DB_INFERENCE_LLM_OLLAMA_MODEL`, `..._BASE_URL`, `..._TEMPERATURE`, `..._TIMEOUT` |

`TEMPERATURE` takes 0 to 1 and defaults to `0.7`; `TIMEOUT` is in seconds and defaults to `60`. For
query translation, a low temperature is the better choice - you want the same question to produce the
same query.

## Reranking

A reranker re-scores an initial result set with a model that reads query and document together. It is
more accurate than vector similarity alone and slower, so it suits a final pass over a shortlist.

| Provider | Enabled by | Default model |
|---|---|---|
| Cohere | `CYROCK_DB_RERANK_COHERE_API_KEY` | `rerank-v3.5` |

`CYROCK_DB_RERANK_COHERE_MODEL` and `CYROCK_DB_RERANK_COHERE_TIMEOUT` are also accepted.

## Loading CSV

`LOAD CSV` reads only from one configured import directory, and filenames in a query are resolved
**relative to it**. Absolute paths, `..` and symlinks that escape the directory are all rejected, so a
query cannot be used to read arbitrary files from the host.

| Variable | Default | Purpose |
|---|---|---|
| `CYROCK_DB_DATA_IMPORT_PATH` | `./storage/import` | The one directory `LOAD CSV` reads from. Must not be blank. |
| `CYROCK_DB_DATA_IMPORT_BATCH_SIZE` | `5000` | Rows committed per transaction during an import. |

```bash
docker run --rm --name cyrock-db -p 8080:8080 \
  -v cyrock-db-data:/data \
  -v "$PWD/imports:/imports:ro" \
  -e CYROCK_DB_DATA_IMPORT_PATH=/imports \
  cyrockai/db:0.9.0
```

A file at `imports/movies.csv` on your machine is then referred to as just `movies.csv`:

```cypher
LOAD CSV WITH HEADERS FROM 'movies.csv' AS row
MERGE (m:Movie {title: row.title})
```

Mounting the directory read-only is a good habit - the engine only ever needs to read it.

## Telemetry

| Variable | Purpose |
|---|---|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP collector endpoint for distributed traces. |

Prometheus metrics need no configuration - see [Operations](operations.md).

## Authentication

The evaluation image seeds three in-memory logins, which is why it is not a production topology. A
general-availability deployment authenticates against your identity provider over OIDC instead. Those
variables are documented with the deployment topology they belong to, which arrives at general
availability.

## Putting it together

A configuration worth keeping for real evaluation work - offline embeddings, a sensible heap, a
persistent volume and an import directory:

```bash
docker run -d --name cyrock-db \
  -p 8080:8080 -p 8081:8081 -p 8082:8082 -p 8085:8085 -p 9090:9090 \
  -v cyrock-db-data:/data \
  -v "$PWD/imports:/imports:ro" \
  -e JAVA_OPTS="-Xmx6g" \
  -e CYROCK_DB_DATA_IMPORT_PATH=/imports \
  cyrockai/db:0.9.0
```

That needs no external service and no provider account - embeddings are in-process by default, so there
is no provider line to add.
