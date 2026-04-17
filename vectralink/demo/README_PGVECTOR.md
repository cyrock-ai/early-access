# Vectralink Demo

A runnable Spring Boot + Vaadin application that demonstrates Vectralink end‑to‑end:

- MySQL (Testcontainers) stores natural data (German cities).
- Debezium Embedded streams CDC events from MySQL into Vectralink Core.
- A Vectorizer converts each city’s coordinates into a 3‑dimensional unit‑sphere vector.
- Pgvector (Testcontainers) persists vectors and performs similarity search.
- A Vaadin map UI lets you insert random cities and click a city to find nearby ones by vector similarity.

Packages live under `ai.cyrock.vectralink.demo-pgvector` subpackages.

## What’s inside

- Spring Boot application entrypoint: `src/main/java/ai/cyrock/vectralink/Application.java`
- Vaadin view with map UI: `src/main/java/ai/cyrock/vectralink/views/DemoView.java`
  - Button “Add random cities” inserts 10 random German cities into MySQL and shows markers on the map.
  - Clicking a marker triggers a similarity search around that city.
- Domain entity and repository:
  - `entity/Worldcity.java` (JPA entity for table `worldcities`)
  - `repo/WorldcityRepository.java` (Spring Data `CrudRepository`)
- Configuration:
  - `config/ContainerConfig.java` launches MySQL 5.7.34 and Qdrant 1.15.5 via Testcontainers and exposes them on localhost (3306, 6333/6334).
  - `config/VectralinkConfig.java` wires the Vectralink pipeline:
    - `Vectorizer<Vector.Float>`: turns `(lat,lng)` into a 3D unit‑sphere vector using `WorldCoordinateUtils.toUnitSphere(...)`.
    - `PgvectorVectorStore` (table `vectorstore`, size 3).
    - `DebeziumConnector` (embedded) → `VectorStoreUpdater` to keep vectors in sync.
    - `SimilaritySearchHandler` using the vectorizer, Qdrant store, and a Spring Data backed `DataRetriever` (`CrudRepositoryDataRetriever`).
- Static data: `src/main/resources/worldcities-ger.json` used to feed random German cities.

See also:
- Core README: `../core/README.md`
- pgvector README: `../pgvector/README.md`
- Debezium README: `../debezium/README.md`
- Spring README: `../spring/README.md`

## Prerequisites

- Java 21
- Docker Desktop (or compatible) running — required by Testcontainers
  - Free local ports: 3306 (MySQL), 5432 (postgre/pgvector), 8080 (demo UI)
- Internet to pull container images on first run

## Quick start

1) Build the project (from repository root):

```bash
mvn -q -DskipTests package
```

2) Run the demo app:

- Using Spring Boot plugin (from repository root):

```bash
mvn -pl demo -am spring-boot:run
```

- Or run the built JAR:

```bash
java -jar demo/target/vectralink-demo-*.jar
```

3) Open the UI:

- Demo: http://localhost:8080

4) Try it out:

- Click “Add random cities” to insert 10 cities into MySQL; markers appear on the map.
- Click any marker:
  - The app runs a similarity search with `SimilaritySearchHandler` for the chosen city.
  - Results are highlighted on the map; the center city is red, nearby matches are orange.
- Use the numeric field to adjust the maximum search distance (km). Internally this is mapped to a minimum cosine similarity threshold using `WorldCoordinateUtils.minCosine(distanceKm)`.

## How it works (pipeline)

- MySQL container is started with binlog/GTID options suitable for Debezium (`ContainerConfig`). It also bootstraps the `worldcities` table.
- Debezium Embedded Engine connects to the MySQL container and emits `before/after` row images.
- `DebeziumConnector` adapts those events to Core `DataChange` and forwards to `DataChangeNotifier`.
- `VectorStoreUpdater` uses:
  - The `Vectorizer` to produce a `Vector.Float` of size 3 from `(lat, lng)`.
  - `DataIdProvider` that reads the entity’s `id` and puts it into `Metadata.ID` for correlation.
  - The `PgvectorVectorStore` to insert/delete vectors accordingly.
- For querying, `SimilaritySearchHandler` vectorizes the clicked city and asks Qdrant for nearest neighbors. It then retrieves the corresponding `Worldcity` rows via `CrudRepositoryDataRetriever` and returns `SimilaritySearchResult` at the natural data level.

### Relevant beans (excerpt)

```java
// Vectorizer: (lat,lng) -> unit-sphere 3D vector
@Bean
Vectorizer<Vector.Float> getVectorizer() {
    return data -> Vector.Float(
        ai.cyrock.vectralink.util.WorldCoordinateUtils.toUnitSphere(
            data.get("lat"),
            data.get("lng")
        )
    );
}

// Qdrant store: size=3
@Bean
PgvectorVectorStore pgvectorVectorStore(PostgreSQLContainer postgre) throws Exception { /* ... */ }

// Debezium -> VectorStoreUpdater pipeline
@Bean(destroyMethod = "stop")
DebeziumConnector getDebeziumConnector(Vectorizer<Vector.Float> vectorizer, PgvectorVectorStore vectorStore) { /* ... */ }

// Natural-data similarity search
@Bean
SimilaritySearchHandler getSimilaritySearchHandler(
    Vectorizer<Vector.Float> vectorizer,
    PgvectorVectorStore vectorStore,
    WorldcityRepository worldcityRepository
) {
    return SimilaritySearchHandler.New(
        vectorizer,
        vectorStore,
        ai.cyrock.vectralink.spring.data.CrudRepositoryDataRetriever.New(worldcityRepository)
    );
}
```

## Configuration notes

- Ports are bound to localhost for convenience:
  - MySQL: 3306
  - Postgre/pgvector HTTP: 5432
  - Demo UI: 8080
- Debezium connection properties (see `VectralinkConfig#mysqlConnectorProperties`) use the MySQL container default credentials `root/test` and write offset/schema history files under `./target/test-data`.
- pgvector table `vectorstore` is created at startup with vector size 3.
- Vaadin development mode will prepare the frontend on first run (downloads Node and builds web assets if needed).

## Troubleshooting

- Docker not running or pull fails → start Docker Desktop and retry.
- Port already in use → stop the conflicting service or change port mappings in `ContainerConfig`.
- First run is slow → Testcontainers pulls images and Vaadin builds frontend; subsequent runs are faster.
- MySQL binlog issues → the container is started with required flags; if customized, ensure Debezium requirements are met.

## Related modules

- Core abstractions and quick start: `../core/README.md`
- pgvector vector store: `../pgvector/README.md`
- Debezium integration: `../debezium/README.md`
- Spring helpers: `../spring/README.md`

## Build from root

```bash
mvn -q -DskipTests package
```

Then run the demo as described above.
