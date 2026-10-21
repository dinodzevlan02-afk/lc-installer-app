# LC spec sheets

For products LED Connection sells with no LC spec sheet (Kroger 345 first).

- `content/{part}.json`: every printed line, each with its source (`src`, never printed).
- `python3 tools/specs/build_spec.py {part}` builds `preview/{part}.pdf` (not published: tools/ never reaches the site).
- After Dino approves: set `"draft": false`, then `--publish` writes `app/specs/`; add the file to `api/shared/specs.js` BY_PART + READY.

Rules: nothing from memory; the supplier's name and model codes never appear on
the sheet. Supplier documents stay outside the repo.

## LC-FL-WS-3CCT (DRAFT 1, 2026-10-21)

Sources: the supplier's 9th Gen flood spec sheet + quote (31 Oct 2025, Dino's
mail) and LC's own item description (Kroger part list, 2026-04-06).

Open before approval:
1. Wattage steps. The supplier's spec sheet prints 50/60/80 W for the 80 W model; its quote and
   LC's item say 40/60/80 W, and Kroger 345 FL1 runs at 40 W. The sheet prints 40/60/80. Confirm with the supplier.
2. CRI: the spec table says Ra > 70 (printed); page 1 of the same sheet shows Ra > 80.
3. Efficacy: 120 lm/W (spec sheet + LC item); the quote says > 140 lm/W.
4. Not on the sheet until documents arrive: UL/ETL, DLC, delivered lumens, IES, warranty.
5. No LC product photo yet (frame left on page 1). Photocell: the supplier sheet mentions it, the LC part does not, so it is left off.
