# AI Knowledge Fabric — User Guide

## What is AI Knowledge Fabric?

AI Knowledge Fabric is a platform for building, running, and managing AI-powered services — without writing code. You configure AI assistants through a web interface, and the platform automatically provisions the underlying infrastructure for you.

The platform covers three main areas: **RAG Chatbots (Topics)**, **Agents**, and **Pipelines**. Each serves a different purpose and can be used independently or combined.

> **Want to build something right away?** [Getting Started](Getting-Started.md) walks the full path
> from installation to your first grounded answer, in order, with links to the detail pages.

---

## RAG Chatbots — Topics

A **Topic** is a private AI chatbot that answers questions based on your own documents. "RAG" stands for Retrieval-Augmented Generation — the AI searches your uploaded content first, then uses that knowledge to produce an accurate, grounded answer instead of relying solely on its general training.

**What you can do with a Topic:**

- **Upload your own documents** — PDFs, Word files, text files, and more. The platform indexes them automatically so the chatbot can search them.
- **Ask questions in natural language** — The chatbot retrieves the most relevant passages from your documents and uses them to answer.
- **Run multiple Topics in parallel** — Each Topic is completely isolated. You can have one for HR policies, another for technical manuals, another for customer FAQs.
- **Connect external tools via MCP** — Extend a chatbot's capabilities by linking it to other running Topics or external tool servers.
- **Customise the chatbot's behaviour** — Each Topic has its own system prompt so you can give it a specific role, tone, or set of instructions.

**Typical workflow:**

1. Create a Topic with a name and description.
2. Choose the language model and embedding model to use.
3. Start the Topic — the platform spins up the required services automatically.
4. Upload your documents on the Data Upload tab.
5. Click the Topic name in the list to open the chat interface.

---

## AI Agents

An **Agent** is an autonomous AI assistant that can reason, plan, and take actions across multiple steps. Unlike a simple chatbot that answers a single question, an Agent can break down a task, use tools, call other services, and work through a multi-step process to reach a result.

Agents run one or more **Pipelines** (see below) that define how the Agent thinks and what tools it has access to.

**What you can do with an Agent:**

- **Run complex, multi-step tasks** — The Agent decides on its own which steps to take to fulfil a request.
- **Connect tools** — Agents can use MCP tool servers to retrieve information, call APIs, or trigger actions in external systems.
- **Run multiple independent Agents** — Each Agent runs in its own isolated container on a dedicated port.
- **Select which Pipeline to use per conversation** — A single Agent can run several different Pipelines; you choose the one that fits your task when you open the chat.

**Typical workflow:**

1. Design a Pipeline that defines the Agent's instructions, model, and tools.
2. Create an Agent and assign the Pipeline to it.
3. Start the Agent — the platform starts the container and registers all assigned Pipelines automatically.
4. Open the Agent chat, select a Pipeline, and start a conversation.

---

## Pipelines — Visual Workflow Designer

A **Pipeline** defines how an AI Agent works: which language model it uses, what instructions it follows, and which tools it can call. Pipelines are built visually in the **Pipeline Designer** — a drag-and-drop canvas where you connect nodes together.

**What you can do in the Pipeline Designer:**

- **Add Agent nodes** — Each Agent node represents one AI step. You configure its model, provider, and system instruction directly in the properties panel.
- **Connect tools** — Drag an MCP Tool node onto the canvas and connect it to an Agent node to give that Agent access to an external tool server.
- **Embed other Pipelines** — Use a Workflow node to call another Pipeline as a reusable sub-step.
- **Link to a Topic** — Use an AI Topic node to route part of a conversation to one of your running RAG chatbots.
- **Define entry and exit points** — A Chat Input node receives the user's message; a Chat Output node returns the final response.
- **Export and import** — Pipelines can be exported as JSON and imported on another instance.

**Node types at a glance:**

| Node | Purpose |
|---|---|
| **Agent** | An AI step with its own model, instructions, and optional tools |
| **MCP Tool** | An external tool server the Agent can call |
| **AI Topic** | A running RAG Topic used as a knowledge source |
| **Workflow** | Embeds another Pipeline as a reusable sub-step |
| **Chat Input** | Entry point — receives the user's message |
| **Chat Output** | Exit point — returns the final response |

---

## MCP Tools

**MCP (Model Context Protocol)** is a standard way to connect AI services to external tools and data sources. The platform includes a built-in **MCP Tool Browser** where you can discover available tool servers from a public catalog and connect them to your Topics or Agents.

**What you can do:**

- Browse the MCP tool catalog to find servers for web search, file access, APIs, and more.
- Connect MCP tool servers to a running Topic so the chatbot can call them during a conversation.
- Add MCP Tool nodes in the Pipeline Designer to give an Agent access to external tools.

---

## Services Summary

| Area | What it provides |
|---|---|
| **Topics (RAG Chatbots)** | Document-grounded Q&A chatbots backed by your own uploaded content |
| **Agents** | Autonomous AI assistants that execute multi-step tasks using tools and Pipelines |
| **Pipelines** | Visual workflow definitions that configure how an Agent reasons and which tools it uses |
| **MCP Tools** | Connections to external tool servers that extend what Topics and Agents can do |
| **AI Servers** *(admin)* | Managed Ollama inference servers and external model provider connections |
| **Docling Servers** *(admin)* | Document pre-processing servers used to convert PDFs/Office files into clean text before embedding |

---

## Logs

Every running Topic and Agent has an **Actions** tab with a live log viewer: it shows recent log history and then streams new entries as they happen, so you can watch a chatbot or agent's activity in real time without shelling into the container.

---

## Roles & Permissions

Access is controlled by roles built from fine-grained permissions (e.g. being able to view Topics without being able to delete them), not a single "admin vs. everyone else" switch. What you see in the navigation menu — and which actions are available on each screen — depends on the permissions your role grants. If something you expect to see is missing, ask an administrator to check your assigned role under **Admin → Users**.

Administrators can also enable Single Sign-On (OIDC, e.g. via Keycloak or Entra ID) instead of, or alongside, local username/password login — ask your administrator which login method applies to your organisation.
