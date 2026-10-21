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
  sites/{id}.json                   a site kept in this app only: name, address, customer, counts, source
  sites/{id}/site.json              its audit rows, solutions and exclusions (format "lc-site")
  jobs/{projectId}.json             one job = one site (customer-portal project or sites/{id})
  jobs/{projectId}/material.json    the material check and its sign-off
  jobs/{projectId}/parts.json       design label -> UL-listed LC part number (LC admins)
  jobs/{projectId}/claims/{ref}.json    one material claim (ref MC-yymmdd-XXXX)
  jobs/{projectId}/pins/{pinId}.json    one installed head
  jobs/{projectId}/photos/{16 hex}.jpg  claim and install photos (JPEG, max 3 MB)
  system/relay.json                 the paired Outlook relay: SHA-256 of its key, who paired it, when
  system/relay-seen.json            when a relay last came for mail, and which (installer | portal | setting)
  system/notify.json                LED Connection's list for every claim email (@ledconnection.com only)
  mailqueue/pending/{id}.json       an email waiting for the Outlook relay (photos inside, base64)
  mailqueue/sent/{id}.json          sent by the relay (attachments dropped, sentAt)
  mailqueue/failed/{id}.json        given up after 5 tries (error)
  deleted/{stamp}-{id}.json         a deleted project's manifest: who, when, why, files, restores
  deleted/{stamp}-{id}/files/{path} every file of that project, under its own path
```

Every job record (job, material, claim, pin) carries `"v": 1`, the shape it
was written in. Change a shape: bump SCHEMA in api/shared/jobs.js and make
the readers handle both, so old records are migrated on purpose.

A site (pins, products, quantities) comes from one of two places:

- **sites/{id}** in this container, when LED Connection uploaded a site file
  here (PUT /api/sites/{id}, home page UPLOAD SITE FILE). Kroger 345 is the
  first: Dino wanted it in the installer app only, not in the customer
  portal. The file is built by tools/sites/build-site.js; the API keeps only
  the solution fields an installer may see and drops signed photo links.
  This one wins over a portal project with the same id.
- otherwise the customer portal's container (projects/{id}.json, site.json,
  portal.json), read with a read-only SAS every time, so the two never
  disagree.

## sites/{id}.json

```json
{ "v": 1, "id": "KR-00345-NV", "name": "Kroger 345 · El Dorado Village",
  "address": "...", "customer": "Kroger", "kind": "exterior", "installDate": "",
  "fixtures": 87, "rows": 113,                      // heads to install, audit rows
  "source": { "audit": "...", "design": "...", "mapping": "...", "built": "2026-10-20", "builder": "tools/sites/build-site.js" },
  "uploaded": "...", "uploadedBy": "dino" }
```

`sites/{id}/site.json` is `{ "format": "lc-site", "version": 1, "site": { "datasets": [{ id, label,
data: [audit rows], solutions: { rowIndex: { fam, lc_sku, tag, watt, mh, tilt, ... } },
excluded: { rowIndex: true } }] } }`, the portal's shape. A re-upload replaces both
files; saved work stays because pin ids come from the dataset id and the audit row id.

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
{ "v": 1, "id": "<portal project id>", "name": "...", "address": "...",
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

## jobs/{projectId}/parts.json

```json
{ "v": 1, "byLabel": { "LC-SLOT-XL-XL1-HV-50-70-TY5SW": { "pn": "LC-SLOT-300W-HV-L5-XX-50-70-T5S-SS-BK", "at": "...", "by": "dino", "byName": "..." } } }
```
An Optimus `pn` always passes the order logic (api/shared/parts.js).

## Who gets a claim email

To: system/notify.json `{ to: [address], at, by }` (home page EMAIL panel,
@ledconnection.com only; absent = INSTALLER_NOTIFY_TO, else cassieh@ +
dinod@). CC: the job's own `notify` on jobs/{projectId}.json,
`{ installersOff: [username], client: [{ name, email }] }` (the project's
EMAILS dialog): every installer on the job whose login has an email, except
those unticked, and the client contacts.

## jobs/{projectId}/claims/{ref}.json

`{ ref, kind: shortage|damaged|wrong|other, kindLabel, lines: [{ key, name, sku, expected, received, damaged }], note, photos: [name], status: "open", at, by, byName, mail: { sent, queued, to, cc, attached, at, reason } }`

`mail` is how the claim email went: `sent` true = handed to Graph or queued
for the Outlook relay (`queued`), false with a `reason` = not emailed (the
claim is saved anyway and the job page shows "not emailed").

## mailqueue/ and system/relay.json

Ported from the customer portal (its docs/email-setup.md). With no Graph
settings, an email is queued in mailqueue/pending/ once a relay is paired;
tools/outlook-relay.ps1 on Dino's PC fetches it (GET /api/relay/outbox, header
X-Relay-Key), sends it through Outlook and acks it (POST, `{ id, ok, error }`),
which moves it to sent/ or, after 5 failures, failed/. system/relay.json is
`{ keyHash, pairedAt, pairedBy }`: the key itself is shown once on the home
page and never stored. The customer portal's relay is accepted too: its key
hash is read from the portal's own system/relay.json (read-only), and its
script polls this app with the same key, so one relay on Dino's PC sends
both apps' emails.

## jobs/{projectId}/pins/{pinId}.json

`pinId` = first 20 hex of sha1(datasetId + NUL + fixture id).
`{ pinId, fid, tag, poleId, product, sku, installed, note, serial, photos: [name], at, by, byName }`

## deleted/{key}.json and deleted/{key}/files/

A project deleted from the home page (api/deleted, LC admins only). `key` =
`{yyyymmddThhmmssZ}-{projectId}`. Every file of the project (jobs/{id}.json,
everything under jobs/{id}/, and for a site uploaded here sites/{id}.json and
sites/{id}/) is COPIED to files/{its own path} and checked there before any
original is removed. Manifest:
`{ v, key, id, name, address, customer, source: installer|portal, installers, at, by, byName, reason, files: [path], counts: { claims, pins, photos, material, parts, site }, restored: [{ at, by, byName }] }`.
A RESET (a clean start, the job stays) uses the same layout with
`kind: "reset"`: files/ holds the job's work (material.json, claims/, pins/,
photos/) plus a copy of jobs/{projectId}.json for its submitted state; the
live job gets `reset: { at, by, archive }` and `submitted: null`. Keys made
since 2026-10-21 carry milliseconds (`20261021T140512345Z-{id}`).
`state: "archiving"` means the delete stopped half way; it can still be
restored. A restore copies the files back (the job record last) and keeps
the archive. Nothing here is ever removed by the app.

## audit/{yyyy-mm}/{stamp}.json

`{ "at", "actor", "action", "target", "detail", "ip" }`. Never rewritten.
