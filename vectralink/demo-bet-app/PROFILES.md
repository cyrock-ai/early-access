# Demo Betting Application - Vector Database Profiles

This betting demo application supports multiple vector database backends through Maven profiles.

## Supported Vector Databases

The application can be built and run with any of the following vector store backends:

| Profile     | Vector Store | SDK Version | Description                            |
|-------------|--------------|-------------|----------------------------------------|
| `qdrant`    | Qdrant       | 1.15.0      | Default profile, gRPC-based            |
| `milvus`    | Milvus       | 2.6.9       | High-performance vector DB             |
| `pgvector`  | PostgreSQL   | 0.1.6       | PostgreSQL with vector extension       |
| `weaviate`  | Weaviate     | Latest      | GraphQL-based vector search            |

## Building with Profiles

### Build with specific profile

```bash
# Build with Qdrant (default)
mvn clean package -P qdrant

# Build with Milvus
mvn clean package -P milvus

# Build with PGVector
mvn clean package -P pgvector

# Build with Weaviate
mvn clean package -P weaviate

<!-- Pinecone profile removed -->
```

### Run with specific profile

```bash
# Run with Qdrant
mvn spring-boot:run -P qdrant

# Run with Milvus
mvn spring-boot:run -P milvus
```

## Profile Architecture

Each profile provides:

1. **Profile-specific Launcher** (`ApplicationXxx.java`)
   - Dedicated main class for easy IDE execution
   - Automatically activates the correct Spring profile
   - Located in: `src/main/profiles/{profile}/ai/cyrock/vectralink/demo/bet/`
   - Examples: `ApplicationQdrant`, `ApplicationMilvus`, `ApplicationPGVector`

2. **Container Configuration** (`TestcontainersXxxConfig.java`)
   - Starts vector database container
   - Configures connection parameters
   - Located in: `src/main/profiles/{profile}/ai/cyrock/vectralink/demo/bet/config/`

3. **Vectralink Configuration** (`VectralinkConfig.java`)
   - Creates vector store bean
   - Configures vectorizer
   - Sets up Debezium CDC connector
   - Located in: `src/main/profiles/{profile}/ai/cyrock/vectralink/demo/bet/config/`

4. **Profile-specific Tests**
   - Integration tests for each vector store
   - Located in: `src/test/profiles/{profile}/`

## How Profiles Work

Maven profiles use `build-helper-maven-plugin` to add profile-specific source directories:

- Main sources: `src/main/profiles/{profile}/`
- Test sources: `src/test/profiles/{profile}/`

The active profile's sources are compiled alongside the base application code in `src/main/java/`.

## Application Services

The application services (like `OpportunityServiceImpl`) are **database-agnostic** and work with any vector store through the `VectorStore<?, Vector.Float>` interface.

Profile-specific configuration beans provide the concrete implementation:
- `QdrantVectorStore` for qdrant profile
- `MilvusVectorStore` for milvus profile  
- `PgVectorStore` for pgvector profile
- etc.

## API Endpoints

All profiles expose the same REST API:

- `GET /api/opportunities?minOdds={min}&maxOdds={max}` - Find betting opportunities by odds range

The vector similarity search efficiently filters odds within the specified range.

## Testing

Run tests with specific profile:

```bash
# Test with Qdrant
mvn test -P qdrant

# Test with Milvus
mvn test -P milvus
```

Tests use the same Testcontainers instances as the application for consistency.

## Adding New Vector Database

To add support for a new vector database:

1. Create profile in `pom.xml` with dependencies
2. Create `src/main/profiles/{profile}/ai/cyrock/vectralink/demo/bet/config/`:
   - `TestcontainersXxxConfig.java` - container setup
   - `VectralinkConfig.java` - vector store configuration
3. Add `@Profile("{profile}")` annotations to configuration classes
4. Create profile-specific tests in `src/test/profiles/{profile}/`
5. Update this README

## Dependencies

Profile-specific dependencies are managed in `pom.xml` under `<profiles>` section.

Base application dependencies (MySQL, Debezium, Spring Boot) are in main `<dependencies>` section and shared across all profiles.

