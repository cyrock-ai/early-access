# Web Search (`WEB_SEARCH`)

Lets an Agent search the web. **Tool-only** — it has no input or output port and cannot be used as a step.

**Category:** Utilities · **Deployed:** yes · **Tool-capable:** **yes (only)**

## Ports

| Port | Kind | Purpose |
|---|---|---|
| Tool (`tool_mcp`) | Tool | Wire to an Agent's Tools port. This is the module's only connection |

## Properties

| Field | Required | Meaning |
|---|---|---|
| Max Results (`maxResults`) | No | Cap on results returned to the agent. Defaults to the engine's own default |
| Custom Tool Description (`description`) | No | Overrides the description shown to the LLM. Empty uses a generated default |

Plus a **selector-driven** engine section — choose **Search Engine** first:

| Engine | Credentials needed |
|---|---|
| **Tavily** | API key |
| **Google Custom Search** | API key **and** a Programmable Search Engine ID — two separate credentials from `programmablesearchengine.google.com` |
| **SearchApi** | API key, plus an engine selector |

## Use cases

- **Current information** the models cannot know — news, prices, recent releases.
- **Fact-checking** an answer against public sources.
- **Research assistant**, combined with an AI Topic module so the agent can consult both internal documents
  and the open web.

## Notes

- **Tool-only.** Wiring it in sequence is impossible — there are no data ports.
- **Google Custom Search needs two credentials.** Supplying only the API key is the usual setup failure.
- **Choose the engine first**, or no credential fields appear.
- Keep Max Results modest — each result consumes context, and ten mediocre results crowd out the good ones.
- The default description is generic. A custom one describing *your* use case improves when the model
  reaches for it.
