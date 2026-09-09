# Framework connectors

Two connectors plug CYROCK.AI DB into the JVM AI frameworks: a Spring AI `VectorStore` and a
LangChain4j `EmbeddingStore`. An application already built on either one keeps the interfaces it
already targets and changes only its wiring.

Both are written against the [Java SDK](java-sdk.md) and nothing else, so there is nothing in them
you could not do by hand. What they save you is the mapping.

> **Early Access scope.** The connectors are licensed for evaluation and internal prototyping. They
> may not be embedded in anything you distribute or expose outside your own organization. Build with
> them freely inside your own walls;
> [start a discussion](https://github.com/cyrock-ai/early-access/discussions) before either becomes
> part of something you ship.

**Both assume the collection or graph already exists.** They read and write; they do not create or
alter schema. [Creating the collection](#creating-the-collection) says what it has to look like.

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

Then the repository and whichever connector you need:

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
        <artifactId>cyrock-db-spring-ai</artifactId>
        <version>0.9.1</version>
    </dependency>
</dependencies>
```

For LangChain4j the artifact is `cyrock-db-langchain4j` at the same version. Either one brings
`cyrock-db-client-java` with it, so you do not declare the SDK separately. Both are also managed by
the SDK BOM, so if you import that - see [Java SDK](java-sdk.md#adding-the-dependency) - you can
leave the `<version>` off.

The `id` in `settings.xml` and in `<repositories>` must match - that is how Maven knows which
credentials to send. Both connectors need Java 21.

**Neither connector brings its framework.** They are compiled against Spring AI **2.0.0** on Spring
Boot **4.1.0** and LangChain4j **1.17.1**, and the framework itself stays whatever your build
resolves - which is what you want when your application already manages it. Spring AI 2.0 needs
Spring Boot 4, so an application still on Boot 3 has to move first.

## Creating the collection

Both connectors write into a collection that already exists, and they are strict about it because
the engine is: metadata in CYROCK.AI DB is **declared**, and an undeclared field name is rejected on
write rather than stored loosely. Three things have to line up.

- **The vector field's dimension must match your embedding model** - 384 for the in-process
  embedder, 1536 for a `text-embedding-3-small`, and so on. It is fixed once the field exists.
- **The content field must be declared.** Both connectors keep the document text in a metadata
  field, `content` by default. It is an ordinary `STRING` field.
- **Every metadata key you pass through the framework must be declared too.** A Spring AI
  `Document`'s metadata map and a LangChain4j `TextSegment`'s `Metadata` both arrive as CYROCK.AI DB
  metadata, so a key nobody declared fails the write.

```java
CollectionDefinition definition = CollectionDefinition.builder()
    .name("support-articles")
    .vectorFields(List.of(VectorFieldDefinition.builder()
        .name("vector")
        .dimension(384)
        .similarityFunction(SimilarityFunction.COSINE)
        .build()))
    .metadataFields(List.of(
        new MetadataFieldDefinition("content", MetadataFieldType.STRING, Cardinality.HIGH, true,  false),
        new MetadataFieldDefinition("topic",   MetadataFieldType.STRING, Cardinality.LOW,  false, false)))
    .build();

String collectionId = client.createCollection(projectId, definition).id();
```

`MetadataFieldDefinition` takes `(name, type, cardinality, fulltext, unique)`. Declaring `content`
with `fulltext` set is what makes the full-text and hybrid retrieval modes below available on it; a
purely vector setup does not need it. [Java SDK](java-sdk.md#creating-a-collection) has the rest of
the schema surface - or create the collection from the [console](web-console.md) or in
[CyQL](cyql.md). The connectors do not care which.

## Spring AI

### The vector store

`CyrockVectorStore` implements `org.springframework.ai.vectorstore.VectorStore`. Build it from a
connected client and the `EmbeddingModel` your application already has:

```java
import ai.cyrock.db.client.java.CyrockDbClient;
import ai.cyrock.db.client.java.CyrockDbClientGrpc;
import ai.cyrock.db.springai.CyrockVectorStore;
import org.springframework.ai.vectorstore.VectorStore;

CyrockDbClient client = CyrockDbClientGrpc.builder()
    .apiKey(apiKey)
    .build();

VectorStore store = CyrockVectorStore.builder()
    .client(client)
    .embeddingModel(embeddingModel)
    .collectionId(collectionId)
    .build();
```

`client`, `embeddingModel` and `collectionId` are required. `vectorField` and `contentField` default
to `vector` and `content`; set them if your collection names them differently. From there it is the
interface you already know:

```java
store.add(List.of(
    Document.builder().id("reset-password")
        .text("Reset a password from the account settings page.")
        .metadata(Map.of("topic", "accounts")).build(),
    Document.builder().id("invoice-schedule")
        .text("Invoices are issued on the first of the month.")
        .metadata(Map.of("topic", "billing")).build()));

List<Document> hits = store.similaritySearch(SearchRequest.builder()
    .query("how do I change my password")
    .topK(5)
    .similarityThreshold(0.5)
    .filterExpression("topic == 'accounts'")
    .build());

for (final Document hit : hits)
{
    System.out.println(hit.getScore() + "  " + hit.getText());
}
```

`add` embeds each document with your `EmbeddingModel` and upserts it, so re-adding the same id
replaces rather than duplicates. `similaritySearch` embeds the query, runs an
approximate-nearest-neighbour search and drops anything below `similarityThreshold`. The filter is
applied before ranking, so a narrow filter still returns a full `topK`.

Deletes come in two shapes:

```java
store.delete(List.of("reset-password"));

store.delete(new FilterExpressionBuilder().eq("topic", "billing").build());
```

Deleting by id removes the documents you added under those ids. Deleting by filter compiles the
expression to a CyQL `DELETE` and applies it server-side, so it is one round trip however many
documents match. Deleting something that is not there is not an error.

### What the filter converter covers

`CyqlFilterExpressionConverter` renders a Spring AI `Filter.Expression` tree into a CyQL filter
string. It covers the comparisons `=`, `!=`, `<`, `<=`, `>`, `>=`, set membership `IN` and `NOT IN`,
the null checks `IS NULL` and `IS NOT NULL`, and `AND`, `OR`, `NOT` with grouping. Dates and times
become CyQL literals at second precision, and an offset or zoned value is rendered as its UTC
instant.

Two things it deliberately refuses. A metadata key that is not a plain identifier is rejected rather
than concatenated into the statement, which is what closes off query injection through a crafted
key. And an expression type CyQL has no equivalent for raises `IllegalArgumentException` at call
time, rather than producing a filter that quietly means something else.

### Spring Boot auto-configuration

Set the collection id and the rest wires itself:

```properties
spring.ai.vectorstore.cyrock.collection-id=<the collection id>
spring.ai.vectorstore.cyrock.api-key=<the key from the startup banner>
```

| Property, under `spring.ai.vectorstore.cyrock` | Default | Meaning |
|---|---|---|
| `collection-id` | empty | The collection to read and write. **Setting it is what activates the auto-configuration** |
| `host` | `localhost` | Hostname of the client gateway |
| `port` | `9090` | The client gateway port, which fronts both the data and platform planes |
| `api-key` | empty | Exchanged for a short-lived token and attached to every call |
| `use-plaintext` | `true` | `false` for TLS |
| `vector-field` | `vector` | The vector field written and searched |
| `content-field` | `content` | The metadata field holding the document text |
| `graph-id` | empty | Set it to activate the Graph RAG advisor below |

With `collection-id` unset the auto-configuration contributes nothing at all, so adding the
dependency to an application that is not ready to use it changes nothing.

It contributes a connected `CyrockDbClient` unless your application already defines one. Defining
your own `@Bean` is the way to reach client options these properties do not cover - a call timeout,
custom credentials - and the auto-configuration then uses yours. The `VectorStore` bean needs an
`EmbeddingModel` bean to be present; without one there is nothing to embed with and no store is
created.

### Grounding a chat client in a graph

A `VectorStore` can only hand back the nearest passages. `CyrockGraphRagAdvisor` is a `ChatClient`
advisor that instead embeds the question, runs a global search over a graph's community summaries,
and prepends what it finds to the user message. That answers "what are the recurring themes here",
which no nearest-neighbour lookup expresses. See [Concepts](concepts.md) for what a community
summary is.

```java
ChatClient chatClient = ChatClient.builder(chatModel)
    .defaultAdvisors(CyrockGraphRagAdvisor.builder()
        .client(client)
        .embeddingModel(embeddingModel)
        .graphId(graphId)
        .topK(5)
        .build())
    .build();

String answer = chatClient.prompt("What are the recurring themes in these incidents?")
    .call()
    .content();
```

It searches every level of the community hierarchy, and if the graph holds no summaries yet it
leaves the request untouched rather than failing - so detect communities and store their summaries
first, or the advisor is a silent no-op.

Setting `spring.ai.vectorstore.cyrock.graph-id` contributes the same advisor as a bean. One thing to
know if you do: the advisor takes its vector field from `vector-field`, the same property the vector
store uses. If your graph names that field differently from your collection, build the advisor
yourself rather than letting the properties configure it.

### Health

With Spring Boot Actuator on the classpath the auto-configuration also contributes a health
indicator that reads the configured collection. A reachable server holding it reports `UP` with the
collection name; anything else reports `DOWN` with a stable reason, and the underlying failure goes
to the log rather than out of the endpoint. That turns a wrong collection id or a wrong endpoint
into a readiness failure instead of a surprise on the first search.

## LangChain4j

### The embedding store

`CyrockEmbeddingStore` implements `dev.langchain4j.store.embedding.EmbeddingStore<TextSegment>`.
LangChain4j keeps embedding outside the store, so this one takes no `EmbeddingModel`: you embed, it
stores.

```java
import ai.cyrock.db.langchain4j.CyrockEmbeddingStore;

EmbeddingStore<TextSegment> store = CyrockEmbeddingStore.builder()
    .client(client)
    .collectionId(collectionId)
    .build();

TextSegment segment = TextSegment.from(
    "Reset a password from the account settings page.",
    Metadata.from("topic", "accounts"));

String id = store.add(embeddingModel.embed(segment).content(), segment);
```

For ingest, reach for `addAll(List<Embedding>, List<TextSegment>)`: it goes out as one batch upsert
rather than a call per segment.

Search honours `maxResults`, `minScore` and the metadata `Filter`:

```java
import static dev.langchain4j.store.embedding.filter.MetadataFilterBuilder.metadataKey;

EmbeddingSearchResult<TextSegment> result = store.search(EmbeddingSearchRequest.builder()
    .queryEmbedding(embeddingModel.embed("how do I change my password").content())
    .maxResults(5)
    .minScore(0.5)
    .filter(metadataKey("topic").isEqualTo("accounts"))
    .build());

for (final EmbeddingMatch<TextSegment> match : result.matches())
{
    System.out.println(match.score() + "  " + match.embedded().text());
}
```

`removeAll(Collection<String>)` removes by id, `removeAll(Filter)` compiles the filter to a CyQL
`DELETE` and applies it in one round trip, and `removeAll()` empties the collection. Removing
something absent is not an error.

`CyqlFilterMapper` renders the LangChain4j filter tree: the comparisons, `IsIn` and `IsNotIn`,
`ContainsString` - which becomes CyQL `CONTAINS`, a case-insensitive substring match on a string
field and element membership on a list field - and `And`, `Or`, `Not`. As on the Spring AI side, a
metadata key that is not a plain identifier is refused rather than concatenated in.

### Retrieving content for AiServices

`ContentRetriever` is the interface `AiServices` actually consumes for RAG, so this is usually the
class you want rather than the store. `CyrockContentRetriever` has three modes, chosen by what you
give the builder:

| Configured with | Mode |
|---|---|
| `embeddingModel` | Vector. The model embeds the query |
| `textField` | Full-text. BM25 on that field, with no embedding backend at all |
| both | Hybrid. Both run, fused with reciprocal-rank fusion |

```java
ContentRetriever retriever = CyrockContentRetriever.builder()
    .client(client)
    .collectionId(collectionId)
    .embeddingModel(embeddingModel)
    .textField("content")
    .maxResults(5)
    .build();

Assistant assistant = AiServices.builder(Assistant.class)
    .chatModel(chatModel)
    .contentRetriever(retriever)
    .build();

String answer = assistant.chat("how do I change my password");
```

Giving it neither an `embeddingModel` nor a `textField` fails at build time - there would be nothing
to search with. The full-text mode is the one worth remembering: it needs no embedding provider and
no network, so a keyword-shaped question can be served by a pipeline with no embedding model
configured. `textField` has to be a `STRING` field declared with `fulltext`.

`maxResults` defaults to 3, matching LangChain4j's own retrievers, which is usually too few once
your documents run longer than a paragraph.

### Retrieving a graph context window

`CyrockGraphContentRetriever` is also a `ContentRetriever`, but it retrieves from a graph: it embeds
the query, seeds a vector search on the graph's nodes, then expands out along the edges to a
configured depth. What comes back is a context window - the matching nodes together with their
related neighbours - which is graph traversal inside an `AiServices` pipeline.

```java
ContentRetriever retriever = CyrockGraphContentRetriever.builder()
    .client(client)
    .graphId(graphId)
    .embeddingModel(embeddingModel)
    .vectorField("embedding")
    .contentField("content")
    .maxResults(5)
    .depth(2)
    .build();
```

`maxResults` is how many **seed** nodes the vector search returns, not how much content comes back:
each seed drags in its neighbourhood, so the amount of text grows with `depth`. It defaults to 5,
and `depth` defaults to 1. Start there and raise it deliberately - depth 3 on a well-connected graph
returns a great deal of text to answer one question with.

A node contributes only if it carries the content field. Nodes without it are skipped rather than
returned empty.

## Document ids

Worth reading once, because there are two id spaces and the difference surprises people.

CYROCK.AI DB numbers documents internally, and a search response carries that internal id rather
than the key you supplied.

- **Spring AI always adds under an id.** A `Document` carries one, generated for you if you did not
  set it, and it becomes the CYROCK.AI DB external key - so `delete(List<String>)` takes the ids you
  added with. A null or blank id is refused rather than quietly replaced.
- **LangChain4j adds both ways.** `add(embedding)`, `add(embedding, segment)` and
  `addAll(embeddings, segments)` let CYROCK.AI DB assign the id and return it. `add(id, embedding)`
  and `addAll(ids, embeddings, segments)` store your id as the external key instead.
- **Search returns the internal id either way.** A document added under your own key comes back from
  a search carrying the internal id, not that key. If you need to correlate a hit with a record of
  your own, keep the key in the metadata as well and read it off there.
- **Removal accepts either form.** A numeric id is tried as an internal id first and falls back to
  an external key; a non-numeric id is always an external key.

## What the connectors do not do

- **No schema creation.** Neither creates or alters a collection or a graph, and neither adds a
  vector field. A missing collection is a 404 on the first call; an undeclared metadata field is a
  rejected write.
- **Blocking only.** Both call the synchronous SDK surface, because the framework interfaces they
  implement are synchronous. The [asynchronous client](java-sdk.md#calling-asynchronously) is there
  when you want calls in flight, but you drive it yourself.
- **Errors arrive as the SDK's.** A failure surfaces as `CyrockDbClientException` with an HTTP
  status code rather than as a framework exception type. [Java SDK](java-sdk.md#errors) has the
  subtypes worth branching on.
- **One collection or one graph each.** An instance is bound to the id it was built with. Point at
  several by building several.

## See also

- [Java SDK](java-sdk.md) - the surface both connectors are built on
- [Concepts](concepts.md) - collections, graphs, vector fields and communities
- [CyQL](cyql.md) - the filter grammar the converters emit
- [Web console](web-console.md) - creating the collection without writing code
- [Troubleshooting](troubleshooting.md)
