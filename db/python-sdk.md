# Python SDK

A gRPC client for Python. It handles the token exchange, connection management and retries, so your
code deals in collections and documents rather than in headers.

> **Early Access scope.** The SDK is licensed for evaluation and internal prototyping. It may not be
> embedded in anything you distribute or expose outside your own organization. Build with it freely
> inside your own walls; [start a discussion](https://github.com/cyrock-ai/early-access/discussions)
> before it becomes part of something you ship.

Every operation comes in two forms: `CyrockDbClient` blocks, and `AsyncCyrockDbClient` is awaited.
They are the same API - see [Calling asynchronously](#calling-asynchronously).

## Installing

The Early Access package is not on PyPI. Install it from the early-access repository, pinned to a
tag, which needs a GitHub account with access to that repository:

```bash
pip install "git+https://github.com/cyrock-ai/early-access@db-v0.9.1#subdirectory=db-client-python"
```

Both names carry the `db-` prefix because that repository holds more than one product; the tag for a
given release is always `db-v` followed by the version. Pin a tag rather than a branch, so an install
is reproducible. Python 3.10 or later.

In a requirements file, the same line works with the tag pinned:

```
cyrock-db @ git+https://github.com/cyrock-ai/early-access@db-v0.9.1#subdirectory=db-client-python
```

If your environment authenticates to GitHub over HTTPS with a token, the usual `git` credential
helper applies - `pip` shells out to `git`, so whatever works for `git clone` works here.

## Protobuf compatibility

The generated gRPC modules are compiled against Protobuf **6.31.1** and `grpcio` **1.74.0**, and both
rules run one way only: the runtime on your machine may be newer than the version the modules were
generated against, never older. An older one refuses to load them.

> The Java SDK documents its floor as Protobuf **4.31.1**. That is the *same* Protobuf release -
> 31.1 - not an older one. Protobuf versions its language runtimes on separate major lines:
> `protobuf-java` 4.31.1 and the `protobuf` package on PyPI 6.31.1 ship from one release. Python has
> no 4.31.1 at all, so do not copy the Java number into a requirements file - it cannot resolve.

Both SDKs are generated from the same release, so a Python and a JVM application talking to the same
server are on the same wire format.

## Connecting

```python
from cyrock_db import CyrockDbClient

with CyrockDbClient(host="localhost", port=9090, api_key="your-api-key") as client:
    ...
```

The client is a context manager; `close()` works too if that suits your code better. One instance is
thread-safe and is meant to serve a whole application - constructing one per request wastes a
connection and a token exchange.

| Option | Default | Meaning |
|---|---|---|
| `host` | `"localhost"` | Hostname or IP |
| `port` | `9090` | gRPC port. See below |
| `use_plaintext` | `True` | `False` for TLS |
| `api_key` | `None` | Exchanged for a short-lived token and attached to calls |
| `channel_credentials` | `None` | Custom credentials, such as mutual TLS. Wins over `use_plaintext` |
| `call_timeout` | `None` | Seconds one request may take. Per request, not a budget for the client |
| `keepalive_time` | `None` | Seconds idle before an HTTP/2 keep-alive ping |
| `keepalive_timeout` | `None` | Seconds to wait for that ping to be answered |
| `max_inbound_message_size` | 4 MiB | Largest response the client will accept, in bytes |

**Which port.** The client sends both control-plane and data-plane calls over one connection, so the
endpoint has to front both. `9090` is the client gateway, which merges them, and is the default. A
bare data-server port such as `9092` is **not** a usable target: it serves the data plane only, so
the client connects successfully and then fails on the first control-plane call rather than at
connect time, which is a confusing way to find out.

**Set `call_timeout` on anything long-lived.** Without it, a request to a server that has stopped
answering but has not closed the connection waits forever, and your code has no way to notice.
Change streams are exempt from it - they are meant to stay open.

## Creating a collection

```python
from cyrock_db.types import (
    Cardinality, CollectionDefinition, MetadataFieldDefinition,
    MetadataFieldType, VectorFieldDefinition,
)

collection = client.create_collection(project_id, CollectionDefinition(
    name="documents",
    vector_fields=(
        VectorFieldDefinition(name="embedding", dimension=384),
    ),
    metadata_fields=(
        MetadataFieldDefinition(name="title", type=MetadataFieldType.STRING,
                                cardinality=Cardinality.HIGH, fulltext=True),
        MetadataFieldDefinition(name="year", type=MetadataFieldType.INTEGER,
                                cardinality=Cardinality.LOW),
    ),
))
```

`cardinality` is required, and the choice is not cosmetic: it selects the index. `HIGH` builds a
binary index, suited to fields with many distinct values and to range and equality lookups. `LOW`
builds a bitmap, suited to fields with few distinct values - a status, a category, a year.

A vector field's `dimension` is fixed once the collection exists. Adding a *new* vector field later
is allowed and takes effect immediately; changing an existing one's dimension is not.

## Documents

```python
from cyrock_db.types import AUTO_ASSIGN_ID, Vector

document_id = client.upsert(
    collection.id, AUTO_ASSIGN_ID,
    {"embedding": Vector(embedding)},
    {"title": "A paper about vectors", "year": 2026},
)

document = client.get_by_id(collection.id, document_id)
page     = client.list(collection.id, offset=0, limit=100)
client.delete(collection.id, document_id)
```

`AUTO_ASSIGN_ID` asks the store to choose an id. Note that `0` is a real id - documents are numbered
from zero - so do not use it to mean "assign me one".

For repeatable ingest, address documents by a key of your own instead. Re-sending the same key
updates rather than duplicating, and the result says which happened:

```python
result = client.upsert_document(collection.id, "paper-2026-001",
                                {"embedding": Vector(embedding)},
                                {"title": "A paper about vectors", "year": 2026})
result.created   # True the first time, False on every re-ingest
```

Numbers keep their type through storage. A Python `int` beyond 2^53 - past what a float can hold
exactly - comes back as the integer you stored, not a rounded one.

## Searching

```python
from cyrock_db.types import SearchRequest

matches = client.search(collection.id, SearchRequest(
    vector_field="embedding", vector=query_embedding, max_results=10,
))

for match in matches:
    print(match.score, match.document.metadata["title"])
```

Combine vector similarity with full-text scoring when a query has both a meaning and some keywords:

```python
from cyrock_db.types import FusionStrategy, HybridSearchRequest, TextQuery, VectorQuery

matches = client.hybrid_search(collection.id, HybridSearchRequest(
    vector_queries=(VectorQuery("embedding", query_embedding, 1.0),),
    text_queries=(TextQuery("title", "machine learning", 1.0),),
    max_results=10,
    fusion=FusionStrategy.RRF,
))
```

`multi_search` does the same across several vector fields, which is how a multi-modal item with a
text embedding and an image embedding is searched.

Vectors and fusion weights travel as 32-bit floats, while a Python `float` is a double. A weight of
`0.7` arrives as `0.699999988`, and a vector read back is the 32-bit rounding of what you sent. Worth
knowing before comparing a returned vector against the original.

## Running CyQL

```python
from cyrock_db.types import QueryParameters

result = client.query(graph.id, """
    MATCH (n:Concept) SIMILAR TO $v ON embedding TOP 5
    RETURN n, score(n) AS s ORDER BY s DESC
""", QueryParameters.builder().vector("v", query_embedding).build())

for row in result.rows:
    print(row["s"], row["n"])
```

`execute` decides where a statement belongs and sends it there - schema statements such as
`CREATE GRAPH` go to the control plane, everything else to the resource:

```python
client.execute(project_id, graph.id, "MATCH (n:Concept) RETURN n")
```

It takes both ids because it cannot know in advance which one the statement needs; pass `None` for
whichever your statement cannot use.

Unlike the Java SDK, this client does not parse a statement before sending it, so a syntax error is
reported by the server rather than refused locally. The message is the server's own.

## Calling asynchronously

`AsyncCyrockDbClient` offers every operation the blocking client has, awaited:

```python
import asyncio
from cyrock_db.aio import AsyncCyrockDbClient

async def main():
    async with AsyncCyrockDbClient(api_key="your-api-key") as client:
        results = await asyncio.gather(*(
            client.search(collection_id, SearchRequest("embedding", query, 10))
            for query in queries
        ))

asyncio.run(main())
```

It does not make a single call faster. It buys **concurrency without threads**: the blocking client
parks a thread for every round trip, so fifty searches at once wants fifty threads doing nothing but
waiting. Here they are in flight on one connection and none waits.

### Where it helps, and where it does not

Reads and searches gain: the server takes a read lock per store, so they run in parallel. Writes to
one collection are serialized behind its write lease regardless of the client, so fanning writes out
mostly moves the queue from your side to the server's. Fan out reads; fan out writes only when they
are independent and across different collections.

### Ordering

Two coroutines started together have no order between them. A read fired alongside its own write may
not see it. Await the first before starting the second when the order is the point:

```python
document_id = await client.upsert(collection_id, AUTO_ASSIGN_ID, vectors, metadata)
document    = await client.get_by_id(collection_id, document_id)
```

Concurrent writes to one collection apply in **arrival** order, not submission order.

### Two differences from the blocking client

The asynchronous client is constructed and closed on its own - there is no method on the blocking
client that hands you one. The two hold separate connections, which is a consequence of how asyncio
gRPC works rather than a choice.

Change streams are the one operation whose shape differs; see below.

## Transactions

Both transaction surfaces are all-or-nothing: every operation commits, or none does.

```python
from cyrock_db.types import RemoveDocumentOp, UpsertDocumentOp

result = client.execute_document_transaction(collection.id, [
    UpsertDocumentOp(id=AUTO_ASSIGN_ID, vectors={"embedding": Vector(first)}, metadata=meta),
    UpsertDocumentOp(id=AUTO_ASSIGN_ID, vectors={"embedding": Vector(second)}, metadata=meta),
    RemoveDocumentOp(document_id=old_id),
])

result.success                       # False if the transaction rolled back
result.results[0].generated_id       # the id the first upsert was assigned
```

`execute_transaction` is the graph equivalent, over `AddNodeOp`, `AddEdgeOp`, `UpsertNodeOp` and the
rest. The per-operation results let a rollback say precisely which operation caused it - an
operation's `error` explains why the *whole* transaction rolled back, not that it failed alone while
the others stood.

Removing something that does not exist is not an error: it reports success, which keeps a cleanup
transaction re-runnable.

## Errors

Every exception extends `CyrockDbClientException`, which carries an **HTTP** status code.

| Exception | Status | Raised when |
|---|---|---|
| `NotFoundException` | 404 | The resource does not exist |
| `ForbiddenException` | 403 | Your permissions do not cover the request |
| `UnauthorizedException` | 401 | Not authenticated |
| `UnavailableException` | 503 | Server unreachable or not accepting requests |
| `DeadlineExceededException` | 504 | The call did not finish within its deadline |
| `DurabilityNotConfirmedException` | 409 | The write committed and is visible, but the durability flush did not confirm |

`UnavailableException` and `DeadlineExceededException` share a base, `RetryableException`. Catch that
rather than comparing numbers - the arithmetic is easy to get wrong in the direction that never
retries:

```python
from cyrock_db import CyrockDbClientException, RetryableException

try:
    matches = client.search(collection.id, request)
except RetryableException:
    ...      # worth another attempt
except CyrockDbClientException as error:
    print(error.status_code, error)
```

429 is deliberately *not* retryable: it is the server asking for less load, not for the same request
again. Nor is `DurabilityNotConfirmedException` - that write already stands, and sending it again
would apply it twice. Verify, alert, or change the durability mode instead.

## Graphs

```python
from cyrock_db.types import AddEdgeRequest, GraphDefinition, ListNodesRequest

graph = client.create_graph(project_id, GraphDefinition(
    name="concepts",
    node_vector_fields=(VectorFieldDefinition(name="embedding", dimension=384),),
))

first  = client.add_node(graph.id, ["Concept"], {"embedding": Vector(a)}, {"title": "vectors"})
second = client.add_node(graph.id, ["Concept"], {"embedding": Vector(b)}, {"title": "indexes"})
client.add_edge(graph.id, AddEdgeRequest(first, second, "RELATES_TO", weight=0.9))

nodes = client.list_nodes(graph.id, ListNodesRequest(labels=["Concept"], limit=100))
```

`get_node` and `remove_node` take either an id or a key of your own, and do the right thing with
each.

**Vectors are opt-in on reads.** `list_nodes`, `neighbors` and `get_nodes` leave them out unless
asked, because collecting them is the expensive part of building a node - at 384 dimensions with 200
neighbours it is around 77,000 floats that most readers never look at:

```python
client.list_nodes(graph.id, ListNodesRequest(limit=100, include_vectors=True))
```

**Sampling.** A page is otherwise the first *n* nodes by id, and id order is insertion order - so a
graph written one label at a time hands back a page whose nodes all share a label. Pass a
`sample_seed` for a representative slice. Seeded rather than random, so a reload shows the same nodes
instead of reshuffling under whoever is reading.

Beyond this the graph surface covers traversal (`neighbors`, `traverse`, `reasoning_chain`),
retrieval-augmented reads (`context_window`, the community layer, `global_search`), agentic memory
(`observe`, `recall`, `decay`) and branching (`fork_graph`, `merge_graph`).

## Change streams

`watch_graph` and `watch_collection` follow changes as they happen. Delivery is at-least-once with a
resumable cursor: record the LSN you last processed, and de-duplicate on it.

```python
from cyrock_db.types import WatchOptions

def on_change(event):
    print(event.op, event.entity_id, event.lsn)

with client.watch_graph(graph.id, WatchOptions.with_snapshot(), on_change) as stream:
    ...                       # events arrive on a background thread
    checkpoint(stream.last_lsn)
```

Start from now, from a snapshot of current state, or from a checkpoint with
`WatchOptions.resume_from(lsn)`. The subscription reconnects by itself on a transient failure and
resumes from the last event it delivered.

Watch for `ChangeOp.DISCONTINUITY`. It does not mean an event was reordered - it means changes were
**lost**, and everything your consumer believes about that resource is stale until it re-snapshots.

The asynchronous client offers this as an iterator instead, which is the natural shape in asyncio:

```python
async for event in await client.watch_graph(graph.id, WatchOptions.from_now()):
    print(event.op, event.lsn)
```

That form does not reconnect. Checkpoint `event.lsn` and re-open with `resume_from` if the stream
ends.

Change streams are not available on a graph branch: a branch has no change log of its own, and the
server refuses the subscription.

## A complete example

```python
from cyrock_db import CyrockDbClient, RetryableException
from cyrock_db.types import (
    AUTO_ASSIGN_ID, Cardinality, CollectionDefinition, MetadataFieldDefinition,
    MetadataFieldType, SearchRequest, Vector, VectorFieldDefinition,
)

with CyrockDbClient(api_key="your-api-key") as client:
    collection = client.create_collection(project_id, CollectionDefinition(
        name="papers",
        vector_fields=(VectorFieldDefinition(name="embedding", dimension=384),),
        metadata_fields=(
            MetadataFieldDefinition(name="title", type=MetadataFieldType.STRING,
                                    cardinality=Cardinality.HIGH, fulltext=True),
            MetadataFieldDefinition(name="year", type=MetadataFieldType.INTEGER,
                                    cardinality=Cardinality.LOW),
        ),
    ))

    for paper in papers:
        client.upsert_document(
            collection.id, paper["doi"],
            {"embedding": Vector(paper["embedding"])},
            {"title": paper["title"], "year": paper["year"]},
        )

    try:
        matches = client.search(collection.id, SearchRequest(
            vector_field="embedding", vector=query_embedding, max_results=10,
        ))
    except RetryableException:
        matches = []

    for match in matches:
        print(f"{match.score:.3f}  {match.document.metadata['title']}")
```

## See also

- [Getting started](getting-started.md) - standing up a server
- [Java SDK](java-sdk.md) - the same API for the JVM
- [REST API](rest-api.md) - the language-agnostic surface
- [CyQL](cyql.md) - the query language
- [Troubleshooting](troubleshooting.md)
