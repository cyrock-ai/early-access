# OIDC Settings

The **OIDC Settings** screen (**Admin → OIDC Settings**, `/admin/oidc`) configures single sign-on via
an OpenID Connect provider — Keycloak, Microsoft Entra ID, Okta, Auth0, and similar — and maps the
provider's groups onto local roles.

Access requires the `AUTH_MANAGE` permission.

The screen has two panels: **Provider Configuration** on the left, **Role Mappings** on the right.

---

## 1. Provider Configuration

| Field | Notes |
|---|---|
| **Auth Strategy** | `Local (form login only)` · `OIDC (SSO only)` · `Both (form login + SSO button)` |
| **Issuer URI** | The provider's issuer URL, e.g. `https://idp.example.com/realms/myrealm`. Discovery documents are read from there |
| **Client ID** | The client registered for this application in your provider |
| **Client Secret** | That client's secret |
| **Roles Claim** | The JWT claim holding the user's group/role names. Default `roles` |
| **Scopes** | Space-separated. Must include `openid`. Default `openid profile email` |

Press **Save** to store the configuration.

### ⚠️ Most fields need a server restart

The note in the panel is the important part:

> **Issuer URI, Client ID, Client Secret, and Scopes are consumed by Spring Security at startup** —
> changes to them take effect only after the application is restarted. Only the **Roles Claim** is
> read at login time and applies immediately.

So the working order is: fill in the fields → Save → **restart the application** → test the login.
Saving alone changes nothing about how login behaves.

### Auth Strategy and the lock-out risk

The strategy stored here is the **authoritative** setting; the `AUTH_MODE` environment variable is
only a fallback used before this record exists.

> **`OIDC (SSO only)` disables the local login form**, including the `admin` account. If the provider
> configuration is wrong, or role mappings do not resolve, nobody can log in — and this screen is
> then unreachable too.
>
> **Use `Both` while setting SSO up.** Keep the local form available, verify that an SSO login works
> end to end and lands in the right role, and only then switch to `OIDC` if you want to enforce SSO.
>
> Recovering from a lock-out requires editing the `auth_config` table directly, setting `strategy`
> back to `LOCAL` or `BOTH`, and restarting.

---

## 2. Role Mappings

The right panel maps provider group names onto local roles.

| Column | Contents |
|---|---|
| **OIDC Group / Role Name** | The value as it appears in the token's roles claim |
| **Local Role** | The role assigned to users in that group |
| 🗑️ | Remove the mapping (with confirmation) |

To add one: type the group name, pick a local role, click **Add Mapping**. Both fields are required.

The group name must match the token value **exactly** — this is a literal comparison. Providers vary
in what they emit (`ai-fabric-admins`, `/ai-fabric-admins`, or a full path), so inspect a real token
rather than guessing. Several groups may map to the same local role.

---

## 3. What happens at login

1. The provider authenticates the user and returns an ID token.
2. The platform looks for a local account by the token's **`sub` claim** — the stable subject
   identifier.
3. **First login:** an account is created automatically. Username comes from the e-mail address
   (falling back to `oidc_<sub>` when no e-mail is present); first and last name are taken from the
   token's `given_name` / `family_name` where available.
4. **Every login:** the roles claim is read, group names are looked up in the mapping table, and if
   any match, **the user's roles are replaced with the mapped set**.

Three consequences worth knowing:

- **Roles are overwritten on every login, not merged.** Editing an SSO user's roles under **User
  Management** is temporary — the next login resets them. Change the mapping instead.
- **No matching mapping means roles are left untouched.** A brand-new SSO user then ends up with no
  roles and effectively sees nothing. Create the mappings *before* letting users log in.
- **Identity is keyed on `sub`, not on e-mail.** If a user's e-mail changes in the provider, the same
  account is still found. Conversely, a user re-created in the provider gets a new `sub` and becomes a
  new account here.

---

## 4. Setting SSO up

1. **In your identity provider:** register a client for this application, note the Client ID and
   secret, set the redirect URI, and make sure the token includes group membership in a claim.
2. **On this screen:** set Auth Strategy to **Both**, fill in Issuer URI, Client ID, Client Secret,
   Roles Claim, and Scopes, then Save.
3. **Add the role mappings** for every group that should have access — at minimum one group mapped to
   a role with enough permissions to be useful.
4. **Restart the application.**
5. **Test:** log in via the SSO button with a test account. Check under **Admin → User Management**
   that the account was created and carries the expected roles.
6. Optionally switch the strategy to **OIDC** once SSO is proven — accepting that the local form,
   including the `admin` account, is then disabled.

---

## 5. Troubleshooting

| Symptom | Cause and fix |
|---|---|
| No SSO button on the login page | Strategy is `Local`, or the application has not been restarted since saving |
| Changes to Issuer/Client/Scopes have no effect | These are read at startup. Restart the application |
| Login fails at the provider | Redirect URI mismatch, or wrong Client ID / Secret. Check the provider's logs |
| SSO login succeeds but the user sees nothing | No mapping matched, so no roles were assigned. Add a mapping for the user's group |
| Mapping exists but is not applied | The **Roles Claim** name is wrong, or the group string does not match exactly. Inspect a real token |
| Roles claim is present but ignored | The claim must be a **list of strings**. A single string or a nested object is not read |
| A user's manually assigned roles keep reverting | Expected — role sync overwrites them on every login. Change the mapping |
| Nobody can log in after switching to `OIDC` | Locked out. Set `strategy` back to `BOTH` in the `auth_config` table and restart |
| Duplicate accounts for the same person | Their `sub` changed in the provider (e.g. the account was re-created). Disable the stale account |
| Username looks like `oidc_a1b2c3…` | No e-mail claim was provided. Add `email` to the scopes and make sure the provider releases it |
| Cannot open the screen | Your role lacks `AUTH_MANAGE` |

---

## Related

- [User Management](User-Management.md) — where provisioned SSO accounts appear
- [Roles & Permissions](Roles-and-Permissions.md) — the roles that mappings point at
