# LC OPTIMUS SERIES (family LC-SLOT), ultra area luminaire, 75 W to 420 W. Built 2026-10-19 for
# the DLC private-label submission (Standard version: no sensor, CRI 80, Type III / IV / V) and
# for customers. Replaces LC SPEC SHEET_Optimus Series Ultra Area Luminaire_V202304.
# Modelled on youlumi-specsheets-20261016\hoist\sheet_hoist.py (LC-XCPA layout). The factory is
# named ZERO times on the sheet (text, metadata, images, file name).
#
# ORDER CODE (Dino, 2026-10-19):
#   LC-SLOT - [size] - [wattage]W - [voltage] - [sensor] - [CCT] - [CRI] - [distribution] - [bracket] - [color]
#   size S = 75/115/145 W, L = 180/200/230 W, XL = 300/420 W; NV = 100-277 VAC, HV = 277-480 VAC;
#   XX = no sensor; 30/40/50; 80; TY03/TY04/TY05; F/R/U/S/T; BK/BR/WH.
#   Example LC-SLOT-S-75W-NV-XX-50-80-TY03-F-BK. Same format as the filled DLC private-label form
#   (AOK Optimus DLC listing 2026-10-19\SSL-LUNA-...-144 models.xlsx), one LC code per DLC model.
#
# PROVENANCE (every number on this sheet)
#  [DLC] lc-sourcing\log\walmart-v811\mail\1008-0011_DLC_Data_Export_2026-08-31.xlsx, sheet
#        "solid-state-lighting", the 144 rows whose model contains "-DV-" and a CRI 80 code
#        (3080/4080/5080) with optics T302/T402/T502 (8 wattages x NV/HV x 3 CCT x 3 optics).
#        Read IN CODE below (load_dlc), columns by header name: Reported Light Output, Reported
#        Efficacy (AC), Reported Input Wattage, Reported Power Factor, Reported Total Harmonic
#        Distortion, Reported CRI (Ra), Reported Backlight/Uplight/Glare (TM-15 BUG), Reported
#        Minimum/Maximum Input Voltage, Dimming Capability and Range ("Continuous Dimming to 10%
#        or below"), Classification ("Standard"), Date Qualified 2026-08-28. Only two of the 144
#        rows carry Tested values (75 W HV 3000K Type IV: 11,814 lm, 156.36 lm/W, 75.56 W at
#        277 V; 145 W NV 3000K Type IV: 21,139 lm tested vs 21,159 lm reported); every printed
#        lumen / efficacy / watt / PF / THD / BUG value is the DLC-REPORTED value, floored to a
#        whole lumen and a whole lm/W (never rounded up). Footnoted "DLC-reported".
#        Optic to LC code: T302 -> TY03 (Type III), T402 -> TY04 (Type IV), T502 -> TY05 (Type V).
#  [CAT] lc-sourcing\log\walmart-v811\aok-1019\1014-0026_..._Catalog_..._for certificate using.pdf
#        p2: dimming continuous, dimming level < 10 pct, 1-10V (wired); rotatable lens; tool-less
#            maintenance; seven brackets; reserved sensor positions; 5 year limited / 10 year
#            warranty.
#        p3: NV = 100-277 VAC, HV = 277-480 VAC; "in case the input voltage fluctuation >= 240 V
#            the High Voltage solution is highly recommended"; Type III / IV / V; tool-free
#            maintenance; cut-off, no uplight; safety rope standard on 300-420 W, ordered
#            separately below 300 W; LED package 5050 (brand not printed, by rule).
#        p4: brackets A slip fitter (dia. 40 / 60 / 76 mm), B adjustable arm, C yoke, D slide and
#            lock, E square pole, F round pole, G trunnion. Vendor 2026-10-19: our S = their D
#            (fits square and round poles, replaces E and F, and is what LC buys). Map A=F, B=R,
#            C=U, D=S, G=T; E and F are not used.
#        p7 parameter table: THD 8-15 pct; PF 0.98-0.99; operating -40 C to 50 C (-40 F to 122 F);
#            surge 10 kV / 20 kV optional; optics T302 80 x 155 deg, T402 90 x 150 deg, T502
#            160 deg; ULOR 0 pct at 0 deg inclination; CCT 3000/4000/5000K; lens polycarbonate;
#            IP66 / IK10 per EN 60529 / EN 62262; vibration 3G per IEC 68-2-6; SCx side view
#            0.02997 / 0.03342 / 0.04686 m2 (S / L / XL); housing heavy-duty die-cast aluminum;
#            finish anti-UV thermosetting polyester (epoxy primer + polyester for very corrosive
#            sites); colours black, bronze, custom; pre-wired 70 cm cable; lifespan L90B10
#            > 100,000 h at Ta 25 C; warranty 5 y standard, 10 y optional; certification
#            UL/cUL/FCC/CE/ENEC/SAA/RoHS; product size S 507 x 327 x 185 mm, L 600 x 410 x 185 mm,
#            300 W 650 x 423 x 380 mm, 420 W 650 x 440 x 390 mm; net weight (+-10 pct) 75 W
#            3.7 kg, 115/145 W 4.0 kg, L 5.6 kg, 300 W 8.9 kg, 420 W 9.6 kg; mounting height
#            generally 4-12 m.
#        p8: bracket weights A 1.1 kg, B 2.0 kg, C 0.9 / 1.0 / 1.5 kg (75-145 / 180-230 /
#            300-420 W), D 1.1 kg, E 1.1 kg, F 1.4 kg, G 1.4 kg; C bracket in cold-rolled steel.
#        p9: construction: heat-dissipation layer, LED board, die-cast unibody housing IP66,
#            tool-less buckle on the driver access panel, rotatable PC lens Type III/IV/V, 1-10V
#            dimmable driver 100-277 V / 277-480 V, surge protection device, bracket access
#            panel for wiring, exchangeable bracket for round / square pole.
#  [OLD] our LC SPEC SHEET_Optimus Series Ultra Area Luminaire_V202304.pdf (7 pages)
#        p1: product description, order logic and brackets F/S/R/U/T, colours BK/BR/WH/CS,
#            single-person installation brackets, field-rotatable lenses, IP66 / IK10 / 3G,
#            limited 5-year / 10-year warranty with www.ledconnection.com/warranty; size table
#            S 16.5 x 10.6 x 2.2 in 10.58 lb (4.8 kg), L 20.2 x 13.8 x 2.2 in 12 lb (5.5 kg),
#            XL 26.7 x 14 x 2.2 in 23.15 lb (10.5 kg); EPA (side) .32 / .36 / .50 ft2; cULus,
#            RoHS, FCC marks in the footer; "actual performance may vary by up to +-10 pct".
#        p2: performance at 277 V, 4000K, CRI 70 (superseded here by [DLC] CRI 80 data).
#        p4: TM-21 L70 123,000 h / 119,000 h (XL2-XL4) at 25 C.
#        p6: bracket fit notes: S straight arm fits 3-4 in round or minimum 3 in square pole;
#            R adjustable arm needs minimum 4 in square pole; F slip fitter fits 2-3/8 in
#            tenons; T trunnion needs a minimum 5.5 in base. Bracket line drawings reused.
#        p7: disclaimer "subject to change without notice".
#        Images reused from [OLD] only (prep_images_optimus.py): p1 render, p6 bracket drawings.
#
# CONFLICTS RESOLVED (more conservative, or DLC value, printed)
#  - Lumens / efficacy: [OLD] p2 CRI 70 figures and [CAT] p7 catalogue figures vs [DLC] CRI 80
#    reported values: printed [DLC], floored. E.g. 75 W 4000K Type III: [OLD] 12,918 lm (CRI 70),
#    [CAT] 12,819 lm, [DLC] NV 12,801 lm / HV 12,345 lm.
#  - Power factor: [CAT] 0.98-0.99 vs [DLC] 0.90-0.97: printed [DLC] ("0.90 or higher").
#  - THD: [CAT] 8-15 pct vs [DLC] 8.4-15 pct: printed "15 percent or lower".
#  - Input wattage: the code carries the nominal wattage; actual input from [DLC] is printed in
#    the tables (e.g. 75 W NV draws 76.4 to 77.9 W).
#  - Rated life: [CAT] L90B10 > 100,000 h vs [OLD] TM-21 L70 119,000-123,000 h (L90 37,000-
#    39,000 h): printed only what both support, "L70 > 100,000 h at 25 C". No TM-21 table.
#  - Dimensions: [OLD] p1 (housing 16.5 x 10.6 x 2.2 in etc.) vs [CAT] p7 product size (larger in
#    every direction): printed [CAT] overall sizes (larger = conservative for clearance).
#  - Weight: [OLD] S 4.8 kg / L 5.5 kg / XL 10.5 kg vs [CAT] S 3.7-4.0 / L 5.6 / XL 8.9-9.6 kg:
#    printed the heavier per size (S 4.8, L 5.6, XL 10.5 kg) as "up to".
#  - EPA: [CAT] SCx side view converted (0.32 / 0.36 / 0.50 ft2) agrees with [OLD] p1.
#  - Lens: [CAT] p3 says PMMA, [CAT] p7 and p9 say polycarbonate: printed polycarbonate.
#  - [CAT] p7 420 W width "440 mm / 16.7 in": 440 mm is 17.3 in; converted in code from mm.
#
# DROPPED / NOT PRINTED
#  - Sensor (SN) and photocell (PC) options, LVDC remote supply, wattage-selectable, NET control,
#    CRI 70/90, custom colour: not on this DLC listing. Note: "Sensor and photocell versions:
#    contact LED Connection".
#  - IDA / DarkSky and DLC Premium marks from [OLD]: not carried over (the DarkSky approval is
#    not documented for this product; the listing is Standard). U0 uplight is printed instead.
#  - LED and driver brands (both sources), photometric plots (old plots are a 160 W model not on
#    this listing; no IES files in hand), the multi-head EPA table and per-bracket L/H/W tables
#    of [OLD] (they disagree with [CAT] sizes), slide-and-lock bracket, pole page.
import math, os, re, sys
from decimal import Decimal, ROUND_HALF_UP
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common as C

NAME = "LC OPTIMUS SERIES"
SERIES = "LC-SLOT"
TITLE = "ULTRA AREA LUMINAIRE &middot; " + NAME
PDF_NAME = "LC SPEC SHEET_OPTIMUS SERIES SLOT 2026.pdf"
PDF_TITLE = "LED Connection Spec Sheet LC-SLOT"
PROJ = "OUTDOOR AREA LIGHTING &nbsp;&middot;&nbsp; 75 W TO 420 W &nbsp;&middot;&nbsp; ISSUED 2026-10-19"
EXAMPLE = ["LC-SLOT", "S", "75W", "NV", "XX", "50", "80", "TY03", "F", "BK"]
DLC_XLSX = r"C:\Users\DinoDzevlan\Downloads\lc-sourcing\log\walmart-v811\mail\1008-0011_DLC_Data_Export_2026-08-31.xlsx"

WATTS = (75, 115, 145, 180, 200, 230, 300, 420)
SIZE_OF = {75: "S", 115: "S", 145: "S", 180: "L", 200: "L", 230: "L", 300: "XL", 420: "XL"}
SIZES = ("S", "L", "XL")
SIZE_NAME = {"S": "Small", "L": "Large", "XL": "X-Large"}
CCTS = (3000, 4000, 5000)
TYS = ((3, "TY03", "Type III"), (4, "TY04", "Type IV"), (5, "TY05", "Type V"))
VOLTS = (("NVS", "NV", "100-277 VAC"), ("HVS", "HV", "277-480 VAC"))


# ---------------------------------------------------------------- units (US first)
def _q(v, nd=1):
    return Decimal(str(v)).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP)


def mm_in(mm):
    return '%s in <span class="mm">(%g mm)</span>' % (_q(Decimal(str(mm)) / Decimal("25.4")), mm)


def kg_lb(kg):
    return '%s lb <span class="mm">(%g kg)</span>' % (_q(Decimal(str(kg)) / Decimal("0.45359237")), kg)


def lb_kg(lb):
    return '%s lb <span class="mm">(%s kg)</span>' % (_q(lb), _q(Decimal(str(lb)) * Decimal("0.45359237")))


def m2_ft2(m2):
    return '%s ft&sup2; <span class="mm">(%s m&sup2;)</span>' % (_q(Decimal(str(m2)) * Decimal("10.7639104"), 2), _q(m2, 3))


def f_c(c):
    return '%d F <span class="mm">(%d C)</span>' % (round(c * 9 / 5.0 + 32), c)


def m_ft(m):
    return "%s ft" % _q(Decimal(str(m)) / Decimal("0.3048"))


def fl(x):
    return int(math.floor(x + 1e-9))


def lm(x):
    return "{:,}".format(fl(x))


# ---------------------------------------------------------------- [DLC] data, read in code
def load_dlc(path):
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    rows = list(wb.worksheets[0].iter_rows(values_only=True))
    H = {h: i for i, h in enumerate(rows[0])}
    pat = re.compile(r"^[A-Z]+-(\d+)WoT-(NVS|HVS)-S5-DV-([345])080-T([345])02-")
    out = {}
    for r in rows[1:]:
        m = pat.match(r[H["Model Number"]] or "")
        if not m:
            continue
        w, v, c, t = int(m.group(1)), m.group(2), int(m.group(3)) * 1000, int(m.group(4))
        assert r[H["Classification"]] == "Standard", r[H["Model Number"]]
        assert r[H["Dimming Capability and Range"]] == "Continuous Dimming to 10% or below"
        assert int(r[H["Reported CCT"]]) == c
        out[(w, v, c, t)] = dict(
            lm=float(r[H["Reported Light Output"]]), lpw=float(r[H["Reported Efficacy (AC)"]]),
            w=float(r[H["Reported Input Wattage"]]), pf=float(r[H["Reported Power Factor"]]),
            thd=float(r[H["Reported Total Harmonic Distortion"]]), cri=float(r[H["Reported CRI (Ra)"]]),
            bug=(int(r[H["Reported Backlight (TM-15 BUG)"]]), int(r[H["Reported Uplight (TM-15 BUG)"]]),
                 int(r[H["Reported Glare (TM-15 BUG)"]])),
            vmin=int(r[H["Reported Minimum Input Voltage"]]), vmax=int(r[H["Reported Maximum Input Voltage"]]),
            date=str(r[H["Date Qualified"]]))
    return out


D = load_dlc(DLC_XLSX)
assert len(D) == 144, len(D)
for (w, v, c, t), d in D.items():
    assert w in WATTS and (d["vmin"], d["vmax"]) == ((100, 277) if v == "NVS" else (277, 480)), (w, v)
    assert d["bug"][1] == 0                                   # U0 everywhere
    assert d["date"] == "2026-08-28"
# BUG depends only on wattage and optic (not on CCT or voltage) - checked, so one table serves all.
BUG = {}
for (w, v, c, t), d in D.items():
    BUG.setdefault((w, t), set()).add(d["bug"])
assert all(len(s) == 1 for s in BUG.values()), BUG
BUG = {k: s.pop() for k, s in BUG.items()}

LM_MIN = min(d["lm"] for d in D.values())
LM_MAX = max(d["lm"] for d in D.values())
LPW_MIN = min(d["lpw"] for d in D.values())
LPW_MAX = max(d["lpw"] for d in D.values())
PF_MIN = min(d["pf"] for d in D.values())
PF_MAX = max(d["pf"] for d in D.values())
THD_MIN = min(d["thd"] for d in D.values())
THD_MAX = max(d["thd"] for d in D.values())
CRI_MIN = min(d["cri"] for d in D.values())
CRI_MAX = max(d["cri"] for d in D.values())
assert fl(LPW_MAX) == 170 and fl(LM_MIN) == 11814 and fl(LM_MAX) == 67113, (LPW_MAX, LM_MIN, LM_MAX)
assert PF_MIN >= 0.9 and THD_MAX <= 15 and CRI_MIN >= 80


def win(w, v):
    ws = [D[(w, v, c, t)]["w"] for c in CCTS for t, _, _ in TYS]
    lo, hi = min(ws), max(ws)
    return ("%.1f" % lo) if abs(hi - lo) < 0.05 else "%.1f-%.1f" % (lo, hi)


def pf_thd(w, v):
    ds = [D[(w, v, c, t)] for c in CCTS for t, _, _ in TYS]
    return min(d["pf"] for d in ds), max(d["thd"] for d in ds)


# ---------------------------------------------------------------- [CAT] / [OLD] physical data
DIM = {"S": (507, 327, 185), "L": (600, 410, 185)}             # [CAT] p7, mm
DIM_XL = {300: (650, 423, 380), 420: (650, 440, 390)}           # [CAT] p7, mm
KG_CAT = {75: 3.7, 115: 4.0, 145: 4.0, 180: 5.6, 200: 5.6, 230: 5.6, 300: 8.9, 420: 9.6}   # [CAT] p7
LB_OLD = {"S": 10.58, "L": 12.0, "XL": 23.15}                   # [OLD] p1
EPA_M2 = {"S": 0.02997, "L": 0.03342, "XL": 0.04686}            # [CAT] p7 SCx side view
EPA_OLD = {"S": 0.32, "L": 0.36, "XL": 0.50}                    # [OLD] p1, ft2
for s in SIZES:
    assert abs(float(_q(Decimal(str(EPA_M2[s])) * Decimal("10.7639104"), 2)) - EPA_OLD[s]) < 0.005, s


def weight_max(s):
    """Heavier of [OLD] and [CAT] for the size, in lb (conservative)."""
    cat_lb = max(KG_CAT[w] for w in WATTS if SIZE_OF[w] == s) / 0.45359237
    return max(LB_OLD[s], cat_lb)


BRK = [  # code, name, fit [OLD p6 / CAT p4], weight kg [CAT p8], drawing
    ("F", "Slip fitter", "2-3/8 in (60 mm) OD tenon. 40 mm and 76 mm sizes on request.", "1.1", "br_F.png"),
    ("R", "Adjustable arm", "Square pole, 4 in minimum.", "2.0", "br_R.png"),
    ("U", "Yoke", "Yoke mount, cold-rolled steel.", "0.9 / 1.0 / 1.5", "br_U.png"),
    ("S", "Straight arm", "3 to 4 in round pole, or square pole 3 in minimum.", "1.1", "br_S.png"),  # S = vendor D bracket (vendor 10/19), not E/F
    ("T", "Trunnion", "Mounting base 5.5 in minimum.", "1.4", "br_T.png"),
]


def kg_list_lb(txt):
    parts = []
    for tok in txt.split(" / "):
        num, *rest = tok.split(" ")
        parts.append("%s lb%s" % (_q(Decimal(num) / Decimal("0.45359237")), (" " + " ".join(rest)) if rest else ""))
    return " / ".join(parts) + ' <span class="mm">(%s kg)</span>' % " / ".join(t.split(" ")[0] for t in txt.split(" / "))


# ---------------------------------------------------------------- tables
def summary_rows():
    """4000K Type III per wattage, NV and HV."""
    out = []
    for w in WATTS:
        n, h = D[(w, "NVS", 4000, 3)], D[(w, "HVS", 4000, 3)]
        b = BUG[(w, 3)]
        out.append('<tr><td class="k">%dW</td><td class="c">%s</td>'
                   '<td class="c">%s W</td><td class="c b">%s lm</td><td class="c">%d</td>'
                   '<td class="c">%s W</td><td class="c b">%s lm</td><td class="c">%d</td>'
                   '<td class="c">B%d-U%d-G%d</td></tr>'
                   % (w, SIZE_OF[w], "%.1f" % n["w"], lm(n["lm"]), fl(n["lpw"]),
                      "%.1f" % h["w"], lm(h["lm"]), fl(h["lpw"]), b[0], b[1], b[2]))
    return "\n".join(out)


def perf_table(v):
    hdr1 = ('<tr><th rowspan="2" style="width:7%%">WATTS</th><th rowspan="2" class="c" style="width:6%%">SIZE</th>'
            '<th rowspan="2" class="c" style="width:10%%">INPUT W</th>'
            + "".join('<th colspan="3" class="c grpth">%s &middot; %s</th>' % (code, name) for _, code, name in TYS) + "</tr>")
    hdr2 = "<tr>" + "".join('<th class="c sub">%dK</th>' % c for _ in TYS for c in CCTS) + "</tr>"
    body = []
    for w in WATTS:
        cells = []
        for t, _, _ in TYS:
            for c in CCTS:
                d = D[(w, v, c, t)]
                cells.append('<td class="c pc">%s<i>%d lm/W</i></td>' % (lm(d["lm"]), fl(d["lpw"])))
        body.append('<tr><td class="k">%dW</td><td class="c">%s</td><td class="c">%s</td>%s</tr>'
                    % (w, SIZE_OF[w], win(w, v), "".join(cells)))
    return '<table class="perf">%s%s%s</table>' % (hdr1, hdr2, "\n".join(body))


def bug_rows():
    out = []
    for w in WATTS:
        out.append('<tr><td class="k">%dW</td>%s</tr>' % (w, "".join(
            '<td class="c">B%d-U%d-G%d</td>' % BUG[(w, t)] for t, _, _ in TYS)))
    return "\n".join(out)


def elec_rows():
    out = []
    for w in WATTS:
        cells = []
        for v, _, _ in VOLTS:
            pf, thd = pf_thd(w, v)
            cells.append('<td class="c">%s</td><td class="c">%.2f</td><td class="c">%.2f%%</td>'
                         % (win(w, v), math.floor(pf * 100) / 100.0, thd))
        out.append('<tr><td class="k">%dW</td>%s</tr>' % (w, "".join(cells)))
    return "\n".join(out)


def dim_rows():
    out = []
    for s in SIZES:
        ws = [w for w in WATTS if SIZE_OF[w] == s]
        if s in DIM:
            L, Wd, Ht = DIM[s]
            sz = ['<td class="c">%s</td><td class="c">%s</td><td class="c">%s</td>' % (mm_in(L), mm_in(Wd), mm_in(Ht))]
            lab = ['<td class="k">%s &middot; %s<br><span class="mm">%s</span></td>' % (s, SIZE_NAME[s], ", ".join("%d W" % w for w in ws))]
            rows = [(lab[0], sz[0])]
        else:
            rows = []
            for w in ws:
                L, Wd, Ht = DIM_XL[w]
                rows.append(('<td class="k">%s &middot; %d W</td>' % (s, w),
                             '<td class="c">%s</td><td class="c">%s</td><td class="c">%s</td>' % (mm_in(L), mm_in(Wd), mm_in(Ht))))
        lbs = weight_max(s)
        for i, (lab, sz) in enumerate(rows):
            tail = ('<td class="c" rowspan="%d">up to %s</td><td class="c" rowspan="%d">%s</td>'
                    % (len(rows), lb_kg(lbs), len(rows), m2_ft2(EPA_M2[s]))) if i == 0 else ""
            out.append("<tr>%s%s%s</tr>" % (lab, sz, tail))
    return "\n".join(out)


def brk_cards():
    out = []
    for code, name, fit, kg, img in BRK:
        out.append('<div class="bk"><div class="bimg"><img src="assets/%s" alt=""></div>'
                   '<div class="bt"><b><span class="o">%s</span> &middot; %s</b><span>%s</span>'
                   '<span class="wt">Bracket weight %s</span></div></div>'
                   % (img, code, name.upper(), fit, kg_list_lb(kg)))
    return "\n".join(out)


def dims_svg():
    """LC schematic (top view and side view), not the factory drawing; not to scale."""
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 190" width="100%">',
         '<defs><marker id="a" viewBox="0 0 6 6" refX="3" refY="3" markerWidth="5" markerHeight="5" '
         'orient="auto-start-reverse"><path d="M0,0 L6,3 L0,6 z" fill="#1A1A2E"/></marker></defs>']
    hs = 'fill="#3b3f52" stroke="#1A1A2E" stroke-width="0.9"'
    ln = 'fill="#eef0f4" stroke="#1A1A2E" stroke-width="0.7"'
    br = 'fill="#9aa0ae" stroke="#1A1A2E" stroke-width="0.8"'
    tx = 'font-family="Poppins" font-size="10" font-weight="700" fill="#f37021"'
    cap = 'font-family="Poppins" font-size="7.5" font-weight="600" fill="#7a7e8c" text-anchor="middle"'
    ar = 'stroke="#1A1A2E" stroke-width="0.7" marker-start="url(#a)" marker-end="url(#a)"'
    ext = 'stroke="#9aa0ae" stroke-width="0.5" stroke-dasharray="2 2"'
    # top view (looking up at the lens): housing 220 x 142, arm stub at left
    x0, y0, L, W = 40, 22, 220, 142
    o.append('<rect x="%g" y="%g" width="34" height="34" rx="3" %s/>' % (x0 - 30, y0 + W / 2 - 17, br))
    o.append('<rect x="%g" y="%g" width="%g" height="%g" rx="12" %s/>' % (x0, y0, L, W, hs))
    o.append('<rect x="%g" y="%g" width="%g" height="%g" rx="6" %s/>' % (x0 + 62, y0 + 14, L - 76, W - 28, ln))
    for i in range(7):
        for j in range(5):
            o.append('<circle cx="%g" cy="%g" r="3.2" fill="#c9ccd6"/>' % (x0 + 80 + i * 19.5, y0 + 30 + j * 20.5))
    o.append('<rect x="%g" y="%g" width="44" height="%g" rx="4" fill="#4a4f63" stroke="#1A1A2E" stroke-width="0.6"/>'
             % (x0 + 10, y0 + 22, W - 44))
    o.append('<line x1="%g" y1="%g" x2="%g" y2="%g" %s/>' % (x0 - 30, y0 + W + 14, x0 + L, y0 + W + 14, ar))
    o.append('<text x="%g" y="%g" %s text-anchor="middle">A</text>' % (x0 + L / 2 - 15, y0 + W + 11, tx))
    o.append('<line x1="%g" y1="%g" x2="%g" y2="%g" %s/>' % (x0 + L + 14, y0, x0 + L + 14, y0 + W, ar))
    o.append('<text x="%g" y="%g" %s>B</text>' % (x0 + L + 20, y0 + W / 2 + 4, tx))
    o.append('<text x="%g" y="12" %s>BOTTOM VIEW, LENS SIDE</text>' % (x0 + L / 2 - 15, cap))
    # side view: thin housing tapering to the free end, bracket at left
    sx, sy = 340, 92
    o.append('<path d="M%g,%g L%g,%g C%g,%g %g,%g %g,%g L%g,%g L%g,%g Z" %s/>'
             % (sx, sy - 10, sx + 120, sy - 10, sx + 190, sy - 9, sx + 220, sy - 4, sx + 236, sy + 2,
                sx + 236, sy + 7, sx, sy + 9, hs))
    o.append('<rect x="%g" y="%g" width="96" height="9" rx="2" fill="#4a4f63" stroke="#1A1A2E" stroke-width="0.6"/>' % (sx + 22, sy + 9))
    o.append('<path d="M%g,%g L%g,%g L%g,%g C%g,%g %g,%g %g,%g Z" %s/>'
             % (sx - 34, sy - 26, sx, sy - 26, sx, sy + 4, sx - 10, sy + 6, sx - 22, sy + 30, sx - 34, sy + 54, br))
    o.append('<line x1="%g" y1="%g" x2="%g" y2="%g" %s/>' % (sx - 34, sy - 40, sx + 236, sy - 40, ar))
    o.append('<text x="%g" y="%g" %s text-anchor="middle">A</text>' % (sx + 100, sy - 44, tx))
    o.append('<line x1="%g" y1="%g" x2="%g" y2="%g" %s/>' % (sx + 236, sy + 54, sx + 250, sy + 54, ext))
    o.append('<line x1="%g" y1="%g" x2="%g" y2="%g" %s/>' % (sx + 236, sy - 26, sx + 250, sy - 26, ext))
    o.append('<line x1="%g" y1="%g" x2="%g" y2="%g" %s/>' % (sx + 246, sy - 26, sx + 246, sy + 54, ar))
    o.append('<text x="%g" y="%g" %s>C</text>' % (sx + 251, sy + 18, tx))
    o.append('<text x="%g" y="166" %s>SIDE VIEW, WITH STRAIGHT ARM BRACKET</text>' % (sx + 100, cap))
    o.append("</svg>")
    return "\n".join(o)


# ---------------------------------------------------------------- shared values
V = dict(
    name=NAME, series=SERIES, foot=C.FOOT, custom=C.CUSTOM, proj=PROJ, hdr=C.hdr(TITLE, SERIES),
    example="-".join(EXAMPLE),
    lm_min=lm(LM_MIN), lm_max=lm(LM_MAX), lpw_min=fl(LPW_MIN), lpw_max=fl(LPW_MAX),
    pf_min="%.2f" % (math.floor(PF_MIN * 100) / 100.0), pf_max="%.2f" % (math.floor(PF_MAX * 100) / 100.0),
    thd_min="%.1f" % THD_MIN, thd_max="%d" % math.ceil(THD_MAX),
    cri_min="%.1f" % CRI_MIN, cri_max="%.1f" % CRI_MAX,
    amb="%s to %s" % (f_c(-40), f_c(50)),
    mh="%s to %s <span class=\"mm\">(4 to 12 m)</span>" % (m_ft(4), m_ft(12)),
    cable='%s in <span class="mm">(70 cm)</span>' % _q(Decimal(700) / Decimal("25.4")),
    epa_s=m2_ft2(EPA_M2["S"]), epa_l=m2_ft2(EPA_M2["L"]), epa_xl=m2_ft2(EPA_M2["XL"]),
    dlc_date="2026-08-28",
)

# ---------------------------------------------------------------- page 1  cover
P1 = """
<section class="page">
  <div class="side"><div class="vt">LED CONNECTION &nbsp;&middot;&nbsp; ULTRA AREA LUMINAIRE &nbsp;&middot;&nbsp; 75 W TO 420 W</div><img src="assets/logo_side_w.png" alt=""></div>
  <div class="proj">%(proj)s</div>
  <img src="assets/slot_hero.png" alt="LC OPTIMUS SERIES area luminaire on a square pole" style="position:absolute;left:1.45in;top:.55in;height:4.55in;width:auto">
  <img src="assets/slot_head.png" alt="LC OPTIMUS SERIES lens and housing" style="position:absolute;left:3.95in;top:2.2in;width:3.05in;height:auto">
  <div style="position:absolute;left:1.25in;right:1.3in;top:5.12in;text-align:center;font-size:6.8pt;color:#7a7e8c">Shown on a square pole with the straight arm bracket (S). Right: housing and lens detail.</div>
  <div class="badges" style="top:.95in">
    <div class="tbadge">DLC<br>STANDARD<i>LISTING IN PROGRESS</i></div>
    <div class="tbadge">IP66<i>SEALED HOUSING</i></div>
    <div class="tbadge">IK10<i>IMPACT RATED</i></div>
    <div class="tbadge">3G<i>VIBRATION</i></div>
    <div class="tbadge">100-277 OR<br>277-480 VAC<i>NV / HV</i></div>
    <div class="tbadge">CRI 80<i>3000K 4000K 5000K</i></div>
  </div>
  <div class="cv">
    <div class="kick">ULTRA AREA LUMINAIRE &middot; LC-SLOT</div>
    <div class="big sm">%(name)s</div>
    <div class="rule"></div>
    <div class="lpw">75 W TO 420 W &middot; UP TO %(lpw_max)d LM/W</div>
    <div class="tag">TYPE III, IV AND V OPTICS &middot; 100-277 OR 277-480 VAC &middot; 1-10V DIMMING &middot; DIE-CAST ALUMINUM &middot; FIVE BRACKETS</div>
    <div class="strip">
      <div><small>WATTAGE</small><span>75 W to<br>420 W</span></div>
      <div><small>LUMENS</small><span>%(lm_min)s<br>to %(lm_max)s</span></div>
      <div><small>EFFICACY</small><span>up to<br>%(lpw_max)d lm/W</span></div>
      <div><small>CCT</small><span>3000K<br>4000K<br>5000K</span></div>
      <div><small>CRI</small><span>80<br><em class="sm">minimum</em></span></div>
      <div><small>OPTICS</small><span>Type III<br>IV, V</span></div>
    </div>
    <div class="pn">ORDERING EXAMPLE &nbsp;<b>%(example)s</b></div>
    <div class="callout">
      <h4>ONE HOUSING FAMILY, EIGHT WATTAGES</h4>
      <p>A slim die-cast aluminum area light for parking lots, streets and loading areas. Three housing sizes cover
         75 W to 420 W, the lens rotates in the field to set Type III, IV or V, and five brackets fit tenons, arms,
         poles and flat surfaces. Lumen and efficacy values are DLC-reported (Standard, CRI 80).</p>
    </div>
  </div>
  %(custom)s
  %(foot)s
</section>
"""

# ---------------------------------------------------------------- page 2  product
P2 = """
<section class="page">
  %(hdr)s
  <div class="body">
    <img class="hero2" src="assets/slot_head.png" alt="" style="width:2.55in;height:auto;top:.28in;right:0">
    <div class="wrapn">
      <div class="h1">ULTRA AREA LUMINAIRE &middot; 75 W TO 420 W</div>
      <div class="big" style="font-size:26pt">%(name)s</div>
      <div class="code">LC-SLOT-S<small>Small housing &middot; 75 W, 115 W, 145 W</small></div>
      <div class="code" style="margin-top:.05in">LC-SLOT-L<small>Large housing &middot; 180 W, 200 W, 230 W</small></div>
      <div class="code" style="margin-top:.05in">LC-SLOT-XL<small>X-Large housing &middot; 300 W, 420 W</small></div>
      <div class="icons">
        <div class="dim0"><span>POWER</span><span>75-420</span><span>W</span></div>
        <div class="dim0"><span>RATING</span><span>IP66</span></div>
        <div class="dim0"><span>IMPACT</span><span>IK10</span></div>
        <div class="dim0"><span>CRI</span><span>80</span></div>
        <div class="dim0"><span>UPLIGHT</span><span>U0</span></div>
      </div>
    </div>
    <div class="hl"><h4>SET THE PATTERN WITHOUT RE-AIMING</h4>
      <p>The lens rotates in the field, so the light direction changes without moving the luminaire. Brackets are
         built for single-person installation, and the driver sits behind a tool-free access panel.</p></div>

    <div class="sec"><h3>PRODUCT DESCRIPTION</h3></div>
    <p class="txt">The LC OPTIMUS SERIES ultra area luminaire is an efficient, cost-effective light for exterior area
      projects. A rugged die-cast aluminum housing carries high-efficacy 5050 LEDs behind a polycarbonate lens, with a
      weather-tight driver compartment that opens without tools for easy maintenance. Three housing sizes cover 75 W to
      420 W, Type III, IV and V distributions come from a field-rotatable lens, and five brackets fit tenons, arms,
      poles and flat surfaces. The 1-10V dimmable driver is available for 100-277 VAC or 277-480 VAC.</p>

    <div class="sec"><h3>OVERVIEW</h3></div>
    <ul class="ov two">
      <li>75 W to 420 W in three housing sizes</li>
      <li>%(lm_min)s to %(lm_max)s lm, DLC-reported</li>
      <li>Up to %(lpw_max)d lm/W, DLC-reported</li>
      <li>High-efficacy 5050 LEDs; CRI 80</li>
      <li>3000K, 4000K or 5000K</li>
      <li>Type III, IV and V; field-rotatable lens</li>
      <li>Zero uplight (U0); cut-off</li>
      <li>NV 100-277 VAC or HV 277-480 VAC</li>
      <li>1-10V dimming, continuous to 10%% or below</li>
      <li>IP66, IK10, 3G vibration rating</li>
      <li>Die-cast aluminum, tool-free driver access</li>
      <li>Limited 5-year warranty; 10-year available</li>
    </ul>

    <div class="sec"><h3>APPLICATIONS</h3></div>
    <ul class="ov two">
      <li>Parking lots</li>
      <li>Streets and site roadways</li>
      <li>Loading bays</li>
      <li>Tennis courts and training fields</li>
      <li>Residential and commercial areas</li>
      <li>Paths and jogging tracks</li>
    </ul>

    <div class="sec"><h3>CONSTRUCTION</h3></div>
    <ul class="ov two">
      <li>Die-cast aluminum unibody housing, sealed to IP66</li>
      <li>Efficient heat-dissipation layer</li>
      <li>LED board behind an optical-grade polycarbonate lens</li>
      <li>Lens rotates in the field for Type III, IV or V</li>
      <li>Driver behind a tool-free buckled access panel</li>
      <li>1-10V dimmable driver, NV or HV</li>
      <li>Surge protection device</li>
      <li>Bracket access panel for wiring; exchangeable bracket</li>
    </ul>
  </div>
  %(foot)s
</section>
"""

# ---------------------------------------------------------------- page 3  order logic + wattage table
P3 = """
<section class="page">
  %(hdr)s
  <div class="body" style="top:.85in">
    <div class="sec" style="margin-top:.1in"><h3>ORDER LOGIC</h3></div>
    <div class="olx">Build the LED Connection ordering code from left to right, one choice per segment.</div>
    <div class="sample"><small>EXAMPLE</small>
      <div class="segs">%(segs)s</div>
    </div>
    <div class="cards" style="grid-template-columns:repeat(5,1fr)">
      <div class="card"><h5>01 FAMILY</h5><div><b>LC-SLOT</b>LC OPTIMUS SERIES ultra area luminaire</div></div>
      <div class="card"><h5>02 SIZE</h5><div><b>S</b>Small, 75 to 145 W<div class="op"><b>L</b>Large, 180 to 230 W</div><div class="op"><b>XL</b>X-Large, 300 and 420 W</div></div></div>
      <div class="card"><h5>03 WATTAGE</h5><div><b>S: 75W 115W 145W</b><div class="op"><b>L: 180W 200W 230W</b></div><div class="op"><b>XL: 300W 420W</b></div><div class="op">Nominal; input watts on page 5</div></div></div>
      <div class="card"><h5>04 VOLTAGE</h5><div><b>NV</b>100-277 VAC<div class="op"><b>HV</b>277-480 VAC</div></div></div>
      <div class="card"><h5>05 SENSOR</h5><div><b>XX</b>No sensor (Standard)<div class="op">Sensor and photocell versions: contact LED Connection</div></div></div>
      <div class="card"><h5>06 CCT</h5><div><b>30</b>3000K<div class="op"><b>40</b>4000K</div><div class="op"><b>50</b>5000K</div></div></div>
      <div class="card"><h5>07 CRI</h5><div><b>80</b>CRI 80 minimum</div></div>
      <div class="card"><h5>08 DISTRIBUTION</h5><div><b>TY03</b>Type III<div class="op"><b>TY04</b>Type IV</div><div class="op"><b>TY05</b>Type V</div></div></div>
      <div class="card"><h5>09 BRACKET</h5><div><b>F</b>Slip fitter<div class="op"><b>R</b>Adjustable arm</div><div class="op"><b>U</b>Yoke</div><div class="op"><b>S</b>Straight arm, square or round pole</div><div class="op"><b>T</b>Trunnion</div></div></div>
      <div class="card"><h5>10 COLOR</h5><div><b>BK</b>Black<div class="op"><b>BR</b>Bronze</div><div class="op"><b>WH</b>White</div></div></div>
    </div>
    <div class="note"><b>Notes:</b> Sensor and photocell versions: contact LED Connection. Additional lens options will carry
      their own distribution code. Where the supply voltage can fluctuate to 240 V or more, HV (277-480 VAC) is recommended.
      Bracket fit and weights are on page 6.</div>

    <div class="sec"><h3>WATTAGE SELECTION &middot; 4000K, TYPE III</h3></div>
    <table class="sum">
      <tr><th rowspan="2" style="width:9%%">WATTAGE</th><th rowspan="2" class="c" style="width:7%%">SIZE</th>
          <th colspan="3" class="c grpth">NV &middot; 100-277 VAC</th><th colspan="3" class="c grpth">HV &middot; 277-480 VAC</th>
          <th rowspan="2" class="c">BUG RATING</th></tr>
      <tr><th class="c sub">INPUT</th><th class="c sub">LUMENS</th><th class="c sub">LM/W</th>
          <th class="c sub">INPUT</th><th class="c sub">LUMENS</th><th class="c sub">LM/W</th></tr>
      %(summary)s
    </table>
    <div class="note">Delivered lumens, efficacy, input watts and BUG ratings are <b>DLC-reported</b> values for the CRI 80
      Standard models (DLC qualified product data, %(dlc_date)s), shown whole, never rounded up. They replace the CRI 70
      figures on the 2023 LED Connection sheet. All CCTs and distributions are on page 5. Actual performance may vary by up
      to 10 percent; site conditions and options affect performance.</div>
  </div>
  %(foot)s
</section>
"""

# ---------------------------------------------------------------- page 4  specifications
P4 = """
<section class="page">
  %(hdr)s
  <div class="body" style="top:.85in">
    <div class="sec" style="margin-top:.1in"><h3>SPECIFICATIONS</h3></div>
    <table class="spec">
      <tr><th style="width:26%%">ITEM</th><th>LC OPTIMUS SERIES &middot; LC-SLOT</th></tr>
      <tr class="grp"><td colspan="2">PERFORMANCE</td></tr>
      <tr><td class="k">Nominal wattage</td><td>S: 75, 115, 145 W &middot; L: 180, 200, 230 W &middot; XL: 300, 420 W</td></tr>
      <tr><td class="k">Delivered lumens</td><td>%(lm_min)s to %(lm_max)s lm, DLC-reported (page 5)</td></tr>
      <tr><td class="k">Efficacy</td><td>%(lpw_min)d to %(lpw_max)d lm/W, DLC-reported</td></tr>
      <tr><td class="k">Colour temperature</td><td>3000K, 4000K or 5000K (segment 06)</td></tr>
      <tr><td class="k">Colour rendering</td><td>CRI 80 minimum; DLC-reported Ra %(cri_min)s to %(cri_max)s</td></tr>
      <tr><td class="k">Distribution</td><td>Type III (80 x 155&deg;), Type IV (90 x 150&deg;), Type V (160&deg;); field-rotatable lens</td></tr>
      <tr><td class="k">Uplight</td><td>U0 on every model (DLC-reported); 0 percent uplight at 0&deg; tilt</td></tr>
      <tr><td class="k">Rated life</td><td>L70 greater than 100,000 h at 25 C ambient</td></tr>
      <tr class="grp"><td colspan="2">ELECTRICAL</td></tr>
      <tr><td class="k">Input voltage</td><td>NV: 100-277 VAC &middot; HV: 277-480 VAC. HV is recommended where the supply can fluctuate to 240 V or more.</td></tr>
      <tr><td class="k">Power factor</td><td>0.90 or higher (DLC-reported %(pf_min)s to %(pf_max)s)</td></tr>
      <tr><td class="k">THD</td><td>15 percent or lower (DLC-reported %(thd_min)s to %(thd_max)s percent)</td></tr>
      <tr><td class="k">Dimming</td><td>1-10V, continuous dimming to 10 percent or below</td></tr>
      <tr><td class="k">Surge protection</td><td>Surge protection device; 10 kV or 20 kV versions available, contact LED Connection</td></tr>
      <tr><td class="k">Wiring</td><td>Pre-wired with a %(cable)s cable; other lengths on request</td></tr>
      <tr><td class="k">Sensor</td><td>None (XX). Sensor and photocell versions: contact LED Connection.</td></tr>
      <tr class="grp"><td colspan="2">MECHANICAL</td></tr>
      <tr><td class="k">Housing</td><td>Heavy-duty die-cast aluminum unibody; tool-free buckled driver access panel</td></tr>
      <tr><td class="k">Lens</td><td>Optical-grade polycarbonate, field-rotatable</td></tr>
      <tr><td class="k">LEDs</td><td>High-efficacy 5050 LEDs</td></tr>
      <tr><td class="k">Finish</td><td>Anti-UV thermosetting polyester; epoxy primer plus polyester for very corrosive sites</td></tr>
      <tr><td class="k">Colour</td><td>Black (BK), bronze (BR), white (WH)</td></tr>
      <tr><td class="k">Mounting</td><td>Slip fitter (F), adjustable arm (R), yoke (U), straight arm (S), trunnion (T); page 6</td></tr>
      <tr><td class="k">EPA, side</td><td>S %(epa_s)s &middot; L %(epa_l)s &middot; XL %(epa_xl)s</td></tr>
      <tr><td class="k">Mounting height</td><td>Generally %(mh)s, to suit the project</td></tr>
      <tr class="grp"><td colspan="2">ENVIRONMENT AND COMPLIANCE</td></tr>
      <tr><td class="k">Ingress / impact</td><td>IP66 (EN 60529) / IK10 (EN 62262)</td></tr>
      <tr><td class="k">Vibration</td><td>3G (IEC 60068-2-6)</td></tr>
      <tr><td class="k">Operating ambient</td><td>%(amb)s</td></tr>
      <tr><td class="k">Safety and EMC</td><td>cULus Listed; FCC; RoHS</td></tr>
      <tr><td class="k">DLC</td><td>DLC listing for LED Connection in progress (Standard)</td></tr>
      <tr><td class="k">Warranty</td><td>Limited 5-year warranty; 10-year warranty available. Terms: www.ledconnection.com/warranty</td></tr>
    </table>
  </div>
  %(custom)s
  %(foot)s
</section>
"""

# ---------------------------------------------------------------- page 5  performance
P5 = """
<section class="page">
  %(hdr)s
  <div class="body" style="top:.85in">
    <div class="sec" style="margin-top:.1in"><h3>PERFORMANCE &middot; NV, 100-277 VAC</h3></div>
    %(perf_nv)s
    <div class="sec"><h3>PERFORMANCE &middot; HV, 277-480 VAC</h3></div>
    %(perf_hv)s
    <div class="note">Each cell: delivered lumens, then efficacy. <b>DLC-reported</b> values for the CRI 80 Standard models
      (DLC qualified product data, %(dlc_date)s), shown whole, never rounded up. INPUT W is the DLC-reported input power
      across the nine CCT and distribution options of that wattage.</div>
    <div class="twocol" style="grid-template-columns:.8fr 1.2fr">
      <div>
        <div class="sec"><h3 style="min-width:0;width:100%%">BUG RATING (TM-15)</h3></div>
        <table>
          <tr><th style="width:22%%">WATTS</th><th class="c">TY03</th><th class="c">TY04</th><th class="c">TY05</th></tr>
          %(bug)s
        </table>
        <div class="note">DLC-reported; the same for every CCT and for NV and HV.</div>
      </div>
      <div>
        <div class="sec"><h3 style="min-width:0;width:100%%">ELECTRICAL BY WATTAGE</h3></div>
        <table class="el">
          <tr><th rowspan="2" style="width:13%%">WATTS</th><th colspan="3" class="c grpth">NV &middot; 100-277 VAC</th><th colspan="3" class="c grpth">HV &middot; 277-480 VAC</th></tr>
          <tr><th class="c sub">INPUT W</th><th class="c sub">PF MIN</th><th class="c sub">THD MAX</th><th class="c sub">INPUT W</th><th class="c sub">PF MIN</th><th class="c sub">THD MAX</th></tr>
          %(elec)s
        </table>
        <div class="note">DLC-reported, lowest power factor and highest THD of the nine options.</div>
      </div>
    </div>
  </div>
  %(foot)s
</section>
"""

# ---------------------------------------------------------------- page 6  dimensions, brackets, notes
P6 = """
<section class="page">
  %(hdr)s
  <div class="body" style="top:.85in">
    <div class="sec" style="margin-top:.1in"><h3>DIMENSIONS</h3></div>
    <div style="width:6.4in;margin:0 auto">%(dims)s</div>
    <div class="note" style="text-align:right;margin-top:-.04in">Schematic, not to scale; dimensions govern.</div>
    <table class="dim" style="margin-top:.04in">
      <tr><th style="width:17%%">SIZE</th><th class="c">A &middot; LENGTH</th><th class="c">B &middot; WIDTH</th><th class="c">C &middot; HEIGHT</th><th class="c">WEIGHT</th><th class="c">EPA, SIDE</th></tr>
      %(dimrows)s
    </table>
    <div class="note">Overall sizes. Weight is the heaviest of the size range. A safety rope is supplied with 300 W and 420 W;
      order it separately for lower wattages.</div>

    <div class="sec"><h3>BRACKETS &middot; SEGMENT 09</h3></div>
    <div class="bgrid">
      %(brk)s
    </div>
    <div class="note">Yoke weight by size: S / L / XL. Brackets are drawn with the luminaire; contact LED Connection for
      pole drilling templates and other pole adapters.</div>

    <div class="twocol" style="margin-top:.02in">
      <div>
        <div class="sec"><h3 style="min-width:0;width:100%%">INSTALLATION</h3></div>
        <ul class="ov">
          <li>Installation and service by a qualified electrician, to local code.</li>
          <li>Power off before installing, servicing or opening the driver panel.</li>
          <li>Ground the luminaire. Choose NV or HV to suit the supply.</li>
        </ul>
      </div>
      <div>
        <div class="sec"><h3 style="min-width:0;width:100%%">NOTES</h3></div>
        <ul class="ov">
          <li>All dimensions and specifications are subject to change without notice.</li>
          <li>LED Connection, LLC is not responsible for claims from improper loading, use, foundation design or installation.</li>
        </ul>
      </div>
    </div>
  </div>
  %(custom)s
  %(foot)s
</section>
"""

EXTRA_CSS = """
.strip span { line-height:1.18; display:block; }
.mm { font-size:.86em; color:#7a7e8c; font-weight:400; }
em.sm { font-style:normal; font-weight:500; font-size:6.8pt; color:#5d6170; }
.segs { font-size:13.5pt; gap:.04in; }
.segs .dash { padding-bottom:.135in; }
.card div.op { padding:0; margin-top:.045in; }
table.spec td { padding:.03in .08in; line-height:1.3; }
table.spec tr.grp td { background:#fdeee5; color:var(--ink); font-weight:800; font-size:6.6pt; letter-spacing:.06em; padding:.03in .08in; }
th.grpth { border-left:1px solid #3a3d55; background:#24243c; }
th.sub { font-size:6pt; padding:.03in .04in; background:#2c2c48; border-left:1px solid #3a3d55; }
table.sum td { padding:.035in .06in; }
table.sum td.b { font-weight:700; }
table.perf { font-size:7pt; }
table.perf td { padding:.025in .03in; }
table.perf td.pc { line-height:1.15; border-left:1px solid #eceef2; }
table.perf td.pc i { display:block; font-style:normal; font-size:5.8pt; color:#7a7e8c; }
table.perf th { padding:.04in .04in; }
table.el td, table.dim td { padding:.03in .05in; }
table.dim td { line-height:1.25; }
.bgrid { display:grid; grid-template-columns:1fr 1fr; gap:.07in .14in; }
.bk { display:flex; align-items:center; gap:.1in; border:1px solid var(--line); padding:.05in .08in; }
.bk .bimg { width:1.75in; height:.62in; display:flex; align-items:center; justify-content:center; flex:none; }
.bk .bimg img { max-width:100%; max-height:100%; }
.bk .bt { font-size:6.8pt; line-height:1.35; color:#454857; }
.bk .bt b { display:block; color:var(--navy); font-size:7.4pt; font-weight:800; letter-spacing:.03em; margin-bottom:.01in; }
.bk .bt b .o { color:var(--orange); }
.bk .bt span { display:block; }
.bk .bt b span.o { display:inline; }
.bk .bt .wt { color:#7a7e8c; margin-top:.02in; }
"""


def segs_html():
    out = []
    for i, s in enumerate(EXAMPLE):
        cls = ' class="o"' if i == 0 else ""
        out.append('<div class="sg"><span%s>%s</span><i>[%02d]</i></div>' % (cls, s, i + 1))
    return '<span class="dash">-</span>'.join(out)


def build():
    v = dict(V)
    v.update(segs=segs_html(), summary=summary_rows(), perf_nv=perf_table("NVS"), perf_hv=perf_table("HVS"),
             bug=bug_rows(), elec=elec_rows(), dims=dims_svg(), dimrows=dim_rows(), brk=brk_cards())
    pages = [P1 % v, P2 % v, P3 % v, P4 % v, P5 % v, P6 % v]
    C.CSS = C.CSS + EXTRA_CSS
    html = C.doc(PDF_TITLE, pages)
    path = os.path.join(HERE, "optimus.html")
    open(path, "w", encoding="utf-8").write(html)
    hits = C.leak_check("LC-SLOT", html)
    pdf = C.to_pdf(path, PDF_NAME)
    C.strip_metadata(pdf, PDF_TITLE, "LED Connection LC OPTIMUS SERIES ultra area luminaire specification")
    return pdf, hits


if __name__ == "__main__":
    print("DLC rows %d; lumens %s-%s; lm/W %d-%d; PF %.4f-%.4f; THD %.2f-%.2f; CRI %.1f-%.1f"
          % (len(D), lm(LM_MIN), lm(LM_MAX), fl(LPW_MIN), fl(LPW_MAX), PF_MIN, PF_MAX, THD_MIN, THD_MAX, CRI_MIN, CRI_MAX))
    for w in WATTS:
        n, h = D[(w, "NVS", 4000, 3)], D[(w, "HVS", 4000, 3)]
        print("  %3d W %-2s  NV %6.2f W %9s lm %3d lm/W | HV %6.2f W %9s lm %3d lm/W | BUG T3 %s"
              % (w, SIZE_OF[w], n["w"], lm(n["lm"]), fl(n["lpw"]), h["w"], lm(h["lm"]), fl(h["lpw"]), BUG[(w, 3)]))
    pdf, hits = build()
    print(pdf, hits)
    print("pdf_text_check:", C.pdf_text_check(pdf))
    for f in C.preview(pdf):
        print(f)
