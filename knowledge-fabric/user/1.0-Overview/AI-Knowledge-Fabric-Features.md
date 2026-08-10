# AI Knowledge Fabric

**AI Knowledge Fabric** is a modular toolkit for building RAG, GraphRAG, and agent pipelines, with automatic container orchestration for Docker and Kubernetes.

---

## Core Capabilities

- Modular construction kit for RAG, GraphRAG, and agent pipelines
- Automatic container orchestration for RAG, GraphRAG, and agents
- Orchestration for Docker / Kubernetes

---

## Integrations & Storage

- **Seamless integration with your existing stack**
- **Graph database options:** CyrockDB (default), Neo4j, Apache Cassandra, Memgraph, or FalkorDB
- **Vector database options:** CyrockDB (default), Qdrant, Pinecone, Milvus, and other vector stores

## Multi-LLM Support

- Connect to any model provider of your choice — from local, self-hosted setups to cloud model providers such as Anthropic, OpenAI, and others

## Enterprise Connectors

- Pre-built connectors for databases, APIs, cloud storage, and enterprise systems

## Direct LLM Chat

- Unmediated language model interactions for flexible conversational experiences
- pre-configured REST interface for chat

## Vector Search

- Semantic similarity search across your entire context base for contextually relevant results

---

## Management Container

- Provides a graphical user interface for configuring orchestration
- Stores credentials for various systems for later use, including:
  - AI model server credentials
  - Vector DB credentials
  - Graph DB credentials
  - Docling server credentials
- Optional OIDC integration
- Provides authentication / authorization for access to:
  - MCP Tools Topics
  - MCP Agent Server Pipelines

---

## RAG Topic Server

- Configuration of a RAG system via a graphical user interface
- **Multi-document format support:**
  - Text, binary (Word, PDF, etc.), images, mixed formats, structured databases, unstructured data
  - Structured data import (JSON, XML, YAML, TOML, CSV, TSV)
  - pre-configured REST interface for uplaoding files to insert and update RAG
- **Configurable chunking:**
  - Multiple combinable chunking strategies
  - Base chunking with overlap, Docling, semantic context enrichment, BM25, and more
- **Configurable retrieval strategy:**
  - Multiple combinable retrieval strategies
  - Dense, hybrid (dense + BM25), reranking
- Configuration of system and user prompts
- Authorized inter-topic connection via MCP

---

## GraphRAG Topic Server

> **Not part of this Early Access release.** GraphRAG Topics appear in the navigation menu and can be
> created and configured, but the feature is still in development and does not work end to end. The
> capabilities below describe where it is going, not what you can rely on today — build with
> [RAG Topics](../4.0-RAG%20Topics/4.1-Overview/Overview.md) and
> [Agents](../5.0-Agents%20and%20Pipelines/5.1-Overview/Overview.md) instead.

- Configuration of a GraphRAG system via a graphical user interface
- Unstructured / structured data-to-graph converter
- Automatic insertion into the graph database
- Automatic updating of the graph database
- Automatic note vectorization based on topic chunking (see RAG)
- Automatic chunk vectorization based on topic chunking (see RAG)
- Automatic community index vectorization
- Individual pipeline strategies possible for insert, update, and other operations
- **Configurable retrieval strategy:**
  - Multiple combinable retrieval strategies
  - Local, global, and hybrid retrieval
  - Dense, hybrid (dense + BM25), reranking, and more

---

## Agent / Pipeline Server

- **Graphical pipeline designer** with components including:
  - Chat input / output
  - SQL DB
  - Graph DB
  - Key-value storage (read / write)
  - Structured output converter
  - API call
  - Data faker
  - File read and write
  - LLM agent
  - Embedding
  - Iterator
  - Loop
  - HITL (human-in-the-loop)
  - Scheduler
  - Guardrails
  - Text splitter
  - Templates
  - Web search
  - ...and more
- Multi-pipeline agent support
- Support for pipelines and sub-pipelines
- Support for Topics within a pipeline
- Support for Graph Topics within a pipeline
- Support for MCP within a pipeline
- Import / export of pipelines

---

## Deployment

- **Multi-cloud support:** AWS, Azure, Google Cloud, or any Kubernetes environment
- **Fully containerized:** complete Docker-based deployment model for consistency across all environments
- **Run-anywhere flexibility:** from local development to on-premise data centers to enterprise cloud deployments
- **Single-command deploy:** launch your entire agent infrastructure with `docker compose` in seconds

---

## Metrics & Logging

- **Audit logging** – complete audit trails for compliance, debugging, and performance analysis
- **Cost monitoring** – real-time tracking of LLM API costs, compute usage, and infrastructure expenses
- **Telemetry tracking** – latency, error rates, throughput, and cost metrics across the entire system
- **Prometheus & Grafana integration** – comprehensive monitoring dashboards with pre-configured metrics and alerts

---

## Security

- **Access control** – fine-grained RBAC, SSO integration, and multi-factor authentication support
- **Data sovereignty** – keep your data in your chosen region or on-premise for regulatory compliance
