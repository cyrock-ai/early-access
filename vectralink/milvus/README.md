# Vectralink Milvus

The Milvus module provides a concrete VectorStore backed by the Milvus vector database. It implements the Core `VectorStore<String, Vector.Float>` API to persist float embeddings, attach arbitrary metadata (payload), and perform similarity search.

If you use Milvus as your vector DB, this module is the drop-in implementation to connect Vectralink’s Core abstractions to a running Milvus instance.

## What’s inside

- `MilvusVectorStore` (and `MilvusVectorStore.Default`):
  - Stores float vectors with auto-generated UUID string IDs.
  - Attaches Core `Metadata` as Json data in `metadata` field
  - Provides search via Milvus’s nearest-neighbor API and returns Core `VectorSearchResult<String, Vector.Float>`.
  - Supports deletions by IDs and `Metadata.ID`.
  - **TODO**: Supports deletions by metadata (payload) filters.

Packages live under `ai.cyrock.vectralink.milvus`.

## How it fits into Vectralink

- Core defines neutral APIs for vectors, metadata, storage, and search.
- Milvus implements `VectorStore<String, Vector.Float>` so you can:
  - insert embeddings along with `Metadata` that links back to your domain (e.g., `Metadata.ID`).
  - run vector similarity searches and receive matches with scores, original vectors, and metadata.
  - delete by vector IDs or by metadata (`Metadata.ID`) conditions to keep the store in sync.
- Use it directly, or wire it with Core’s `VectorStoreUpdater` for CDC-driven synchronization, and `SimilaritySearchHandler` for natural-data search.

## Prerequisites

- Java 21
- A running Milvus instance (local or remote)
  - Default port is 19530
  - Make sure the target collection exists with the correct vector size and distance metric (e.g., cosine, dot, euclid)
  - Make sure the target collection has the following required fields: 
    - `id` DataType: `VarChar`, primary, no autoId
    - `vector` DataType: `FloatVector` with correct vector size / dimension
    - `metadata` Datatype: `JSON`
  - Make sure the `vector` field has an index with correct distance metric.
  - Consider adding an additional index for the `id` field.
- Milvus Java client is brought by this module’s dependencies

## Quick start

### 1) Create a Milvus client and store

```java
import ai.cyrock.vectralink.*;
import ai.cyrock.vectralink.milvus.MilvusVectorStore;
import io.milvus.v2.client.ConnectConfig;
import io.milvus.v2.client.MilvusClientV2;

// 1) Build a Milvus client (adjust host to your environment)
ConnectConfig  config = ConnectConfig.builder().uri("localhost").build();
MilvusClientV2 client = new MilvusClientV2(config);

String collection = "products_embeddings"; // ensure it exists in Milvus with required fields and correct vector size/metric

// 2) Create the VectorStore
MilvusVectorStore store = MilvusVectorStore.New(client, collection);
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

// VectorStoreUpdater keeps Milvus in sync based on DataChange events
VectorStoreUpdater updater = VectorStoreUpdater.New(
    vectorizer,
    idProvider,
    store
);

DataChangeNotifier notifier = DataChangeNotifier.New(updater);
```

Now you can feed `notifier` with create/update/delete events (e.g., from the Debezium module) and keep Milvus updated automatically.

## Metadata and payload mapping

`MilvusVectorStore` converts Core `Metadata` json-encoded metadata value. 

Search results return the stored payload back as Core `Metadata`.

**TODO** Deletion by metadata translates each provided key-value pair into a Milvus filter condition; all conditions are combined with logical AND.

## Distance metrics, vector size, and precision

- `MilvusVectorStore` operates on Core `Vector.Float` (float32 arrays).
- Configure your collection in Milvus with the required fields, correct vector size and distance metric that matches how your embeddings were generated.
- Metric selection (e.g., cosine) and collection parameters are controlled on the Milvus side at collection creation time.

## Error handling

- Client calls are performed via async gRPC and awaited; runtime exceptions wrap interruptions or execution errors.
- Ensure network connectivity to Milvus and that the collection exists and is healthy.

## Integration with other modules

- Core: uses `VectorStore`, `VectorSearch*`, `Metadata`, `VectorStoreUpdater`.
- Debezium: feeds CDC events into `VectorStoreUpdater` to upsert/delete vectors.
- Spring: provides data retrieval utilities, enabling `SimilaritySearchHandler` to return natural entities.
- Demo: runnable examples showing end-to-end wiring.

## Build

- Build from the repository root:
  - `mvn -q -DskipTests package`
