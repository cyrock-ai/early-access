# Vectralink Pinecone

The Pinecone module provides a concrete VectorStore backed by the Pinecone vector database. It implements the Core `VectorStore<String, Vector.Float>` API to persist float embeddings, attach arbitrary metadata (payload), and perform similarity search.

If you use Pinecone as your vector DB, this module is the drop-in implementation to connect Vectralink’s Core abstractions to a running Pinecone instance.

> The Pinecone module uses Pinecone Java SDK `v6.x` for Pinecone API `2025-10`.


## What’s inside

- `PineconeVectorStore` (and `PineconeVectorStore.Default`):
  - Stores float vectors with auto-generated UUID string IDs.
  - Attaches Core `Metadata` as Pinecone metadata.
  - Provides search via Pinecone’s nearest-neighbor API and returns Core `VectorSearchResult<String, Vector.Float>`.
  - Supports deletions by IDs and and `Metadata.ID`.
  - **TODO**: Supports deletions by metadata (payload) filters.

Packages live under `ai.cyrock.vectralink.pinecone`.

## How it fits into Vectralink

- Core defines neutral APIs for vectors, metadata, storage, and search.
- Pinecone implements `VectorStore<String, Vector.Float>` so you can:
  - insert embeddings along with `Metadata` that links back to your domain (e.g., `Metadata.ID`).
  - run vector similarity searches and receive matches with scores, original vectors, and metadata.
  - delete by vector IDs or by metadata (`Metadata.ID`) conditions to keep the store in sync.
- Use it directly, or wire it with Core’s `VectorStoreUpdater` for CDC-driven synchronization, and `SimilaritySearchHandler` for natural-data search.

## Prerequisites

- Java 21
- A running Pinecone instance (local or remote)
  - Default ports are 5080, 5081, 5082
  - Make sure the target index exists with the correct vector size and distance metric (e.g., cosine, dot, euclid)
- Pinecone Java client (Java SDK `v6.x` for Pinecone API `2025-10`) is brought by this module’s dependencies

## Quick start

### 1) Create a Pinecone client and store

```java
import ai.cyrock.vectralink.*;
import ai.cyrock.vectralink.pinecone.PineconeVectorStore;
import io.pinecone.clients.Index;
import io.pinecone.clients.Pinecone;

// 1) Build a Pinecone client
Pinecone pc = new Pinecone.Builder(apiKey).build();

String denseIndexName = "example-dense-index"; // ensure it exists in Pinecone with correct vector size/metric
String namespace = "test";

// 2) Get the Pinecone index
Index denseIndex = pc.getIndexConnection(denseIndexName);

// 4) Create the VectorStore
PineconeVectorStore store = PineconeVectorStore.New(denseIndex, namespace);
```


### 2) Insert vectors with metadata

```java
// Vectorizer example
Vectorizer<Vector.Float> vectorizer = d -> Vector.Float(0.12f, 0.98f, 0.53f);

// Wrap your domain object
record Product(String id, String title, String description) {}
Data data = Data.New(new Product("p-1", "Wireless Mouse", "Ergonomic, silent clicks"));

// Create a vector and metadata (link back to your domain with Metadata.ID)
Vector.Float v = vectorizer.vectorize(data);
Metadata md = Metadata.New(java.util.Map.of(Metadata.ID, "p-1", "category", "peripherals"));

// Insert one or multiple vectors. IDs are generated (UUID strings) and returned
java.util.List<String> ids = store.insert(java.util.List.of(v), md);
String pointId = ids.getFirst();
```

### 3) Search for similar vectors

```java
VectorSearchRequest<Vector.Float> req = VectorSearchRequest.New(
    v,   // query vector
    10,  // max results
    0.0  // min score threshold (client-side filtered)
);

VectorSearchResult<String, Vector.Float> result = store.search(req);
for (VectorSearchMatch<String, Vector.Float> match : result.matches()) {
    double score = match.score();
    String vectorId = match.vectorId();
    Metadata payload = match.metadata();
    String naturalId = payload.get(Metadata.ID); // your original object ID
}
```

### 4) Delete by IDs or by metadata

```java
// By IDs
store.deleteByIds(ids);

// By metadata (payload) – matches all provided keys (logical AND)
Metadata criteria = Metadata.New(java.util.Map.of(
    Metadata.ID, "p-1"
));
store.deleteByMetadata(criteria);
```

### 5) End-to-end wiring with CDC

```java
// Provide a stable ID extractor for your domain
DataIdProvider<String> idProvider = d -> d.get("id");

// VectorStoreUpdater keeps Pinecone in sync based on DataChange events
VectorStoreUpdater updater = VectorStoreUpdater.New(
    vectorizer,
    idProvider,
    store
);

DataChangeNotifier notifier = DataChangeNotifier.New(updater);
```

Now you can feed `notifier` with create/update/delete events (e.g., from the Debezium module) and keep Pinecone updated automatically.

## Metadata and payload mapping

`PineconeVectorStore` converts Core `Metadata` to Pinecone metadata values.

Search results return the stored payload back as Core `Metadata`.

Deletion by metadata translates each provided key-value pair into a Pinecone filter condition; all conditions are combined with logical AND.

## Distance metrics, vector size, and precision

- `PineconeVectorStore` operates on Core `Vector.Float` (float32 arrays).
- Configure your index in Pinecone with the correct vector size and distance metric that matches how your embeddings were generated.
- Metric selection (e.g., cosine) and index parameters are controlled on the Pinecone side at index creation time.

## Error handling

- Client calls are performed via gRPC; runtime exceptions wrap interruptions or execution errors.
- Ensure network connectivity to Pinecone and that the index exists and is healthy.

## Integration with other modules

- Core: uses `VectorStore`, `VectorSearch*`, `Metadata`, `VectorStoreUpdater`.
- Debezium: feeds CDC events into `VectorStoreUpdater` to upsert/delete vectors.
- Spring: provides data retrieval utilities, enabling `SimilaritySearchHandler` to return natural entities.
- Demo: runnable examples showing end-to-end wiring.

## Build

- Build from the repository root:
  - `mvn -q -DskipTests package`
