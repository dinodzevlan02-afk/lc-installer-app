# SHEET 2 - LC STRATA T8, 4 ft T8 LED tube, Type A, LC-STR8-4A-10W-840.
# Kroger interior comparison package, 2026-10-12. LC-XCPA layout, 2 pages.
#
# DATA-DRIVEN: every printed value lives in SPEC below. A row whose value is None
# is not printed (no placeholders). When the factory datasheet / LM-79 arrives,
# fill the value and the source tag in SPEC and rebuild; the cover strip, the
# overview list and the specification table all read from SPEC.
#
# PROVENANCE
#  [DS]   Factory datasheet "Specs of T8 Type A", received 2026-10-12 20:16 (5 pages):
#         10 W bare lamp; on a normal-ballast-factor T8 ballast 12.5 W system and
#         1,850 lm (+/-10%); 4000K; Ra83, R9>0; PF 0.9; beam 200 deg; 50,000 h; 5 years;
#         damp location; glass body with PET coating, frosted lens, G13; operating
#         -20 to 45 C; size A 1198 / B 1205 / C 1213 mm, D 26 mm; emergency- and
#         dimmable-ballast compatible; UL 1993 current-leakage protection; ballast
#         compatibility list (112 rows, all Y). SUPERSEDES the email's 2,000 lm / 13 W.
#  [EM]   Factory email to Dino, received 2026-10-09 23:24 (reply to the 10/6 RFQ):
#         4 ft T8 Type A, 4000K; 2,000 lm (+/-10%); lamp power 10 W; system power
#         on ballast 13 W. (Also: industrial pack 25 pcs/carton, prices, a UL file
#         number and a DLC ID: not printed, see below.)
#  [DEF]  Definitional for the product class, not a measured value: a 4 ft T8 lamp
#         uses the G13 medium bi-pin base; UL Type A means the tube runs on the
#         existing fluorescent ballast.
#  [PHOTO] Generic tube photograph from LED Connection's own 2025 Kroger comparison
#         (package-20261012/assets/p7_x423); no logo or marking on it.
#
# DROPPED / NOT YET CONFIRMED (asked of the factory 2026-10-12)
#  CRI, beam angle, rated life (L70), warranty, lens material, power factor, THD,
#  ballast compatibility list, LM-79 report, exact length and weight, operating
#  temperature. Efficacy is NOT printed: the email does not say whether the 2,000 lm
#  was measured bare or on a ballast, so 200 lm/W (lamp) and 154 lm/W (system) are
#  both unproven; the 2025 LC tube sheets' 200 lm/W was a boosted figure.
#  UL and DLC: vendor-stated in the email only. No certificate, no UL Product iQ
#  read, no QPL read, and a listing in the factory's name does not list an LC-branded
#  part. Not printed, not even as "UL listed / DLC listed" without numbers: for a
#  Kroger rebate a DLC claim is a claim to the utility. Set verified=True in CERTS
#  only after reading the certificate / QPL entry, and only once it covers the LC
#  part (multiple listing or private label).
#  The "840" segment is Dino's part number; by convention 8 = CRI 80s, which is NOT
#  confirmed, so the order card describes 840 as the 4000K colour code only.
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common as C

SKU = "LC-STR8-4A-10W-840"
NAME = "LC STRATA T8"
TITLE = "4 FT T8 LED TUBE &middot; TYPE A &middot; " + NAME
PDF_NAME = "LC SPEC SHEET_4 ft T8 LED Tube Type A LC Strata T8 %s.pdf" % SKU
PROJ = "PROJECT: KROGER INTERIOR &nbsp;&middot;&nbsp; 4 FT T8 TUBE &nbsp;&middot;&nbsp; ISSUED 2026-10-13"
CODE_OK = ("str8",)

# ---------------------------------------------------------------- the one place to edit
# key: (group, label, value or None, source tag)
SPEC = [
    ("size",     "PHYSICAL",   "Lamp",                    "4 ft T8 LED tube",                       "[EM]"),
    ("base",     "PHYSICAL",   "Base",                    "G13 medium bi-pin",                      "[DEF]"),
    ("length",   "PHYSICAL",   "Overall length",          "47.8 in (1,213 mm) with pins; 47.2 in (1,198 mm) between lampholders", "[DS]"),
    ("dia",      "PHYSICAL",   "Diameter",                "1.02 in (26 mm), T8",                    "[DS]"),
    ("weight",   "PHYSICAL",   "Weight",                  None,                                     None),
    ("lens",     "PHYSICAL",   "Lens / tube material",    "Glass tube with PET shatter coating, frosted lens", "[DS]"),
    ("type",     "ELECTRICAL", "Operation",               "Type A: runs on the existing T8 fluorescent ballast", "[EM][DEF]"),
    ("lamp_w",   "ELECTRICAL", "Lamp power",              "10 W",                                   "[EM]"),
    ("sys_w",    "ELECTRICAL", "System power, on ballast", "12.5 W (normal ballast factor)",        "[DS]"),
    ("pf",       "ELECTRICAL", "Power factor",            "0.9 (set by the ballast)",               "[DS]"),
    ("thd",      "ELECTRICAL", "THD",                     None,                                     None),
    ("ballasts", "ELECTRICAL", "Compatible ballasts",     "112 T8 electronic ballasts on the compatibility list: 93 instant start, 17 programmed start (2 triac dimming), 2 instant start 0-10 V dimming. Emergency ballast compatible", "[DS]"),
    ("lumens",   "LIGHT",      "Light output",            "1,850 lm on a normal-ballast-factor T8 ballast, tolerance &plusmn;10 percent", "[DS]"),
    ("cct",      "LIGHT",      "Colour temperature",      "4000K",                                  "[EM]"),
    ("cri",      "LIGHT",      "CRI",                     "83 (R9 above 0)",                        "[DS]"),
    ("beam",     "LIGHT",      "Beam angle",              "200&deg;",                               "[DS]"),
    ("efficacy", "LIGHT",      "Efficacy, system",        "148 lm/W (1,850 lm / 12.5 W on ballast)", "[DS]"),
    ("life",     "LIFE",       "Rated life",              "50,000 hours",                           "[DS]"),
    ("loc",      "LIFE",       "Location",                "Damp locations",                         "[DS]"),
    ("warranty", "LIFE",       "Warranty",                "5 years",                                "[DS]"),
    ("temp",     "LIFE",       "Operating temperature",   "-4 to 113&deg;F (-20 to 45&deg;C)",      "[DS]"),
]
# Listings: printed only when verified=True. Enter the number only from the certificate
# or QPL page itself, and remove it from common.VENDOR_WORDS at the same time.
CERTS = [
    dict(name="UL listed", number=None, verified=False),
    dict(name="DLC listed", number=None, verified=False),
]

S = {k: v for k, g, lab, v, src in SPEC}
for k, g, lab, v, src in SPEC:
    assert (v is None) == (src is None), k
PENDING = [lab for k, g, lab, v, src in SPEC if v is None]


def spec_table():
    out = []
    for grp in ("PHYSICAL", "ELECTRICAL", "LIGHT", "LIFE"):
        rows = [(lab, v) for k, g, lab, v, src in SPEC if g == grp and v is not None]
        if not rows:
            continue
        out.append('<tr><th colspan="2">%s</th></tr>' % grp)
        out += ['<tr><td class="k" style="width:38%%">%s</td><td>%s</td></tr>' % r for r in rows]
    certs = [c for c in CERTS if c["verified"]]
    if certs:
        out.append('<tr><th colspan="2">LISTINGS</th></tr>')
        out += ['<tr><td class="k">%s</td><td>%s</td></tr>' % (c["name"], c["number"] or "") for c in certs]
    return "\n".join(out)


def strip():
    cells = [("SIZE", "4 ft<br>T8"), ("LUMENS", S["lumens"].split(" lm")[0] + " lm"),
             ("LAMP POWER", S["lamp_w"]), ("ON BALLAST", S["sys_w"].split(" (")[0] + "<br>system"), ("CCT", S["cct"]), ("TYPE", "A")]
    if S["cri"]:
        cells[0] = ("CRI", S["cri"].split(" (")[0])
    return "\n".join('<div><small>%s</small><span>%s</span></div>' % c for c in cells)


def overview():
    items = ["4 ft T8 LED tube, G13 medium bi-pin base",
             "Type A: runs on the existing T8 fluorescent ballast",
             "1,850 lm on a normal-ballast-factor T8 ballast (tolerance &plusmn;10 percent)",
             "10 W lamp power; 12.5 W system power on ballast",
             "4000K colour temperature"]
    extra = [("cri", "CRI %s"), ("beam", "Beam angle %s"), ("life", "Rated life %s"), ("warranty", "%s warranty"),
             ("pf", "Power factor %s"), ("thd", "THD %s"), ("lens", "%s"), ("loc", "%s")]
    items.append("Works with emergency and dimmable T8 ballasts on the compatibility list")
    items += [fmt % S[k] for k, fmt in extra if S[k]]
    items += [c["name"] for c in CERTS if c["verified"]]
    return "\n".join("<li>%s</li>" % i for i in items)


V = dict(sku=SKU, name=NAME, proj=PROJ, foot=C.FOOT, hdr=C.hdr(TITLE, SKU), strip=strip(), overview=overview(),
         spec=spec_table(), custom=C.CUSTOM.replace('class="custom"', 'class="custom" style="bottom:.45in"'))

# ---------------------------------------------------------------- page 1  cover
P1 = """
<section class="page">
  <div class="side"><div class="vt">LED CONNECTION &nbsp;&middot;&nbsp; T8 LED TUBE &nbsp;&middot;&nbsp; 4 FT TYPE A</div><img src="assets/logo_side_w.png" alt=""></div>
  <div class="proj">%(proj)s</div>
  <img src="assets/str8_tube_soft.png" alt="4 ft T8 LED tube" style="position:absolute;left:2.05in;top:.95in;width:5.3in;height:auto">
  <div class="badges">
    <div class="tbadge">TYPE A<i>BALLAST<br>COMPATIBLE</i></div>
    <div class="tbadge">1,850<br>LUMENS<i>ON BALLAST</i></div>
    <div class="tbadge">4000K<i>NEUTRAL</i></div>
  </div>
  <div class="cv" style="right:1.45in">
    <div class="kick">4 FT T8 LED TUBE &middot; TYPE A &middot; BALLAST COMPATIBLE</div>
    <div class="big">%(name)s</div>
    <div class="rule"></div>
    <div class="lpw">1,850 LM &middot; 12.5 W SYSTEM &middot; 4000K</div>
    <div class="tag">RUNS ON THE EXISTING T8 BALLAST &middot; NO REWIRING &middot; G13 BI-PIN</div>
    <div class="strip">
      %(strip)s
    </div>
    <div class="pn">PART NO. &nbsp;<b>%(sku)s</b></div>
    <div class="callout">
      <h4>RELAMP ON THE BALLAST ALREADY IN THE FIXTURE</h4>
      <p>A Type A tube runs on the T8 fluorescent ballast that is already installed: the lamp is swapped, the ballast stays,
         and nothing is rewired. 1,850 lm on a normal-ballast-factor ballast; 10 W lamp, 12.5 W for the tube and ballast together.</p>
    </div>
  </div>
  %(custom)s
  %(foot)s
</section>
"""

# ---------------------------------------------------------------- page 3  specifications
P3 = """
<section class="page">
  %(hdr)s
  <div class="body">
    <div class="sec" style="margin-top:.1in"><h3>SPECIFICATIONS</h3></div>
    <table>
      %(spec)s
    </table>
  </div>
  %(custom)s
  %(foot)s
</section>
"""

# ---------------------------------------------------------------- page 2  data
P2 = """
<section class="page">
  %(hdr)s
  <div class="body">
    <img class="hero2" src="assets/str8_tube.jpeg" alt="" style="width:2.6in;height:auto;top:.2in;right:0">
    <div class="wrapn" style="padding-right:2.8in">
      <div class="h1">4 FT T8 LED TUBE &middot; TYPE A</div>
      <div class="big" style="font-size:28pt">%(name)s</div>
      <div class="code">%(sku)s<small>4 ft T8 &middot; Type A &middot; 1,850 lm on ballast &middot; 10 W lamp &middot; 4000K</small></div>
    </div>

    <div class="sec" style="margin-top:.32in"><h3>PRODUCT DESCRIPTION</h3></div>
    <p class="txt">A 4 ft T8 LED tube for relamping fluorescent troffers, wraps and strips. As a Type A tube it runs on the
      T8 fluorescent ballast already in the fixture, so the lamp is swapped and nothing is rewired. On a normal-ballast-factor
      ballast it gives 1,850 lm at 4000K and CRI 83 from 10 W of lamp power; with the ballast, the system draws 12.5 W. Light output and system power depend on the
      ballast the tube runs on.</p>

    <div class="sec"><h3>OVERVIEW</h3></div>
    <ul class="ov two">
      %(overview)s
    </ul>

    <div class="sec"><h3>ORDER LOGIC</h3></div>
    <div class="sample"><small>SAMPLE CODE</small>
      <div class="segs">
        <div class="sg"><span class="o">LC</span><i>[01]</i></div><span class="dash">-</span>
        <div class="sg"><span class="o">STR</span><i>[02]</i></div>
        <div class="sg"><span>8</span><i>[03]</i></div><span class="dash">-</span>
        <div class="sg"><span>4</span><i>[04]</i></div>
        <div class="sg"><span>A</span><i>[05]</i></div><span class="dash">-</span>
        <div class="sg"><span>10W</span><i>[06]</i></div><span class="dash">-</span>
        <div class="sg"><span class="o">840</span><i>[07]</i></div>
      </div>
    </div>
    <div class="cards" style="grid-template-columns:repeat(7,1fr)">
      <div class="card"><h5>01 BRAND</h5><div><b>LC</b>LED Connection</div></div>
      <div class="card"><h5>02 MODEL</h5><div><b>STR</b>Strata LED tube</div></div>
      <div class="card"><h5>03 LAMP</h5><div><b>8</b>T8</div></div>
      <div class="card"><h5>04 LENGTH</h5><div><b>4</b>4 ft</div></div>
      <div class="card"><h5>05 TYPE</h5><div><b>A</b>Type A, ballast compatible</div></div>
      <div class="card"><h5>06 WATTS</h5><div><b>10W</b>10 W lamp power</div></div>
      <div class="card"><h5>07 COLOUR</h5><div><b>840</b>4000K</div></div>
    </div>
  </div>
  %(custom)s
  %(foot)s
</section>
"""


def build():
    html = C.doc("LED Connection spec sheet " + SKU, [P1 % dict(V, custom=C.CUSTOM), P2 % V, P3 % V])
    path = os.path.join(HERE, "strata.html")
    open(path, "w", encoding="utf-8").write(html)
    hits = C.leak_check(SKU, html, extra_ok=CODE_OK)
    low = html.lower()
    # nothing unconfirmed may reach the page
    if not any(c["verified"] for c in CERTS):
        for w in ("ul listed", "etl", "dlc", "listed"):
            if re.search(r"\b%s\b" % re.escape(w), low):
                hits.append("unverified listing %r" % w)
    for key, w in (("efficacy", "lm/w"), ("warranty", "warranty"), ("beam", "beam angle"), ("cri", "cri"),
                   ("life", "l70"), ("pf", "power factor"), ("thd", "thd")):
        if S[key] is None and re.search(r"\b%s\b" % re.escape(w), low):
            hits.append("unconfirmed %s %r on the page" % (key, w))
    pdf = C.to_pdf(path, PDF_NAME)
    C.strip_metadata(pdf, "LED Connection Spec Sheet %s" % SKU, "LED Connection 4 ft T8 LED tube, Type A, specification")
    return pdf, hits


if __name__ == "__main__":
    print("not yet confirmed (not printed):", ", ".join(PENDING))
    pdf, hits = build()
    print(pdf, hits)
    print("pdf_text_check:", C.pdf_text_check(pdf))
    for f in C.preview(pdf):
        print(f)
