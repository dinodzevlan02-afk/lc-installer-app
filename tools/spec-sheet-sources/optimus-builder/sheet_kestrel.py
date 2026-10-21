# SHEET 1 - LC KESTREL 3, 3 in LED track head, LC-KST3-20W-T-BA-H-95-30-15.
# Kroger interior comparison package, 2026-10-12. LC-XCPA layout, 4 pages.
# Part number pattern from the 2025 LC cross (LC-SSTL3-20W-T-BA-H-95-30-15-X):
# 20W, T = track, BA = finish code, H = H-type adapter, 95 CRI, 3000K, 15 deg.
#
# PROVENANCE (every number on this sheet). Source folder log/kroger-t8-20261006.
#  [QT]   Factory quotation dated 2026-10-10, CRI 95 build (replies-1012): 3 in
#         (80 mm) head, H x 156 mm; H-type adaptor compatible with Halo track; 25-20-15 W
#         switchable = 2450-2000-1500 lm switchable; 3000K; AC120V, triac dimming;
#         power factor 0.9; LED Luminus CXM-11-30-95 (CRI >= 95); beam 15 deg;
#         honeycomb and snoot offered as separate items. Prices/MOQ/terms not used.
#  [SPEC] Factory series specification, 4 pages (replies-1012), column for the
#         80 mm head, H-track model:
#         p1  Class I; 3-wire 1-circuit track (H); 80 x 156 mm; 360 deg horizontal
#             rotation, 90 deg vertical tilt; 120 VAC, 60 Hz; 250 mA max.
#         p2  input 15-20-25 W; PF > 0.92; THD < 12%; TRIAC or ELV; CCR; 1-100%;
#             inrush 5 A / 135 us; start < 500 ms; off < 1 s; OTP, OVP; > 100,000
#             switching cycles; noise <= 23 dB; COB; 15/24/36/60 deg optics;
#             shield angle 8 deg; SDCM < 3; RG1; flicker < 25%; Pst LM < 0.8;
#             SVM < 0.3. (Footnote 2: electrical values at 120 VAC, max power.)
#         p3  L70 B50 102,000 h; L80 B10 76,000 h; L90 B10 35,000 h at Ta 25 C;
#             ambient -10 to +35 C, not for totally enclosed spaces; RH 20-80%;
#             storage -20 to +75 C; IP20; IK08; glow wire 650 C 30 s; finish white
#             RAL 9016 or black RAL 7021; warranty 5 years; accessories snoot and
#             honeycomb.
#         p4  mechanical table (H): D 80, L1 155, L3 37, H1 20, H3 156 mm; power DIP
#             switch on this size; honeycomb D1 72 / H1 5 / T1 3 mm; 30 deg shielding
#             snoot D1 80 / L1 50 / L2 56 mm.
#  [LED]  Luminus CXM-11 Gen 6 datasheet PDS-003320 rev 05, p5: CRI 95 bin, 2700K and
#         3000K: R9 > 80 (R9 tolerance +/-5); p2: suffix -3 = 3-step MacAdam ellipse.
#  [ATM]  ETL Authorization to Mark, report 240400446SHA-001, issued 30-Jun-2025:
#         standards UL 1574 (track lighting systems) and CSA C22.2 No. 250.570; the
#         model pattern for the series covers the 80 mm H-track model number.
#  [IES]  replies-1009 photometric file for the CRI 90 build, 15 deg optic, 20.62 W
#         (LumELE line records the test at 231 V). Used ONLY for the relative
#         distribution and the beam/field angles, computed below in code.
#
# CONFLICTS RESOLVED
#  - Power factor: [SPEC] > 0.92 at max power vs [QT] 0.9 for the CRI 95 build:
#    printed 0.9 (the quote for the build being sold).
#  - Dimming: [QT] says triac; [SPEC] (the series driver) says TRIAC or ELV: printed
#    TRIAC or ELV from the specification of the series.
#  - Lumens: [SPEC] 2650 lm is the CRI 90 build at 25 W; printed the [QT] CRI 95
#    values only.
#
# DROPPED (not confirmed for this build, or not ours to print)
#  - Absolute photometry: CBCP, total lumens, candela tables, illuminance. The only
#    files are the CRI 90 build; the CRI 95 build is untested.
#  - Spec-sheet CBCP 9,500 cd, 106 lm/W, 2,650 lm, UGR grade, R9 50: CRI 90 build.
#  - ETL control number: read off the certificate, but the certificate is in the
#    factory's name and brand, the quoted CRI 95 build carries a different item
#    code from the listed model number, and the number looks the factory up.
#  - FCC: stated in the specification, no certificate or test report held.
#  - Weight, carton data, EPA: carton data only (per carton), not per head.
#  - Other CCTs and optics in CRI 95: not confirmed by the factory.
#  - "Halo" (third-party track brand in the quote): not printed; H-type is the
#    generic adapter name and the H segment of the part number.
#  - ETL listing printed WITHOUT a number: the certificate is the factory's; an LC
#    multiple listing is needed before the mark carries LED Connection's name.
#  - Brushed aluminium: OFFERED per factory email 2026-10-13 (body brushed aluminium,
#    adapter silver; MOQ/surcharge not printed). BA in the part number = brushed aluminium.
#  - Flicker: factory LFASuite reports 2024-04-09, 25 W setting, 120 V 60 Hz:
#    100%% 7.999%% / 80%% 6.667%% / 50%% 0.774%% / 20%% 0.000%%; IEEE 1789 low risk / no effect.
import math, os, sys
from decimal import Decimal, ROUND_HALF_UP
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common as C
import ies

SKU = "LC-KST3-20W-T-BA-H-95-30-15"
NAME = "LC KESTREL 3"
TITLE = "3 IN LED TRACK HEAD &middot; " + NAME
PDF_NAME = "LC SPEC SHEET_3 in LED Track Head LC Kestrel 3 %s.pdf" % SKU
PROJ = ("PROJECT: KROGER INTERIOR &nbsp;&middot;&nbsp; 3 IN TRACK HEAD &nbsp;&middot;&nbsp; ISSUED 2026-10-13")
CODE_OK = ("kst3",)
IES20 = os.path.join(HERE, "..", "replies-1009", "20W- Matter-3000K-RA90-D15.ies")


def _r(v, f, nd):
    q = Decimal(1).scaleb(-nd)
    return str((Decimal(str(v)) * Decimal(f)).quantize(q, rounding=ROUND_HALF_UP))


def in_mm(mm, nd=2):
    """Imperial first, from the metric source: '3.15 in (80 mm)'."""
    return "%s in (%g mm)" % (_r(mm, Decimal(1) / Decimal("25.4"), nd), mm)


def f_c(c):
    return "{:,.0f} F ({:g} C)".format(round(c * 9 / 5.0 + 32), c)


def ft_in(inches):
    ft, i = divmod(int(round(inches)), 12)
    return "%d ft %d in" % (ft, i) if ft else "%d in" % i


# ---------------------------------------------------------------- data
SETTINGS = [(15, 1500), (20, 2000), (25, 2450)]                 # [QT]
PN_W, PN_LM = 20, 2000                                          # part number = 20 W setting
for w, lm in SETTINGS:
    assert lm % 1 == 0
LPW = {w: int(round(lm / float(w))) for w, lm in SETTINGS}       # derived, nominal
D_MM, L1_MM, L3_MM, H1_MM, H3_MM = 80, 155, 37, 20, 156         # [SPEC p4]
HC = (72, 5, 3)                                                 # honeycomb D1, H1, T1 [SPEC p4]
SN = (80, 50, 56)                                               # snoot D1, L1, L2 [SPEC p4]

# [IES] relative distribution, CRI 90 build. Beam (50 percent) and field (10 percent)
# angles averaged over the 12 measured planes.
D = ies.read(IES20)
assert abs(D["watts"] - 20.62) < 0.01


def _angles(d):
    out = []
    for ih in range(d["nh"] - 1):
        c = d["cd"][ih]; va = d["vang"]; pk = c[0]; row = []
        for frac in (0.5, 0.1):
            t = pk * frac
            for i in range(1, len(c)):
                if c[i] < t <= c[i - 1]:
                    row.append(2 * (va[i - 1] + (c[i - 1] - t) / (c[i - 1] - c[i]) * (va[i] - va[i - 1])))
                    break
        out.append(row)
    return (sum(r[0] for r in out) / len(out), sum(r[1] for r in out) / len(out))


BEAM, FIELD = _angles(D)
PEAK = ies.max_cd(D)[0]
REL = dict(D)
REL["cd"] = [[v / PEAK * 100.0 for v in row] for row in D["cd"]]


def polar():
    return ies.polar_svg(REL, [(0, "#f37021", "0-180 deg plane"), (90, "#1A1A2E", "90-270 deg plane")],
                         "RELATIVE INTENSITY, PERCENT OF PEAK", size=330, rel=True)


def linear_svg():
    """Relative intensity against angle from nadir, 0-40 deg, mean of the 12 planes."""
    W_, H_ = 330, 300
    x0, y0, x1, y1 = 38, 24, W_ - 12, H_ - 40
    va = D["vang"]
    n = D["nh"] - 1
    mean = [sum(REL["cd"][ih][iv] for ih in range(n)) / n for iv in range(D["nv"])]
    sx = lambda a: x0 + (x1 - x0) * a / 40.0
    sy = lambda p: y1 - (y1 - y0) * p / 100.0
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="100%%">' % (W_, H_),
         '<rect width="100%" height="100%" fill="#ffffff"/>',
         '<text x="%g" y="12" font-family="Poppins" font-size="7.5" font-weight="700" fill="#1b1d2b" '
         'text-anchor="middle">RELATIVE INTENSITY AGAINST ANGLE</text>' % (W_ / 2.0)]
    for p in range(0, 101, 25):
        o.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#d9dbe1" stroke-width="0.6"/>' % (x0, sy(p), x1, sy(p)))
        o.append('<text x="%g" y="%g" font-family="Poppins" font-size="6.5" fill="#8a8d99" text-anchor="end">%d%%</text>'
                 % (x0 - 4, sy(p) + 2, p))
    for a in range(0, 41, 5):
        o.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#d9dbe1" stroke-width="0.4"/>' % (sx(a), y0, sx(a), y1))
        o.append('<text x="%g" y="%g" font-family="Poppins" font-size="6.5" fill="#8a8d99" text-anchor="middle">%d</text>'
                 % (sx(a), y1 + 11, a))
    o.append('<text x="%g" y="%g" font-family="Poppins" font-size="6.8" fill="#1b1d2b" text-anchor="middle">'
             'Angle from beam centre, degrees</text>' % ((x0 + x1) / 2.0, y1 + 24))
    for p, lab in ((50, "beam edge, 50%%"), (10, "field edge, 10%%")):
        o.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#f37021" stroke-width="0.7" stroke-dasharray="3 2"/>'
                 % (x0, sy(p), x1, sy(p)))
        o.append('<text x="%g" y="%g" font-family="Poppins" font-size="6.3" fill="#f37021" text-anchor="end">%s</text>'
                 % (x1 - 2, sy(p) - 3, lab.replace("%%", "%")))
    pts = " ".join("%g,%g" % (sx(a), sy(m)) for a, m in zip(va, mean) if a <= 40)
    o.append('<polyline points="%s" fill="none" stroke="#1A1A2E" stroke-width="1.8" stroke-linejoin="round"/>' % pts)
    for ang in (BEAM / 2.0, FIELD / 2.0):
        o.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#f37021" stroke-width="0.7"/>' % (sx(ang), y0, sx(ang), y1))
    o.append("</svg>")
    return "\n".join(o)


def spread_rows():
    rows = []
    for ft in (6, 8, 10, 12, 15):
        b = 2 * ft * 12 * math.tan(math.radians(BEAM / 2.0))
        f = 2 * ft * 12 * math.tan(math.radians(FIELD / 2.0))
        rows.append('<tr><td class="k">%d ft (%.1f m)</td><td class="c">%s (%.2f m)</td><td class="c">%s (%.2f m)</td></tr>'
                    % (ft, ft * 0.3048, ft_in(b), b * 0.0254, ft_in(f), f * 0.0254))
    return "\n".join(rows)


def dims_svg():
    """LC-drawn schematic from the mechanical table [SPEC p4]; front view and side view."""
    s = 1.25                                  # px per mm
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 270" width="100%">',
         '<defs><marker id="a" viewBox="0 0 6 6" refX="3" refY="3" markerWidth="5" markerHeight="5" orient="auto-start-reverse">'
         '<path d="M0,0 L6,3 L0,6 z" fill="#1A1A2E"/></marker></defs>']
    st = 'fill="#f4f4f6" stroke="#1A1A2E" stroke-width="1"'
    tx = 'font-family="Poppins" font-size="7.5" fill="#1A1A2E"'
    top = 22
    # front view
    cx = 70
    o.append('<rect x="%g" y="%g" width="%g" height="%g" %s/>' % (cx - L3_MM * s / 2, top, L3_MM * s, H1_MM * s, st))
    o.append('<rect x="%g" y="%g" width="%g" height="%g" %s/>' % (cx - 6, top + H1_MM * s, 12, (H3_MM - D_MM - H1_MM) * s, st))
    cy = top + (H3_MM - D_MM / 2.0) * s
    o.append('<circle cx="%g" cy="%g" r="%g" %s/>' % (cx, cy, D_MM * s / 2, st))
    o.append('<circle cx="%g" cy="%g" r="%g" fill="#ffffff" stroke="#1A1A2E" stroke-width="0.8"/>' % (cx, cy, D_MM * s / 2 - 9))
    o.append('<circle cx="%g" cy="%g" r="%g" fill="#fdeee5" stroke="#f37021" stroke-width="0.8"/>' % (cx, cy, 14))
    yb = top + H3_MM * s + 14
    o.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#1A1A2E" stroke-width="0.7" marker-start="url(#a)" marker-end="url(#a)"/>'
             % (cx - D_MM * s / 2, yb, cx + D_MM * s / 2, yb))
    o.append('<text x="%g" y="%g" %s text-anchor="middle">A</text>' % (cx, yb + 11, tx))
    o.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#1A1A2E" stroke-width="0.7" marker-start="url(#a)" marker-end="url(#a)"/>'
             % (cx - L3_MM * s / 2, top - 8, cx + L3_MM * s / 2, top - 8))
    o.append('<text x="%g" y="%g" %s text-anchor="middle">D</text>' % (cx, top - 11, tx))
    o.append('<text x="%g" y="%g" font-family="Poppins" font-size="6.8" fill="#7a7e8c" text-anchor="middle">FRONT</text>' % (cx, 266))
    # side view
    x0 = 175
    cyl_top = top + (H3_MM - D_MM) * s
    o.append('<rect x="%g" y="%g" width="%g" height="%g" rx="2" %s/>' % (x0, cyl_top, L1_MM * s, D_MM * s, st))
    o.append('<rect x="%g" y="%g" width="%g" height="%g" fill="#e6e7ec" stroke="#1A1A2E" stroke-width="0.8"/>'
             % (x0, cyl_top, 14, D_MM * s))
    ax = x0 + L1_MM * s * 0.62
    o.append('<rect x="%g" y="%g" width="%g" height="%g" %s/>' % (ax - 6, top + H1_MM * s, 12, (H3_MM - D_MM - H1_MM) * s, st))
    o.append('<rect x="%g" y="%g" width="%g" height="%g" %s/>' % (ax - L3_MM * s / 2, top, L3_MM * s, H1_MM * s, st))
    yb2 = cyl_top + D_MM * s + 14
    o.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#1A1A2E" stroke-width="0.7" marker-start="url(#a)" marker-end="url(#a)"/>'
             % (x0, yb2, x0 + L1_MM * s, yb2))
    o.append('<text x="%g" y="%g" %s text-anchor="middle">B</text>' % (x0 + L1_MM * s / 2, yb2 + 11, tx))
    xr = x0 + L1_MM * s + 14
    o.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#1A1A2E" stroke-width="0.7" marker-start="url(#a)" marker-end="url(#a)"/>'
             % (xr, top, xr, top + H3_MM * s))
    o.append('<text x="%g" y="%g" %s text-anchor="middle">C</text>' % (xr + 9, top + H3_MM * s / 2 + 3, tx))
    o.append('<text x="%g" y="%g" font-family="Poppins" font-size="6.8" fill="#7a7e8c" text-anchor="middle">SIDE, HEAD LEVEL</text>'
             % (x0 + L1_MM * s / 2, 266))
    o.append('<text x="%g" y="%g" font-family="Poppins" font-size="6.2" fill="#7a7e8c" text-anchor="middle">track</text>'
             % (ax, top - 4))
    o.append("</svg>")
    return "\n".join(o)


COMMON = dict(sku=SKU, name=NAME, foot=C.FOOT, custom=C.CUSTOM, proj=PROJ, hdr=C.hdr(TITLE, SKU),
              w=PN_W, lm="{:,}".format(PN_LM), lpw=LPW[PN_W],
              d=in_mm(D_MM), l1=in_mm(L1_MM), l3=in_mm(L3_MM), h3=in_mm(H3_MM),
              beam="%.0f" % BEAM, field="%.0f" % FIELD,
              amb="%s to %s" % (f_c(-10), f_c(35)), sto="%s to %s" % (f_c(-20), f_c(75)),
              t25=f_c(25), gw=f_c(650))

# ---------------------------------------------------------------- page 1  cover
P1 = """
<section class="page">
  <div class="side"><div class="vt">LED CONNECTION &nbsp;&middot;&nbsp; LED TRACK HEAD &nbsp;&middot;&nbsp; 3 IN</div><img src="assets/logo_side_w.png" alt=""></div>
  <div class="proj">%(proj)s</div>
  <img src="assets/kst3_white.png" alt="3 in LED track head, white" style="position:absolute;left:1.5in;top:.7in;width:2.6in;height:auto">
  <img src="assets/kst3_black.png" alt="3 in LED track head, black" style="position:absolute;left:4.45in;top:1.45in;width:2.25in;height:auto">
  <div style="position:absolute;left:1.25in;right:1.3in;top:5.1in;text-align:center;font-size:6.8pt;color:#7a7e8c">Shown in white and in black. This part number (BA) is the brushed aluminum finish.</div>
  <div class="badges" style="top:1.05in">
    <div class="tbadge">ETL<br>LISTED<i>UL 1574</i></div>
    <div class="tbadge">CRI 95<i>R9 &gt; 80 LED</i></div>
    <div class="tbadge">TRIAC / ELV<br>DIMMING<i>1-100 PCT</i></div>
    <div class="tbadge">H-TYPE<br>TRACK<i>3-WIRE</i></div>
    <div class="tbadge">5 YEAR<i>WARRANTY</i></div>
  </div>
  <div class="cv">
    <div class="kick">3 IN LED TRACK HEAD &middot; CRI 95 &middot; 15&deg; SPOT</div>
    <div class="big">%(name)s</div>
    <div class="rule"></div>
    <div class="lpw">%(lm)s LM AT %(w)d W &middot; 3000K</div>
    <div class="tag">SWITCHABLE 15 / 20 / 25 W &middot; CRI 95 COB &middot; TRIAC OR ELV DIMMING &middot; H-TYPE TRACK &middot; 360&deg; ROTATION, 90&deg; TILT &middot; BRUSHED ALUMINUM</div>
    <div class="strip">
      <div><small>HEAD</small><span>%(d_short)s<br>(80 mm)</span></div>
      <div><small>WATTAGE</small><span>15 / 20 / 25 W<br>switchable</span></div>
      <div><small>LUMENS</small><span>%(lm)s lm<br>at %(w)d W</span></div>
      <div><small>CCT</small><span>3000K</span></div>
      <div><small>BEAM</small><span>15&deg;</span></div>
      <div><small>CRI</small><span>95+</span></div>
    </div>
    <div class="pn">PART NO. &nbsp;<b>%(sku)s</b></div>
    <div class="callout">
      <h4>A CRI 95 SPOT FOR RETAIL DISPLAY</h4>
      <p>A 3 in class head with a CRI 95 chip-on-board source and a 15&deg; optic. One head covers three outputs: a switch on
         the head sets 15, 20 or 25 W (1,500, 2,000 or 2,450 lm). It dims on TRIAC or ELV dimmers from 1 to 100 percent and
         fits H-type 3-wire, 1-circuit track.</p>
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
    <img class="hero2" src="assets/kst3_white.png" alt="" style="width:1.75in;height:auto;top:.1in;right:.25in">
    <div class="wrapn">
      <div class="h1">3 IN LED TRACK HEAD &middot; CRI 95 &middot; 15&deg; SPOT</div>
      <div class="big" style="font-size:28pt">%(name)s</div>
      <div class="code">%(sku)s<small>%(w)d W setting &middot; %(lm)s lm &middot; 3000K &middot; CRI 95 &middot; 15&deg; &middot; H-type track</small></div>
      <div class="icons">
        <div class="dim0"><span>DIMMING</span><span>TRIAC</span><span>ELV</span></div>
        <img src="assets/ic_watt.png" alt="wattage selectable">
        <img src="assets/ic_warranty.png" alt="5 year warranty">
        <div class="dim0"><span>BEAM</span><span>15&deg;</span></div>
      </div>
      <div class="hl"><h4>ONE HEAD, THREE OUTPUTS</h4>
        <p>A switch on the head sets 15, 20 or 25 W. The part number is the 20 W setting, %(lm)s lm; the same head gives
           1,500 lm at 15 W or 2,450 lm at 25 W, set on site to suit the display.</p></div>
    </div>

    <div class="sec"><h3>PRODUCT DESCRIPTION</h3></div>
    <p class="txt">An LED track head for retail display lighting. A CRI 95 chip-on-board source (Luminus CXM-11) behind a 15&deg;
      optic puts a tight, high-colour-quality spot on product, with an 8&deg; shielding angle. The cylinder head is 3.15 in (80 mm)
      across, rotates 360&deg; on the track and tilts 90&deg;. A switch on the head selects 15, 20 or 25 W. The driver dims on TRIAC
      (leading-edge) or ELV (trailing-edge) dimmers from 1 to 100 percent by constant current reduction. The adapter fits
      H-type 3-wire, 1-circuit track. Brushed aluminum finish (white and black also offered); honeycomb louver and snoot accessories are
      available.</p>

    <div class="sec"><h3>OVERVIEW</h3></div>
    <ul class="ov two">
      <li>Switchable 15 / 20 / 25 W; %(lm)s lm at %(w)d W</li>
      <li>3000K, CRI 95 or higher</li>
      <li>LED R9 above 80 (LED maker's minimum for the bin)</li>
      <li>3-step MacAdam ellipse LED bin</li>
      <li>15&deg; beam, 8&deg; shielding angle</li>
      <li>TRIAC or ELV dimming, 1-100 percent</li>
      <li>120 VAC, 60 Hz; power factor 0.9</li>
      <li>THD below 12 percent</li>
      <li>Flicker IEEE 1789 low risk across the dimming range (8.0 percent at full output)</li>
      <li>L70 (B50) 102,000 h at %(t25)s</li>
      <li>360&deg; rotation, 90&deg; tilt</li>
      <li>H-type 3-wire, 1-circuit track adapter</li>
      <li>ETL listed to UL 1574, track lighting</li>
      <li>Finish brushed aluminum, white or black; 5 year warranty</li>
    </ul>

    <div class="sec"><h3>DIMENSIONS</h3></div>
    <div class="dims"><div style="width:3.75in">%(dims)s</div>
      <div class="w"><b>Unit: inch (mm)</b><br>
        A &nbsp;Head diameter %(d)s<br>
        B &nbsp;Head length %(l1)s<br>
        C &nbsp;Overall height, track to head %(h3)s<br>
        D &nbsp;Track adapter width %(l3)s<br><br>
        <b>Mounting</b><br>H-type 3-wire, 1-circuit track<br>360&deg; horizontal rotation, 90&deg; vertical tilt<br><br>
        <span style="color:#7a7e8c">Drawing is schematic; dimensions govern.</span></div></div>
  </div>
  %(foot)s
</section>
"""

# ---------------------------------------------------------------- page 3  order + data
PERF = "\n".join(
    '<tr%s><td class="k">%d W%s</td><td class="c">%s lm</td><td class="c">%d lm/W</td><td class="c">3000K</td>'
    '<td class="c">95+</td><td class="c">15&deg;</td></tr>'
    % (' style="font-weight:700"' if w == PN_W else "", w, " &middot; this part" if w == PN_W else "",
       "{:,}".format(lm), LPW[w]) for w, lm in SETTINGS)

P3 = """
<section class="page">
  %(hdr)s
  <div class="body" style="top:.85in">
    <div class="sec" style="margin-top:.1in"><h3>ORDER LOGIC</h3></div>
    <div class="olx">The LED Connection part number for this head. Segment 01 is always LC.</div>
    <div class="sample"><small>SAMPLE CODE</small>
      <div class="segs">
        <div class="sg"><span class="o">LC</span><i>[01]</i></div><span class="dash">-</span>
        <div class="sg"><span class="o">KST</span><i>[02]</i></div>
        <div class="sg"><span>3</span><i>[03]</i></div><span class="dash">-</span>
        <div class="sg"><span>20W</span><i>[04]</i></div><span class="dash">-</span>
        <div class="sg"><span>T</span><i>[05]</i></div><span class="dash">-</span>
        <div class="sg"><span>BA</span><i>[06]</i></div><span class="dash">-</span>
        <div class="sg"><span>H</span><i>[07]</i></div><span class="dash">-</span>
        <div class="sg"><span>95</span><i>[08]</i></div><span class="dash">-</span>
        <div class="sg"><span>30</span><i>[09]</i></div><span class="dash">-</span>
        <div class="sg"><span class="o">15</span><i>[10]</i></div>
      </div>
    </div>
    <div class="cards" style="grid-template-columns:repeat(10,1fr)">
      <div class="card"><h5>01 BRAND</h5><div><b>LC</b>LED Connection</div></div>
      <div class="card"><h5>02 MODEL</h5><div><b>KST</b>Kestrel track head</div></div>
      <div class="card"><h5>03 SIZE</h5><div><b>3</b>3 in class, 3.15 in (80 mm)</div></div>
      <div class="card"><h5>04 WATTS</h5><div><b>20W</b>20 W setting; switch 15/20/25 W</div></div>
      <div class="card"><h5>05 MOUNT</h5><div><b>T</b>Track</div></div>
      <div class="card"><h5>06 FINISH</h5><div><b>BA</b>Brushed aluminum, silver adapter</div></div>
      <div class="card"><h5>07 ADAPTER</h5><div><b>H</b>H-type, 3-wire, 1-circuit</div></div>
      <div class="card"><h5>08 CRI</h5><div><b>95</b>CRI 95 or higher</div></div>
      <div class="card"><h5>09 CCT</h5><div><b>30</b>3000K</div></div>
      <div class="card"><h5>10 BEAM</h5><div><b>15</b>15&deg; optic</div></div>
    </div>
    <div class="note">This sheet covers the configuration above. Other colour temperatures and optics are quoted separately.</div>

    <div class="sec"><h3>PERFORMANCE DATA</h3></div>
    <table>
      <tr><th style="width:20%%">SWITCH SETTING</th><th class="c">RATED LUMENS</th><th class="c">EFFICACY</th>
          <th class="c">CCT</th><th class="c">CRI</th><th class="c">BEAM</th></tr>
      %(perf)s
    </table>
    <div class="note">Rated lumens are the values stated for the CRI 95 build. Efficacy is rated lumens divided by the switch
      setting, rounded.</div>

    <div class="twocol" style="margin-top:.02in">
      <div>
        <div class="sec"><h3 style="min-width:0;width:100%%">ELECTRICAL DATA</h3></div>
        <table>
          <tr><td class="k" style="width:44%%">Input voltage</td><td>120 VAC, 60 Hz</td></tr>
          <tr><td class="k">Input power</td><td>15 / 20 / 25 W, switch on head</td></tr>
          <tr><td class="k">Input current</td><td>250 mA max.</td></tr>
          <tr><td class="k">Power factor</td><td>0.9</td></tr>
          <tr><td class="k">THD</td><td>Below 12 percent</td></tr>
          <tr><td class="k">Dimming</td><td>TRIAC or ELV, 1-100 percent</td></tr>
          <tr><td class="k">Dimming method</td><td>Constant current reduction</td></tr>
          <tr><td class="k">Inrush current</td><td>5 A, 135 &micro;s</td></tr>
          <tr><td class="k">Start / turn-off time</td><td>Below 500 ms / below 1 s</td></tr>
          <tr><td class="k">Protection</td><td>Over-temperature, over-voltage</td></tr>
          <tr><td class="k">Switching cycles</td><td>Above 100,000</td></tr>
          <tr><td class="k">Electrical class</td><td>Class I (grounded)</td></tr>
        </table>
        <div class="note">Current, THD and inrush at 120 VAC and maximum power.</div>
      </div>
      <div>
        <div class="sec"><h3 style="min-width:0;width:100%%">LIGHT QUALITY</h3></div>
        <table>
          <tr><td class="k" style="width:44%%">LED source</td><td>Chip-on-board, Luminus CXM-11</td></tr>
          <tr><td class="k">CCT</td><td>3000K</td></tr>
          <tr><td class="k">CRI</td><td>95 or higher</td></tr>
          <tr><td class="k">R9</td><td>Above 80, LED maker's minimum for the bin</td></tr>
          <tr><td class="k">Colour consistency</td><td>3-step MacAdam ellipse (LED bin)</td></tr>
          <tr><td class="k">Beam / shielding</td><td>15&deg; / 8&deg;</td></tr>
          <tr><td class="k">Percent flicker (120 V, 60 Hz)</td><td>8.0 at 100%%, 6.7 at 80%%, 0.8 at 50%%, 0 at 20%% output; IEEE 1789 low risk</td></tr>
          <tr><td class="k">Flicker Pst LM / SVM</td><td>Below 0.8 / below 0.3</td></tr>
          <tr><td class="k">Blue light hazard</td><td>Risk group 1</td></tr>
          <tr><td class="k">L70 (B50)</td><td>102,000 h at %(t25)s</td></tr>
          <tr><td class="k">L80 (B10)</td><td>76,000 h at %(t25)s</td></tr>
          <tr><td class="k">L90 (B10)</td><td>35,000 h at %(t25)s</td></tr>
        </table>
      </div>
    </div>
  </div>
  %(foot)s
</section>
"""

# ---------------------------------------------------------------- page 4  photometry + compliance
P4 = """
<section class="page">
  %(hdr)s
  <div class="body" style="top:.85in">
    <div class="sec" style="margin-top:.1in"><h3>BEAM DISTRIBUTION</h3></div>
    <div class="band" style="margin-top:0"><b>Measured on the CRI 90 build.</b> The curves below are from a goniophotometer test of the
      CRI 90 build of this head with a 15&deg; optic, at 20.6 W, normalised to percent of peak. They show the beam shape only.
      The CRI 95 build has not been photometrically tested, so no candela, lumen or illuminance values are printed.</div>
    <div class="photo-grid" style="margin-top:.1in">
      <div class="pcard"><h6>POLAR, RELATIVE</h6><div class="sub">0-180 and 90-270 deg planes, nadir at bottom</div><div class="pw">%(polar)s</div></div>
      <div class="pcard"><h6>BEAM PROFILE, RELATIVE</h6><div class="sub">Mean of the 12 measured planes</div><div class="pw">%(lin)s</div></div>
    </div>
    <table style="margin-top:.1in">
      <tr><th style="width:28%%">DISTANCE TO SURFACE</th><th class="c">BEAM DIAMETER, %(beam)s&deg; (50 PCT OF PEAK)</th>
          <th class="c">FIELD DIAMETER, %(field)s&deg; (10 PCT OF PEAK)</th></tr>
      %(spread)s
    </table>
    <div class="note">Beam and field angles are measured from the test file and averaged over 12 planes; diameters are for a head
      aimed straight at the surface.</div>

    <div class="twocol">
      <div>
        <div class="sec"><h3 style="min-width:0;width:100%%">CERTIFICATION</h3></div>
        <table>
          <tr><td class="k" style="width:38%%">Safety listing</td><td>ETL listed, track lighting: UL 1574; CSA C22.2 No. 250.570</td></tr>
          <tr><td class="k">Location</td><td>Indoor, IP20</td></tr>
          <tr><td class="k">Impact</td><td>IK08</td></tr>
          <tr><td class="k">Glow-wire test</td><td>%(gw)s, 30 s</td></tr>
        </table>
        <div class="note">The listing and standards are as read off the certificate. LED Connection prints a listing control number
          only once it is confirmed for this exact build.</div>
        <div class="sec"><h3 style="min-width:0;width:100%%">ENVIRONMENT</h3></div>
        <table>
          <tr><td class="k" style="width:38%%">Ambient, operating</td><td>%(amb)s</td></tr>
          <tr><td class="k">Humidity</td><td>20-80 percent RH</td></tr>
          <tr><td class="k">Storage</td><td>%(sto)s</td></tr>
        </table>
        <div class="note">Not for totally enclosed spaces.</div>
      </div>
      <div>
        <div class="sec"><h3 style="min-width:0;width:100%%">FINISH AND ACCESSORIES</h3></div>
        <table>
          <tr><th style="width:38%%">FINISH</th><th>DESCRIPTION</th></tr>
          <tr><td class="k">BA &middot; Brushed aluminum</td><td>Body brushed aluminum, adapter silver (this part number)</td></tr>
          <tr><td class="k">White</td><td>RAL 9016</td></tr>
          <tr><td class="k">Black</td><td>RAL 7021</td></tr>
        </table>
        <table style="margin-top:.08in">
          <tr><th style="width:38%%">ACCESSORY</th><th>SIZE, inch (mm)</th></tr>
          <tr><td class="k">Honeycomb louver</td><td>%(hc)s</td></tr>
          <tr><td class="k">Snoot, 30&deg; shielding</td><td>%(sn)s</td></tr>
        </table>
        <div class="note">Accessories are ordered separately.</div>
        <div class="sec"><h3 style="min-width:0;width:100%%">WARRANTY</h3></div>
        <ul class="ov"><li>5 year limited warranty. Full terms are issued with the order acknowledgement.</li></ul>
      </div>
    </div>
  </div>
  %(custom)s
  %(foot)s
</section>
"""


def build():
    v = dict(COMMON)
    v.update(d_short="3.15 in", dims=dims_svg(), perf=PERF, polar=polar(), lin=linear_svg(), spread=spread_rows(),
             hc="%s dia., %s deep" % (in_mm(HC[0]), in_mm(HC[1])),
             sn="%s dia., %s long" % (in_mm(SN[0]), in_mm(SN[2])))
    v["custom"] = C.CUSTOM.replace('class="custom"', 'class="custom" style="bottom:.45in"')
    pages = [P1 % dict(v, custom=C.CUSTOM), P2 % v, P3 % v, P4 % v]
    html = C.doc("LED Connection spec sheet " + SKU, pages)
    path = os.path.join(HERE, "kestrel.html")
    open(path, "w", encoding="utf-8").write(html)
    hits = C.leak_check(SKU, html, extra_ok=CODE_OK)
    pdf = C.to_pdf(path, PDF_NAME)
    C.strip_metadata(pdf, "LED Connection Spec Sheet %s" % SKU, "LED Connection 3 in LED track head specification")
    return pdf, hits


if __name__ == "__main__":
    print("IES (CRI 90 build): %.2f W, %.0f lm, peak %.0f cd, beam %.1f deg, field %.1f deg"
          % (D["watts"], ies.total_lumens(D), PEAK, BEAM, FIELD))
    pdf, hits = build()
    print(pdf, hits)
    print("pdf_text_check:", C.pdf_text_check(pdf))
    for f in C.preview(pdf):
        print(f)
