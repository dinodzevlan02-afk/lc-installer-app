# Installer App storage layout

Storage account **stled03**, container **installer-app**, **private** (no
anonymous access). Its own container: the app never writes into the customer
portal's `customer-portal` container. Every record is one UTF-8 JSON file.
Anything that WRITES should go through the app's API (or follow the same
rules), because the API is what enforces who may do what.

Writes use blob ETags: create-only (`If-None-Match: *`) for new records and
`If-Match: <etag>` for updates, so two writers never silently overwrite each
other.

```
installer-app/
  system/setup.json                 written once, when the first admin is created
  users/{username}.json             one login
  invites/{sha256(token)}.json      one live invite / reset link
  audit/{yyyy-mm}/{stamp}.json      one event, append-only
```

## users/{username}.json

`username` is lowercase letters, digits and `. _ @ -`, 3-64 chars.

```json
{
  "username": "mike.crew",
  "name": "Mike Crew",
  "email": "",                   // optional for installers
  "phone": "+1 555 010 2030",
  "company": "Crew A",           // LC's own crew or the subcontractor
  "role": "installer",           // "lc-admin" | "installer"
  "password": { "alg": "scrypt", "N": 16384, "r": 8, "p": 1, "salt": "<b64>", "hash": "<b64>" },  // null until the invite is used
  "invite": { "hash": "<sha256 hex>", "expires": "...", "kind": "invite", "sentAt": "..." },  // only while a link is live
  "sessionVersion": 3,           // bumped to sign the user out everywhere
  "disabled": false,
  "mustChangePassword": false,   // true after an admin sets a temporary password
  "failedLogins": 0, "lockedUntil": "...",   // lockout after 5 wrong passwords, 15 min
  "created": "...", "createdBy": "dino", "lastLogin": "...",
  "updated": "...", "updatedBy": "..."
}
```

**Never** expose `password`, `invite.hash`, `failedLogins` or `lockedUntil`.
The API strips them (`publicUser` in api/shared/app.js).

| role | sees | manages |
|---|---|---|
| `lc-admin` | everything | logins |
| `installer` | their own login (and, once built, their own jobs) | nothing |

## invites/{sha256}.json

`{ "username", "expires", "kind": "invite" | "reset" }`. The token itself is
never stored; a newer link retires the older one.

## audit/{yyyy-mm}/{stamp}.json

`{ "at", "actor", "action", "target", "detail", "ip" }`. Never rewritten.
