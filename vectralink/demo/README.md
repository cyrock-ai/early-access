# Vectralink Demo Application

This directory contains a comprehensive demo application showcasing Vectralink's capabilities with various vector database implementations.

## Overview

The Vectralink Demo is a Spring Boot application with Vaadin UI that demonstrates real-time Change Data Capture (CDC) integration with vector databases. It provides a practical example of how to synchronize relational database changes with vector stores for semantic search capabilities.

## Supported Vector Databases

The demo supports multiple vector database backends, each with its own profile:

- **[Milvus](README_MILVUS.md)** - Open-source vector database built for scalable similarity search
- **[pgvector](README_PGVECTOR.md)** - PostgreSQL extension for vector similarity search
- **[Pinecone (v6)](README_PINECONE_6.md)** - Managed vector database service (SDK v6)
- **[Qdrant](README_QDRANT.md)** - High-performance vector search engine
- **[Weaviate](README_WEAVIATE.md)** - AI-native vector database

## Prerequisites

- **Java 21** or higher
- **Maven 3.6+**
- **Docker** and **Docker Compose** (for running vector databases locally)
- Access to the vector database of your choice (either running locally or cloud-hosted)

## Quick Start

### Step 1: Build the Project

First, build the entire Vectralink project from the root directory with your chosen profile:

```bash
# Build with Milvus profile
mvn clean install -P milvus

# Or with another profile:
# mvn clean install -P pgvector
# mvn clean install -P qdrant
# mvn clean install -P weaviate
# mvn clean install -P pinecone6
```

### Step 2: Switch to the `demo` directory

```bash
# Go to the demo directory
cd demo
```

### Step 3: Run the Application

Run the Spring Boot application with the corresponding profile:

```bash
# Run with Milvus profile
mvn spring-boot:run -P milvus

# Or with another profile:
# mvn spring-boot:run -P pgvector
# mvn spring-boot:run -P qdrant
# mvn spring-boot:run -P weaviate
# mvn spring-boot:run -P pinecone6
```

The application will start on `http://localhost:8080` (default port). (Weaviate demo runs on port `8081` by default.)

## Available Profiles

Each profile configures the application to work with a specific vector database:

| Profile | Vector Database | Dependencies |
|---------|----------------|--------------|
| `milvus` | Milvus | vectralink-milvus |
| `pgvector` | PostgreSQL + pgvector | vectralink-pgvector |
| `qdrant` | Qdrant | vectralink-qdrant |
| `weaviate` | Weaviate | vectralink-weaviate |
| `pinecone6` | Pinecone (SDK v6) | vectralink-pinecone |

## Detailed Setup Guides

For detailed setup instructions specific to each vector database,
please refer to the individual README files:

- **[Milvus Setup Guide](README_MILVUS.md)**
- **[pgvector Setup Guide](README_PGVECTOR.md)**
- **[Pinecone v6 Setup Guide](README_PINECONE_6.md)**
- **[Qdrant Setup Guide](README_QDRANT.md)**
- **[Weaviate Setup Guide](README_WEAVIATE.md)**

## Application Features

The demo application provides:

- **Vaadin-based Web UI** for interactive demonstrations
- **Real-time CDC Integration** using Debezium
- **Automatic Vector Embedding** of database changes
- **Semantic Search** capabilities
- **Multi-vector-database Support** through profiles

## Troubleshooting

### Runtime Issues

1. **Port already in use**: Change the port in `application.properties`:
   ```properties
   server.port=8081
   ```

2. **Vector database connection failed**: Verify the database is running and connection parameters are correct

3. **Profile not activated**: Ensure you're using the `-P` flag with the correct profile name

## License

See the main project LICENSE file for details.

---

**Note**: This is a demonstration application. For production use cases, please review and adjust security, performance, and configuration settings according to your requirements.

