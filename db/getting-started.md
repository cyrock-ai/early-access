# Getting started

From nothing to a working vector search and a graph query. Budget about ten minutes, most of it
waiting for the first start.

## What you need

- **Docker**, any recent version. No JDK, no database, no search cluster.
- **4 GB of memory** available to the container. 6 GB is more comfortable if you intend to load a
  larger dataset.
- `curl` and [`jq`](https://jqlang.github.io/jq/) for the REST steps further down. Only those steps
  need them - the console, and everything you can reach from it, needs nothing but Docker.
- Ports `8080`, `8081`, `8082`, `8085` and `9090` free on your machine. If some are taken, see
  [Troubleshooting](troubleshooting.md).

The image is multi-architecture, so Apple Silicon and ARM servers run natively without emulation.

## 1. Start it

```bash
docker run --rm --name cyrock-db \
  -p 8080:8080 -p 8081:8081 -p 8082:8082 -p 8085:8085 -p 9090:9090 \
  -v cyrock-db-data:/data \
  -e JAVA_OPTS=-Xmx3g \
  cyrockai/db:0.9.0
```

Two flags worth keeping. The named volume is what makes your data survive a restart - leave `-v` off
for a throwaway run. And `--name cyrock-db` is what lets every later `docker logs cyrock-db` or
`docker exec cyrock-db ...` in this manual find your container; without it Docker assigns a random
name and those commands have nothing to match.

First start takes **30 to 60 seconds** while the engine creates its storage and seeds a tenant. You
can watch for readiness rather than guess:

```bash
docker ps    # the STATUS column shows "health: starting", then "healthy"
```

## 2. Read the startup banner

When it is ready, the container prints a banner. It holds the three things you need:

```
==========================================================
  CYROCK.AI DB UI ready at  http://localhost:8080
  Login (super-admin):  superadmin / superadmin
  Login (admin):        defaultadmin / defaultadmin
  Login (member):       member / member
  Platform REST API:    http://localhost:8081
  Platform gRPC:        localhost:9091
  Data REST API:        http://localhost:8082
  Data gRPC:            localhost:9092
  Client gRPC gateway:  localhost:9090
  MCP endpoint:         http://localhost:8085/mcp
  Project ID:           3613a31d-9829-4e01-8525-c436a34eb704
  Storage:              /data

  API key (REST / Java SDK / MCP):
    H1-q5LPq5j9_hVfpO8tIuKzIEC3Il98nPgOoh5iTJws
  Also cached in /data/bootstrap-state.properties
==========================================================
```

Keep the **API key** and the **project ID** to hand - every programmatic interface needs them. Both
are also written to `bootstrap-state.properties` in the storage directory, so you can recover them
later without restarting:

```bash
docker exec cyrock-db cat /data/bootstrap-state.properties
```

The three logins are seeded at different role levels so you can see what each role can do. They are
in-memory evaluation accounts; a real deployment authenticates against your identity provider.

## 3. Log in to the console

Open <http://localhost:8080> and sign in as `superadmin` / `superadmin`.

You land on the admin area, which shows the seeded organization, project and users. The **workbench**
is where you work with data.

## 4. Load a sample dataset

Rather than starting empty:

1. Go to **Graphs** in the workbench and press **Try Samples**.
2. Both sample graphs are pre-selected. Press **Create Selected**.

You get two graphs - a movies graph and a retail graph - with nodes, typed edges and vector
embeddings already computed. The **Collections** list has its own **Try Samples** button with three
document sets, including an FAQ knowledge base.

Loading takes a few seconds per dataset; progress is shown per template.

## 5. Your first vector search

Open the **movies** graph and switch to the query view. Vector search in CyQL reads as a clause on a
normal match:

```cypher
MATCH (m:Movie)
SIMILAR TO $query ON embedding TOP 5
RETURN m.title, m.tagline, score()
```

`$query` is the text you are searching for; the engine embeds it and ranks by similarity.
`score()` returns the similarity so you can see how confident each match is.

Try "a heist that goes wrong" and then "love across time". The results are ranked by meaning, not by
keyword overlap - nothing in the first query needs to contain the word "heist".

## 6. Your first graph query

Vector search finds a starting point; the graph tells you what surrounds it. Traversal uses arrow
patterns:

```cypher
MATCH (p:Person)-[:ACTED_IN]->(m:Movie)
WHERE m.title = 'The Matrix'
RETURN p.name
```

The two combine, which is the point of the engine - find semantically, then expand structurally:

```cypher
MATCH (m:Movie)
SIMILAR TO $query ON embedding TOP 3
MATCH (m)<-[:ACTED_IN]-(p:Person)
RETURN m.title, p.name, score()
```

[CyQL](cyql.md) covers the language properly.

## 7. Your first REST call

Each server wants a different credential, which is the thing worth getting straight up front:

- **Platform** (`8081`) - definitions and tenancy - takes the API key directly.
- **Data** (`8082`) - documents, search, queries - takes a short-lived token, valid 300 seconds, that
  you exchange the API key for.

```bash
API_KEY=<the key from the banner>
PROJECT_ID=<the project ID from the banner>

# Platform: list this project's collections, using the API key.
curl -sS "http://localhost:8081/api/v1/projects/$PROJECT_ID/collections" \
  -H "X-API-Key: $API_KEY"

# Data: exchange the key for a token, then use the token.
TOKEN=$(curl -sS -X POST http://localhost:8081/api/v1/token \
  -H "X-API-Key: $API_KEY" | jq -r .token)

curl -sS "http://localhost:8082/api/v1/collections/<collection-id>/documents" \
  -H "Authorization: Bearer $TOKEN"
```

Sending the bearer token to the platform server returns `401`; sending the raw API key to the data
server does too. [REST API](rest-api.md) explains why.

Both servers publish an interactive Swagger UI, which is the easiest way to explore the rest of the
surface - <http://localhost:8081/swagger-ui> for platform operations and
<http://localhost:8082/swagger-ui> for data operations. See [REST API](rest-api.md).

## Where to go next

- **Understand the model** - [Concepts](concepts.md) explains collections against graphs, and when to
  reach for which.
- **Use it from Java** - [Java SDK](java-sdk.md). The connection needs no port argument.
- **Connect an agent** - [MCP](mcp.md) wires Claude to the engine's 39 tools.
- **Turn on embeddings without a provider account** - [Configuration](configuration.md) covers the
  in-process ONNX embedder, which needs no API key and no network.
- **Keep it running** - [Operations](operations.md) covers volumes, backup, health and sizing.
