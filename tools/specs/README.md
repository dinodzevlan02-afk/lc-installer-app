# LC spec sheets (Installer App)

Published 2026-10-21 (Dino: spec sheet beside the installation guide on the pin card):
app/specs/LC-Floodlight-Selectable.pdf, LC-Nightshade-Full-Cutoff-Wallpack.pdf,
LC-Universal-Downlight-Series.pdf, mapped in api/shared/specs.js. Rebuild = copy the
preview over the app/specs file. The open items below still stand.

Built with the project skill `.claude/skills/lc-spec-sheet` (the sourcing desk's LC
template pipeline, moved here 2026-10-21). Read its SKILL.md first.

- `<SKU>.json`: the product file, every value with its source (`src`, never printed).
- `sources/<SKU>/`: the supplier document it was read from (tools/ is never deployed).
- `preview/<SKU>.pdf`: the built sheet. `preview/_work/` is scratch (git-ignored).

    python3 .claude/skills/lc-spec-sheet/scripts/make_sheet.py tools/specs/LC-FL-WS-3CCT.json

## LC-FL-WS-3CCT (Kroger 345 FL1, slip fitter -SF)

Dino 2026-10-21: no red banner, no draft text on the sheet, warranty 5 years, rated life 50,000 h.
Open items (kept here and in the product file _open_items, never printed):
1. Wattage: supplier sheet 50/60/80 W, quote and LC item 40/60/80 W; FL1 is set at 40 W. Confirm with the supplier.
2. CRI: Ra > 70 (table) vs Ra > 80 (cover badge). Efficacy: 120 lm/W (sheet) vs > 140 lm/W (quote).
3. Rated life: supplier says 30,000 h; LC rates 50,000 h, needs LM-80 / TM-21.
4. Pending: UL/ETL under LED Connection, DLC, IES (photometric page), family name.

## LC-FWP-WS-3CCT NightShade full cutoff wall pack (Kroger 345 FCW1, FCW2)

Open items (never printed):
1. Wattage: supplier datasheet and LC item 45/60/75W; LED Connection's 2023 sheet prints 45/65/75W. Printed 45/60/75W.
2. Kroger 345 FCW1 runs at 20W: not a setting of this fixture. The only LC sheet with 20W is LC-WP07-20W (SharePoint _vaughan > Spec Sheets, 2025-04-23), a different SKU. Decide how FCW1 is documented.
3. HV 347/480V is on the 2023 LC sheet but not in the supplier datasheet: left off the order logic.
4. Efficacy: LC sheet up to 130 lm/W, supplier 140 lm/W. Printed 130.
5. Operating temperature: supplier -40F to +104F (printed); LC 2023 sheet -25C to 50C.
6. UL listed, Dark Sky, DLC logos on the 2023 sheet: not printed until verified under LED Connection.

## LC-UDL-8-A Universal Downlight 8 in + LC-UDL-8-GR goof ring (Kroger 345 DL1-GR)

Open items (never printed):
1. CCT: LC sheet and the switch label read 3000/3500/4000K; LC item text says 30/40/50K. Printed 3000/3500/4000K. Kroger 345 uses 4000K (in both).
2. Voltage: LC sheet table 120-277V (printed), its overview 100-277VAC.
3. What '-A' stands for is not written anywhere; printed as the item text describes it.
4. Efficacy computed from the LC sheet's 8 in lumens (113 lm/W at 12/16W, 107 at 22W); family headline on the old sheet was up to 115 lm/W.
5. No supplier datasheet on file (NetSuite points to RZ Lighting): no wiring colours, weight or installation steps on this sheet.
6. Goof ring: NetSuite text only, no drawing.

