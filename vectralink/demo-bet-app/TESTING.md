# Demo Bet App - Test Organization

## Test Structure

Tests in this project are organized into two categories:

### 1. Profile-Agnostic Tests
Located in: `src/test/java/`

These tests **run with ANY profile** (or no profile):
- `BlueprintGeneratorTest` - Tests blueprint generation logic
- `SportRepositoryIT` - Tests JPA repository operations  
- `MarketServiceIT` - Tests business logic (no vector store dependency)

**Running:**
```bash
# Run without profile (fast, no containers except MySQL)
mvn test

# Also works with any profile
mvn test -P qdrant
mvn test -P milvus
```

### 2. Profile-Specific Tests
Located in: `src/test/profiles/{profile}/`

These tests **require specific vector database profile**:

#### Qdrant Tests (`src/test/profiles/qdrant/`)
- `OpportunityServiceVectorSearchIT` - Tests vector similarity search
- `CdcDeletionSyncIT` - Tests CDC deletion synchronization
- `VectralinkCdcIT` - Tests complete CDC flow to Qdrant

**Running:**
```bash
# Only runs when qdrant profile is active
mvn test -P qdrant
```

#### Milvus Tests (`src/test/profiles/milvus/`)
- `OpportunityServiceVectorSearchIT` - Tests vector similarity search
- `CdcDeletionSyncIT` - Tests CDC deletion synchronization
- `VectralinkCdcIT` - Tests complete CDC flow to Milvus

**Running:**
```bash
# Only runs when milvus profile is active
mvn test -P milvus
```

## Test Base Classes

### `AbstractIntegrationTest`
- Located: `src/test/java/`
- **NO profile enforcement** - works with any profile
- Provides:
  - Spring Boot test context
  - Automatic cleanup before each test
  - MySQL container (via application config)
  
### `AbstractQdrantIntegrationTest`  
- Located: `src/test/profiles/qdrant/`
- **Activates profiles:** `qdrant` + `test`
- Extends `AbstractIntegrationTest`
- Provides:
  - Qdrant container (via application config)
  - Test-specific configuration (DDL auto-update, disabled scheduler)
  - CDC synchronization to Qdrant

### `AbstractMilvusIntegrationTest`
- Located: `src/test/profiles/milvus/`
- **Activates profiles:** `milvus` + `test`
- Extends `AbstractIntegrationTest`
- Provides:
  - Milvus container (via application config)
  - Test-specific configuration (DDL auto-update, disabled scheduler)
  - CDC synchronization to Milvus

## Profile Configuration

### Test Profile (`application-test.properties`)
Activated for **all integration tests** via `AbstractQdrantIntegrationTest` (and similar for other profiles):

```properties
# Auto-create/update database schema
spring.jpa.hibernate.ddl-auto=update

# Disable scheduler to prevent interference with tests
scheduler.odds.enabled=false

# Debug logging
logging.level.ai.cyrock=DEBUG
```

### Vector Database Profile
Each test extending `AbstractQdrantIntegrationTest` (or similar) automatically:
- Starts the correct vector database container
- Configures vector store beans
- Enables CDC synchronization

## Running Tests

### Without Profile (Fast)
```bash
mvn clean test
# Runs: 5 tests from BlueprintGeneratorTest
# Time: ~3-5 seconds
```

### With Qdrant Profile
```bash
mvn clean test -P qdrant
# Runs: 5 + 8 Qdrant-specific tests = 13 tests total
# Time: ~60-120 seconds (includes container startup + CDC synchronization)
```

### With Milvus Profile
```bash
mvn clean test -P milvus
# Runs: 5 + 8 Milvus-specific tests = 13 tests total
# Time: ~60-120 seconds (includes container startup + CDC synchronization)
```

### Specific Test Class
```bash
# Profile-agnostic test
mvn test -Dtest=BlueprintGeneratorTest

# Qdrant-specific test (requires profile)
mvn test -P qdrant -Dtest=OpportunityServiceVectorSearchIT

# Milvus-specific test (requires profile)
mvn test -P milvus -Dtest=OpportunityServiceVectorSearchIT
```

### Specific Test Method
```bash
mvn test -P qdrant -Dtest=OpportunityServiceVectorSearchIT#testVectorSearchFindsSpecificOddsRange
mvn test -P milvus -Dtest=OpportunityServiceVectorSearchIT#testVectorSearchFindsSpecificOddsRange
```

## Test Output

### Successful Run Without Profile
```
[INFO] Tests run: 5, Failures: 0, Errors: 0, Skipped: 0
[INFO] BUILD SUCCESS
```

### Successful Run With Qdrant Profile
```
[INFO] Tests run: 5, Failures: 0, Errors: 0, Skipped: 0 -- in BlueprintGeneratorTest
[INFO] Tests run: 5, Failures: 0, Errors: 0, Skipped: 0 -- in OpportunityServiceVectorSearchIT
[INFO] Tests run: 1, Failures: 0, Errors: 0, Skipped: 0 -- in CdcDeletionSyncIT
[INFO] Tests run: 2, Failures: 0, Errors: 0, Skipped: 0 -- in VectralinkCdcIT
[INFO] Tests run: 1, Failures: 0, Errors: 0, Skipped: 0 -- in SportRepositoryIT
[INFO] Tests run: 1, Failures: 0, Errors: 0, Skipped: 0 -- in MarketServiceIT
[INFO] 
[INFO] Results: Tests run: 15, Failures: 0, Errors: 0, Skipped: 0
[INFO] BUILD SUCCESS
```

## Adding Tests for New Profiles

When adding support for new vector database (e.g., Weaviate, Pinecone):

### 1. Create Profile-Specific Test Base Class
```java
// src/test/profiles/weaviate/ai/cyrock/vectralink/demo/bet/AbstractWeaviateIntegrationTest.java
@ActiveProfiles({"weaviate", "test"})
public abstract class AbstractWeaviateIntegrationTest extends AbstractIntegrationTest {
}
```

### 2. Copy Qdrant or Milvus Tests to New Profile
```bash
cp -r src/test/profiles/qdrant/* src/test/profiles/weaviate/
# or
cp -r src/test/profiles/milvus/* src/test/profiles/weaviate/
```

### 3. Update Test Classes
- Change extends `AbstractQdrantIntegrationTest` → `AbstractWeaviateIntegrationTest`
- Update Qdrant-specific code (e.g., `QdrantClient` → `WeaviateClient`)
- Update comments

### 4. Run Tests
```bash
mvn test -P weaviate
```

## Test Isolation

### Cleanup Strategy
`AbstractIntegrationTest.cleanupBeforeTest()`:
1. Clears all MySQL tables
2. Waits for CDC to sync to vector store
3. Ensures clean state for each test

### Avoiding Flaky Tests
- Use `Awaitility` for async operations (CDC synchronization)
- Wait for vector store to be synced before assertions
- Use deterministic test data (PredefinedBlueprints)

Example:
```java
// Wait for CDC to sync
await()
    .atMost(10, TimeUnit.SECONDS)
    .pollInterval(500, TimeUnit.MILLISECONDS)
    .untilAsserted(() -> {
        List<OpportunityDto> result = opportunityService.findByOddsRange(minOdds, maxOdds);
        assertThat(result).hasSize(expectedCount);
    });
```

## Troubleshooting

### Tests Don't Run with Profile

**Problem:** `mvn test -P qdrant` shows only 5 tests

**Solution:** Ensure profile test sources are compiled:
```bash
mvn clean test-compile -P qdrant
# Should compile ~9 test files
```

### Database Schema Missing

**Problem:** `Table 'betdb.sports' doesn't exist`

**Solution:** Ensure test profile is activated:
```java
@ActiveProfiles({"qdrant", "test"})  // test profile enables DDL auto-update
```

### CDC Tests Hang

**Problem:** Test runs forever waiting for CDC sync

**Solution:**
1. Check Debezium logs for errors
2. Verify MySQL binlog is enabled
3. Increase timeout in `Awaitility.await()`

### Container Startup Fails

**Problem:** `Port already in use` or `Container failed to start`

**Solution:**
```bash
# Stop all containers
docker stop $(docker ps -q)

# Clean Docker
docker system prune -f
```

## CI/CD Integration

### GitHub Actions Workflow
```yaml
jobs:
  test-qdrant:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          java-version: '21'
      - name: Test with Qdrant
        run: mvn test -P qdrant -pl demo-bet-app -am
```

### Matrix Testing (All Profiles)
```yaml
strategy:
  matrix:
    profile: [qdrant, milvus, pgvector, weaviate]
steps:
  - run: mvn test -P ${{ matrix.profile }}
```

## Performance

### Test Execution Times

| Test Suite                       | Without Profile | With Qdrant |
|----------------------------------|-----------------|-------------|
| BlueprintGeneratorTest           | 0.1s            | 0.1s        |
| OpportunityServiceVectorSearchIT | N/A             | 17s         |
| CdcDeletionSyncIT                | N/A             | 15s         |
| VectralinkCdcIT                  | N/A             | 20s         |
| SportRepositoryIT                | 1s              | 1s          |
| MarketServiceIT                  | 1s              | 1s          |
| **Total**                        | **~3s**         | **~60s**    |

*Note: Times include container startup (first test ~10s overhead)*

## Best Practices

1. ✅ **Keep profile-agnostic tests fast** - no containers unless necessary
2. ✅ **Use meaningful test names** - describe what is being tested
3. ✅ **Wait for async operations** - use Awaitility for CDC sync
4. ✅ **Clean state before each test** - extend AbstractIntegrationTest
5. ✅ **Document test requirements** - profile, containers, setup
6. ✅ **Test one thing per test method** - easier to debug failures
7. ✅ **Use deterministic data** - PredefinedBlueprints, not random

## See Also

- [PROFILES.md](PROFILES.md) - Maven profiles guide
- [LAUNCHERS.md](LAUNCHERS.md) - Running application with profiles
- [README.md](README.md) - Application documentation

