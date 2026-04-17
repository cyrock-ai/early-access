# Vectralink Spring

The Spring module provides small, focused adapters to integrate Vectralink Core with Spring Data repositories. It lets you plug your existing `CrudRepository` into Core’s natural-data similarity search so you can retrieve your domain entities directly from vector search matches.

## What’s inside

- `CrudRepositoryDataRetriever<T, ID>` (and `CrudRepositoryDataRetriever.Default`):
  - An adapter that implements Core’s `DataRetriever<ID>` on top of a Spring Data `CrudRepository<T, ID>`.
  - Converts entities returned by the repository into Core `Data` objects via `Data.New(entity)`.
  - Supports retrieving a single entity by ID and batching `findAllById` into a `List<Data>`.

Packages live under `ai.cyrock.vectralink.spring.data`.

## How it fits into Vectralink

- Core’s `SimilaritySearchHandler` returns matches at the natural-data level by:
  1) vectorizing your input (using a `Vectorizer`),
  2) running vector search (via a `VectorSearchHandler`, e.g., your `VectorStore`),
  3) looking up your domain objects by IDs present in match metadata (`Metadata.ID`).
- This module provides step (3) for Spring apps: a `DataRetriever<ID>` backed by your `CrudRepository`.

Typical end-to-end wiring:

````java
import ai.cyrock.vectralink.*;
import ai.cyrock.vectralink.spring.data.CrudRepositoryDataRetriever;
import org.springframework.data.repository.CrudRepository;

// Your domain
record Product(String id, String title, String description) {}

// Your Spring Data repository
interface ProductRepository extends CrudRepository<Product, String> {}

// Vectorizer (example)
Vectorizer<Vector.Float> vectorizer = d -> Vector.Float( /* embed */ 0.1f, 0.2f, 0.3f );

// Vector store (e.g., Qdrant) that also serves as VectorSearchHandler
// VectorStore<String, Vector.Float> store = new QdrantVectorStore(...);

// Data retriever backed by Spring Data repository
ProductRepository productRepository = /* injected by Spring */ null;
DataRetriever<String> retriever = CrudRepositoryDataRetriever.New(productRepository);

// Build SimilaritySearchHandler
SimilaritySearchHandler simSearch = SimilaritySearchHandler.New(
    vectorizer,
    /* vectorSearchHandler */ /* store */ null,
    retriever
);

// Perform natural-data similarity search
Data origin = Data.New(new Product("p-1", "Wireless Mouse", "Ergonomic, silent"));
SimilaritySearchRequest request = SimilaritySearchRequest.New(origin, 10, 0.0);
// SimilaritySearchResult result = simSearch.search(request);
// result.matches().forEach(m -> {
//     double score = m.score();
//     Data similar = m.data();      // wraps a Product loaded via repository
//     Product p = similar.entity(); // cast back if needed
// });
````

Notes:
- The `SimilaritySearchHandler` expects `Metadata.ID` to be present in the vector search matches' metadata. Make sure your `VectorStore` stores that when inserting vectors (Core and Qdrant README show how to set it).
- The order of returned `Data` is matched to the order of vector search matches. If some IDs cannot be found, Core throws a runtime exception.

## Spring Boot style configuration (example)

Below is a simple configuration illustrating how you might wire beans in a Spring Boot application. Adjust to your application needs.

````java
import ai.cyrock.vectralink.*;
import ai.cyrock.vectralink.spring.data.CrudRepositoryDataRetriever;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
class VectralinkConfig {

    @Bean
    Vectorizer<Vector.Float> vectorizer() {
        return d -> Vector.Float( /* call your embedding service */ 0.1f, 0.2f );
    }

    @Bean
    DataIdProvider<String> idProvider() {
        // Ensure this matches your entity ID field
        return d -> d.get("id");
    }

    @Bean
    DataRetriever<String> dataRetriever(ProductRepository productRepository) {
        return CrudRepositoryDataRetriever.New(productRepository);
    }

    @Bean
    SimilaritySearchHandler similaritySearchHandler(
        Vectorizer<Vector.Float> vectorizer,
        VectorSearchHandler<?, Vector.Float> vectorSearchHandler, // e.g., your VectorStore bean
        DataRetriever<String> dataRetriever
    ) {
        return SimilaritySearchHandler.New(vectorizer, vectorSearchHandler, dataRetriever);
    }
}
````

To keep embeddings in sync from CDC, wire Debezium + `VectorStoreUpdater` similarly (see the Debezium README for details).

## ID mapping

- Your Spring entity ID type must match the ID used in `Metadata.ID` when vectors are inserted.
- For example, if your repository is `CrudRepository<Product, String>`, then your `VectorStore` should store `Metadata.ID` as the `String` product ID.

## Error handling

- `CrudRepositoryDataRetriever.Default#retrieveAllByIds` converts the iterable returned by `findAllById` into a stream. If some IDs are missing, the Core `SimilaritySearchHandler` will detect a size mismatch and throw (by design), helping you keep consistency between the vector store and the source of truth.

## Integration with other modules

- Core: provides `SimilaritySearchHandler`, `DataRetriever`, `Metadata`, and the vector abstractions.
- Qdrant: concrete `VectorStore<String, Vector.Float>` storing vectors and payload; works out of the box with this retriever.
- Debezium: source of `DataChange` events; pair with `VectorStoreUpdater` to keep vectors in sync.
- Demo: shows how pieces can be combined in a runnable application.

## Requirements and build

- Java 21
- Spring Data (e.g., `spring-data-commons` / `spring-boot-starter-data-*`) provided by your application.
- Build from the repository root:
  - `mvn -q -DskipTests package`

## API reference (essentials)

- `CrudRepositoryDataRetriever.New(CrudRepository<T, ID> repository)`
  - Returns a `DataRetriever<ID>` backed by the given repository.
- Methods implemented:
  - `Optional<Data> retrieveById(ID id)` -> wraps `repository.findById(id)`
  - `List<Data> retrieveAllByIds(List<ID> ids)` -> wraps `repository.findAllById(ids)`
