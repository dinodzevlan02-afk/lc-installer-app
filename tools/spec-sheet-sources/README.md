# LC spec sheet sources (for the lc-spec-sheet skill)

Pushed from Dino's PC on 2026-10-21 so the Installer App session can build the
**lc-spec-sheet** skill and finish the Kroger 345 spec sheets. Nothing here runs in
the app; `tools/` is never deployed. Not for main as-is: it is source material.

The desk has **two** LC spec sheet builders. They make different-looking sheets.
The skill should pick one, or merge them, with Dino.

## 1. `desk-pipeline/`: the LC template overlay (LC-BFL, LC-FL-WS-3CCT)

- `specsheet/AGENT.md` is the house rulebook (the "LC spec sheet skill" Dino means):
  never name the factory, only verified certifications, nothing commercial, LC-first
  SKUs, the family name and SKU prefix are Dino's to assign, IES needed for the
  photometric page.
- `specsheet/rebrand.py` turns a draft (`*.draft.json`, values read from the supplier
  document, every value `verified:false`) into a sheet dict. `overlay.py` prints it on
  `specsheet/assets/template_LC-TP.pdf` (3 pages) with the Poppins fonts. `build.py
  check()` is the release gate; drafts pass `allow_no_ul=True`. `project-sheet.py`
  has `leak_check()` (supplier words in the output = refusal).
- `haber-specsheet.py` is the email-driven wrapper. It imports `haber.py` (the desk
  agent: model calls, config) and `slack/links.py`, which are NOT included. For a
  scripted build you need only `rebrand`, `overlay`, `build` and `project-sheet.leak_check`,
  as the two examples do.
- `examples/build_lc_bfl.py` (Oct 1, bullet flood) and `examples/build_lc_fl_ws.py`
  (Oct 21, Kroger 345 FL1 flood) are the worked examples. The example PDFs are their output.
  Paths in them point at Dino's PC (`C:\Users\DinoDzevlan\...`, OneDrive `Spec Sheet Drafts`).
- Traps found on Oct 21, worth building into the skill:
  - The red PRE-RELEASE band and the page-3 NOTE box print **nothing** when the text
    overflows. Keep the band to about 5 short lines, the NOTE to one line. Longer
    lists (conflicts) go in their own box (see build_lc_fl_ws.py, page 3).
  - A cover chip wraps at about 10 characters ("3000/4000/5000K" broke). Use "30/40/50K".
  - The rebrand labels the life chip "L70". Rated life is not L70; override the chip.

## 2. `optimus-builder/`: the HTML builder (LC Optimus, Kestrel 3, Strata T8, Youlumi family)

- `common.py` (doc shell, CSS, vendor-word leak check, HTML to PDF, metadata strip,
  previews) plus one `sheet_*.py` per product, each writing `<name>.html` and the PDF.
  `verify.py` / `verify_optimus.py` re-check a built PDF independently.
- `assets/`: LED Connection logos, icons, product renders and bracket drawings,
  Poppins fonts.
- `common.OUT` and the source folders are Dino's PC paths. The supplier source folders
  (`_src_cat`, `_src_ies`, `_src_inst`, `_src_old`, `_src_pages`) were left out on
  purpose: they are supplier catalogs, IES files and pages, not LED Connection's.

## 3. `sources/`

- `Spec sheet for Gen 9 LED Flood light.pdf`: the supplier datasheet LC-FL-WS-3CCT was
  read from (80W platform). Its quotation is not here (pricing).

## LC-FL-WS-3CCT draft (Kroger 345 FL1), the open points

- Wattage: supplier sheet 50/60/80W, quote and LC item 40/60/80W, FL1 set at 40W.
  The sheet prints 40/60/80W, to be confirmed with the supplier.
- CRI: table Ra >70, cover badge Ra >80. Efficacy: sheet 120 lm/W, quote >140 lm/W.
- Warranty, UL/ETL under LED Connection, IES, LM-80/TM-21: pending.

## Note on the example draft

`desk-pipeline/examples/LC-BFL.model.draft.json` is the draft both examples load as their shape. On Dino's PC it is `Spec Sheet Drafts/0930-0255-Spec-sheet-for-angle-adjustable-bullet-flood-light.model.draft.json` (renamed here: the long name broke the Windows path limit).
