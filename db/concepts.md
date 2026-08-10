# Concepts

The engine holds two shapes of data, and one decision matters more than any other: which one you
should be using.

## Collections and documents, or graphs and nodes

**Collections** hold documents. A document is a bag of fields with an id. Use a collection when your
records are independent of each other - product descriptions, support articles, chat messages,
chunks of a PDF. This is the shape you want for classic retrieval and RAG.

**Graphs** hold nodes and edges. A node is like a document, but it can be connected to other nodes by
typed, directed, weighted edges. Use a graph when the relationships carry meaning you want to query -
who acted in what, which component depends on which, how a customer reached a purchase.

Both support vector search on their fields, so the choice is not "graph for structure, collection for
vectors". The question is only whether you need to traverse relationships. If you do not, a collection
is simpler and faster.

You can have both in one project, and query each in CyQL.

## Fields and vector fields

A field has a declared type - text, number, boolean, a date, a vector. Declaring types is what lets
the engine index them, so filters stay fast as data grows.

A **vector field** stores an embedding: an array of floats representing meaning. You can supply
vectors yourself, or name an embedding provider and let the engine compute them on write. Similarity
is measured by cosine, dot product or euclidean distance - your choice per field.

A collection or graph can carry **several** vector fields. That is how multi-modal search works: an
image embedding and a text embedding on the same record, searched independently or together.

## Metadata and filtering

Everything that is not a vector is metadata, and it is indexed for filtering. Filters combine with
vector search in a single query rather than being applied afterwards, which matters: a filter applied
after the fact would throw away most of your top-k and leave you with too few results.

```cypher
MATCH (m:Movie)
WHERE m.released > 2000 AND m.genre = 'thriller'
SIMILAR TO $query ON embedding TOP 10
RETURN m.title, score()
```

The filter narrows the candidate set; the vector search ranks what survives.

## Labels

Nodes carry one or more **labels** - `Movie`, `Person`, `Customer`. A label is a category, and a node
can hold several at once, which is how you model a thing that is genuinely two things (a `Person` who
is also an `Employee`). Match on any of them:

```cypher
MATCH (n:Person) RETURN n.name
```

Documents in collections have no labels; they are the simpler shape by design.

## Organizations, projects and roles

**Organization** is the tenant boundary. Inside it, a **project** is a namespace holding collections
and graphs. Everything you create belongs to a project, which is why the project ID appears in API
paths and in the startup banner.

A **person** gets access through a membership, which carries one of four roles. Each is a strict
superset of the one below it - broadly:

| Role | Can |
|---|---|
| VIEWER | Read and search collections, documents and graphs, and subscribe to change streams. No writes. |
| MEMBER | Everything VIEWER can, plus full CRUD on collections, documents and graphs, and graph branching. |
| ADMIN | Everything MEMBER can, plus management of projects, members, users, API keys, service identities and CDC sinks, and the audit log. |
| OWNER | Everything ADMIN can, plus organization settings. |

That is a summary rather than the full permission set - each role bundles a list of individual
permissions, and the console shows exactly which.

An **API key** works differently: it carries its own explicit set of permissions rather than a role,
so a key can be narrower than any role. That is what makes it safe to hand one to an agent - see
[MCP](mcp.md). Whatever the key holds applies uniformly, so a call through the REST API, the SDK or an
MCP tool can never reach past it.

The evaluation image seeds three logins so you can compare the roles side by side. VIEWER is not
among them; add a membership with that role in the console if you want to see a read-only person, or
create an API key holding only the read permissions.

| Login | Role |
|---|---|
| `superadmin` / `superadmin` | OWNER |
| `defaultadmin` / `defaultadmin` | ADMIN |
| `member` / `member` | MEMBER |

## Authentication

Two credential types, for two different lifetimes:

- An **API key** is long-lived and identifies a client. You get one in the startup banner.
- A **token** is short-lived, 300 seconds, and authorizes individual calls. You obtain one by
  presenting the API key.

The Java SDK and the MCP server handle this exchange for you. Over REST you do it yourself - see
[REST API](rest-api.md).

## Durability and transactions

Every statement commits atomically. There is no separate flush to worry about and no window where a
write is acknowledged but not durable.

A **transaction** groups several operations so they either all apply or none do, with rollback if
something fails partway. Storage is built into the engine, so this needs no external database.

## Graph branching

A graph can be **forked** into an isolated copy, changed there, and then merged back or discarded.
This is what makes experiments safe: reshaping a schema, testing a bulk change or trying a different
extraction pass does not touch the graph everyone else is reading.
