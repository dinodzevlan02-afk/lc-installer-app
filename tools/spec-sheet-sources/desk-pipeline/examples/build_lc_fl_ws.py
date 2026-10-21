# LC spec sheet DRAFT for LC-FL-WS-3CCT, the 40/60/80W 3CCT flood on Kroger 345 (SO636, design tag FL1).
# Dino 2026-10-21 (via the Installer App session): "build it like LC spec sheet skill ... Use LC spec sheet."
# Same pipeline and rules as LC-BFL (build_lc_bfl.py): rebrand -> leak check -> check -> overlay on the LC
# template; factory never named; DRAFT band; only what the vendor documents print.
# Source: the vendor's "9th Gen LED Flood Light" sheet, 80W platform (FL0908-80W), and its quotation.
# The part numbers are the ones LED Connection already sells (Kroger Standard Part Numbers, 2026-04-06):
# LC-FL-WS-3CCT-SF (slip-fitter) and LC-FL-WS-3CCT-Y (yoke). No new order logic is invented.
import io, json, os, sys, importlib.util
import pymupdf
sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"C:\Users\DinoDzevlan\Downloads\lc-sourcing"
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("hs", os.path.join(ROOT, "haber-specsheet.py"))
HS = importlib.util.module_from_spec(spec); spec.loader.exec_module(HS)
rebrand, overlay, builder, PS = HS.rebrand, HS.overlay, HS.builder, HS.PS

VENDOR_PDF = os.path.join(ROOT, r"log\rab-bullet-20260929\torshare-2025\Spec sheet for Gen 9 LED Flood light.pdf")

# The LC-BFL model draft gives the shape; every value below replaces its values.
dj = json.load(io.open(os.path.join(HS.DRAFTS, "0930-0255-Spec-sheet-for-angle-adjustable-bullet-flood-light.model.draft.json"), encoding="utf-8"))
SRC = "vendor 9th Gen flood datasheet (80W platform) and its quotation"


def f(vals, note):
    return {"candidates": vals, "confirm": note, "verified": False, "source": SRC}


dj["_source_document"] = {"file": os.path.basename(VENDOR_PDF), "vendor": "Torshare", "models": ["TS-FL0908-80W"]}
dj["product_type"] = "LED Flood Light"
dj["_category"] = "lighting"
dj["extracted"] = {
    "wattage": f(["40W", "60W", "80W"], "field selectable; CONFLICT: datasheet says 50/60/80W, quote and LC item say 40/60/80W"),
    "voltage": f(["120-277VAC"], "datasheet table"),
    "efficacy": f(["120 lm/W"], "datasheet table; CONFLICT: quote says >140 lm/W"),
    "cct": f(["3000K", "4000K", "5000K"], "field selectable"),
    "cri": f(["Ra >70"], "datasheet table; CONFLICT: cover badge says Ra >80"),
    "lifetime": f(["30,000 h"], "datasheet table, rated life"),
    "ip_rating": f(["IP65, wet location"], "datasheet features + table"),
    "power_factor": f([">0.9"], "datasheet cover badge"),
    "current": f(["0.733 A at 80W"], "datasheet table, 80W platform"),
    "controls": f(["0-10V dimming (purple DIM+, pink DIM-)"], "datasheet wiring diagram"),
    "adjustment": f(["Wattage and CCT switches under a rear cover"], "datasheet power adjustment steps"),
    "mounting": f(["Yoke (Y)", "Slip-fitter (SF), pole up to 2-3/8 in (60 mm), aiming 0-90 deg"], "datasheet installation pages"),
    "material": f(["ADC12 die-cast aluminium, integrated heat-sink fins, drainage groove"], "datasheet features"),
    "finish": f(["Bronze (grey-brown)", "Black"], "datasheet features"),
    "operating_temp": f(["-40 F to +104 F"], "datasheet table"),
    "storage_temp": f(["-40 F to +158 F"], "datasheet table"),
}
dj["possible_certifications"] = {}   # no ETL/UL under LED Connection on file: nothing reaches the sheet

FAMILY = "Selectable Floodlight"     # placeholder until Dino names the family
SKU = "LC-FL-WS-3CCT"
PTYPE = "LED Flood Light, Selectable"
sheet = rebrand.to_sheet(dj, FAMILY, PTYPE, SKU)
sheet["cover"]["subtitle"] = "DRAFT - PLACEHOLDER FAMILY NAME - REQUIRES DINO'S APPROVAL"
sheet["cover"]["tagline"] = "SELECTABLE POWER. SELECTABLE CCT. YOKE OR SLIP-FITTER."
sheet["cover"]["chips"] = {"WATTAGE": "40/60/80W", "VOLTAGE": "120-277V", "LIFESPAN": "30,000 h",
                           "WARRANTY": "Pending", "CRI": ">70", "CCT": "30/40/50K"}
sheet["cover"]["headline_efficacy"] = "120 LM/W"
sheet["cover"]["positioning"] = ("A die-cast flood for building, sign and site lighting. Power and colour temperature are set in the "
                                 "field, and the same fixture ships on a yoke or a slip-fitter. "
                                 "For custom solutions please contact our sales representative.")
sheet["badges"] = ["3 WATTAGES", "3 CCTS", "IP65", "0-10V"]
sheet["quality_line"] = "ADC12 die-cast aluminium with integrated fins, IP65 with a drainage groove, wet-location rated."
sheet["description"] = (
    "The Selectable Floodlight is a die-cast aluminium flood for building, sign and site lighting. Power (40, 60 or 80W) and "
    "colour temperature (3000, 4000 or 5000K) are set on switches under a rear cover, so one fixture covers several designs. "
    "It runs on 120-277VAC with 0-10V dimming, is IP65 and wet-location rated, and mounts on a yoke or a slip-fitter "
    "(pole up to 2-3/8 in, aiming 0-90 deg). On a 480V circuit it needs a step-down transformer to 277V.")
sheet["overview"] = [r for r in sheet["overview"] if not r.startswith(("Current", "Adjustment"))][:9] + [
    "Input: 120-277VAC only. A 480V circuit needs a step-down transformer to 277V."]
sheet["order_logic"] = {
    "sample_code": "LC - FL - WS - 3CCT - Y",
    "segments": [
        {"n": "01", "name": "BRAND", "options": [["LC", "LED Connection - fixed, every SKU"]]},
        {"n": "02", "name": "SERIES", "options": [["FL", "Floodlight"]]},
        {"n": "03", "name": "WATTAGE", "options": [["WS", "40/60/80W selectable"]]},
        {"n": "04", "name": "CCT", "options": [["3CCT", "3000/4000/5000K selectable"]]},
        {"n": "05", "name": "MOUNTING", "options": [["Y", "Yoke"], ["SF", "Slip-fitter"]]},
    ]}
# Dimensions go on page 2 beside the drawing (added after the build), not in the three grey boxes.
sheet["dimensions"] = {}

vw = {"torshare", "ledman", "fl0903", "fl0908", "fl0912", "fl0930", "ts-fl0908", "9th gen", "gen 9"}
leaks = PS.leak_check(sheet, vw)
if leaks:
    raise SystemExit("vendor identity leaked: %s" % leaks)

# Hero photo and dimension drawings, cropped from the vendor sheet (pages 1 and 3) without its logo or model table.
doc = pymupdf.open(VENDOR_PDF)
z = pymupdf.Matrix(3, 3)
hero_png = os.path.join(HERE, "hero.png")
doc[0].get_pixmap(matrix=z, clip=pymupdf.Rect(46, 274, 548, 612)).save(hero_png)
draw_png = os.path.join(HERE, "drawing.png")
doc[2].get_pixmap(matrix=z, clip=pymupdf.Rect(14, 414, 386, 590)).save(draw_png)
sheet["hero_png"] = hero_png

blocking, warn = builder.check(sheet, allow_no_ul=True)
if blocking:
    raise SystemExit("blocked: %s" % blocking)
# The red band holds only a few short lines: overflow makes the template print NOTHING (seen on the first build).
# The full conflict list goes in the NOTE box on page 3.
print("builder warnings:", warn)
band = ["DRAFT - REQUIRES DINO'S APPROVAL. Values as read from the supplier documents, none verified.",
        "Placeholder family name. Part numbers LC-FL-WS-3CCT-Y / -SF kept as already sold.",
        "CONFLICTS on wattage, CRI and efficacy between supplier documents: see the NOTE on page 3.",
        "Pending: warranty, UL/ETL under LED Connection, IES photometrics, LM-80 / TM-21.",
        "Photo and drawings come from the supplier sheet: check them for any supplier mark."]
# The NOTE box prints in capitals and also blanks on overflow: keep it one line; the list gets its own box below.
sheet["electrical"]["note"] = "Draft: the supplier documents disagree on wattage, CRI and efficacy. See DRAFT CONFLICTS below."
CONFLICTS = (
    "Wattage: supplier sheet 50/60/80W; supplier quote and LC item 40/60/80W; Kroger 345 FL1 is set at 40W. Printed 40/60/80W, "
    "confirm the 40W setting with the supplier.\n"
    "CRI: parameter table Ra >70, cover badge Ra >80. Printed >70.\n"
    "Efficacy: supplier sheet 120 lm/W, supplier quote >140 lm/W. Printed 120 lm/W.\n"
    "Photocell: mentioned in the supplier's feature text, not in its table or our part number. Not on this sheet.\n"
    "Warranty: the supplier's badge says 5 years. LED Connection sets its own warranty; shown as Pending.")
out = os.path.join(HS.DRAFTS, "DRAFT LC Spec Sheet - LC-FL-WS-3CCT - Selectable Floodlight - requires Dino approval.pdf")
tmp = out.replace(".pdf", ".tmp.pdf")
path, poppins = overlay.build(sheet, band, tmp)

# Page 2: the drawing on the left, the 80W dimensions on the right, in the space the grey boxes use.
IN = 25.4
def mm(x):
    return "%d mm" % round(x * IN)
pdf = pymupdf.open(path)
p2 = pdf[1]
R, F = overlay.R, overlay.Fonts(p2)
p2.insert_image(R(60, 995, 560, 1140), filename=draw_png, keep_proportion=True)
lines = ("YOKE (E x F x D)\n9.61 x 10.07 x 3.23 in\n(%s x %s x %s)\n\nSLIP-FITTER (A x B x D)\n9.42 x 14.35 x 3.23 in\n(%s x %s x %s)\n\nWEIGHT  4.96 lb (2.25 kg)"
         % (mm(9.61), mm(10.07), mm(3.23), mm(9.42), mm(14.35), mm(3.23)))
p2.draw_rect(R(585, 1000, 900, 1140), color=None, fill=overlay.GREY)
overlay.text(p2, F, R(600, 1006, 890, 1136), lines, "semi", 7.6, overlay.INK, lh=1.2)
# Page 3: DRAFT CONFLICTS in the free space between LUMEN MAINTENANCE and the footer (page points, not design px).
p3 = pdf[2]
F3 = overlay.Fonts(p3)
PX = overlay.PX
box = pymupdf.Rect(36, 704, 576, 764)
p3.draw_rect(box, color=None, fill=(0.99, 0.94, 0.90))
p3.draw_rect(pymupdf.Rect(36, 704, 38.5, 764), color=None, fill=overlay.ORANGE)
overlay.text(p3, F3, R(77, 704 / PX + 6, 880, 704 / PX + 20), "DRAFT CONFLICTS", "bold", 6.6, overlay.INK)
overlay.text(p3, F3, R(77, 704 / PX + 22, 880, 764 / PX - 2), CONFLICTS, "light", 6.0, overlay.INK, lh=1.2)
pdf.save(out, garbage=3, deflate=True)
pdf.close()
os.remove(tmp)
print("built:", out)
