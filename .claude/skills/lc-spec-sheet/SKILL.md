---
name: lc-spec-sheet
description: Build an LED Connection (LC) spec sheet PDF for a product LC sells, on the LC template (navy rail, hero photo, six cover chips, product description / overview / dimensions, order logic / electrical data / lumen maintenance). Use whenever Dino asks for an "LC spec sheet", "spec sheet in LC format", "LC template", or a spec sheet for a sourced product (e.g. a Kroger 345 item with no LC sheet). Not for installation guides (tools/guides) and not for the catalog's own Optimus generator.
---

# LC spec sheet

The sourcing desk's spec-sheet pipeline, moved here on 2026-10-21 (Dino: "make it a
proper skill ... to installer app repository"). The engine in `scripts/specsheet/` is
the desk's code, copied unchanged except one line (hero size when there is no banner).
The house rulebook is `references/rulebook.md`. Read it before the first sheet of a
session; the rules below are the short form, not a replacement.

## Hard rules (from the rulebook, Dino's decisions)

1. **Never name the factory.** Not its name, model codes, part-number scheme, marketing
   phrases, or a photo with its badge. Every product file lists `vendor_words`; the build
   refuses if any appears in the sheet data or the rendered PDF text.
2. **Only verified certifications.** UL/ETL needs a file number AND the named standard,
   under LED Connection. DLC needs a human-checked Product ID. Unverified = omitted, never
   estimated. `certifications` stays `{}` until then.
3. **Nothing commercial.** No price, cost, MOQ, incoterm, lead time.
4. **Every code starts with LC; family names and SKU prefixes are Dino's.** Keep part
   numbers LC already sells; never invent a new order logic. An unnamed family is a
   placeholder and the cover subtitle says so.
5. **Order logic lists only options LC actually buys**, not the factory's full catalogue.
6. **Nothing from memory.** Every value comes from a document (supplier datasheet, quote,
   LC item text, test report). Each `extracted` field carries `src`.
7. **Conflicts are listed, not resolved by guessing.** They go in `conflicts` (page 3 box)
   and in your report to Dino.
8. **No IES file = no photometric page.** Never trace a curve or borrow a sibling's.
9. **No red PRE-RELEASE banner** (Dino, 2026-10-21: "remove this red banner"). A draft
   shows as the cover subtitle "DRAFT - ... REQUIRES DINO'S APPROVAL" plus the DRAFT
   CONFLICTS box. `"banner": [...]` brings the band back only if Dino asks for it.
10. **Draft until Dino approves.** Without a UL/ETL listing under LC the sheet is a draft
    (`"draft": true` waives the UL gate for the build only); it is never published.
11. **Warranty 5 years, rated life 50,000 h** on LC sheets (Dino, 2026-10-21), as `extracted.warranty` / `extracted.lifetime` and the WARRANTY / LIFESPAN chips. Where the supplier states less, list it in `conflicts`.

## How to build one

1. Gather the documents: the supplier datasheet PDF (put it in
   `tools/specs/sources/<SKU>/`, tools/ is never deployed), the quote (read it, do not
   store prices), LC's item text / part numbers.
2. Copy `tools/specs/LC-FL-WS-3CCT.json` (live example; `examples/` holds the frozen self-test copy) to `tools/specs/<SKU>.json` and replace every value.
3. Find the hero photo and dimension drawing crops on the datasheet (render the pages
   with pymupdf, read the image, pick a clip in PDF points). No supplier logo inside.
4. Build:
   `python3 .claude/skills/lc-spec-sheet/scripts/make_sheet.py tools/specs/<SKU>.json`
5. Render every page to PNG and LOOK at it before sending (overflow traps below).
6. Send Dino the PDF with: what was read from where, the conflicts, what is pending.

Product file keys (paths relative to the file): `sku`, `family`, `product_type`,
`product_type_label`, `category` (lighting | display), `draft`, `vendor_pdf`, `out`,
`source_note`, `vendor_words`, `extracted` {field: {values, src}}, `certifications`,
`cover` {subtitle, tagline, chips (six), headline_efficacy, positioning}, `badges`,
`quality_line`, `description`, `overview` or `overview_drop` / `overview_max` /
`overview_add`, `order_logic` {sample_code, segments [{n, name, options [[code, text]]}]},
`hero` {page, clip}, `dims_panel` {drawing {page, clip}, text}, `electrical_note`,
`conflicts` [lines], optional `banner`.

Display products (LED screens): chips PITCH · BRIGHTNESS · TRANSPARENCY · REFRESH · IP ·
WARRANTY; no CRI/CCT/efficacy/DLC/IES/lumen maintenance. See rulebook 5a.

## Traps (found on real builds)

- The page-3 NOTE box prints in capitals and prints NOTHING when it overflows: one line.
  Longer lists go in `conflicts`.
- A cover chip wraps at about 10 characters: "30/40/50K", not "3000/4000/5000K".
- rebrand labels the life chip "L70". Rated life is not L70: set `chips` with "LIFESPAN".
- A vendor table with several models: build from the column the quote names, and say which.

## Check the skill still works

`python3 .claude/skills/lc-spec-sheet/scripts/selftest.py` rebuilds the flood example and
compares it with the desk's own PDF (`examples/LC-FL-WS-3CCT.reference.pdf`). Run it after
touching anything in `scripts/`.

## After Dino approves

Set `"draft": false` only with a verified UL/ETL under LC, drop the subtitle's DRAFT line,
write the PDF to `app/specs/<file>.pdf`, add it to `api/shared/specs.js` BY_PART + READY
(tests/specs.test.js keeps them in step), and stage it for the LC catalog
(fixtures/{id}/spec-sheet/).

## Not in this skill

The desk's second builder (HTML, behind the LC Optimus, Kestrel 3, Strata T8 sheets) is on
branch `skill/lc-spec-sheet-sources` under `tools/spec-sheet-sources/optimus-builder/`.
