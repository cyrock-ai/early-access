# Early Access to CYROCK libraries

Welcome to the CYROCK.AI Early Access programme. This repository is where Early Access products are
distributed: their documentation lives here, and where a product ships a Java artifact, it is
published to this repository's GitHub Packages registry.

Two products are in the programme today — **CYROCK.AI DB**, the unified AI data engine, and
**AI Knowledge Fabric**, the platform for building RAG chatbots, agents and pipelines on top of it.
Both run from a container image, so neither needs building.

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

---

[<img src="knowledge-fabric/assets/cyrock-ai-mark-azure.svg" alt="AI Knowledge Fabric" width="104" height="116" />](knowledge-fabric/README.md)

## AI Knowledge Fabric

**RAG chatbots, agents and visual pipelines, without writing code.** You configure what you want
through a web interface — a chatbot grounded in your own documents, an agent that works through a
multi-step task, a pipeline drawn on a canvas — and the platform generates and orchestrates the
container stacks underneath, on either Docker Compose or Kubernetes.

Full documentation: **[knowledge-fabric/README.md](knowledge-fabric/README.md)**

### Quick start

Two containers: the management app and a PostgreSQL configuration store. Everything else — RAG
services, vector databases, Ollama, Docling, agent servers — is created at runtime by the app itself,
as you create Topics and Agents in the UI. Both images are public on Docker Hub, so there is nothing
to build.

```bash
mkdir -p /opt/aiknowledgefabric && cd /opt/aiknowledgefabric

curl -o docker-compose.yml \
  https://raw.githubusercontent.com/cyrock-ai/early-access/main/knowledge-fabric/docker-compose.yml

docker compose up -d
```

First start pulls both images and initialises the schema, usually one to three minutes. Then open
<http://localhost:8080> and sign in as `admin` / `admin` — change that password immediately under
**Profile → Change Password**.

Before setting `docker compose up` loose on a shared machine, note that the app mounts the host's
Docker socket, which is what lets it start and stop container stacks for you. That is equivalent to
root access on the host, so run this on a host you control and keep port 8080 off the public
internet. [The installation guide](knowledge-fabric/user/2.0-Installation/docker-compose-installation.md)
covers the `.env` settings worth changing first — database password, JWT secret, metrics key — and the
reverse-proxy setup.

[Getting started](knowledge-fabric/user/1.0-Overview/Getting-Started.md) then walks the whole path in
order: registering a model provider, creating your first RAG Topic, uploading documents, and asking
the first grounded question. Allow 30–60 minutes.

### No SDK to install

Unlike CYROCK.AI DB, this product ships no Java artifact — nothing to add to your `settings.xml` or
`pom.xml`. Topic and Agent APIs are reachable over REST with a JWT you mint in the UI; see
[the REST API chapter](knowledge-fabric/user/4.0-RAG%20Topics/4.5-REST-API/REST-API.md).
