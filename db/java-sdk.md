# Java SDK

A gRPC client for the JVM. It handles the token exchange, connection management and retries, so your
code deals in collections and documents rather than in headers.

> **Early Access scope.** The SDK is licensed for evaluation and internal prototyping. It may not be
> embedded in anything you distribute or expose outside your own organization. Build with it freely
> inside your own walls; [start a discussion](https://github.com/cyrock-ai/early-access/discussions)
> before it becomes part of something you ship.

## Adding the dependency

The Early Access packages are on GitHub Packages, which needs a GitHub account and a token with the
`read:packages` scope. Add the credentials to your Maven `settings.xml`:

```xml
<servers>
    <server>
        <id>cyrock-early-access</id>
        <username>your-github-username</username>
        <password>your-personal-access-token</password>
    </server>
</servers>
```

Then the repository and the dependency in your project:

```xml
<repositories>
    <repository>
        <id>cyrock-early-access</id>
        <name>CYROCK.AI Early Access Packages</name>
        <url>https://maven.pkg.github.com/cyrock-ai/early-access</url>
    </repository>
</repositories>

<dependencies>
    <dependency>
        <groupId>ai.cyrock.db</groupId>
        <artifactId>cyrock-db-client-java</artifactId>
        <version>0.9.1</version>
    </dependency>
</dependencies>
```

The `id` in `settings.xml` and in `<repositories>` must match - that is how Maven knows which
credentials to send. The SDK needs Java 21, and pulls in gRPC but no Spring and no storage engine.

## Protobuf compatibility

The SDK's generated gRPC classes are compiled against Protobuf **4.31.1** and bring
`com.google.protobuf:protobuf-java` along with them. Protobuf's rule here runs one way only: the
`protobuf-java` on your classpath may be newer than the version the classes were generated against,
never older. Generating against 4.31.1 rather than the newest release is deliberate - it leaves room
for applications whose own dependency management holds Protobuf at an older 4.x version than the SDK
would otherwise bring.

A version your build manages wins over the one the SDK asks for. Spring Boot 4.1 and later manage
Protobuf through a property, so that is where to move it if you need to. Anything from 4.31.1 upwards
works; 4.35.1 below is the version the SDK resolves on its own, and the one it is tested against:

```xml
<properties>
    <protobuf-java.version>4.35.1</protobuf-java.version>
</properties>
```

Below 4.31.1, the first generated class your code touches throws `ProtobufRuntimeVersionException` -
see [Troubleshooting](troubleshooting.md). Protobuf 3.x is a different major version and is not
supported.

To take the SDK together with the gRPC and Protobuf versions it was tested against, import the BOM
instead of pinning anything yourself:

```xml
<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>ai.cyrock.db</groupId>
            <artifactId>cyrock-db-bom</artifactId>
            <version>0.9.1</version>
            <type>pom</type>
            <scope>import</scope>
        </dependency>
    </dependencies>
</dependencyManagement>

<dependencies>
    <dependency>
        <groupId>ai.cyrock.db</groupId>
        <artifactId>cyrock-db-client-java</artifactId>
    </dependency>
</dependencies>
```

Maven takes the first managed version it finds, so an import only wins over the imports below it: if
your framework's BOM is imported first, its Protobuf and gRPC versions stay in force and this one
changes nothing.

## Connecting

```java
import ai.cyrock.db.client.java.CyrockDbClient;
import ai.cyrock.db.client.java.CyrockDbClientGrpc;

try (CyrockDbClient client = CyrockDbClientGrpc.builder()
    .apiKey("<the key from the startup banner>")
    .build())
{
    // ...
}
```

`close()` declares `IOException`, so the enclosing method needs to throw or catch it.

No host and no port. The defaults are `localhost:9090`, which is exactly where the container's
client gateway listens, so a local evaluation needs neither. Point it elsewhere when you need to:

```java
CyrockDbClientGrpc.builder()
    .host("cyrock-db.internal")
    .port(9090)
    .apiKey(apiKey)
    .build();
```

Port `9090` is the **client gateway**, which fronts both the data and the platform plane. The client
needs both - the key exchange lives on the platform side - so this is the port to use rather than the
individual server ports.

The client is thread-safe and holds a connection pool. Create one per application, not one per
request, and close it on shutdown (or let try-with-resources do it).

## Creating a collection

Fields come in two lists: vector fields and metadata fields. **The vector list may be empty**: a
collection without a vector field is a document store with metadata filtering, and only similarity
search is unavailable on it. Full-text search is available on top of that for each STRING field
declared with `fulltext` - the fourth constructor argument below, `false` in both of these fields.

```java
CollectionDefinition definition = CollectionDefinition.builder()
    .name("articles")
    .vectorFields(List.of(VectorFieldDefinition.builder()
        .name("vector")
        .dimension(384)
        .similarityFunction(SimilarityFunction.COSINE)
        .build()))
    .metadataFields(List.of(
        new MetadataFieldDefinition("title", MetadataFieldType.STRING, Cardinality.HIGH, false, false),
        new MetadataFieldDefinition("topic", MetadataFieldType.STRING, Cardinality.LOW,  false, false)))
    .build();

String collectionId = client.createCollection(projectId, definition).id();
```

`MetadataFieldDefinition` takes `(name, type, cardinality, fulltext, unique)`. Cardinality picks the
indexing strategy - `HIGH` for values that are nearly unique per record, `LOW` for a small set of
repeated values. Set `fulltext` to index the field for BM25 `SEARCH`.

## Documents

```java
client.upsertDocument(
    collectionId,
    "how-to-reset-a-password",                              // your own external key
    Map.of("vector", VectorInput.of(embedding)),            // vector fields
    Map.of("title", "Resetting a password",                 // metadata fields
           "topic", "accounts"));

Document found = client.getDocument(collectionId, "how-to-reset-a-password");
client.removeDocument(collectionId, "how-to-reset-a-password");
```

The key is yours to choose, and upsert inserts or replaces, so re-running an import does not create
duplicates.

`VectorInput.of(float[])` passes an embedding you computed. `VectorInput.of(String)` passes text and
has the server embed it, which needs an embedding provider configured - see
[Configuration](configuration.md).

## Searching

```java
List<Match> matches = client.search(collectionId,
    SearchRequest.builder("vector", queryVector, 10)
        .filter("topic = \"accounts\"")
        .build());
```

The builder takes the vector field, the query vector and the maximum number of results. The filter is
applied before ranking, so all ten results survive it. `multiSearch` searches several vector fields at
once and `hybridSearch` fuses BM25 with vector similarity.

## Running CyQL

Often the shortest path, especially for traversal. Three methods, differing only in what the statement
is scoped to - picking the wrong one is the easiest mistake to make here:

| Method | Scope |
|---|---|
| `executeCollectionStatement(collectionId, ...)` | One collection |
| `executeStatement(graphId, ...)` | One graph |
| `executeProjectStatement(projectId, ...)` | Project-wide DDL - `CREATE COLLECTION`, `SHOW COLLECTIONS` |

```java
StatementResult result = client.executeCollectionStatement(
    collectionId,
    "MATCH (d) WHERE d.topic = $topic RETURN d.title",
    QueryParameters.builder().param("topic", "accounts").build());

for (Map<String, Object> row : result.rows())
{
    System.out.println(row.get("d.title"));
}
```

`StatementResult` carries `columns()`, `rows()` and, for writes, a `summary()`. Pass values through
`QueryParameters` rather than concatenating them into the statement; `.vector(name, float[])` binds a
vector for a `SIMILAR TO $v` clause.

## Calling asynchronously

Every method above blocks: the calling thread waits for the round trip. That is what you want for a
script, and what you do not want when several calls could be in flight at once - fifty searches would
need fifty threads, each doing nothing but waiting.

`client.async()` returns the same operations returning `CompletableFuture`:

```java
import ai.cyrock.db.client.java.CyrockDbAsyncClient;

CyrockDbAsyncClient async = client.async();

CompletableFuture<List<Match>> matches = async.search(collectionId,
    SearchRequest.builder("vector", queryVector, 10).build());
```

It shares the synchronous client's connection, its key exchange and its lifecycle. There is nothing
extra to build and nothing extra to close - closing the synchronous client closes both.

### Fanning out

The point of it. These fifty searches share one connection and no threads wait:

```java
List<CompletableFuture<List<Match>>> pending = queries.stream()
    .map(query -> async.search(collectionId,
        SearchRequest.builder("vector", query, 10).build()))
    .toList();

CompletableFuture
    .allOf(pending.toArray(new CompletableFuture[0]))
    .join();

List<List<Match>> results = pending.stream().map(CompletableFuture::join).toList();
```

### Ordering: chain what depends, fan out what does not

Two futures started together have **no** order. Fired alongside its own write, a read may not see it.
When the second call depends on the first, chain them:

```java
CompletableFuture<Document> written = async
    .upsert(collectionId, -1L, Map.of("vector", VectorInput.of(vector)), metadata)
    .thenCompose(id -> async.getById(collectionId, id));
```

This is the one habit to carry over from the blocking API, where statement order gave you the
ordering for free.

Concurrent writes to the same collection are applied in the order they **arrive**, which is not
necessarily the order you submitted them in. Fanning writes out is fine when they are independent;
when one must follow another, chain it.

### Failures

A future completes exceptionally rather than throwing. `CompletableFuture` wraps the cause, so unwrap
one level before matching on it:

```java
async.getDocument(collectionId, externalKey)
    .exceptionally(error ->
    {
        Throwable cause = error instanceof CompletionException && error.getCause() != null
            ? error.getCause()
            : error;
        System.err.println(cause.getMessage());
        return null;
    });
```

`join()` and `get()` wrap it the same way. What is inside is the `CyrockDbClientException` the
synchronous client would have thrown for the same failure - the same subtype and the same status code,
since both surfaces share one mapping - so a catch block moving across only needs the unwrap. Once
unwrapped, [the subtypes](#errors) apply unchanged, `RetryableException` included, which matters most
here: a caller holding many calls in flight is exactly the one who wants to retry the two failures
resending can fix.

### Threading

A continuation attached without an executor runs on a gRPC transport thread. Keep those short, and
give anything that blocks - or touches a UI - an executor of its own:

```java
async.search(collectionId, request)
    .thenAcceptAsync(this::render, myExecutor);
```

Cancelling a returned future cancels the call, so a caller who stops caring stops costing the server
work.

### Which to use

Both APIs are the same operations against the same server, and mixing them on one client is fine.
Reach for the asynchronous one when calls overlap; the blocking one reads better when they do not.

## Transactions

```java
client.executeDocumentTransaction(collectionId, List.of(
    CollectionOperation.upsert(...),
    CollectionOperation.remove(...)));
```

Every operation applies or none does. Graphs have the same thing as `executeTransaction(graphId,
List<GraphOperation>)`.

## Errors

Everything the client throws is a `CyrockDbClientException`, an unchecked exception carrying the
server's message and a status code. The code is **always an HTTP status**, never the gRPC status number
the transport uses underneath - a server that is not serving requests reads as 503, not as the 14 the
wire calls it. Do not read a retry rule off the number, though: some `4xx` report the server's condition
rather than a bad request - 429 while it sheds load, 409 on a conflict - so branch on the subtypes
instead:

```java
try
{
    client.getDocument(collectionId, externalKey);
}
catch (final CyrockDbClientException.NotFoundException e)
{
    // The document is not there - for this caller that is an answer, not a failure.
}
catch (final CyrockDbClientException.RetryableException e)
{
    // The server was unreachable, or it did not answer in time: resending can work.
    retryWithBackoff();
}
catch (final CyrockDbClientException e)
{
    System.err.println(e.getStatusCode() + " " + e.getMessage());
    throw e;
}
```

The failures worth branching on have a subtype, so the decision does not have to be arithmetic on a
status code:

| Subtype | Status | Thrown when |
|---|---|---|
| `NotFoundException` | 404 | The collection, graph, document or node does not exist |
| `ForbiddenException` | 403 | Authenticated, but not permitted to do this |
| `UnauthorizedException` | 401 | Not authenticated, or the API key was refused |
| `UnavailableException` | 503 | The server could not be reached, or was reached but is not serving this request right now - a restart, a deployment, a dropped connection |
| `DeadlineExceededException` | 504 | The call did not finish within its deadline |
| `DurabilityNotConfirmedException` | 409 | The write **committed and is visible**, but the durability flush did not confirm |

`UnavailableException` and `DeadlineExceededException` extend `RetryableException`, which is the type to
catch when resending is the answer. A retryable failure says nothing about whether the request was
applied - a deadline can expire on a write the server goes on to commit - so a non-idempotent operation
needs the same care here as anywhere else.

**`DurabilityNotConfirmedException` is the one worth handling deliberately, and the obvious reaction is
wrong.** Do not retry it: the commit stands, so sending the request again applies it twice. The write is
already readable. What is unconfirmed is only whether it would survive a power loss, so the useful
responses are to verify it, to alert, or to reconsider the durability mode - not to repeat it. It is
deliberately not a `RetryableException` for that reason.

Anything without a subtype arrives as a plain `CyrockDbClientException` with its projected status - 400
for an invalid argument or a failed precondition, 409 for a conflict, 429 when the server is shedding
load, 500 for an internal failure, 501 for something this server does not implement.

Token expiry is **not** something to handle: the client re-exchanges automatically.

## Graphs

The graph API mirrors the document one, with edges and traversal added:

```java
String graphId = client.createGraph(projectId, graphDefinition).id();

long matrix = client.addNode(graphId,
    List.of("Movie"),                              // labels
    Map.of("embedding", VectorInput.of(vector)),
    Map.of("title", "The Matrix"));

client.addEdge(graphId, AddEdgeRequest.builder()
    .type("ACTED_IN").source(keanu).target(matrix).build());

List<Node> neighbours = client.neighbors(graphId, NeighborsRequest.builder()
    .nodeId(matrix).edgeType("ACTED_IN").build());
```

Nodes carry a list of labels, not one. Beyond a single hop, CyQL is clearer than assembling calls - see
[CyQL](cyql.md). The client also covers traversal, context windows, graph branching, the Graph RAG
community operations and agentic memory; the full method list is on `CyrockDbClient`.

## A complete example

This compiles and runs against the evaluation container as-is:

```java
import ai.cyrock.db.client.java.CyrockDbClient;
import ai.cyrock.db.client.java.CyrockDbClientException;
import ai.cyrock.db.client.java.CyrockDbClientGrpc;
import ai.cyrock.db.data.Cardinality;
import ai.cyrock.db.data.CollectionDefinition;
import ai.cyrock.db.data.Match;
import ai.cyrock.db.data.MetadataFieldDefinition;
import ai.cyrock.db.data.MetadataFieldType;
import ai.cyrock.db.data.QueryParameters;
import ai.cyrock.db.data.SearchRequest;
import ai.cyrock.db.data.SimilarityFunction;
import ai.cyrock.db.data.StatementResult;
import ai.cyrock.db.data.VectorFieldDefinition;
import ai.cyrock.db.data.VectorInput;

import java.io.IOException;
import java.util.List;
import java.util.Map;

public final class Example
{
    private static final int DIMENSION = 384;

    public static void main(final String[] args) throws IOException
    {
        final String apiKey    = System.getenv("CYROCK_DB_API_KEY");
        final String projectId = System.getenv("CYROCK_DB_PROJECT_ID");

        try (final CyrockDbClient client = CyrockDbClientGrpc.builder()
            .apiKey(apiKey)
            .build())
        {
            final CollectionDefinition definition = CollectionDefinition.builder()
                .name("sdk-example")
                .vectorFields(List.of(VectorFieldDefinition.builder()
                    .name("vector")
                    .dimension(DIMENSION)
                    .similarityFunction(SimilarityFunction.COSINE)
                    .build()))
                .metadataFields(List.of(
                    new MetadataFieldDefinition("title", MetadataFieldType.STRING, Cardinality.HIGH, false, false),
                    new MetadataFieldDefinition("topic", MetadataFieldType.STRING, Cardinality.LOW,  false, false)))
                .build();

            final String collectionId = client.createCollection(projectId, definition).id();

            final float[] embedding = new float[DIMENSION];
            embedding[0] = 1.0f;

            client.upsertDocument(
                collectionId,
                "how-to-reset-a-password",
                Map.of("vector", VectorInput.of(embedding)),
                Map.of("title", "Resetting a password", "topic", "accounts"));

            final List<Match> matches = client.search(collectionId,
                SearchRequest.builder("vector", embedding, 5)
                    .filter("topic = \"accounts\"")
                    .build());
            System.out.println("matches: " + matches.size());

            final StatementResult result = client.executeCollectionStatement(
                collectionId,
                "MATCH (d) WHERE d.topic = $topic RETURN d.title",
                QueryParameters.builder().param("topic", "accounts").build());
            System.out.println("rows: " + result.rows());
        }
        catch (final CyrockDbClientException e)
        {
            System.err.println("failed: " + e.getMessage());
        }
    }
}
```

Set `CYROCK_DB_API_KEY` and `CYROCK_DB_PROJECT_ID` from the startup banner and run it. Nothing else is
needed - no port, no token handling, no configuration file.

## See also

- [Getting started](getting-started.md) - standing up a server
- [Python SDK](python-sdk.md) - the same API for Python
- [REST API](rest-api.md) - the language-agnostic surface
- [CyQL](cyql.md) - the query language
- [Troubleshooting](troubleshooting.md)
