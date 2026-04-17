# Vectralink Debezium Spring

The Debezium Spring module provides seamless integration between Vectralink Core and Debezium CDC (Change Data Capture) through Spring Boot auto-configuration.

## Features

### Bean Validation

The module validates that all required Vectralink CDC beans are properly configured in your Spring application context. It ensures that the following beans exist:
- `Vectorizer<Vector.Float>` - for converting data to vectors
- `VectorStore<?, Vector.Float>` - for storing vectors
- `DebeziumConnector` - for CDC integration

If any required bean is missing, the application will fail to start with a clear error message.

### Configuration Example

You need to define the required beans in your Spring configuration:

```java
@Configuration
public class MyVectralinkConfig {
    
    @Bean
    public Vectorizer<Vector.Float> vectorizer() {
        // Define how to convert your domain data to vectors
        return data -> Vector.Float(/* ... */);
    }
    
    @Bean
    public VectorStore<?, Vector.Float> vectorStore() throws Exception {
        // Create and configure your vector store (Qdrant, Milvus, etc.)
        return QdrantVectorStore.New(/* ... */);
    }
    
    @Bean
    public DebeziumConnector debeziumConnector(
            Vectorizer<Vector.Float> vectorizer,
            VectorStore<?, Vector.Float> vectorStore
    ) throws Exception {
        DataIdProvider<String> idProvider = d -> d.get("id");
        VectorStoreUpdater updater = VectorStoreUpdater.New(vectorizer, idProvider, vectorStore);
        DataChangeNotifier notifier = DataChangeNotifier.New(updater);
        
        Properties p = new Properties();
        p.setProperty("connector.class", "io.debezium.connector.mysql.MySqlConnector");
        // ... more properties
        
        return DebeziumConnector.New(p, notifier);
    }
}
```

The auto-configuration will validate that all three beans are present during application startup.

## Quick Start

### Step 1: Add Dependency

Maven:
```xml
<dependency>
    <groupId>ai.cyrock</groupId>
    <artifactId>vectralink-debezium-spring</artifactId>
    <version>1.0.0-SNAPSHOT</version>
</dependency>
```

### Step 2: Configure Required Beans

```java
@Configuration
public class VectralinkConfig {
    
    @Bean
    public Vectorizer<Vector.Float> vectorizer() {
        return data -> {
            float value = data.get("value");
            return Vector.Float(value / 100.0f);
        };
    }
    
    @Bean
    public VectorStore<?, Vector.Float> vectorStore(QdrantContainer qdrantContainer) throws Exception {
        QdrantClient client = new QdrantClient(/* ... */);
        
        // Create collection
        client.createCollectionAsync(
            Collections.CreateCollection.newBuilder()
                .setCollectionName("my-collection")
                .setVectorsConfig(/* ... */)
                .build()
        ).get();
        
        return QdrantVectorStore.New(client, "my-collection");
    }
    
    @Bean
    public DebeziumConnector debeziumConnector(
            Vectorizer<Vector.Float> vectorizer,
            VectorStore<?, Vector.Float> vectorStore
    ) throws Exception {
        DataIdProvider<String> idProvider = d -> d.get("id");
        VectorStoreUpdater updater = VectorStoreUpdater.New(vectorizer, idProvider, vectorStore);
        DataChangeNotifier notifier = DataChangeNotifier.New(updater);
        
        Properties p = new Properties();
        p.setProperty("name", "my-connector");
        p.setProperty("connector.class", "io.debezium.connector.mysql.MySqlConnector");
        p.setProperty("offset.storage", "org.apache.kafka.connect.storage.FileOffsetBackingStore");
        p.setProperty("offset.storage.file.filename", "./target/offsets.dat");
        p.setProperty("database.hostname", "localhost");
        p.setProperty("database.port", "3306");
        p.setProperty("database.user", "root");
        p.setProperty("database.password", "password");
        p.setProperty("table.include.list", "mydb.mytable");
        p.setProperty("topic.prefix", "my-app");
        p.setProperty("schema.history.internal", "io.debezium.storage.file.history.FileSchemaHistory");
        p.setProperty("schema.history.internal.file.filename", "./target/schema-history.dat");
        
        return DebeziumConnector.New(p, notifier);
    }
}
```

### Step 3: Bean Validation

The module will automatically validate that all required beans are present during application startup. If any bean is missing, the application will fail to start with a clear error message.

Once all beans are properly configured, database changes captured by Debezium will be:
1. Vectorized using your `Vectorizer`
2. Stored in your `VectorStore`
3. Available for similarity search

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│  Database (MySQL, PostgreSQL, etc.)                     │
└─────────────────────────────────────────────────────────┘
                     ↓ (CDC)
┌─────────────────────────────────────────────────────────┐
│  DebeziumConnector (configured as @Bean)                │
│    - Captures INSERT, UPDATE, DELETE events             │
│    - Embedded engine (no Kafka needed)                  │
└─────────────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│  VectorStoreUpdater (provided by DebeziumConnector)     │
│    - Converts changes to vectors via Vectorizer         │
│    - Updates VectorStore                                │
└─────────────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│  VectorStore (Qdrant, Milvus, etc.)                     │
│    - Stores vectors for similarity search               │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  VectralinkDebeziumAutoConfiguration                    │
│    - Validates all required beans exist at startup      │
│    - Fails fast with clear error messages               │
└─────────────────────────────────────────────────────────┘
```
