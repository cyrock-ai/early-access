# Vectralink Core

Vectralink Core provides the foundational abstractions to work with vector embeddings alongside your domain data. It defines neutral interfaces for vectors, metadata, search, vectorization, and change propagation that other modules (Qdrant, Spring, Debezium, ...) build upon.

If you want to integrate a new vector database, an embedding provider, or a data source, this module is the place to start.

## What’s inside

Core is a pure-Java module (Java 21) with no runtime dependencies beyond the JDK. It contains the following building blocks:

- Data and metadata
  - `Data`: a lightweight wrapper to access arbitrary domain objects (POJOs/records/JSON-like) in a uniform way.
  - `Metadata`: key-value store for embedding context and identifiers. Includes a well-known key `Metadata.ID` to link back to your natural data.

- Vectors and vectorization
  - `Vector`: sealed interface with `Vector.Float` and `Vector.Double` implementations.
  - `Vectorizer<V extends Vector<?>>`: converts `Data` into vectors (embeddings).

- Vector storage and search
  - `VectorStore<VID, V extends Vector<?>>`: insert and delete vectors, extends `VectorSearchHandler` for similarity search.
  - `VectorSearchHandler<VID, V>`: performs searches using a `VectorSearchRequest<V>` and returns a `VectorSearchResult<VID, V>` composed of `VectorSearchMatch<VID, V>`.

- Natural-data similarity search (end-to-end convenience)
  - `SimilaritySearchHandler`: orchestrates vectorization + vector search + data retrieval to return natural `Data` matches.
  - `DataRetriever<ID>`: fetches natural data by IDs found in vector matches.

- Change data capture (CDC) integration primitives
  - `DataChange(before, after)`: represents create/update/delete events.
  - `DataChangeHandler`: callback interface for handling changes.
  - `DataChangeNotifier`: helper that dispatches `DataChange` events to a handler.
  - `DataIdProvider<ID>`: extracts a stable ID from `Data` used to correlate embeddings.
  - `VectorStoreUpdater`: a `DataChangeHandler` that keeps a `VectorStore` in sync with your source of truth.

Packages live under `ai.cyrock.vectralink`.

## Quick start

Below are minimal examples to illustrate how the core API pieces fit together. These snippets are framework-agnostic; real implementations are provided in other modules (e.g., `qdrant`, `spring`, `debezium`).

### 1) Create vectors and store them

```java
import ai.cyrock.vectralink.*;
import java.util.Map;

// 1) Wrap your domain object as Data
record Product(String id, String title, String description) {}

Data data = Data.New(new Product("p-1", "Wireless Mouse", "Ergonomic, silent clicks"));

// 2) Vectorize it (dummy vectorizer example)
Vectorizer<Vector.Float> vectorizer = d -> {
    // your embedding logic here (e.g., call an embedding service)
    return Vector.Float(0.12f, 0.98f, 0.53f);
};
Vector.Float vector = vectorizer.vectorize(data);

// 3) Prepare metadata linking back to your data ID
Metadata md = Metadata.New(Map.of(Metadata.ID, "p-1"));

// 4) Insert into a VectorStore (use a real implementation from another module)
// VectorStore<String, Vector.Float> store = ... e.g., QdrantVectorStore from the qdrant module
// String vid = store.insert(vector, md);
```

### 2) Run vector similarity search

```java
// Build a vector search request
VectorSearchRequest<Vector.Float> req = VectorSearchRequest.New(
    vector,    // query vector
    10,        // max results
    0.0        // min score threshold
);

// VectorSearchResult<String, Vector.Float> result = store.search(req);
// for (VectorSearchMatch<String, Vector.Float> match : result.matches()) {
//     String idFromMetadata = match.metadata().get(Metadata.ID);
//     double score = match.score();
//     // use idFromMetadata to fetch your domain object
// }
```

### 3) Natural data similarity search (all-in-one)

```java
// DataRetriever maps vector-match IDs back to your domain data
DataRetriever<String> retriever = ids -> /* load all products by IDs */ java.util.List.of();

// Wire SimilaritySearchHandler with a Vectorizer + VectorSearchHandler (from your VectorStore)
// VectorSearchHandler<?, Vector.Float> vectorSearch = store; // VectorStore extends VectorSearchHandler
SimilaritySearchHandler simSearch = SimilaritySearchHandler.New(
    vectorizer,
    /* vectorSearch */ null, // replace with your VectorStore or dedicated handler
    retriever
);

SimilaritySearchRequest simReq = SimilaritySearchRequest.New(
    data, // the origin object we want similar items for
    10,
    0.0
);

// SimilaritySearchResult simResult = simSearch.search(simReq);
// simResult.matches().forEach(m -> {
//     double score = m.score();
//     Data similar = m.data();
// });
```

### 4) Keep embeddings in sync with your database changes

```java
// Provide a stable ID for each Data instance
DataIdProvider<String> idProvider = d -> d.get("id");

// VectorStoreUpdater wires vectorization + store mutations to CDC events
VectorStoreUpdater updater = VectorStoreUpdater.New(
    vectorizer,
    idProvider,
    /* vectorStore */ null // your VectorStore implementation
);

DataChangeNotifier notifier = DataChangeNotifier.New(updater);

// On create
Product created = new Product("p-2", "Keyboard", "Low profile");
notifier.notifyDataChange(new DataChange(null, Data.New(created)));

// On update
Product updated = new Product("p-2", "Keyboard", "Low profile, backlit");
notifier.notifyDataChange(new DataChange(Data.New(created), Data.New(updated)));

// On delete
notifier.notifyDataChange(new DataChange(Data.New(updated), null));
```

## Key types recap

- `Vector`
  - `Vector.Float` and `Vector.Double` plus helper constructors: `Vector.Float(...)`, `Vector.Double(...)`.
- `Metadata`
  - Dynamic key-value map; use `Metadata.New(Map.of(...))`. The `Metadata.ID` key is used to correlate vectors with natural data.
- `VectorStore<VID, V>`
  - `insert(List<V>, Metadata)` and `deleteByIds(List<VID>)` / `deleteByMetadata(Metadata)`; also `search(VectorSearchRequest<V>)` via `VectorSearchHandler`.
- `VectorSearch*`
  - `VectorSearchRequest<V>`, `VectorSearchResult<VID, V>`, `VectorSearchMatch<VID, V>`.
- `SimilaritySearch*`
  - `SimilaritySearchRequest`, `SimilaritySearchResult`, `SimilaritySearchMatch`, `SimilaritySearchHandler` to work at the natural data level.
- `Data*`
  - `Data`, `DataRetriever<ID>`, `DataIdProvider<ID>`, `DataChange`, `DataChangeHandler`, `DataChangeNotifier`.
- `Vectorizer<V>`
  - Your embedding step; implement against your provider of choice.

## Integrations in this repository

- Qdrant vector store: see `qdrant/` for `QdrantVectorStore` and configuration.
- Spring adapters: see `spring/` for repository/data retriever helpers.
- Debezium CDC: see `debezium/` for connectors and change streams.
- Demo app: see `demo/` for runnable examples wiring everything together.

## Requirements and build

- Java 21
- Maven build is driven from the root POM. Core is included as a module:
  - `mvn -q -DskipTests package` from the repository root builds all modules, including Core.

## Design notes

- Abstractions are minimal and side-effect free; implementations live in other modules.
- `VectorStore` intentionally couples storage and search to keep the minimal surface for integrations.
- `Metadata` is the link between embeddings and your domain; ensure `Metadata.ID` is set for proper correlation.

