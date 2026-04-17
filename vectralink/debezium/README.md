# Vectralink Debezium

The Debezium module integrates Debezium Embedded Engine to stream Change Data Capture (CDC) events from your relational database into Vectralink’s synchronization pipeline.

It provides a small, focused API to run Debezium inside your JVM and forward "before/after" row images to the Core module where embeddings can be created, updated, or deleted accordingly.

## What’s inside

- `DebeziumConnector` (and `DebeziumConnector.Default`):
  - A `Service` that starts/stops a Debezium Embedded Engine.
  - Consumes change events and forwards them as `DataChange` objects via a `DataChangeNotifier`.
  - Wraps Debezium’s Kafka Connect `Struct` values as `Data` using a lightweight adapter so you can access fields by name.

Packages live under `ai.cyrock.vectralink.debezium`.

## How it fits into Vectralink

- Debezium emits CDC row-change events (create/update/delete) from your source database.
- `DebeziumConnector.Default` converts those into Core’s `DataChange` (`before`/`after`) and calls `DataChangeNotifier`.
- In Core you typically use `VectorStoreUpdater` as the `DataChangeHandler` to:
  - on create: vectorize `after` and insert into your `VectorStore`;
  - on update: delete by metadata for `before`, then insert vector for `after`;
  - on delete: delete by metadata for `before`.

This keeps your embeddings in sync with your natural data.

## Quick start

### 1) Provide a DataChange pipeline

```java
import ai.cyrock.vectralink.*;
import ai.cyrock.vectralink.debezium.DebeziumConnector;

// 1) Your vectorizer
Vectorizer<Vector.Float> vectorizer = data -> Vector.Float( /* call your embedding provider */ 0.1f, 0.2f );

// 2) Provide a stable ID from CDC records (field name must exist in your table/schema)
DataIdProvider<String> idProvider = d -> d.get("id");

// 3) Your VectorStore implementation (e.g., Qdrant)
// VectorStore<String, Vector.Float> vectorStore = new QdrantVectorStore(...);

// 4) Wire the updater and notifier
VectorStoreUpdater updater = VectorStoreUpdater.New(vectorizer, idProvider, /* vectorStore */ null);
DataChangeNotifier notifier = DataChangeNotifier.New(updater);
```

### 2) Configure Debezium Embedded

Supply standard Debezium engine properties. Below is a minimal example for MySQL; consult Debezium docs for your database and production hardening.

```java
import java.util.Properties;

Properties props = new Properties();
props.setProperty("name", "mysql-embedded-connector");
props.setProperty("connector.class", "io.debezium.connector.mysql.MySqlConnector");
props.setProperty("database.hostname", "localhost");
props.setProperty("database.port", "3306");
props.setProperty("database.user", "debezium");
props.setProperty("database.password", "dbz");
props.setProperty("database.server.id", "184054");
props.setProperty("database.server.name", "mysqlserver");
props.setProperty("database.include.list", "appdb");
props.setProperty("table.include.list", "appdb.products");
props.setProperty("include.schema.changes", "false");
props.setProperty("topic.prefix", "dbz");
// Snapshotting (choose per your needs)
props.setProperty("snapshot.mode", "initial");
```

PostgreSQL example (partial):

```java
Properties props = new Properties();
props.setProperty("name", "pg-embedded-connector");
props.setProperty("connector.class", "io.debezium.connector.postgresql.PostgresConnector");
props.setProperty("database.hostname", "localhost");
props.setProperty("database.port", "5432");
props.setProperty("database.user", "postgres");
props.setProperty("database.password", "postgres");
props.setProperty("database.dbname", "appdb");
props.setProperty("schema.include.list", "public");
props.setProperty("table.include.list", "public.products");
props.setProperty("topic.prefix", "dbz");
// See Debezium docs for logical decoding setup and slot configuration
```

Important: The connector expects the change value to contain `before` and `after` fields (standard Debezium payload). The provided implementation checks for their presence before emitting a `DataChange`.

### 3) Start the connector

```java
DebeziumConnector connector = DebeziumConnector.New(props, notifier);
connector.start();

// ... later, when shutting down
connector.stop();
```

## API reference (essentials)

- `DebeziumConnector.New(Properties debeziumProperties, DataChangeNotifier notifier)`
  - Creates a `DebeziumConnector.Default` with your configuration and downstream notifier.
- Lifecycle (`Service<DebeziumConnector>`):
  - `start()` spins up the Debezium Engine on a single-threaded executor and begins streaming events.
  - `stop()` shuts down the executor and engine.
- Event handling:
  - Internally implements `DebeziumEngine.ChangeConsumer<RecordChangeEvent<SourceRecord>>#handleBatch(...)`.
  - For each event, if the record contains `before`/`after`, it creates `DataChange(before?, after?)` using an internal `StructDataWrapper` that implements Core’s `Data` interface.

## Mapping CDC to your domain

Debezium’s record values are Kafka Connect `Struct`s. The adapter exposes:

- `Data.entity()` -> the raw `Struct`
- `Data.keys()`   -> all field names from the schema
- `Data.get(String key)` -> field value by name

Your `DataIdProvider` should return a stable identifier coming from one of these fields (e.g., the primary key).

## Tips and gotchas

- Ensure your connector properties are correct for the DB type, version, and security settings.
- For MySQL, configure a replica user and enable binlog. For Postgres, set up logical decoding and replication slots.
- Snapshot strategy matters: `initial`, `schema_only`, `never`, etc., depending on your bootstrap plan.
- The `table.include.list` should be as specific as possible to limit noise.
- Consider filtering out tombstone/heartbeat topics if present (via Debezium properties).
- Handle backpressure by keeping the downstream processing fast; the embedded engine runs in-process.

## Integration with other modules

- Core: consumes `DataChange` via `DataChangeNotifier` and `VectorStoreUpdater`.
- Qdrant: provides a concrete `VectorStore` to persist embeddings and perform vector search.
- Spring: helper utilities to retrieve domain objects by ID, enabling natural-data similarity search.
- Demo: runnable examples showing end-to-end wiring.

## Requirements and build

- Java 21
- Debezium Embedded Engine (brought by this module’s dependencies)
- Build from the repository root:
  - `mvn -q -DskipTests package`

