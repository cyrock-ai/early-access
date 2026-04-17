# Vectralink Weaviate

The Weaviate module provides a concrete VectorStore backed by the Weaviate vector database. It implements the Core `VectorStore<String, Vector.Float>` API to persist float embeddings, attach arbitrary metadata (payload), and perform similarity search.

If you use Weaviate as your vector DB, this module is the drop-in implementation to connect Vectralink’s Core abstractions to a running Weaviate instance.

## What’s inside

- `WeaviateVectorStore` (and `WeaviateVectorStore.Default`):
  - Stores float vectors with auto-generated UUID string IDs.
  - Attaches Core `Metadata` as Json payload in `metadata` field.
  - Stores `Metadata.ID` value from Core `Metadata` in `_ext_id` field.
  - Provides search via Weaviate’s nearest-neighbor API and returns Core `VectorSearchResult<String, Vector.Float>`.
  - Supports deletions by IDs and `Metadata.ID`.
  - **TODO**: Supports deletions by metadata (payload) filters.

Packages live under `ai.cyrock.vectralink.weaviate`.

## How it fits into Vectralink

- Core defines neutral APIs for vectors, metadata, storage, and search.
- Weaviate implements `VectorStore<String, Vector.Float>` so you can:
  - insert embeddings along with `Metadata` that links back to your domain (e.g., `Metadata.ID`).
  - run vector similarity searches and receive matches with scores, original vectors, and metadata.
  - delete by vector IDs or by metadata (`Metadata.ID`) conditions to keep the store in sync.
- Use it directly, or wire it with Core’s `VectorStoreUpdater` for CDC-driven synchronization, and `SimilaritySearchHandler` for natural-data search.

## Prerequisites

- Java 21
- A running Weaviate instance (local or remote)
  - Make sure the target collection exists with the correct vector size and distance metric (e.g., cosine, dot, euclid)
  - Target collection requires fields `_ext_id` and `metadata` with `TEXT` datatype
- Weaviate Java client is brought by this module’s dependencies

## Quick start

### 1) Create a Weaviate client and store

```java
import ai.cyrock.vectralink.*;
import ai.cyrock.vectralink.weaviate.WeaviateVectorStore;
import io.weaviate.client.Config;
import io.weaviate.client.WeaviateClient;

// 1) Build a Weaviate client (adjust host/port/tls to your environment)
Config config = new Config("http", "localhost:8080");
WeaviateClient client = new WeaviateClient(config);

String collection = "products_embeddings"; // ensure it exists in Weaviate with required fields

// 2) Create the VectorStore
WeaviateVectorStore store = WeaviateVectorStore.New(client, collection);
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
String entryId = ids.getFirst();
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

// VectorStoreUpdater keeps Weaviate in sync based on DataChange events
VectorStoreUpdater updater = VectorStoreUpdater.New(
    vectorizer,
    idProvider,
    store
);

DataChangeNotifier notifier = DataChangeNotifier.New(updater);
```

Now you can feed `notifier` with create/update/delete events (e.g., from the Debezium module) and keep Weaviate updated automatically.

## Metadata and payload mapping

`WeaviateVectorStore` converts Core `Metadata` to json-encoded metadata value. `Metadata.ID` is stored as text in extra field

Search results return the stored payload back as Core `Metadata`.

**TODO** Deletion by metadata translates each provided key-value pair into a Weaviate filter condition; all conditions are combined with logical AND.

## Distance metrics, vector size, and precision

- `WeaviateVectorStore` operates on Core `Vector.Float` (float32 arrays).
- Configure your collection in Weaviate with the correct distance metric that matches how your embeddings were generated.
- Metric selection (e.g., cosine) and collection parameters are controlled on the Weaviate side at collection creation time.

## Error handling

- Client calls are performed via sync calls; runtime exceptions wrap execution errors.
- Ensure network connectivity to Weaviate and that the collection exists and is healthy.

## Integration with other modules

- Core: uses `VectorStore`, `VectorSearch*`, `Metadata`, `VectorStoreUpdater`.
- Debezium: feeds CDC events into `VectorStoreUpdater` to upsert/delete vectors.
- Spring: provides data retrieval utilities, enabling `SimilaritySearchHandler` to return natural entities.
- Demo: runnable examples showing end-to-end wiring.

## Build

- Build from the repository root:
  - `mvn -q -DskipTests package`
