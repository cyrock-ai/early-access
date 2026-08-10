# User Management

The **User Management** screen (**Admin → User Management**, `/admin/users`) lists all user accounts
and is where local accounts are created and edited.

| Permission | What it grants |
|---|---|
| `USER_VIEW` | Open the screen and browse the list |
| `USER_MANAGE` | The **New User** button and the edit action on each row |

With only `USER_VIEW` the list is read-only — no create, no edit.

---

## 1. The user list

| Column | Notes |
|---|---|
| **First Name** / **Last Name** | Sortable |
| **Email** | Sortable |
| **Username** | The login name. Sortable |
| **Roles** | Comma-separated list of assigned roles |
| **Created** | Account creation timestamp, in your local timezone |
| **Disabled** | `Yes` / `No` — see [Disabled vs. Locked](#3-disabled-vs-locked) |
| **Locked** | `Yes` / `No` |
| ✏️ | Edit (only with `USER_MANAGE`) |

The **Search** box filters across first name, last name, e-mail, and username as you type. It does
not search roles.

---

## 2. Creating and editing a user

**New User** and the edit icon both open the same form.

| Field | Required | Notes |
|---|---|---|
| **First Name** | Yes | |
| **Last Name** | Yes | |
| **Email** | Yes | |
| **Username** | Yes | The login name |
| **Password** / **Repeat Password** | Yes, **on creation only** | Hidden when editing — see below |
| **Roles** | At least one | Checkbox list of all defined roles. A new user is pre-checked with `USER` |
| **User disabled** | — | See below |
| **User locked** | — | See below |

Passwords are stored as BCrypt hashes, never in plain text.

### Password rules (new users)

Enforced when creating an account:

- At least **10 characters**
- Must contain **at least one digit or special character** — letters alone are rejected
- Both password fields must match

### You cannot change another user's password here

**The password fields are shown only when creating a user.** When you edit an existing account they
are hidden entirely, and there is no "reset password" action on this screen.

Consequences for a forgotten password:

- Users change their own password under **Profile → Change Password** (requires `PROFILE_EDIT`).
- An administrator cannot set a new password for someone else through the UI. The practical options
  are to have the user reset it themselves, or to create a replacement account and disable the old
  one.

### At least one role is required

Saving with no role checked is rejected with *"At least one role required"*. A user without a role
would be able to log in but see nothing.

---

## 3. Disabled vs. Locked

Two independent flags, both shown as columns in the list:

| Flag | Meaning |
|---|---|
| **User disabled** | The account is deactivated — use this for people who have left or should no longer have access |
| **User locked** | The account is locked — the conventional use is a temporary block, e.g. after suspicious activity |

Either flag blocks login. They are separate switches, so an account can be both. To restore access,
clear the flag and save.

**Prefer disabling over deleting.** There is deliberately **no delete action** on this screen — user
records are referenced by chat sessions and metric events, so deactivating keeps that history intact
and consistent.

---

## 4. The initial admin account

A fresh installation is seeded with one account:

| Username | Password | Role |
|---|---|---|
| `admin` | `admin` | `ADMIN` |

**Change this password immediately** after the first login, via **Profile → Change Password**. Since
an administrator cannot reset another user's password from this screen, also create a second account
with the `ADMIN` role as a fallback — if you lose access to the only administrator account, the
remaining route is direct database access.

---

## 5. SSO users

When OIDC single sign-on is enabled, accounts are created **automatically on first login** and appear
in this list alongside local accounts. Two things behave differently for them:

- The username is derived from the e-mail address (or from the OIDC subject if no e-mail is
  provided), so it may look unusual.
- **Roles are overwritten on every login** whenever a matching group mapping exists. Editing the
  roles of an SSO user here is therefore temporary — the next login resets them. Change the mapping
  instead, under **Admin → OIDC Settings**.

See [OIDC Settings](OIDC-Settings.md) for details.

---

## 6. Troubleshooting

| Symptom | Cause and fix |
|---|---|
| **New User** button missing | Your role lacks `USER_MANAGE` |
| No edit icon on the rows | Same — `USER_VIEW` alone is read-only |
| Password rejected on creation | Minimum 10 characters **and** at least one digit or special character |
| Cannot find the password fields when editing | By design — they only appear when creating. Users change their own password under **Profile** |
| Save rejected with "At least one role required" | Check at least one role |
| A user logs in but sees an empty navigation menu | Their role grants no view permissions. Check the role under **Admin → Roles & Permissions** |
| A user cannot log in at all | Check the **Disabled** and **Locked** columns |
| An SSO user's roles keep reverting | Expected — OIDC role sync overwrites them on each login. Adjust the mapping under **OIDC Settings** |
| No way to delete a user | Intentional. Set **User disabled** instead, to keep chat and metric history consistent |
| Search does not find someone by role | The filter covers name, e-mail, and username only. Sort by the Roles column instead |

---

## Related

- [Roles & Permissions](Roles-and-Permissions.md) — what the assigned roles actually allow
- [OIDC Settings](OIDC-Settings.md) — SSO login and automatic role assignment
