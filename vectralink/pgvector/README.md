# Vectralink pgvector

The pgvector module provides a concrete VectorStore backed by the pgvector vector database. It implements the Core `VectorStore<String, Vector.Float>` API to persist float embeddings, attach arbitrary metadata (payload), and perform similarity search.

If you use pgvector as your vector DB, this module is the drop-in implementation to connect Vectralink’s Core abstractions to a running pgvector instance.

## What’s inside

- `PgvectorVectorStore` (and `PgvectorVectorStore.Default`):
  - Stores float vectors with auto-generated UUID string IDs.
  - Attaches Core `Metadata` as Json payload in `metadata`field.
  - Provides search via pgvector’s nearest-neighbor API and returns Core `VectorSearchResult<String, Vector.Float>`.
  - Supports deletions by IDs and `Metadata.ID`.
  - **TODO**: Supports deletions by metadata (payload) filters.

Packages live under `ai.cyrock.vectralink.pgvector`.

## How it fits into Vectralink

- Core defines neutral APIs for vectors, metadata, storage, and search.
- pgvector implements `VectorStore<String, Vector.Float>` so you can:
  - insert embeddings along with `Metadata` that links back to your domain (e.g., `Metadata.ID`).
  - run vector similarity searches and receive matches with scores, original vectors, and metadata.
  - delete by vector IDs or by metadata (`Metadata.ID`) conditions to keep the store in sync.
- Use it directly, or wire it with Core’s `VectorStoreUpdater` for CDC-driven synchronization, and `SimilaritySearchHandler` for natural-data search.

## Prerequisites

- Java 21
- A running Postgres instance (local or remote) with pgvector
  - Default port is 5432
  - Make sure the target table exists with the correct vector size
  - Make sure the `vector` extension for the datasource is active
  - Make sure the target table has the following required fields: 
    - `id` DataType: `UUID`, primary, no autoId
    - `vector` DataType: `vector` with correct vector size / dimension
    - `metadata` Datatype: `json`
- pgvector Java client is brought by this module’s dependencies

## Quick start

### 1) Create a pgvector datasource and store

```java
import ai.cyrock.vectralink.*;
import ai.cyrock.vectralink.pgvector.PgvectorVectorStore;
import org.postgresql.ds.PGSimpleDataSource;

// 1) Build a pgvector datasource (adjust host/port/databasename and credentials to your environment)
PGSimpleDataSource source = new PGSimpleDataSource();
source.setUrl("jdbc:postgresql://localhost:5432/pgvector_demo");
source.setUser("postgres");
source.setPassword("postgres");

// 2) Ensure "vector" extension is active
try(Connection conn = source.getConnection();
  Statement setupStmt = conn.createStatement();) 
{
  setupStmt.executeUpdate("CREATE EXTENSION IF NOT EXISTS vector");
}

String tablename = "products_embeddings"; // ensure it exists in DataSource with correct vector size

// 3) Create the VectorStore
PgvectorVectorStore store = PgvectorVectorStore.New(source, tablename);
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

// VectorStoreUpdater keeps pgvector in sync based on DataChange events
VectorStoreUpdater updater = VectorStoreUpdater.New(
    vectorizer,
    idProvider,
    store
);

DataChangeNotifier notifier = DataChangeNotifier.New(updater);
```

Now you can feed `notifier` with create/update/delete events (e.g., from the Debezium module) and keep pgvector updated automatically.

## Metadata and payload mapping

`PgvectorVectorStore` converts Core `Metadata` to JSON values.

Search results return the stored payload back as Core `Metadata`.

## Distance metrics, vector size, and precision

- `PgvectorVectorStore` operates on Core `Vector.Float` (float32 arrays).
- Configure your table in pgvector with the correct vector size that matches how your embeddings were generated.
- Metric selection (e.g., cosine) and collection parameters are predefined in `PgvectorVectorStore`.

## Error handling

- Client calls are performed via jdbc calls; runtime exceptions wrap interruptions or execution errors.
- Ensure network connectivity to pgvector and that the table exists.

## Integration with other modules

- Core: uses `VectorStore`, `VectorSearch*`, `Metadata`, `VectorStoreUpdater`.
- Debezium: feeds CDC events into `VectorStoreUpdater` to upsert/delete vectors.
- Spring: provides data retrieval utilities, enabling `SimilaritySearchHandler` to return natural entities.
- Demo: runnable examples showing end-to-end wiring.

## Build

- Build from the repository root:
  - `mvn -q -DskipTests package`
