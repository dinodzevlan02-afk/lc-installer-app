# LC spec sheet DRAFT for the Torshare bullet flood Dino accepted 2026-09-30
# (TS-BFL0225-25W-X-TCP, shipped set at 15W). Dino 2026-10-01: "make LC spec sheet out of the
# torshare product, use LC Template skill ... the name will start LC-BFL-(Vendor order logic)".
# Built through the specsheet pipeline (rebrand -> check -> overlay), with the order logic in the
# vendor's ORDER but LC's own codes (AGENT.md 1.1), and only the options agreed to buy (AGENT.md 4).
import io, json, os, sys, importlib.util
sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"C:\Users\DinoDzevlan\Downloads\lc-sourcing"
spec = importlib.util.spec_from_file_location("hs", os.path.join(ROOT, "haber-specsheet.py"))
HS = importlib.util.module_from_spec(spec); spec.loader.exec_module(HS)
rebrand, overlay, builder, PS = HS.rebrand, HS.overlay, HS.builder, HS.PS

DRAFT = os.path.join(HS.DRAFTS, "0930-0255-Spec-sheet-for-angle-adjustable-bullet-flood-light.model.draft.json")
dj = json.load(io.open(DRAFT, encoding="utf-8"))
SRC = "vendor datasheet (beam spread adjustable bullet flood), quotation 2026-09-30, vendor emails 2026-09-29/30"

def f(vals, note):
    return {"candidates": vals, "confirm": note, "verified": False, "source": SRC}

# The agreed configuration only.
dj["extracted"] = {
    "wattage": f(["15W", "20W", "25W"], "field selectable; shipped set at 15W"),
    "voltage": f(["120-277VAC"], "input voltage"),
    "efficacy": f([">=120 lm/W"], "vendor figure; needs the test report of this part"),
    "cct": f(["3000K", "4000K", "5000K"], "field selectable"),
    "cri": f(["Ra >70"], "CRI"),
    "lifetime": f([">=50,000 h"], "rated life"),
    "warranty": f(["5 years"], "warranty"),
    "beam": f(["47-70 deg (NEMA 4x4)", "71-100 deg (NEMA 5x5)", "101-130 deg (NEMA 6x6)"], "field-adjustable lens"),
    "mounting": f(['1/2" NPS knuckle (standard)', "ground spike", "wall mount plate"], "mounting"),
    "material": f(["Die-cast aluminium housing, PC lens"], "housing"),
    "finish": f(["Grey brown (RAL 8019)", "Verde green (custom order)"], "finish"),
    "operating_temp": f(["-40 F to +113 F"], "operating temperature"),
    "controls": f(["Button photocell (dusk to dawn)"], "photocell"),
    "power_factor": f([">=0.9"], "power factor"),
}
dj["possible_certifications"] = {}   # ETL is the factory's listing; LC multiple listing pending - nothing reaches the sheet

FAMILY = "Bullet Flood Series"
SKU = "LC-BFL"
PTYPE = "LED Bullet Flood, Beam Adjustable"
sheet = rebrand.to_sheet(dj, FAMILY, PTYPE, SKU)
sheet["cover"]["subtitle"] = "DRAFT - PLACEHOLDER FAMILY NAME - REQUIRES DINO'S APPROVAL"
sheet["cover"]["tagline"] = "SELECTABLE POWER. SELECTABLE CCT. ADJUSTABLE BEAM."
sheet["cover"]["chips"] = {"WATTAGE": "15/20/25W", "VOLTAGE": "120-277V", "LIFESPAN": "50,000 h",
                           "WARRANTY": "5 years", "CRI": ">70", "CCT": "3000/4000/5000K"}
sheet["cover"]["headline_efficacy"] = ">=120 LM/W"
sheet["cover"]["positioning"] = ("A compact die-cast bullet flood for landscape, facade and sign lighting. Power, colour temperature "
                                 "and beam spread are all set in the field, so one fixture covers accent spots and wide floods. "
                                 "For custom solutions please contact our sales representative.")
sheet["badges"] = ["3 WATTAGES", "3 CCTS", "3 BEAMS", "5 year warranty"]
sheet["quality_line"] = "Die-cast aluminium housing, wet-location rated, 5-year warranty."
sheet["dimensions"] = {"Weight": "approx. 0.6 kg / 1.3 lb", "Mounting": "1/2 in NPS knuckle", "Drawing": "to follow"}
sheet["description"] = ("The Bullet Flood Series is a compact die-cast aluminium bullet flood for landscape, facade and sign lighting. "
    "Power (15, 20 or 25W), colour temperature (3000, 4000 or 5000K) and beam spread (NEMA 4x4, 5x5 or 6x6) are all set in the field, "
    "so one fixture covers narrow accents and wide floods. It runs on 120-277VAC with a dusk-to-dawn photocell, mounts on a standard 1/2 in NPS knuckle, ground spike or wall plate, "
    "and is suitable for wet locations.")
sheet["order_logic"] = {
    "sample_code": "LC - BFL - 25 - BA - 3C - PC - KN - GB",
    "segments": [
        {"n": "01", "name": "BRAND", "options": [["LC", "LED Connection - fixed, every SKU"]]},
        {"n": "02", "name": "SERIES", "options": [["BFL", "Bullet Flood"]]},
        {"n": "03", "name": "WATTAGE", "options": [["25", "15/20/25W selectable"]]},
        {"n": "04", "name": "BEAM", "options": [["BA", "4x4/5x5/6x6 beam"]]},
        {"n": "05", "name": "CCT", "options": [["3C", "3/4/5K selectable"]]},
        {"n": "06", "name": "CONTROL", "options": [["PC", "Photocell"]]},
        {"n": "07", "name": "MOUNTING", "options": [["KN", '1/2" NPS knuckle'], ["SP", "Ground spike"], ["WP", "Wall plate"]]},
        {"n": "08", "name": "FINISH", "options": [["GB", "Grey brown (RAL 8019)"], ["VG", "Verde green"]]},
    ]}

vw = {"torshare", "ledman", "ts-bfl0215", "ts-bfl0225", "tcp"}
leaks = PS.leak_check(sheet, vw)
if leaks:
    raise SystemExit("vendor identity leaked: %s" % leaks)
hero = os.path.join(HS.FROM, "0930-0255-Spec-sheet-for-angle-adjustable-bullet-flood-light - hero.png")
if os.path.exists(hero):
    sheet["hero_png"] = hero
blocking, warn = builder.check(sheet, allow_no_ul=True)
if blocking:
    raise SystemExit("blocked: %s" % blocking)
band = [HS.APPROVAL,
        "Family name 'Bullet Flood Series' is a placeholder. SKU prefix LC-BFL per Dino 2026-10-01; segments follow the vendor's order in LC codes.",
        "Built on the configuration accepted 2026-09-30: 25W platform shipped set at 15W. Only the options agreed to buy are in the order logic.",
        "ETL: the factory's listing (report 230400862SHA-001, UL 1598 Ed.5 + CSA C22.2 No.250.0) - LC multiple listing pending. No certification is claimed on this sheet.",
        "No IES file for this exact part (25W platform at 15W, 3000K, 5x5) - photometric page omitted; requested from the vendor 2026-09-30.",
        "Efficacy, lumens and rated life are vendor figures, not yet backed by a test report or LM-80/TM-21 for this part.",
        "Hero photo lifted from the vendor datasheet. Check it carries no vendor badge or watermark."] + warn
out = os.path.join(HS.DRAFTS, "DRAFT LC Spec Sheet - LC-BFL - Bullet Flood Series - requires Dino approval.pdf")
path, poppins = overlay.build(sheet, band, out)
print("built:", path)
