# Roles & Permissions

The **Roles & Permissions** screen (**Admin → Roles & Permissions**, `/admin/roles`) defines what
users are allowed to do. Access requires the `ROLE_MANAGE` permission.

Access control has **two layers**, both edited here:

| Layer | Question it answers |
|---|---|
| **Permissions** | *May this role do X at all?* — e.g. create Topics, manage servers, view metrics |
| **Resource Access** | *Which specific Topics, Agents, and Pipelines may this role see?* |

Holding `TOPIC_VIEW` does not imply access to *every* Topic — the second layer narrows it down.

---

## 1. Screen layout

Two panels side by side:

- **Left — Roles:** the list of roles with their descriptions, a `built-in` badge where applicable,
  and a **New Role** button.
- **Right — Permissions:** appears once you select a role. Permission checkboxes grouped into cards,
  the Resource Access section below, and **Save Changes** / **Delete Role** in the header.

Nothing is saved until you press **Save Changes**.

---

## 2. The built-in roles

A fresh installation is seeded with two roles, both flagged `built-in`:

| Role | Description | Contents |
|---|---|---|
| **ADMIN** | Full system access | Every permission, including all admin areas |
| **USER** | Standard user access | Topics, GraphRAG Topics, Agents, Pipelines (view/create/edit/delete/start/chat/upload), MCP tools, own profile, and log reading — but no admin permissions |

Built-in roles behave differently from custom ones:

| | Built-in | Custom |
|---|---|---|
| Rename | No | No (name is fixed at creation) |
| Change permissions | **ADMIN: no** — checkboxes are disabled and Save is greyed out with the tooltip *"Built-in ADMIN role always has all permissions"*. **USER: yes** | Yes |
| Delete | No — the Delete button is disabled | Yes |

ADMIN is deliberately immutable so an installation cannot be locked out of its own administration.

---

## 3. Permission groups

Permissions are grouped into cards, each checkbox with a short description:

| Group | Permissions |
|---|---|
| **Topics & Chat** | View · Create · Edit · Delete · Start/Stop · Chat · Upload Documents |
| **Agents** | View · Create · Edit · Delete · Start/Stop · Chat |
| **Pipelines** | View · Create · Edit · Delete |
| **MCP & Profile** | View MCP Tools · Edit Own Profile |
| **Server Infrastructure** | View Servers · Manage Servers |
| **User & Role Management** | View Users · Manage Users · Manage Roles |
| **System Configuration** | View LLM Config · Manage LLM Config · Auth Settings · View Metrics |
| **API** | API Access — use the REST API with a Bearer token |

### The View/Manage split

Most admin areas separate reading from changing. `SERVER_VIEW` shows AI servers, Docling servers, and
vector databases but hides every Add/Edit/Delete button; `SERVER_MANAGE` adds them. The same pattern
applies to `CONFIG_VIEW`/`CONFIG_MANAGE` and `USER_VIEW`/`USER_MANAGE`. This lets you grant read-only
insight into the infrastructure without granting change rights.

### Permissions the navigation menu depends on

The **Admin** menu group appears only if a role holds at least one of `SERVER_VIEW`, `CONFIG_VIEW`,
`USER_VIEW`, `ROLE_MANAGE`, `AUTH_MANAGE`, or `METRICS_VIEW` — and each entry within it is shown
individually per permission. If a user reports a missing menu entry, the cause is almost always the
corresponding `*_VIEW` permission.

---

## 4. ⚠️ Permissions not shown on this screen

**Some permissions exist but have no checkbox here.** The checkbox cards do not cover:

- **GraphRAG permissions** — `GRAPHRAG_VIEW`, `GRAPHRAG_CREATE`, `GRAPHRAG_EDIT`, `GRAPHRAG_DELETE`,
  `GRAPHRAG_START`, `GRAPHRAG_CHAT`, `GRAPHRAG_UPLOAD`
- **Log permissions** — `TOPIC_LOGS`, `LOGS_READ`, `LOGS_ADMIN`

This matters because **Save Changes writes exactly the set of ticked checkboxes** and discards
anything not represented on screen. Pressing Save on a role therefore **silently removes** its
GraphRAG and log permissions.

The seeded `USER` role holds `GRAPHRAG_*`, `TOPIC_LOGS`, and `LOGS_READ`, so editing and saving it
costs those users access to GraphRAG Topics and the log viewer.

**What to do:**

- Avoid pressing Save on a role whose GraphRAG or log access matters, unless you accept the loss.
- For **built-in** roles the loss is repaired on the next application restart — startup reconciles
  built-in roles by re-adding their seeded permissions. For **custom** roles it is permanent, and
  those permissions cannot be granted through the UI at all.
- If a custom role needs GraphRAG or log access, it currently has to be granted directly in the
  database.

---

## 5. Resource Access

Below the permission cards, three cards list every existing resource with a checkbox each:

| Card | Contents |
|---|---|
| **Topics** | All Topics, by name |
| **Agent Servers** | All Agents, by name |
| **Pipelines** | All Pipelines, by name |

Ticking an entry grants this role access to that specific resource. This is the second access layer:
a role needs **both** the general permission (`TOPIC_VIEW`) **and** access to the individual Topic.

Resource assignments are saved together with the permissions when you press **Save Changes**.

> Newly created Topics, Agents, and Pipelines are **not** automatically added to existing roles. After
> creating a resource that a role should see, come back here and tick it — otherwise members of that
> role will not find it in their list.

---

## 6. Creating and deleting roles

### New Role

Opens a dialog with **Role Name** (required, must be unique) and **Description** (free text, shown
under the name in the list).

The role is created with **no permissions at all**. Select it afterwards, tick what it needs, and
press **Save Changes**. The name cannot be changed later — only the description, permissions, and
resource assignments.

### Delete Role

Only available for custom roles. A confirmation dialog warns that *"Users assigned this role will
lose its permissions."*

**Check for affected users first**, under **Admin → User Management** — the Roles column shows who
holds the role. Since every user must have at least one role, deleting the only role a user holds
leaves that account without permissions.

---

## 7. Recommended setup

1. Leave **ADMIN** untouched, and give it to as few people as possible.
2. Decide whether **USER** fits your needs. If you edit it, be aware of
   [section 4](#4-️-permissions-not-shown-on-this-screen).
3. Create purpose-built roles rather than widening `USER` — e.g. a `READER` role with `TOPIC_VIEW` +
   `TOPIC_CHAT` + `PROFILE_EDIT` and resource access to a few Topics.
4. For read-only oversight, combine the `*_VIEW` permissions without their `*_MANAGE` counterparts.
5. Grant `API_ACCESS` only to accounts that genuinely drive the REST API from scripts.
6. Whenever you add a Topic, Agent, or Pipeline, revisit the Resource Access cards of the roles that
   should see it.

---

## 8. Troubleshooting

| Symptom | Cause and fix |
|---|---|
| Cannot open the screen | Your role lacks `ROLE_MANAGE` |
| Checkboxes greyed out, Save disabled | You selected the built-in **ADMIN** role, which always holds all permissions |
| Delete button greyed out | Built-in roles cannot be deleted |
| A user has `TOPIC_VIEW` but sees no Topics | Resource Access — no Topics are ticked for their role |
| A newly created Topic is invisible to a role | New resources are not auto-assigned. Tick it under Resource Access |
| GraphRAG Topics disappeared for standard users | The `USER` role was saved on this screen, dropping its GraphRAG permissions. Restart the application to restore them for built-in roles — see [section 4](#4-️-permissions-not-shown-on-this-screen) |
| The log viewer stopped working for a role | Same cause — `TOPIC_LOGS` / `LOGS_READ` were dropped on save |
| A whole admin area is missing from the menu | The corresponding `*_VIEW` permission is not granted |
| Buttons visible but actions refused | A `*_VIEW` permission is granted without the matching `*_MANAGE` |
| Role name rejected | A role with that name already exists |
| Cannot rename a role | Names are fixed after creation. Create a new role and reassign the users |

---

## Related

- [User Management](User-Management.md) — assigning roles to accounts
- [OIDC Settings](OIDC-Settings.md) — mapping SSO groups onto these roles
