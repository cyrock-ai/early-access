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
        <version>0.9.0</version>
    </dependency>
</dependencies>
```

The `id` in `settings.xml` and in `<repositories>` must match - that is how Maven knows which
credentials to send. The SDK needs Java 21, and pulls in gRPC but no Spring and no storage engine.

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

Fields come in two lists: vector fields and metadata fields. **At least one vector field is
required.**

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
server's message:

```java
try
{
    client.getDocument(collectionId, documentId);
}
catch (final CyrockDbClientException e)
{
    // Not found, permission denied, invalid request, transport failure.
    System.err.println(e.getMessage());
}
```

There is deliberately no subtype per failure mode in this release - branch on the message if you must,
but treat that as temporary. Token expiry is **not** something to handle: the client re-exchanges
automatically.

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
