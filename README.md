# Early Access to CYROCK libraries

Welcome to the CYROCK.AI Early Access programme. This repository is where Early Access products are
distributed: their documentation lives here, and their Java artifacts are published to this
repository's GitHub Packages registry.

Everything here is pre-release software licensed for evaluation and internal, non-production use.
Please read the [licence](./LICENSE) before you start - it is short, and two of its terms are easy to
trip over: no production or revenue-generating use, and no publishing benchmarks or comparisons
without our written consent. We are always happy to discuss performance with you directly.

## Products

[<img src="vectralink/etc/vectralink-logo-with-text.svg" alt="Vectralink" width="500" />](vectralink/README.md)

[<img src="db/etc/cyrock-ai-db-logo.svg" alt="CYROCK.AI DB" width="500" />](db/README.md)

---

## Vectralink

**Vector Database Synchronization.** A modular Java framework that keeps your vector embeddings in
sync with your source-of-truth data through change data capture, and lets you query by semantic
similarity - across Qdrant, Pinecone, pgvector, Weaviate and Milvus.

Full documentation: **[vectralink/README.md](vectralink/README.md)**

### Installation

Vectralink is distributed as Maven artifacts. First, add your GitHub credentials to your
`settings.xml`. More info can be found in the official
[GitHub documentation](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-apache-maven-registry#installing-a-package).

```xml
<servers>
    <server>
        <id>cyrock-early-access</id>
        <username>your-github-username</username>
        <password>your-personal-access-token</password>
    </server>
</servers>
```

Add the following repository.

```xml
<repositories>
    <repository>
        <id>cyrock-early-access</id>
        <name>GitHub CYROCK Early Access Packages</name>
        <url>https://maven.pkg.github.com/cyrock-ai/early-access</url>
    </repository>
</repositories>
```

Now you can use the
[CYROCK packages](https://github.com/orgs/cyrock-ai/packages?repo_name=early-access). See also the
starter [pom.xml](./pom.xml) in this repository.

---

## CYROCK.AI DB

**The Unified AI Data Engine.** Vector search, knowledge graphs, agentic memory and hybrid retrieval
in a single engine with storage built in - replacing the vector database, graph database, metadata
store and agent memory layer you would otherwise run side by side.

Full documentation: **[db/README.md](db/README.md)**

### Quick start

CYROCK.AI DB ships as one container image, so there is nothing to build. It is public on Docker Hub,
mirrored to the GitHub Container Registry, and native on both `linux/amd64` and `linux/arm64`.

```bash
docker run --rm \
  -p 8080:8080 -p 8081:8081 -p 8082:8082 -p 8085:8085 -p 9090:9090 \
  -v cyrock-db-data:/data \
  -e JAVA_OPTS=-Xmx3g \
  cyrockai/db:latest
```

First start takes 30-60 seconds. Then open <http://localhost:8080> and sign in as
`superadmin` / `superadmin`. The container prints an API key and a project ID on startup - those are
what the REST APIs, the Java SDK and the MCP endpoint need.

[Getting started](db/getting-started.md) walks through loading a sample dataset and running your first
vector search and graph query.

### Java SDK

Optional - the console, the REST APIs and the MCP endpoint need nothing installed. The SDK uses the
same `cyrock-early-access` server and repository shown above:

```xml
<dependency>
    <groupId>ai.cyrock.db</groupId>
    <artifactId>cyrock-db-client-java</artifactId>
    <version>0.9.0</version>
</dependency>
```

See [db/java-sdk.md](db/java-sdk.md) for connecting and a complete worked example.

### AI agents

The image exposes 39 tools over the Model Context Protocol at `http://localhost:8085/mcp`, so Claude
and other MCP clients can search, query and write directly. See [db/mcp.md](db/mcp.md).
