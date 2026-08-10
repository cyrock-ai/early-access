# Web console

One console at <http://localhost:8080> covering both administration and data work. Sign in with a
seeded login - `superadmin` / `superadmin` shows everything.

## Two areas

**Administration** manages the tenant: organizations, projects, users and their roles, and API keys.
This is where you look when a permission question comes up, or when you need a second API key for a
different client.

**Workbench** is where the data is: collections, graphs, queries and visualization. Most of your time
is here.

What you can see depends on your role, which is the point of the three seeded logins - sign in as
`member` to see the console as someone with data access but no administrative power.

## Sample datasets

The fastest way to have something real to query. Both list views carry a **Try Samples** button:

- **Graphs** offers a movies graph and a retail graph - nodes, typed edges and pre-computed
  embeddings.
- **Collections** offers three document sets, including an FAQ knowledge base.

All templates are pre-selected in the dialog; press **Create Selected** to build them. Progress shows
per template, and each takes a few seconds. Deselect the ones you do not want.

Because the samples ship with embeddings, vector search works immediately - no provider account and
no configuration.

## Creating a collection or graph

**Collections → New** asks for a name and a field list. Each field needs a type; vector fields also
need dimensions and a similarity function. Declaring types is what makes filters fast later, so it is
worth a moment's thought rather than making everything text.

If a language model is configured, a wizard will propose a schema from a description of your data -
useful as a starting point, though check the field types before accepting it. Without a model
configured, you define fields directly; nothing is lost.

**Graphs → New** works the same way, and you add edge types as you create edges.

## Querying

Each collection and graph has a query view: write [CyQL](cyql.md), run it, read the results as a table.

Two things worth knowing:

- **Use parameters.** The view has a parameter panel. It avoids quoting problems and is a better habit
  than editing values into the query text.
- **`score(...)` is a column.** Return it whenever you use `SEARCH` or `SIMILAR TO` - the ranking
  score tells you whether a result set is genuinely good or merely the best of a bad batch. It takes
  the variable it scores, so `score(d)` for a document and `score(m)` for a node.

Query history is kept, so an afternoon of exploration is recoverable.

## Graph visualization

A graph opens as an interactive force-directed view, in 2D or 3D. Nodes are coloured by label and
sized by connectivity.

- Drag to reposition, scroll to zoom, click a node to see its fields.
- Expand a node to pull in its neighbours, which is the natural way to explore outward from a search
  result.
- The result of a query can be visualized rather than tabulated - run a traversal, then look at the
  shape of what came back.

Visualization is for understanding structure, not for rendering everything. A view of a few hundred
nodes is informative; a view of fifty thousand is a hairball. Filter or start from a search result.

## Natural language search

If a language model is configured, you can describe what you want in plain language and have it
translated into CyQL. The generated query is shown before it runs.

Read it. Translation is a good accelerator and an unreliable oracle - it is genuinely useful for
recalling syntax you half-remember, and it will occasionally produce something that runs and answers a
subtly different question.

## Monitoring

The console surfaces engine health, storage size and slow queries. For anything continuous, scrape the
Prometheus endpoint instead - see [Operations](operations.md).
