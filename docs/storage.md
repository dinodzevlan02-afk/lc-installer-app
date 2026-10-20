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
  jobs/{projectId}.json             one job = one customer-portal project
  jobs/{projectId}/material.json    the material check and its sign-off
  jobs/{projectId}/claims/{ref}.json    one material claim (ref MC-yymmdd-XXXX)
  jobs/{projectId}/pins/{pinId}.json    one installed head
  jobs/{projectId}/photos/{16 hex}.jpg  claim and install photos (JPEG, max 3 MB)
```

The site itself (pins, products, quantities) is NOT stored here: it is read
from the customer portal's container (projects/{id}.json, site.json,
portal.json) with a read-only SAS, every time, so the two never disagree.

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
| `lc-admin` | everything | logins, jobs |
| `installer` | their own login, and the jobs that name them | their jobs: counts, claims, installed pins |

## invites/{sha256}.json

`{ "username", "expires", "kind": "invite" | "reset" }`. The token itself is
never stored; a newer link retires the older one.

## jobs/{projectId}.json

```json
{ "id": "<portal project id>", "name": "...", "address": "...",
  "installers": ["mike.crew"],            // who may see and work the job
  "created": "...", "createdBy": "dino",
  "submitted": { "at": "...", "by": "mike.crew", "byName": "...", "heads": 120 } }   // null until submitted
```

## jobs/{projectId}/material.json

```json
{ "lines": { "<fam · lc_sku>": { "received": 5, "damaged": 1, "note": "" } },
  "approved": { "at": "...", "by": "...", "byName": "...", "short": 1, "damaged": 1, "over": 0,
                "summary": [{ "key", "name", "sku", "expected", "received", "damaged", "short", "over" }] },
  "history": [{ "approved": {...}, "reopenedAt": "...", "reopenedBy": "dino" }] }
```
`expected` is always the site's own count at sign-off, never the page's.

## jobs/{projectId}/claims/{ref}.json

`{ ref, kind: shortage|damaged|wrong|other, kindLabel, lines: [{ key, name, sku, expected, received, damaged }], note, photos: [name], status: "open", at, by, byName }`

## jobs/{projectId}/pins/{pinId}.json

`pinId` = first 20 hex of sha1(datasetId + NUL + fixture id).
`{ pinId, fid, tag, poleId, product, sku, installed, note, serial, photos: [name], at, by, byName }`

## audit/{yyyy-mm}/{stamp}.json

`{ "at", "actor", "action", "target", "detail", "ip" }`. Never rewritten.
