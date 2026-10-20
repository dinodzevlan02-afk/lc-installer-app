# LC Installer App - working notes

The code and commits carry the *what*; this file carries the *why*.

## What this is

LED Connection's app for installers in the field, a companion to the customer
portal (`dinodzevlan02-afk/lc-customer-portal`). Repo created 2026-10-20.
Tablet first, installable (manifest + sw.js).

Live: https://witty-plant-08257f31e.2.azurestaticapps.net (Azure SWA created
in the portal linked to GitHub like the customer portal; push to main
deploys after dev/smoke.js passes in the same workflow).

## The job flow (Dino, 2026-10-20; Walmart 2741 first)

1. **Material check** (job.html, step 1). One line per product from the
   design: expected = heads of that product, received / damaged steppers
   (autosave), MATCH / SHORT / OVER / DAMAGED. REPORT A PROBLEM files a claim
   (short / damaged / wrong / other, lines, note, up to 6 photos; damaged
   needs a photo). The contact strip at the bottom (LED Connection, 702.847.7680,
   dinod@) comes from INSTALLER_CONTACT_PHONE / _EMAIL. The installer SIGNS
   OFF the counted quantities (confirm box); that unlocks the install even
   when something is short (judgment call: the claim covers it). Signed-off
   counts lock; an LC admin can reopen them (PATCH reopenMaterial).
2. **Install** (step 2). Google satellite + labels (same tiles as the
   portal), one pin per head: orange to do, green installed, grey excluded.
   Filter chips per tag (done / total), labels at zoom 19+ or on the
   filtered tag. Pin card: tag, pole heads, product, options, design tag,
   MH / arrangement / tilt / arm, what it replaces, spec sheet, install
   guide, catalog PDFs, photo (required), serial, note, SAVE AS INSTALLED,
   NEXT (same pole first, then nearest). SUBMIT JOB once every head is saved.
3. **Install guide** (manual.html?job=&p=). Generated per product from the
   design and catalog. LC DRAFT until Dino approves the wording: product-
   specific details (wire colours, torque) always point to the fixture's own
   label and instructions, never guessed.

Server rules (api/jobwork): expected quantities come from the site, never the
page; pins need the material signed off and a photo; excluded heads cannot
be installed; a submitted job is locked; only jobs that name the installer
are visible (404 otherwise). Claim emails are NOT sent yet: the office sees
claims on the job page. Next: mail like the portal's (Cassie + Dino).

## Reading the customer portal (2026-10-20)

- api/shared/site.js reads projects/{id}.json, site.json, portal.json from
  the portal's container with INSTALLER_PORTAL_SAS (read + list only) via
  portalStore(), which hands out only reading calls. Never writes there.
- Field meanings are the portal's: one audit row = one head; ds.solutions /
  ds.excluded keyed by row INDEX; tag = row.schedule; pole = row['pole id'];
  asset.pos (MOVE PINS) wins over row.latitude/longitude; product key =
  fam + ' · ' + lc_sku; names by cpShortProduct (ported, keep in step).
- WHITELIST: only named fields leave site.js / catalog.js. Pricing, vendor,
  vn_sku, skbSnapshot, designNote, audit notes, NetSuite number never reach
  an installer (smoke checks it).
- Pin ids: sha1(dsId + fid), so saved installs survive a site re-upload as
  long as the audit row keeps its id.
- Spec sheets, photos and manufacturer PDFs come from the LC catalog
  (internal-catalog/catalog-data.json, server-side, cached an hour) by
  sol.prodId; sol.specSheetUrl wins.
- Locally: put a real site in dev/.portal/projects/... (gitignored);
  otherwise dev/fixtures/portal holds TEST-SITE-01, which is SYNTHETIC
  (pipeline tests only, never results).

## Security: the customer portal's model, its own keys (2026-10-20)

Dino: "all same security, like the catalog and customer portal". The sign-in
layer is copied from lc-customer-portal (api/shared/auth.js, store.js,
invite.js, portal.js -> app.js, the endpoints, dev/server.js, the smoke test
approach). Keep it in step with the portal when either changes.

- Private repo. Azure Static Web App, `api/` = Azure Functions (classic v3
  model, Node, **no npm deps**). Rules live in api/shared/auth.js and are
  re-checked by every endpoint; the pages only decide what to draw.
- Passwords scrypt. Unknown usernames cost the same time as wrong passwords
  and get the same message. 5 wrong passwords lock a login for 15 min.
- Session: HttpOnly Secure SameSite=Strict cookie **`lci_s`** (12 h). Every
  POST/PATCH must send **`X-LCI: 1`** (CSRF guard). Different names from the
  portal's `lcp_s` / `X-LCP` on purpose, and its own secret, so a session in
  one app is never a session in the other.
- Each request re-reads the user, so switch-off / password change end
  sessions at once via `sessionVersion`.
- First admin via one-time setup with INSTALLER_SETUP_KEY; system/setup.json
  is a create-only write, so it works once.
- New logins get a one-time set-password link (7 days, only its SHA-256
  stored). No email goes out yet: the link comes back to the LC admin ONCE
  to pass on (installers may have only a phone). Add mail later the
  portal's way (api/shared/mail.js, docs/email-setup.md there).
- Guard rails: nobody switches themselves off or changes their own role;
  the last active LC admin cannot be removed.
- Everything is written to audit/{yyyy-mm}/ (append-only).
- Storage: its OWN private container `installer-app` in stled03. The
  portal's `customer-portal` is read only, with its own read/list SAS.
  Layout in **docs/storage.md**.
- dev/, docs/, tools/ and CLAUDE.md answer 404 on the live site
  (staticwebapp.config.json), plus nosniff / DENY framing / referrer headers.
- No secret is ever committed. Production values live only in the Azure app
  settings (docs/azure-setup.md); local ones are generated by dev/server.js.

## Roles (judgment call 2026-10-20, change when the build needs it)

- `lc-admin` - LED Connection office: manages logins, sees everything.
- `installer` - field crew, LC's own or a subcontractor (`company`).
  Manages nobody. Email optional, phone allowed.
Logins are LED Connection only, as in the portal.

## Writing back to the customer portal

Not built. Installed dates, serials and photos belong in the portal's asset
records eventually; that goes through the portal's API with its own key,
never by writing its container.

## Local dev and tests

- `node dev/server.js` serves the site AND runs api/ on http://localhost:4310
  with storage in `dev/.data` (gitignored). Setup key locally is
  `local-dev-setup-key`.
- `node dev/smoke.js` - 99 checks through the real HTTP API on a throwaway
  store: setup once, CSRF header, cookie flags, invite once, lockout,
  installer cannot manage logins, switch-off and password change end
  sessions, last admin, audit, token never stored; jobs: visibility, no
  pricing/vendor/notes, BOM counts, moved pins, material sign-off, claims,
  photos, pins, submit. Runs in CI before every deploy.

## Conventions

- Dark HUD look from the portal (lci.css): orange `#f37021`, cyan `#22d3ee`,
  Orbitron, Barlow, JetBrains Mono. BETA strip from lci.js.
- Phone first: installers are on site. Under `(pointer:coarse)` every
  control reaches 44 px.
- US projects imperial by default. No emoji as icons.
