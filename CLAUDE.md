# LC Installer App - working notes

The code and commits carry the *what*; this file carries the *why*.

## What this is

LED Connection's app for installers in the field, a companion to the customer
portal (`dinodzevlan02-afk/lc-customer-portal`). Repo created 2026-10-20.
Tablet first, installable (manifest + sw.js).

Live: https://witty-plant-08257f31e.2.azurestaticapps.net (Azure SWA created
in the portal linked to GitHub like the customer portal; push to main
deploys after `npm test` passes in the same workflow).

## Layout and how we work (engineering-mentor session, 2026-10-20)

| Path | What | Deployed |
|---|---|---|
| `app/` | the website: pages, lci*.js, css, icons, sw.js, staticwebapp.config.json | yes, the ONLY folder published (app_location "app") |
| `api/` | Azure Functions; rules in api/shared | yes, as the API |
| `tests/` | site.test.js (unit, node:test), api.test.js (HTTP checks), fixtures/ | no |
| `dev/` | dev server | no |
| `docs/`, `tools/`, `CLAUDE.md` | notes, setup script | no |

- Allow-list, not deny-list: a new folder is private unless it is inside app/.
- `npm test` runs both test files; CI runs it before every deploy.
- Branch per feature, small commits that each pass on their own, a PR even
  when solo (Azure builds a preview site for it), merge to main to deploy.
- Stored job records carry `v` (SCHEMA in api/shared/jobs.js).

## The job flow (Dino, 2026-10-20; Walmart 2741 first)

1. **Material check** (app/job.html, step 1). One line per product from the
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
   PIN SIZE (50-250%, pins and tags) and MAP OPACITY (10-100%, washes the
   aerial to WHITE, never darker) in one pop-up under the zoom buttons, as
   in the customer portal (Dino, 2026-10-20). Per tablet, in its browser:
   localStorage lc_installer_pin_size / lc_installer_map_wash.
3. **Job sheet** (app/manual.html?job=&p=; was "install guide"). Generated per product from the
   design and catalog. LC DRAFT until Dino approves the wording: product-
   specific details (wire colours, torque) always point to the fixture's own
   label and instructions, never guessed.

Server rules (api/jobwork): expected quantities come from the site, never the
page; pins need the material signed off and a photo; excluded heads cannot
be installed; a submitted job is locked; only jobs that name the installer
are visible (404 otherwise). Claim emails are NOT sent yet: the office sees
claims on the job page. Next: mail like the portal's (Cassie + Dino).

## UL-listed part numbers (Dino, 2026-10-20)

"Change all the codes that are on the design ... apply these codes first."
The photometric design labels heads its own way (A-05: LC-SLOT-XL-XL1-HV-
50-70-TY5SW, by head size + IES file); what ships and is installed is the
UL-listed LC part number from the spec sheet's ORDER LOGIC
(lc-catalog/lc-skb.js OPTIMUS_OPTS + buildSku, 11 segments:
LC-SLOT-{W}W-{volt}-L5-{sensor}-{CCT}-{CRI}-{optic}-{bracket}-{color}).
- Per job: jobs/{id}/parts.json, design label -> part number, set by LC
  admins on the job page (PART NUMBERS panel); PUT /api/jobs/{id}/parts.
  api/shared/parts.js refuses an Optimus number outside the order logic
  (keep its code lists in step with lc-skb.js); other LC- numbers are
  accepted and shown as not checked. Installers see saved numbers on the
  material line, pin card and install guide; the product NAME follows the
  part number ("Optimus 300W · T5S"). Never the supplier's code.
- Walmart A-05 decisions (Dino): pole heads S11-S16 straight square arm
  (SS), wall heads S09-W / S09-W-N and S10 yoke (U), TY5SW -> T5S, TY4W ->
  T4 (the wide optics have no order code), black, no sensor, S10 CRI 70.
  Wattage from the schedule's own watts (S1 75, 145, L3 230, XL1 300, XL2
  420, all within 2.2%). These are DECIDED in parts.js and APPLY on any
  job with that design label until a different number is saved (Dino, on
  the 2741 pin card: "I need you to upload the codes here"; no save click
  needed). The panel marks them Decided vs Saved. The pin card leads with
  the part number and spells out what it means (PART NO. MEANS).
  S09-W and S09-W-N give the same part number (the "-N" is not an order
  code).
- Wall packs (Dino, 2026-10-20): FCW2 FCW-45-NV-740-CT -> LC-WP-40W-H-40K
  (the 40W substitution, as on Kroger, which ran darker than the design
  there), FCW3 FCW-20-NV-740-CT -> LC-WP-40W-L-40K (40W low-output tier;
  no 20W exists). parts.js checks LC-WP numbers against lc-skb.js WP_OPTS
  (LC-WP-{watt}W-{H|L}-{CCT}K[-{acc}]; CRI is not in the LC code).
- Floods FL3 LC-FL-170-HV-50 / FL4 LC-FL-40-NV-50: no flood order logic in
  lc-skb.js. Dino will give the LC numbers; until then they show the
  design label. Typed in the panel, they are accepted as "not checked".
- Every checked number carries parts.means, the one line the pin card and
  job sheet print under PART NO. MEANS.
- Installation guide PDF per product (Dino, 2026-10-20: "installation guide
  here as pdf ... what is relevant for the product"): an Optimus head
  installs the way its BRACKET mounts, so the guide is picked from the
  bracket in the SAVED part number (api/shared/guides.js), one PDF per
  bracket in app/guides/optimus/LC-Optimus-Installation-Guide-{code}.pdf.
  Orange INSTALLATION GUIDE (PDF) button on the material line and pin card,
  a card at the top of the page. guides.js READY lists the brackets whose
  PDF is committed (the API cannot see app/ on Azure); tests/guides.test.js
  fails when READY and the folder disagree. Not ready: the card opens the
  product's catalog SPEC SHEET instead (Dino, 2026-10-20: "link the spec
  sheet in it") and says the bracket guide is being prepared. The generated page (manual.html) is now called the JOB
  SHEET so it is not confused with the PDF guide. The PDFs are public like
  every file in app/ (catalog spec sheets are public too).
- The guides' CONTENT is LED Connection's own Optimus installation manuals
  (DNC1, April 2024), one per bracket F / R / SR / SS / T / U, from
  SharePoint LEDDocuments > LED > Sales > Sales - D&E > Product > Spec
  Sheet > Active > Optimus (Dino attached them 2026-10-20). Kept as
  masters in tools/guides/source/. Dino then asked to "rebrand in the new
  format LC, not like a spec sheet": tools/guides/extract_figures.py crops
  the manuals' own drawings, content/{code}.json holds their words (tools,
  parts, steps, torque, dimensions; _common.json the shared safety page),
  build_guides.py sets them in the LC look (dark cover, part-number chips,
  four steps a page, wiring, Installer App record + support card) into
  app/guides/optimus/. Nothing added from memory; contact is the manuals'
  own (702.847.7680, info@ledconnection.com). The manuals print the
  supplier's bracket letter in "connect the cable in the E holder" (F=A,
  R=B, SR=F, SS=E, T=G): the LC guides say "the bracket holder". Rebuild:
  extract_figures.py, then build_guides.py; check with --preview first.

## Who sees what (Dino, 2026-10-20)

- LED Connection admins: PROJECTS on the home page = the customer-portal
  projects that have a job here (Dino: "just keep this one Walmart"). Every
  other portal project with a site waits in the ADD A PROJECT picker;
  starting a job IS adding the project, so there is no second list to keep
  in step. GET /api/projects (LC only) still returns every portal project;
  the page filters. INSTALLERS changes who installs a job at any time (LC
  only; installer logins only; whoever is unticked loses it at once, their
  saved work stays; the audit records added / removed). Walmart Store 2741
  (51 fixtures, read live 2026-10-20) is the first project added this way.
- Installers: MY JOBS only, the jobs whose `installers` name them; any
  other job answers 404 and the project list 403.
- "Has a site" = projects/{id}/site.json exists in the portal's listing.

## Reading the customer portal (2026-10-20)

- api/shared/site.js reads projects/{id}.json, site.json, portal.json from
  the portal's container with INSTALLER_PORTAL_SAS (read + list only) via
  portalStore(), which hands out only reading calls. Never writes there.
- Field meanings are the portal's: one audit row = one head; ds.solutions /
  ds.excluded keyed by row INDEX; tag = the DESIGN's tag sol.tag (S13, FCW2,
  FL3: the photometric sheet's luminaire schedule; Dino 2026-10-20 "use this
  tag names"), falling back to the audit's row.schedule (kept as auditTag,
  shown on the pin card); pole = row['pole id'];
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
  otherwise tests/fixtures/portal holds TEST-SITE-01, which is SYNTHETIC
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
- Only app/ is published, so dev/, docs/, tools/, tests/ and CLAUDE.md never
  reach the site; app/staticwebapp.config.json adds nosniff / DENY framing /
  referrer headers.
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
- `npm test` = tests/site.test.js (7 unit tests of the site reader: product
  names as the portal shows them, counts, excluded heads, moved pins, no
  internal fields) + tests/parts.test.js (order logic) + tests/guides.test.js + tests/api.test.js, 136 checks through the real HTTP API on a throwaway
  store: setup once, CSRF header, cookie flags, invite once, lockout,
  installer cannot manage logins, switch-off and password change end
  sessions, last admin, audit, token never stored; jobs: visibility, no
  pricing/vendor/notes, BOM counts, moved pins, material sign-off, claims,
  photos, pins, submit. Runs in CI before every deploy.

## Open items

1. Short product names: the portal's comment says LC-SLOT-230W-NV-L5-...-T5S
   reads "Optimus 230W · T5S", its code shows "Optimus L5 230W · T5S" (the
   L5 segment matches the S/L/XL head-size rule). This app matches what the
   portal shows (tests/site.test.js). Dino: is L5 ever a head size? Fix in
   both apps together.
2. Secrets were shown in chat screenshots on 2026-10-20 (installer-app SAS,
   JWT secret). Rotate the JWT secret; move INSTALLER_STORAGE_SAS to a
   stored access policy so it can be revoked without rotating stled03 key1.
3. Blob soft delete / versioning on stled03 is not confirmed: until it is,
   a deleted claim or pin record is gone. Turn it on, then restore one
   record once to prove it.
4. Errors only go to context.log. Turn on Application Insights for the SWA.

5. Walmart 2741 head count: the A-05 luminaire schedule (Dino's screenshot,
   2026-10-20) gives 26 positions = 41 heads (FCW2 6, FCW3 1, FL3 4, FL4 1,
   S09-W-N 1, S09-W 2, S10 2, S11 1, S12 4, S13 6, S14 3, S15 8, S16 2);
   the app read 40 heads to install from the portal. Compare the design-tag
   filter counts with the schedule to find the missing head (likely a
   design head with no audit pin, or one excluded that should not be).

## Conventions

- Dark HUD look from the portal (lci.css): orange `#f37021`, cyan `#22d3ee`,
  Orbitron, Barlow, JetBrains Mono. BETA strip from lci.js.
- Phone first: installers are on site. Under `(pointer:coarse)` every
  control reaches 44 px.
- US projects imperial by default. No emoji as icons.
