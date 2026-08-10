# License

The **License** screen (**Admin → License**, `/admin/license`) shows whether the installation has a
valid cyrock.ai license, and how current usage compares to the licensed feature limits.

Requires `CONFIG_VIEW` to open and `CONFIG_MANAGE` to paste or change a key. Without
`CONFIG_MANAGE` the key field is read-only and the Save button is hidden.

---

## 1. Running without a license

The platform **works without a license key** — it falls back to free-tier limits:

| Resource | Free-tier limit |
|---|---|
| Topics | 3 |
| GraphRAG Topics | 3 |
| Agents | 2 |
| Pipelines | 10 |

The limits are enforced at **creation time**: once you reach the limit, the create action is refused
until you delete an existing resource or install a license. Everything else — chat, ingestion, MCP
tools, user management — is unaffected.

> Validation is **fully offline**. The key is verified cryptographically against a built-in trust
> store; the platform never contacts a licensing server, so an air-gapped installation works
> normally.

---

## 2. The three sections

### License Key

A text area for the key, plus **Save**. Keys start with `CY-…`.

Paste the key you received and click **Save**. The platform immediately re-validates and the page
refreshes with the new status — no restart needed.

**Leaving the field empty is meaningful**: the platform then falls back to a chain of external
sources (see [Where the key comes from](#3-where-the-key-comes-from)), which is how a key can be
injected by the deployment instead of typed into the UI.

### Status

| Element | Meaning |
|---|---|
| **Valid** (green) / **Invalid** (red) | Whether a usable license was found |
| Reason text | Why — e.g. no key found, signature invalid, expired, wrong product |
| **Licensee** | The e-mail address the license was issued to (only when valid) |
| **Expires** | The expiry date, or *Never (perpetual)* for a perpetual license (only when valid) |

"Invalid" is not an error state that blocks anything — it simply means free-tier limits apply.

### Feature Limits

Current usage against the licensed maximum, as `used / limit`:

```
Topics        2 / 10
Agents        1 / 5
Pipelines     4 / 25
```

The counts are live counts of existing records. A licensed limit replaces the free-tier default; if
your license does not specify a particular feature, that feature falls back to its free-tier value.

> GraphRAG Topics have their own limit (free-tier: 3) which is enforced on creation but is **not
> displayed** in this section — only Topics, Agents, and Pipelines are listed.

---

## 3. Where the key comes from

The platform looks for a key in this order and uses the **first** one it finds:

| # | Source | Typical use |
|---|---|---|
| 1 | The key stored via this screen | Normal case — an admin pastes it once |
| 2 | `CYROCK_LICENSE_KEY` environment variable | Container deployments; inject via `docker-compose.yml` or a Kubernetes Secret |
| 3 | `cyrock.license.key` JVM property | `-Dcyrock.license.key=…` at startup |
| 4 | A license file — `CYROCK_LICENSE_FILE`, `./cyrock.license`, or `~/.cyrock/license` | Mounting the key as a file rather than an env var |
| 5 | A `cyrock.license` resource on the classpath | Pre-licensed custom builds |

**A key saved in the UI wins over all of them.** If you set `CYROCK_LICENSE_KEY` and it appears to be
ignored, check whether a key is already stored on this screen — clear the field and save to fall back
to the environment.

For the Docker Compose setup, `CYROCK_LICENSE_KEY` is the intended place for the key — see the
installation guide.

---

## 4. Applying a new or renewed license

1. Open **Admin → License**.
2. Paste the new key over the old one and click **Save**.
3. Confirm **Status** shows *Valid*, and check **Licensee** and **Expires**.
4. Confirm the new numbers under **Feature Limits**.

Validation happens immediately on save, so a wrong or truncated key shows up right away.

> **When a license expires**, the platform reverts to free-tier limits. Existing resources are **not
> deleted or stopped** — Topics and Agents above the free-tier limit keep running and stay usable;
> you simply cannot create new ones until the license is renewed. Watch the **Expires** date, since
> nothing else warns you.

---

## 5. Troubleshooting

| Symptom | Cause and fix |
|---|---|
| Status *Invalid*, reason mentions no key | No key stored and none found in the environment/file chain. Paste the key, or set `CYROCK_LICENSE_KEY` |
| Status *Invalid* after pasting | Key truncated or altered on copy — line breaks and stray spaces matter. Copy it again, complete |
| Status *Invalid*, reason mentions expiry | The license has expired. Renew it and paste the new key |
| Status *Invalid*, reason mentions the product | The key was issued for a different product. Request a Knowledge Fabric key |
| `CYROCK_LICENSE_KEY` seems ignored | A key stored via the UI takes precedence. Clear the field and save |
| "Limit reached" when creating a Topic/Agent/Pipeline | The licensed (or free-tier) limit is reached. Check **Feature Limits**, delete an unused resource, or upgrade |
| GraphRAG creation blocked but no limit shown | The GraphRAG limit is enforced but not displayed on this screen. Free tier allows 3 |
| The Save button is missing | Your role lacks `CONFIG_MANAGE`. Ask an administrator |
| Limits did not change after saving a valid key | Re-open the screen. The counts and limits are read when the page is built |

---

## Related

- [Docker Compose installation](../../2.0-Installation/docker-compose-installation.md) — where `CYROCK_LICENSE_KEY` is set
- [Roles & Permissions](../3.5-Users-Roles-and-Authentication/Roles-and-Permissions.md) — the `CONFIG_MANAGE` permission this screen requires
