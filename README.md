# Early Access to CYROCK libraries

Welcome to the CYROCK.AI Early Access programme. This repository is where Early Access products are
distributed: their documentation lives here, and their Java artifacts are published to this
repository's GitHub Packages registry.

Everything here is pre-release software licensed for evaluation and internal, non-production use.
Please read the [licence](./LICENSE) before you start - it is short, and the term easiest to trip over
is that it covers no production or revenue-generating use.

Questions and feedback belong in this repository:
[issues](https://github.com/cyrock-ai/early-access/issues) when something is broken, and
[discussions](https://github.com/cyrock-ai/early-access/discussions) for everything else. Both are
public, so please keep anything confidential to your organization out of them.

---

[<img src="db/etc/cyrock-ai-db-logo.svg" alt="CYROCK.AI DB" width="500" />](db/README.md)

## CYROCK.AI DB

**The Unified AI Data Engine.** Vector search, knowledge graphs, agentic memory and hybrid retrieval
in a single engine with storage built in - replacing the vector database, graph database, metadata
store and agent memory layer you would otherwise run side by side.

Full documentation: **[db/README.md](db/README.md)**

### Quick start

CYROCK.AI DB ships as one container image, so there is nothing to build. It is public on Docker Hub,
mirrored to the GitHub Container Registry, and native on both `linux/amd64` and `linux/arm64`.

```bash
docker run --rm --name cyrock-db \
  -p 8080:8080 -p 8081:8081 -p 8082:8082 -p 8085:8085 -p 9090:9090 \
  -v cyrock-db-data:/data \
  -e JAVA_OPTS=-Xmx3g \
  cyrockai/db:0.9.0
```

Pin the version rather than tracking `latest`, so an upgrade is something you choose. The `--name` is
what lets `docker logs cyrock-db` and the other commands in the manual find your container.

First start takes 30-60 seconds. Then open <http://localhost:8080> and sign in as
`superadmin` / `superadmin`. The container prints an API key and a project ID on startup, which is what
the Java SDK and the MCP endpoint authenticate with. Over REST the API key goes to the platform port
directly, and the data port wants a short-lived token you exchange it for - [REST API](db/rest-api.md)
covers that, and it is the first thing worth reading there.

[Getting started](db/getting-started.md) walks through loading a sample dataset and running your first
search and graph query.

### Java SDK

Optional - the console, the REST APIs and the MCP endpoint need nothing installed.

The SDK is distributed as a Maven artifact from this repository's GitHub Packages registry. Add your
GitHub credentials to your `settings.xml` first. More info can be found in the official
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

Add the following repository. The `id` must match the `<server>` above - that is how Maven knows which
credentials to send.

```xml
<repositories>
    <repository>
        <id>cyrock-early-access</id>
        <name>GitHub CYROCK Early Access Packages</name>
        <url>https://maven.pkg.github.com/cyrock-ai/early-access</url>
    </repository>
</repositories>
```

Then the dependency:

```xml
<dependency>
    <groupId>ai.cyrock.db</groupId>
    <artifactId>cyrock-db-client-java</artifactId>
    <version>0.9.0</version>
</dependency>
```

See [db/java-sdk.md](db/java-sdk.md) for connecting and a complete worked example, the
[published packages](https://github.com/orgs/cyrock-ai/packages?repo_name=early-access), and the
starter [pom.xml](./pom.xml) in this repository.

### AI agents

The image exposes 39 tools over the Model Context Protocol at `http://localhost:8085/mcp`, so Claude
and other MCP clients can search, query and write directly. See [db/mcp.md](db/mcp.md).
