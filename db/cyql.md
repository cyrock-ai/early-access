# CyQL

CyQL is the query language for both collections and graphs. If you know Cypher you will be at home
immediately; the additions are vector similarity, full-text search and CSV loading as first-class
clauses rather than bolted-on functions.

## Reading data

A query matches a pattern and returns fields:

```cypher
MATCH (m:Movie)
WHERE m.released > 2000
RETURN m.title, m.released
ORDER BY m.released DESC
LIMIT 10
```

`MATCH` binds a variable to things that fit a pattern, `WHERE` filters, `RETURN` projects.
Documents in a collection are matched as label-less, edge-less nodes:

```cypher
MATCH (d)
WHERE d.category = 'billing'
RETURN d.title, d.body
```

## Vector similarity

`SIMILAR TO ... ON ... TOP` ranks matches by meaning:

```cypher
MATCH (m:Movie)
SIMILAR TO $qv ON embedding TOP 5
RETURN m.title, score(m)
```

- `$qv` is a **vector** parameter - the query embedding, supplied with the statement. `SIMILAR TO`
  does not accept text and does not embed anything for you; compute the vector with the same model
  the field was written with. [Java SDK](java-sdk.md) shows a request carrying one.
- `ON embedding` names the vector field, so a record with several vector fields can be searched on
  each independently.
- `TOP 5` is how many nearest neighbours to consider. It takes a literal, not a parameter.
- `score(m)` returns the similarity. It takes the variable it scores, so it is `score(m)` here and
  `score(d)` in a collection query - a bare `score()` will not parse.

`WHERE` comes after the clauses that belong to the `MATCH` - the similarity, the full-text search and
the edge pattern - and filters apply **before** ranking, so a narrow filter still returns a full
result set:

```cypher
MATCH (m:Movie)
SIMILAR TO $qv ON embedding TOP 10
WHERE m.released > 2000 AND m.genre = 'thriller'
RETURN m.title, m.released, score(m)
ORDER BY score(m) DESC
```

## Full-text search

`SEARCH ... ON ... TOP` does BM25 keyword scoring, which beats vector search when the user typed an
exact term - a product code, a name, an error string:

```cypher
MATCH (d)
SEARCH 'connection timeout' ON body TOP 10
RETURN d.title, score(d)
```

Running both and combining them is hybrid retrieval, and it is usually better than either alone.

## Traversal

Edges are arrow patterns. Direction and type both matter:

```cypher
MATCH (p:Person)-[:ACTED_IN]->(m:Movie)
WHERE m.title = 'The Matrix'
RETURN p.name
```

Bind the edge itself when you want its properties:

```cypher
MATCH (p:Person)-[r:RATED]->(m:Movie)
WHERE r.stars >= 4
RETURN p.name, m.title, r.stars
```

Variable-length traversal follows a chain to a bounded depth:

```cypher
MATCH (p:Person)-[:KNOWS*1..3]->(other:Person)
WHERE p.name = 'Alice'
RETURN other.name
```

Always bound the depth. An unbounded traversal on a well-connected graph will visit most of it.

## Combining vector search and traversal

This is the pattern that motivates the engine: find an entry point semantically, then use structure
to gather context.

```cypher
MATCH (m:Movie)
SIMILAR TO $qv ON embedding TOP 3 -[:ACTED_IN]-(p:Person)
RETURN m.title, p.name, score(m)
```

Retrieval that includes a record's neighbourhood gives a language model considerably more to work
with than the record alone.

## Paging

`SKIP` (or `OFFSET`, which means the same thing) with `LIMIT`:

```cypher
MATCH (m:Movie)
RETURN m.title
ORDER BY m.title
SKIP 20 LIMIT 10
```

Always `ORDER BY` when paging. Without a sort, "page 3" is not a stable idea.

## Writing data

```cypher
CREATE (m:Movie {title: 'Arrival', released: 2016})
```

`MERGE` creates only if nothing matches, which makes an import safe to re-run:

```cypher
MERGE (p:Person {name: 'Denis Villeneuve'})
```

Update and delete:

```cypher
MATCH (m:Movie) WHERE m.title = 'Arrival'
SET m.tagline = 'Why are they here?'

MATCH (m:Movie) WHERE m.released < 1950
DELETE m
```

An edge is written as part of a pattern, so one statement creates both ends and the edge between
them:

```cypher
CREATE (p:Person {name: 'Denis Villeneuve'})-[:DIRECTED]->(m:Movie {title: 'Arrival'})
```

A query has a single `MATCH`, and its pattern starts from one node and may extend through one edge to
another - `(a)-[:R]->(b)`, which is how the traversal examples above reach a second node. What it
cannot do is bind two unconnected patterns, so matching two existing nodes and joining them is not
expressible; use the edge endpoint on the REST API or `addEdge` in the SDK for that.

## Loading CSV

`LOAD CSV` bulk-imports without writing a client:

```cypher
LOAD CSV WITH HEADERS FROM 'movies.csv' AS row
MERGE (m:Movie {title: row.title})
ON CREATE SET m.released = toInteger(row.released)
```

Each row runs the statement that follows. `WITH HEADERS` uses the first line for column names, so
`row.title` refers to a column rather than a position.

The filename is resolved relative to the server's configured import directory, and cannot escape it -
absolute paths and `..` are rejected. That is deliberate: it stops a query being used to read
arbitrary files from the host. See [Configuration](configuration.md) for the directory setting.

## Schema

Collections and graphs can be created and changed in CyQL:

```cypher
CREATE COLLECTION articles (
  VECTOR vector DIMENSION 384 SIMILARITY COSINE,
  METADATA title STRING CARDINALITY HIGH,
  METADATA body STRING CARDINALITY HIGH FULLTEXT
)

SHOW COLLECTIONS

DESCRIBE COLLECTION articles
```

Those are three separate statements; send them one at a time. A collection needs at least one
vector field, and `CARDINALITY` picks the index: `HIGH` for values that are nearly unique per
record, `LOW` for a small repeated set. `FULLTEXT` is what makes a field usable with `SEARCH`.

`ALTER COLLECTION` adds fields and indexes to something that already holds data.

Schema statements are project-scoped, so they go to the project statements endpoint on the platform
port rather than to a collection on the data port - see [REST API](rest-api.md) for which port takes
which credential.

## Parameters

Pass values as named parameters rather than pasting them into the query text. It avoids quoting
problems, and it lets the engine reuse a query plan:

```cypher
MATCH (m:Movie)
SIMILAR TO $qv ON embedding TOP 10
WHERE m.released > $since
RETURN m.title, score(m)
```

Every interface accepts a parameter map alongside the statement, and vector parameters are passed
separately from scalar ones. `TOP` is the exception: it takes a literal.

## Read-only against read-write

Some entry points only accept reads, which is a safety feature rather than a limitation - it is how
you give an agent or a reporting tool query access without also granting it the ability to delete.
The MCP tool catalogue splits along the same line; see [MCP](mcp.md).
