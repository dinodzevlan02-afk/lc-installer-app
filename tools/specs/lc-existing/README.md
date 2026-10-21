# LED Connection's existing sheets for the other Kroger 345 (SO636) products

LED Connection's own documents only, copied from Dino's PC on 2026-10-21
(OneDrive: LED Documents - Engineering > LC SPEC SHEETS, and Teams chat files).

| File | What it covers | Notes |
|---|---|---|
| `LC SPEC SHEET_Full Cutoff Wallpack_TS Quick Ship.pdf` (2023-05-09) | **LC-FWP** Full Cutoff Wallpack, **WS 45/65/75W**, **3CCT** 30/40/50K, NV 120-277V / HV 347/480V, BL/BR/CS, PC, EM8W | The order logic matches the SO636 part **LC-FWP-WS-3CCT** exactly. Covers **FCW2 at 45W**. Does **not** list 20W. |
| `LC SPEC SHEET_Nightshade Series Full Cutoff Wallpack.pdf` (2021-08-13) | **LC-FCWP** NightShade, 30W / 50W / WS 15/30/50/72W, single CCTs (30K/40K/50K), FT/WT reflector, OS, PC | Older, different part family (LC-FCWP, no 3CCT). No 20W either. |
| `LC SPEC SHEET_Universal Downlight Series.pdf` (2022-01-04) | **LC-UDL-4/6/8/10**. LC-UDL-8: 12/16/22W (1350/1800/2350 lm), 3000/3500/4000K, 120-277V 0-10V | No separate sheet for the goof ring. The sheet only says "Goof rings provide support for oversized downlight cavities". |
| `Optimus House shield - line drawings.pdf` (DNC1, April 2024) | House-side shield for the **Optimus small** head: 10.78 x 5.11 in plate, hole spacing | LC-SLOT-LG-SHIELD is the LARGE shield; this drawing is for the small one. No LC sheet for the large shield found. |

## What could not be pushed (SharePoint only, not synced to this PC: text read, file not downloaded)

- `Nightshade series Full Cutoff Wallpack - DLC Code 20w.pdf` (_vaughan > Spec Sheets, modified 2025-03-27).
  It is the NightShade FC wallpack sheet "1-24-24-For Jim".
- `TS-WP07-20W-H-TCP.pdf` (Marketing > _Branding > 01 - LED > Projects > 0013-SpecSheet-Rebates >
  04-23-25--TS-WP07-40W-H-TCP--20w28w, 2025-04-23; copy in _vaughan > Spec Sheets). An **LC sheet for a
  20W NightShade full cutoff wall pack**: order logic **LC-WP07** - 20W - H (120-277VAC) - TCP (CCT
  selectable) - CT (90x100 deg) - MS / EM / EMS / PT / PMS / EMSPT; -40F to +104F, IP65, CRI 80+, 50,000 h,
  5-year warranty, 11.4 x 5.1 x 6.72 in, 0-10V (purple DIM+, gray DIM-), L70 160,000 h at 25C, 89.6% at
  50,000 h (LM-80 / TM-21). The folder name says a 40W platform set to 20/28W for rebates.
  **This is the only LED Connection document found that covers a 20W full cutoff wall pack.**
  Its file name and "dlc code" line carry the factory's model code; strip that before reuse.

## Not found

- KTAT-70-480-277-RJS (480V to 277V step-down, FL1): no LED Connection sheet or drawing. Only internal
  records mention it ("480V Stepdown Transformer, 347V/480V to 277V", a change order, a warehouse RCA).
- LC-UDL-8-GR goof ring: no LC sheet or drawing; NetSuite/BOM text only: "Goof Ring LED Downlight,
  Up to 12" Diam." (12 in goof ring for the 8 in downlight).

## Supplier sources pushed with these (tools/specs/sources/)

- `sources/LC-FWP-WS-3CCT/fcw-spec-install.pdf`: the wall pack supplier's spec sheet and installation instruction (7 pages): 45/60/75W selectable, 3000/4000/5000K, 140 lm/W, 120-277V, 0-10V, photocell. It shows no 20W setting either.
- LC-UDL-8-A / -GR: supplier per a NetSuite quote export is RZ Lighting (Up-shine's sister company). No local RZ/Up-shine document is clearly the 8 in 12/16/22W universal downlight, so none is pushed; confirm the model in NetSuite first.
- LC-SLOT-LG-SHIELD: only the LED Connection drawing above (small Optimus), which carries no supplier mark.
