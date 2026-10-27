# LC Installer App - working notes

The code and commits carry the *what*; this file carries the *why*.

## What this is

LED Connection's app for installers in the field, a companion to the customer
portal (`dinodzevlan02-afk/lc-customer-portal`). Repo created 2026-10-20.
Tablet first, installable (manifest + sw.js).

Live: https://witty-plant-08257f31e.2.azurestaticapps.net (Azure SWA created
in the portal linked to GitHub like the customer portal; push to main
deploys after `npm test` passes in the same workflow).

## Working with Dino: his browser (Dino, 2026-10-21)

Standing permission: "I'm allowing you to take control of my computer when
you need through Microsoft Edge extension of the Claude so you can control
the app." Use the Claude extension in his Edge whenever a step needs his
browser instead of stopping to hand it back: uploading a site file on the
live installer app, checking a deploy on the live site, the LC catalog
admin, downloading a file from SharePoint that this session can only read
as text. Still ask first before anything outward-facing or hard to undo
(sending email, deleting, payments, changing logins), and say what was done
in his browser. The extension's tools exist only while it is connected to
the session; if they are not there, say so rather than guessing.

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
   needs a photo). Layout (Dino, 2026-10-23, from the Claude Design canvas
   "Installer App · Material Check (iPad)"): full width, one compact row per
   product with bigger text, the documents behind one DOCUMENTS button (a
   pop-up with the set up in full, guide, spec sheet, job sheet, catalog
   PDFs), and NO phone / email strip under the list ("remove here contact
   number and my emails"). Next, waiting on Dino: a short "Set up" line in
   the row (full text in the pop-up), a desktop table layout, and RECORD A
   MESSAGE (voice / camera / screen to the project's LC list; needs an
   upload + email endpoint; Safari on iPad cannot record the screen).
   Billie Jo's feedback (2026-10-27, Dino: "do your recommendation"): a red
   REPORT on every product row opens the claim with that product ticked
   (and the kind preset from its count); the footer one is REPORT OTHER
   PROBLEM. The main button reads CHECKLIST n / N, filling as products are
   counted, then PROCEED TO INSTALLATION; it opens a checklist (per product
   OK / SHORT / DAMAGED / TO COUNT) with the confirm box. Server and the
   sign-off email are unchanged. The installer SIGNS
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
   design and catalog. No DRAFT note on the page (Dino, 2026-10-21:
   "removed completely from every pin on every site"). Product-
   specific details (wire colours, torque) always point to the fixture's own
   label and instructions, never guessed.

Server rules (api/jobwork): expected quantities come from the site, never the
page; pins need the material signed off and a photo; excluded heads cannot
be installed; a submitted job is locked; only jobs that name the installer
are visible (404 otherwise).

## Claim email (Dino, 2026-10-21)

"When I press SEND CLAIM, this email needs to go to Cassie, me, with the
photo inside ... with a note, and also the quantities that are missing",
the way the customer portal sends through Outlook.
- POST /api/jobs/{id}/claims saves the claim, then emails it in the same
  request (api/shared/claimmail.js): To INSTALLER_NOTIFY_TO, default
  cassieh@ + dinod@ledconnection.com; subject "[MC-...] Material claim:
  {problem} - {job}"; a table per line (product, part no., tags, expected,
  received, MISSING = expected - received, damaged), the note, who reported
  it (name, company, phone), a link to the job, the photos attached. The
  part number is the saved one, else the decided one; never the supplier's
  code, no pricing.
- api/shared/mail.js is the portal's, ported: Graph when INSTALLER_MAIL_*
  are set, else the Outlook relay once paired, else dev/.data/outbox.
  Dino BCC'd on anything he is not addressed on. A failed email never fails
  the claim: claim.mail records how it went, the toast and the job page say
  "not emailed" with the reason.
- The relay is this app's own (its own key, folder %USERPROFILE%\
  .lc-installer-relay, mutex LCInstallerOutlookRelay), not the portal's.
  Home page EMAIL panel (LC only): status, PAIR OUTLOOK RELAY shows the key
  once; save it as key.txt in that folder and run tools/outlook-relay.ps1 as
  a scheduled task on Dino's PC (same as the portal's, docs there).
  /api/relay/status feeds the panel.
- No second pairing (Dino, 2026-10-21: "don't ask ... just do it. I need
  these emails"): the CUSTOMER PORTAL'S relay, already running on his PC,
  is accepted here (mail.js relayHashes reads the portal's system/relay.json
  key hash, read-only) and its script (lc-customer-portal
  tools/outlook-relay.ps1) polls this app's outbox too with the same key
  (ledger ids "lci:"). His PC needs that script pulled and the task
  restarted once. Claims queue meanwhile and go out when it next polls.
- Who gets it (Dino, same day: "who do we want to report this ... add new
  email ... all from LED Connection ... and who I assigned as installer and
  who is going to be client"): To = LED Connection's list, edited on the
  EMAIL panel (system/notify.json, @ledconnection.com only). CC per project
  (EMAILS on its row, job.notify): the job's installers by their login
  email (on unless unticked, so one added later hears too) and the client
  contacts typed there. There are no client logins in this app; installers
  never see who else is emailed.
- Three sets on the project's EMAILS dialog, each with an x and an add
  (Dino, 2026-10-21: "add also LED Connection contact ... installer
  contact ... I can remove them"): LED Connection (the panel's list; x takes
  someone off THIS project only, job.notify.lcOff, shown under "Not on this
  project" with a put-back; adds are @ledconnection.com, job.notify.lc, on
  To), Installers (logins, x = installersOff; plus contacts of any domain,
  job.notify.installer, on CC), Client (on CC). A project keeps at least one
  LED Connection address. Nothing saves until SAVE; an address typed but
  not ADDed goes in with it.
- Default LED Connection list (Dino, 2026-10-21, "for the testing
  purposes"): Cassie, Dino, David X. Williams (davidw@) and Sergei
  Vasilyev (sergeiv@). A list saved on the EMAIL panel replaces it.
- Why nothing arrived at first (2026-10-21): claims were queued, but the
  relay on Dino's PC still ran the old script (portal only). The EMAIL panel
  now shows the one PowerShell command (pull + restart) whenever a relay is
  paired but has not checked in for 15 minutes, and SEND TEST EMAIL
  (POST /api/relay/test, LC only, audit mail.test) proves the route without
  filing a claim.

## Everything on site is emailed to the same list (Dino, 2026-10-21)

"Send claim ... and also when I do the sign off ... and everything that I do
install, if someone is reporting a problem or flagging something, I want
that to be reaching out to all of these emails."
- Same recipients and route as a claim (claimmail.js deliver: LED
  Connection's list on To, the job's installers + client on CC, Outlook
  relay), same rule: the record is saved first, a failed email never fails
  it, `mail` on the record says how it went.
- MATERIAL SIGN-OFF: "[job] Material signed off: everything received" or
  ": N short, M damaged", a table per product (part no., tags, expected,
  received, short, over, damaged), who signed, what is next.
- FLAG A PROBLEM (new): a button on every pin card, also after submit. Kinds
  pole / power / access / fit / other, note and up to 6 photos (note or
  photo required). POST /api/jobs/{id}/flags -> jobs/{id}/flags/FL-....json;
  email "[FL-...] Install problem: {kind} - {job}" with tag, pole, fixture,
  product + part no., note, photos attached. Listed on the pin card and
  under PROBLEMS FLAGGED. Reset clears flags with the rest of the work.
- SUBMIT: "[job] Install submitted: N fixtures", plus how many claims /
  flags are still open.
- Installers never see the addresses: API replies and stored records carry
  only sent / queued / how many (jobs.js forViewer); LC admins see all.

## Installed fixtures, approval of a finished job (Dino, 2026-10-21)

"A notification for every fixture that is installed ... the proof being
uploaded a photo ... and a big one where the project is done ... asking
approval ... a link where they will enter the app and approve it and it's a
done deal."
- Each fixture's FIRST save as installed emails the list: "[job] Installed:
  {tag} · pole {pole} (n of N)" with its photo(s) attached, product + part
  no., serial, note. An update or an undo sends nothing. Per project switch
  in EMAILS ("Email each installed fixture", job.notify.installs each | off,
  default each): Kroger 345 is 88 emails.
- SUBMIT now sends "[job] Install complete: N fixtures - approval needed"
  with a REVIEW AND APPROVE button to /job.html?id=..&review=1 (opens the
  install view; sign-in first, the login redirect keeps the query). No
  approve-by-link token: a forwarded email cannot approve anything.
- LC admins see "waiting for your approval" on the job: APPROVE (optional
  note; POST /api/jobs/{id}/accept -> job.accepted, "Install approved"
  email, job done) or SEND BACK (reason required; POST .../sendback ->
  job.sentBack[], submitted cleared, "Install sent back" email; the
  installer sees why, fixes, submits again). Installers cannot do either.
  Home page badges: Waiting approval / Approved. Reset clears accepted too.
- Judgment call: "our end" = LED Connection admins approve, not the client.

## Deleting a project (Dino, 2026-10-21)

"Delete ... only by LED Connection user ... asked, are you sure? ...
activity log ... save everything in backend in a case I need to return
back."
- DELETE on each Projects row (LC only; the API refuses installers). The
  dialog lists what goes (job and its installers, material check, claims,
  installed heads, photos, part numbers, the uploaded site) and needs
  "DELETE" typed; an optional reason is kept.
- api/deleted copies every file to deleted/{stamp}-{id}/files/ and checks
  the copy BEFORE removing anything; removes the job record first so nobody
  saves into it mid-delete, then archives anything saved in between. A
  portal project's own data is never touched: it returns to the ADD picker.
- Activity log: audit job.delete / job.restore with who, plus the DELETED
  PROJECTS list on the home page (who, when, why, restored by whom).
- RESTORE puts it all back as it was (job record last) and keeps the
  archive; refused while a project with that id is there again.

## Resetting a project: a clean start (Dino, 2026-10-21)

"Besides deleting the project ... deleting all the work on the pins ...
make a clean project ... only LED Connection accounts."
- RESET on each Projects row (LC only), the same dialog as DELETE in reset
  mode: type RESET, optional reason. Clears the WORK: material counts and
  sign-off, claims, installed heads, photos, and "submitted". Keeps the job,
  its installers, the site, part numbers and claim emails. Judgment call:
  "the work on the pins" taken as all installer work, so the installer
  starts again from the material check.
- api/deleted mode "reset": archives the work AND a copy of the job record
  to deleted/{key}/files/ (key now has milliseconds, so a delete and a reset
  in the same second never collide), checks the copy, removes the work,
  archives and removes anything saved meanwhile, then clears submitted
  (job.reset records who/when/archive). Audit job.reset.
- The activity log lists it as Reset. RESTORE undoes it (work and submitted
  state back) only while nobody has saved new work since: never overwrites.

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

## Kroger 345 installation guides (Dino, 2026-10-21: "push the guides")
- Same builder and LC look as the Optimus guides (build_guides.py takes a
  `product` block): flood yoke FL-Y, flood slip fitter FL-SF, NightShade
  wall pack FWP, from each product's own instructions in tools/specs/sources/
  (figures: tools/guides/kroger345/extract_figures.py). Published in
  app/guides/flood/ and app/guides/wallpack/, picked by LC part number
  (guides.js BY_PART + PART_READY, tests/guides.test.js keeps them = folders).
- The flood guides carry the 480V step-down as a section: no wiring sheet
  exists for the transformer, so it sends the installer to its own label.
- Downlight LC-UDL-8-A + goof ring LC-UDL-8-GR (Dino, 2026-10-21: "it's RZ
  Lighting ... Upshine ... use [the LC Universal Downlight sheet] ... goof
  ring, find something online"): content/UDL.json from LC's own sheet plus
  online sources in tools/guides/source/kroger345/downlight/ (no installation
  sheet exists for the maker's 8 in DL254; steps and drawings from a goof
  ring instruction for a spring-clip downlight with its box on a whip). Wire
  colours are in no source: the guide sends the installer to the label.
  app/guides/downlight/, BY_PART LC-UDL-8-A.
- Not built, no source anywhere: Optimus large house-side shield
  LC-SLOT-LG-SHIELD (only the SMALL shield's dimension drawing exists).
- Open: FCW1 is set to 20W, but this wall pack's DIP gives 45/60/75W only.

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

## Sites kept in the installer app only (Dino, 2026-10-20)

Kroger 345 (KR-00345-NV, El Dorado Village, 5564 Camino Al Norte, North Las
Vegas; NetSuite 1191; Kroger PO 2698315, requester Jim Green) "written only in
the installer app": nothing goes to the customer portal.
- sites/{id}.json + sites/{id}/site.json in this app's container, the portal's
  "lc-site" shape. site.js reads them FIRST, then the portal; same id = this
  app's wins. GET /api/projects lists both (source "installer" | "portal").
- PUT /api/sites/{id} (LC only; home page UPLOAD SITE FILE). api/shared/
  sitefile.js keeps only the solution fields site.js reads and drops `images`
  (signed SAS links), refuses rows/solutions that do not line up.
- The file is built by tools/sites/build-site.js from tools/sites/{id}/:
  fixtures.csv (LED Audit app export; KR-00345-NV = audit project 73, from the
  1191 job folder Design/w new tags), survey-mapping.tsv (Field Survey
  audit_results.xlsx), project.json (the approved design's schedule). The
  DESIGN wins on product fields (the survey's flood label said -30 (3000K);
  A-02 says LC-FL32A-40-480-40).
- Approved design = the A-02 sent with the PO on 2026-09-09 (tags S01, S02-HS,
  S03, FL1, FCW1, FCW2, DL1-GR; = "A-02-Tag fix.pdf"). "A-02 Approved.pdf"
  (Apr 7) still has the old tags: not it.
- KR-00345-NV: 113 audit rows + 1 added = 114, 88 heads to install (= A-02),
  24 gas-canopy heads excluded (existing LED, not in the design), 20227 /
  20233 removed (double head -> single).
- The 6th FL1 (design 6, audit 5): Dino 2026-10-20 "put the 6th flood on
  20203's pole": project.json "added" ADD-FL1-01, placed opposite 20203
  across pole G12's centre; the pin card says NEW HEAD (row.added, whitelisted
  in site.js) instead of Replaces.
- Pole positions (Dino, 2026-10-21, "fix the location of the pins, same as
  the customer portal"): the audit dropped the two heads of each back-to-back
  S03 pole 25-31 ft apart. build-site.js tidyPoles (project.json, 4 ft):
  every pole with 2+ heads goes to the middle of its own heads' audit pins,
  heads on an even ring, the audit position kept as audit latitude /
  longitude. 28 pins moved (S03 18, FL1 6, S02-HS 2, removed 2), max 12 ft;
  pin ids unchanged. NOT yet checked against the aerial: this session's
  network blocks Google / Esri / OSM. project.poleAt { G15: { lat, lng } }
  pins a pole to a spot measured from the aerial once that is possible.
- Heads placed from the aerial (Dino, 2026-10-21, screenshots of the live
  map: "canopy heads ... array, symmetrical; downlights below the canopy,
  straight lines; wall packs on the building, not in the air"): project.json
  placeAt.heads { auditId: { lat, lng, why } }, applied after the pole tidy.
  Measured from his own screenshots: each fitted to the pins' coordinates
  (similarity, residual under 1.3 px = 0.11 m at 0.085 m/px), then canopy
  edges and wall faces read off the aerial in them. 63 heads: fuel canopy
  2 x 12 (CP2 in the middle of the first row), downlights on even spacing
  along each canopy line (walkway canopy centre line, entrance grid), five
  wall packs onto the wall face. The 4 north downlights were off-screen and
  keep their audit spots. Takes effect when the rebuilt site file is uploaded
  (UPLOAD SITE FILE); pin ids and saved work are unchanged.
- Pole ids: blank audit pole ids take the Field Survey group (G10...); heads
  to install still without one (the floods) join the pole whose centre is
  within 6 m. Wall packs and downlights stay off poles.
- Spec sheets (Dino, 2026-10-20 "add the spec sheets"): a product with no
  catalog prodId finds its catalog product by FAMILY name when exactly one
  catalog product has it (catalog.js byFamily): the Optimus heads. The rest
  have no catalog product, so LED Connection's own spec sheet PDFs are
  bundled in app/specs/ by part number (api/shared/specs.js BY_PART + READY,
  tests/specs.test.js keeps READY = folder): LC-FWP-WS-3CCT -> the
  Nightshade Series Full Cutoff Wallpack sheet, LC-UDL-8-A -> the Universal
  Downlight Series sheet (Marketing-2025 > LED > SpecSheets). Waiting on
  the PDFs (SharePoint gives this session text only, not the file). No LC
  sheet found for the LC-FL-WS-3CCT flood (the Architectural Floodlight
  is LC-AFL, the Utility Floodlight LC-UFL).
- The Nightshade wall pack sheet lists 45/65/75W; SO636 says FCW1 is set to
  20W. Confirm the 20W setting with Dino.
- Part numbers (Dino, 2026-10-20), from what NetSuite SO636 SHIPPED, not
  the Walmart rules: Optimus = the 230W hardware (Dino: "230W hardware"),
  bronze, 4000K CRI 80, straight arm SS: S03 LC-SLOT-230W-HV-L5-XX-40-80-
  T5S-SS-BR; S01 and S02-HS LC-SLOT-230W-HV-L5-XX-40-80-T4-SS-BR (one
  fixture, dip switch to 75W; S02-HS adds LC-SLOT-LG-SHIELD). No order logic
  for the rest, so the LC item that shipped (not checked): FCW1/FCW2
  LC-FWP-WS-3CCT (set 20W / 45W), FL1 LC-FL-WS-3CCT-SF (slip fitter, Dino 2026-10-21: "they have a slip
  fitter mount", not the yoke -Y; 40W, through a
  480-to-277V step-down), DL1-GR LC-UDL-8-A + goof ring LC-UDL-8-GR.
- parts.js SETUP[label]: how a head is set up where the part number does not
  say it (dip switch, shield, goof ring, transformer). Shown as SET UP on the
  material line, pin card and job sheet, only while the decided number
  applies. Look-alike lines (same part number) get their design tags in the
  name ("Optimus 230W · T4 · S02-HS").
- The landlord's audit (project 74, "Audit Data - 5-27-26.csv", NetSuite 1583)
  is a different job.

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
  stored), EMAILED at once (Dino, 2026-10-21, "mandatory ... same like the
  customer portal"): api/users deliverLink -> mail.js inviteEmail, worded
  for the role (installer + company, or LED Connection admin), same route
  as every app email (Graph, else the Outlook relay), Dino BCC'd. Sent
  only after the login is saved. NEW LINK / RESET LINK email too. The link
  shows on the page (once) only when the email will not reach them: no
  email on the login (installers may have only a phone), mail not set up
  or failed, or queued while the relay has not checked in for 15 minutes.
- Putting an installer on a job (INSTALLERS, or START JOB with them ticked)
  emails that installer "[job] New install job for you" with an OPEN THE
  JOB button, to them alone (claimmail.js notifyAssigned).
- Page messages on the home page are a floating toast (#msg fixed at the
  bottom), so a result never lands out of sight.
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
- `installer` - field crew, LC's own or a subcontractor. Manages nobody.
  Email optional, phone allowed.
- Installer companies (Dino, 2026-10-21: "first a customer, then people
  inside that customer that will be installers, and we allocate them to a
  site as we go ... they only see the projects we assign them"): the
  portal's Customers, for crews. companies/{id}.json (api/companies, LC
  only: name, office phone / email, status). Every installer login belongs
  to one (users.companyId, required by the API; its name is kept on the
  login as `company` and renamed with it). Home page: INSTALLER COMPANIES
  AND LOGINS, one group per company (+ ADD PERSON presets the add form,
  SWITCH OFF signs all its people out and refuses their sign-in), then
  "Not in a company yet" (logins made before this, MOVE TO), then LED
  Connection admins. The INSTALLERS dialog groups people by company with a
  "whole crew" tick. Visibility is still per person (a job lists
  usernames): judgment call, so a big crew can be split across sites.
  LED Connection's own field people go in a company called LED Connection.
Logins are LED Connection only, as in the portal.

## Writing back to the customer portal

Not built. Installed dates, serials and photos belong in the portal's asset
records eventually; that goes through the portal's API with its own key,
never by writing its container.

## Local dev and tests

- `node dev/server.js` serves the site AND runs api/ on http://localhost:4310
  with storage in `dev/.data` (gitignored). Setup key locally is
  `local-dev-setup-key`.
- `npm test` = tests/sites.test.js (KR-00345-NV build against the A-02
  schedule, upload check) + tests/site.test.js (7 unit tests of the site reader: product
  names as the portal shows them, counts, excluded heads, moved pins, no
  internal fields) + tests/parts.test.js (order logic) + tests/guides.test.js + tests/api.test.js, 250 checks through the real HTTP API on a throwaway
  store: setup once, CSRF header, cookie flags, invite once, lockout,
  installer cannot manage logins, switch-off and password change end
  sessions, last admin, audit, token never stored; jobs: visibility, no
  pricing/vendor/notes, BOM counts, moved pins, material sign-off, claims,
  photos, pins, submit; claim email (outbox, note, missing, photo) and the Outlook relay (pair LC only, key hash only, queue, fetch, ack; the portal relay's key; LC list @ledconnection.com only; per-project installers and client on CC); delete and restore (LC only, confirmation, archive complete before removal, audit, portal untouched); reset (job, installers and site stay; undo refused after new work); uploaded sites (LC only, nothing internal stored,
  same pin ids on replace). Runs in CI before every deploy.

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

## Installable app (Dino, 2026-10-21: "a standalone app, like the customer portal")
- Icon: the LED Connection logo (app/lc-logo.png, the portal's file) on the
  dark tile with the orange frame, and a cyan open-end wrench under it, so it
  reads as the installer's app next to the portal and the LED Audit App.
  Source and rebuild: tools/icon/ (icon-192/512, maskable in the 80% safe
  zone, apple-touch-icon-180, favicon-16/32).
- INSTALL APP in the BETA banner (lci.js) when the browser offers the
  install (beforeinstallprompt: Edge / Chrome desktop, Android) and the page
  is not already the app. On iPad / iPhone there is no prompt, so the button
  shows a tip: Share, then Add to Home Screen.
- Manifest: start_url index.html, handle_links preferred (app links open in
  it), launch_handler navigate-existing, a "My jobs" shortcut. Served as
  application/manifest+json (staticwebapp.config mimeTypes), as in the portal.
- sw.js stays NETWORK FIRST and never touches /api/; CACHE lci-shell-v2 after
  the icon change. Removing the BETA banner removes INSTALL APP with it.

## Conventions

- Dark HUD look from the portal (lci.css): orange `#f37021`, cyan `#22d3ee`,
  Orbitron, Barlow, JetBrains Mono. BETA strip from lci.js.
- Phone first: installers are on site. Under `(pointer:coarse)` every
  control reaches 44 px.
- US projects imperial by default. No emoji as icons.
