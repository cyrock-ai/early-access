# REST API

Two REST surfaces, on two ports, split by concern:

| Port | Surface | Swagger UI |
|---|---|---|
| `8081` | Platform - organizations, projects, users, API keys, tokens | <http://localhost:8081/swagger-ui> |
| `8082` | Data - collections, documents, graphs, nodes, edges, search | <http://localhost:8082/swagger-ui> |

The Swagger UI on a running container is the authoritative reference for every endpoint, parameter
and response shape. This chapter covers the part Swagger cannot explain on its own: how
authentication works.

## What lives where

The split is not arbitrary, and it decides which credential you need:

- **Platform (8081)** owns *definitions and tenancy* - creating and listing collections and graphs,
  projects, organizations, users, API keys, CDC sinks, the audit log.
- **Data (8082)** owns *the data itself* - documents, nodes, edges, search, transactions, CyQL
  statements.

So a collection is created on `8081` and then filled with documents on `8082`. Surprising the first
time; it follows from the data server holding no user database of its own.

## The auth model

Two credentials, and - this is the part worth reading carefully - **each server wants a different
one**:

| Server | Credential | Header |
|---|---|---|
| Platform (8081) | The API key itself | `X-API-Key: <api-key>` |
| Data (8082) | A short-lived token | `Authorization: Bearer <token>` |

The API key is long-lived and comes from the startup banner. The token lasts **300 seconds** and is
obtained by presenting the API key to the platform server. The data server accepts only the token: it
authorizes purely from the token's claims, which is what lets it scale without a user database.

Sending a bearer token to the platform server returns `401`, and it is an easy hour to lose. Use the
API key there.

### Exchange the key for a token

```bash
API_KEY=<the key from the startup banner>

curl -sS -X POST http://localhost:8081/api/v1/token \
  -H "X-API-Key: $API_KEY"
```

```json
{
  "token": "eyJhbGciOiJIUzI1NiJ9...",
  "expiresIn": 300
}
```

Note the exchange happens on the **platform** port even when your work is entirely on the data port.

### Use the token

```bash
TOKEN=$(curl -sS -X POST http://localhost:8081/api/v1/token \
  -H "X-API-Key: $API_KEY" | jq -r .token)

curl -sS "http://localhost:8082/api/v1/collections/$COLLECTION_ID/documents" \
  -H "Authorization: Bearer $TOKEN"
```

### Refreshing

Tokens are not renewed in place; you exchange again. In a long-running client, exchange when a call
returns 401 rather than tracking the clock - it is one code path instead of two, and it handles a
restarted server for free. The [Java SDK](java-sdk.md) does this for you.

## A short walkthrough

Everything below assumes `$TOKEN` and the project ID from the banner.

### Create a collection

On the **platform** port, with the **API key** - and note the fields are split into `vectorFields` and
`metadataFields` rather than one list:

```bash
curl -sS -X POST "http://localhost:8081/api/v1/projects/$PROJECT_ID/collections" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
        "name": "articles",
        "vectorFields": [
          {"name": "vector", "dimension": 384, "similarityFunction": "COSINE"}
        ],
        "metadataFields": [
          {"name": "title", "type": "STRING", "cardinality": "HIGH"},
          {"name": "body",  "type": "STRING", "cardinality": "HIGH", "fulltext": true},
          {"name": "topic", "type": "STRING", "cardinality": "LOW"}
        ]
      }'
```

**At least one vector field is required** - a collection without one is rejected with `400`.

`cardinality` picks the indexing strategy: `HIGH` for values that are nearly unique per record,
`LOW` for a small set of repeated values like a category or status. `fulltext: true` adds BM25 indexing
so the field can be used with `SEARCH`.

The response carries the collection id used in every data-plane path below.

Creating definitions is often easier in the console or through the [Java SDK](java-sdk.md), which takes
typed builders rather than hand-written JSON. The Swagger UI on `8081` has the exact schema for every
field option.

### Search

On the **data** port, with the **token**:

```bash
curl -sS -X POST "http://localhost:8082/api/v1/collections/$COLLECTION_ID/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
        "vectorField": "vector",
        "vector": [0.01, 0.02, 0.03],
        "maxResults": 5,
        "filter": "topic = \"accounts\""
      }'
```

```json
{"matches": []}
```

The `vector` array above is shortened to keep the example readable. It must hold **exactly** as many
numbers as the field's dimension - 384 for the collection created earlier - and a shorter one is
rejected with a `400` saying so. In practice you are pasting an embedding from your model rather than
typing numbers, so this is usually a matter of piping one in rather than composing it by hand.

The filter narrows candidates before ranking, so a restrictive filter still yields a full
`maxResults`.

`maxResults` is optional - leave it out and you get 10. That holds for the multi-, hybrid- and
natural-language searches too. Optional fields generally can be left out rather than spelled with a
placeholder value: the exceptions are the few where an omitted value would be destructive or meaningless,
such as `maxAgeHours` on `POST /api/v1/graphs/{id}/decay`, which is required because a zero age would prune
the whole graph. Those answer with a `400` naming the field.

### Documents and CyQL statements

The remaining data-plane endpoints follow the same pattern - data port, bearer token:

| Endpoint | Purpose |
|---|---|
| `POST /api/v1/collections/{id}/documents` | Upsert a document (`metadata`, `vectors`, optional `externalKey` and `id`) |
| `POST /api/v1/collections/{id}/documents/batch` | Upsert many at once |
| `GET /api/v1/collections/{id}/documents` | List documents |
| `POST /api/v1/collections/{id}/hybrid-search` | BM25 and vector fused |
| `POST /api/v1/collections/{id}/statements` | Run a [CyQL](cyql.md) statement (`statement`, `parameters`) |
| `POST /api/v1/collections/{id}/transaction` | Several operations, applied atomically |
| `POST /api/v1/collections/{id}/nl-search` | Natural-language search, if a language model is configured |

Graphs mirror this under `/api/v1/graphs/{id}/...` with nodes, edges, traversal, context windows and the
Graph RAG operations.

Omitting `id` on an upsert has the store assign one, which is what you want for a new document; the
assigned id comes back in the response. Giving an `id` replaces that document - including `id: 0`, which is
a real document rather than a "no id" marker, so leave the field out rather than sending a zero.

**Take the exact request bodies from the Swagger UI** at <http://localhost:8082/swagger-ui>, or from the
OpenAPI document it is generated from:

```bash
curl -sS http://localhost:8082/api-docs > openapi.json
```

That is generated from the running server, so it cannot drift the way a hand-copied example in a manual
can. When a body is rejected the response usually names the field - see [Errors](#errors) below. For
anything beyond a quick curl, the [Java SDK](java-sdk.md) is less work - it takes typed builders
instead of JSON.

## Errors

Standard HTTP status codes, with an [RFC 7807](https://www.rfc-editor.org/rfc/rfc7807) problem
document as the body:

| Status | Means |
|---|---|
| `400` | The request is malformed - a bad filter, a vector of the wrong length, a field that does not bind. |
| `401` | Missing or invalid credential. On the data port, usually an expired token. |
| `403` | Authenticated, but this role may not do this. |
| `404` | No such collection, graph or document. |
| `409` | A conflict, such as a uniqueness violation. |

When a `400` comes from a field that would not bind, `detail` names the property at fault, so you rarely
need to bisect a payload:

```json
{
  "title": "Bad Request",
  "status": 400,
  "detail": "vectorFields[0].dimension: Cannot deserialize value of type `java.lang.Integer` from String \"lots\": not a valid `java.lang.Integer` value",
  "instance": "/api/v1/projects/.../collections"
}
```

Rejected enum values list what is accepted, which is quicker than looking them up:

```
similarityFunction: ... not one of the values accepted for Enum class: [COSINE, EUCLIDEAN, DOT_PRODUCT]
```

Not every `400` can be attributed to a single field. A request the server parsed but rejected on its
merits carries the reason without a property - `At least one vector field is required` - and a body that
is not valid JSON at all reports the parse position instead, since there is no field to point at.

A `401` on a call that worked a few minutes ago is almost always the 300-second token expiry. Server-side
failures return a `500` without a `detail` - if you hit one, the container log has the reason.

## Health and metrics

Unauthenticated on purpose, so a load balancer or `docker` healthcheck can reach them:

```bash
curl http://localhost:8082/actuator/health
curl http://localhost:8082/actuator/prometheus
```

See [Operations](operations.md).
