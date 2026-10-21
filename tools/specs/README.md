# LC spec sheets (Installer App)

Built with the project skill `.claude/skills/lc-spec-sheet` (the sourcing desk's LC
template pipeline, moved here 2026-10-21). Read its SKILL.md first.

- `<SKU>.json`: the product file, every value with its source (`src`, never printed).
- `sources/<SKU>/`: the supplier document it was read from (tools/ is never deployed).
- `preview/<SKU>.pdf`: the built sheet. `preview/_work/` is scratch (git-ignored).

    python3 .claude/skills/lc-spec-sheet/scripts/make_sheet.py tools/specs/LC-FL-WS-3CCT.json

## LC-FL-WS-3CCT (Kroger 345 FL1), DRAFT

Dino 2026-10-21: no red banner, no draft text on the sheet, warranty 5 years, rated life 50,000 h.
Open items (kept here and in the product file _open_items, never printed):
1. Wattage: supplier sheet 50/60/80 W, quote and LC item 40/60/80 W; FL1 is set at 40 W. Confirm with the supplier.
2. CRI: Ra > 70 (table) vs Ra > 80 (cover badge). Efficacy: 120 lm/W (sheet) vs > 140 lm/W (quote).
3. Rated life: supplier says 30,000 h; LC rates 50,000 h, needs LM-80 / TM-21.
4. Pending: UL/ETL under LED Connection, DLC, IES (photometric page), family name.
