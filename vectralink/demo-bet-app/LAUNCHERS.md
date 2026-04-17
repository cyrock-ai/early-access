# Running Demo Bet App with Profile Launchers

## Quick Start - Using Profile Launchers in IDE

The easiest way to run the demo-bet-app with a specific vector database is to use the profile-specific launcher classes.

### Available Launchers

Each profile has its own main class that automatically activates the correct Spring profile:

| Launcher Class              | Vector Store | Location                                              |
|-----------------------------|--------------|-------------------------------------------------------|
| `ApplicationQdrant`         | Qdrant       | `src/main/profiles/qdrant/.../ApplicationQdrant.java`|
| `ApplicationMilvus`         | Milvus       | `src/main/profiles/milvus/.../ApplicationMilvus.java`|
| `ApplicationPGVector`       | PGVector     | `src/main/profiles/pgvector/.../ApplicationPGVector.java`|
| `ApplicationWeaviate`       | Weaviate     | `src/main/profiles/weaviate/.../ApplicationWeaviate.java`|
| (Pinecone launchers removed) | n/a | n/a |

### Running in IntelliJ IDEA

1. Build the project with the desired profile first:
   ```bash
   mvn clean compile -P qdrant
   ```

2. In IntelliJ IDEA:
   - Navigate to the launcher class (e.g., `ApplicationQdrant`)
   - Right-click on the file
   - Select "Run 'ApplicationQdrant.main()'"

The launcher automatically:
- Activates the correct Spring profile (`qdrant`, `milvus`, etc.)
- Starts the appropriate vector database container
- Configures the application to use that vector store

### Running from Command Line

Using Maven exec plugin:

```bash
# Qdrant
mvn compile exec:java -P qdrant -Dexec.mainClass="ai.cyrock.vectralink.demo.bet.ApplicationQdrant"

# Milvus
mvn compile exec:java -P milvus -Dexec.mainClass="ai.cyrock.vectralink.demo.bet.ApplicationMilvus"

# PGVector
mvn compile exec:java -P pgvector -Dexec.mainClass="ai.cyrock.vectralink.demo.bet.ApplicationPGVector"

# Weaviate
mvn compile exec:java -P weaviate -Dexec.mainClass="ai.cyrock.vectralink.demo.bet.ApplicationWeaviate"

# Pinecone profiles removed from this repository
<!-- Pinecone launchers were removed from the demo-bet-app distribution. -->
```

Using Spring Boot Maven plugin:

```bash
mvn spring-boot:run -P qdrant
```

## How Launchers Work

Each launcher class:

```java
package ai.cyrock.vectralink.demo.bet;

import org.springframework.boot.builder.SpringApplicationBuilder;

public class ApplicationQdrant {
    public static void main(String[] args) {
        new SpringApplicationBuilder(Application.class)
                .profiles("qdrant")  // Automatically activates profile
                .run(args);
    }
}
```

This approach:
- ✅ Works seamlessly in IDE (no need to configure run configurations)
- ✅ Automatically activates the correct Spring profile
- ✅ Ensures the right vector database is used
- ✅ Simplifies switching between vector stores during development

## Troubleshooting

### "Class not found" error

Make sure you've compiled the project with the correct profile first:
```bash
mvn clean compile -P qdrant
```

### Container startup issues

Check that Docker is running and ports are available:
- Qdrant: 6333, 6334
- Milvus: 19530, 9091
- PGVector: 5432
- Weaviate: 8080
- Pinecone: 5080, 5081, 5082

### Wrong vector store being used

Verify that:
1. You're running the correct launcher class
2. The Maven profile matches the launcher (use `-P` flag)
3. No `spring.profiles.active` is set in `application.properties`

## See Also

- [PROFILES.md](PROFILES.md) - Complete guide to Maven profiles
- [README.md](README.md) - General application documentation

