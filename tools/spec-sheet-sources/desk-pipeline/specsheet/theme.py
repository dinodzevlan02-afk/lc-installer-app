"""
The LED Connection spec sheet design system, read off the two reference
sheets (Omnitron LC-LHB-OLH, Triproof LC-TP).

Written as one file because the first attempt rebuilt the CONTENT of those
sheets and ignored the DESIGN, and the result looked nothing like them. The
layout is not decoration here - a spec sheet that does not look like the rest
of the catalogue reads as a document from somewhere else.

What the references actually do:

  * A navy left sidebar on the cover, carrying the family name rotated
    vertically in orange, with the logo at its foot.
  * A hero product image over an orange circuit-trace pattern.
  * Product type in small grey caps ABOVE a very large black family name.
  * A short orange rule, then the headline efficacy in large orange.
  * Six spec columns divided by thin vertical rules - small orange caps
    labels over large bold values.
  * Section headers as filled navy bars with white caps and letterspacing,
    each with a thin orange rule running to the right edge.
  * Callouts on cream with a thick orange left bar.
  * The order-logic sample code on a navy panel: brand and series in orange,
    the rest white, with segment markers beneath.
  * Segment columns with orange header bars over light grey bodies.
  * Tables with a navy header row and alternating row fills.
  * A navy footer bar on every page with orange field labels.
"""

NAVY = "#1b2138"
ORANGE = "#f47b20"
CREAM = "#fdf0e6"
GREY_BG = "#f4f4f4"
GREY_TX = "#7a7f8c"
INK = "#1a1a1a"

CSS = """
*{box-sizing:border-box}
body{margin:0;background:#e9e9ec;color:%(ink)s;
  font-family:'Segoe UI',Montserrat,Arial,sans-serif;-webkit-print-color-adjust:exact;
  print-color-adjust:exact}
.page{position:relative;width:8.5in;height:11in;background:#fff;margin:0 auto 16px;
  overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.15)}

/* ---- cover sidebar ---- */
.rail{position:absolute;left:0;top:0;bottom:0;width:.62in;background:%(navy)s}
.rail-txt{position:absolute;left:0;bottom:1.35in;width:.62in;text-align:center;
  transform:rotate(-90deg);transform-origin:center;white-space:nowrap;
  color:%(orange)s;font-size:6.5pt;font-weight:800;letter-spacing:1.4px}
.rail-logo{position:absolute;left:.08in;bottom:.42in;width:.46in}
.rail-logo img,.logo-tr img,.phead img{width:100%%;height:auto;display:block}

/* ---- hero ---- */
.hero{position:relative;margin-left:.62in;height:4.05in;background:#fff;
  border-bottom:0;overflow:hidden}
.hero .trace{position:absolute;inset:0}
.hero .shot{position:absolute;inset:0;display:flex;align-items:center;
  justify-content:center}
.hero .shot img{max-width:74%%;max-height:80%%;object-fit:contain}
.hero .noshot{position:absolute;inset:0;display:flex;align-items:center;
  justify-content:center;color:#c8ccd6;font-size:8pt;letter-spacing:1.5px;
  font-weight:700}
.logo-tr{position:absolute;right:.45in;top:.3in;width:1.05in}

/* ---- cover body ---- */
.cbody{margin-left:.62in;padding:.28in .45in 0 .38in}
.ptype{font-size:11pt;color:#5b6070;letter-spacing:.4px;margin-bottom:.02in}
.fam{font-size:37pt;font-weight:800;line-height:.96;letter-spacing:-.5px;
  text-transform:uppercase}
.rule{width:1.55in;height:3.5px;background:%(orange)s;margin:.12in 0 .1in}
.eff{font-size:23pt;font-weight:800;color:%(orange)s;letter-spacing:-.3px}
.sub{font-size:9.5pt;color:#5b6070;letter-spacing:.3px;margin-top:.04in}

.specs{display:flex;margin-top:.26in;border-top:1px solid #e3e5ea;
  border-bottom:1px solid #e3e5ea}
.specs div{flex:1;padding:.11in .1in;border-left:1px solid #e3e5ea}
.specs div:first-child{border-left:0;padding-left:0}
.specs span{display:block;font-size:6.5pt;font-weight:800;color:%(orange)s;
  letter-spacing:.9px;margin-bottom:3px}
.specs b{font-size:12.5pt;font-weight:800;letter-spacing:-.2px}

.callout{background:%(grey)s;border-left:5px solid %(orange)s;padding:.14in .18in;
  margin-top:.24in}
.callout b{display:block;font-size:9.5pt;font-weight:800;letter-spacing:.5px;
  margin-bottom:4px}
.callout p{margin:0;font-size:9pt;line-height:1.45}
.custom{text-align:right;font-style:italic;font-size:8.5pt;color:#5b6070;
  margin-top:.12in}
.certs{position:absolute;right:.42in;top:4.35in;text-align:center}
.certs div{width:.38in;height:.38in;border:2px solid #9aa0ae;border-radius:50%%;
  margin-bottom:.11in;font-size:6.5pt;font-weight:800;color:#7a8090;
  display:flex;align-items:center;justify-content:center}

/* ---- inner page header ---- */
.phead{margin:.34in .45in .1in;display:flex;align-items:flex-end;gap:.12in}
.phead .t{font-size:7.5pt;font-weight:800;color:%(orange)s;letter-spacing:.9px;
  padding-bottom:4px;border-bottom:2px solid %(orange)s;white-space:nowrap}
.phead .s{font-size:7.5pt;color:#9aa0ae;letter-spacing:.9px;padding-bottom:4px;
  flex:1;border-bottom:1px solid #dcdfe6}
.phead .lg{width:.85in;margin-bottom:2px;flex:none}

.body{padding:0 .45in}
.secbar{display:flex;align-items:center;margin:.22in 0 .12in}
.secbar b{background:%(navy)s;color:#fff;font-size:10pt;font-weight:800;
  letter-spacing:1.3px;padding:.075in .22in}
.secbar i{flex:1;height:2px;background:%(orange)s;opacity:.75}
p.txt{font-size:9pt;line-height:1.55;text-align:justify;margin:.04in 0}
ul.ov{list-style:none;padding:0;margin:.06in 0}
ul.ov li{font-size:9pt;line-height:1.62;padding-left:.16in;position:relative}
ul.ov li:before{content:"";position:absolute;left:0;top:.075in;width:4px;height:4px;
  background:%(orange)s}

.badges{display:flex;gap:.16in;margin:.16in 0 .06in}
.badge{width:.52in;height:.52in;border:2px solid %(orange)s;border-radius:50%%;
  display:flex;align-items:center;justify-content:center;text-align:center;
  font-size:5pt;font-weight:800;line-height:1.15;color:%(navy)s;padding:3px}

.cream{background:%(cream)s;border-left:5px solid %(orange)s;padding:.14in .18in;
  margin:.16in 0}
.cream b{display:block;font-size:9.5pt;font-weight:800;letter-spacing:.5px;
  margin-bottom:4px}
.cream p{margin:0;font-size:9pt;line-height:1.5;text-align:justify}

table{width:100%%;border-collapse:collapse;margin-top:.06in}
th{background:%(navy)s;color:#fff;font-size:7.5pt;font-weight:800;letter-spacing:.7px;
  text-align:left;padding:.075in .11in}
td{font-size:8.5pt;padding:.07in .11in;border-bottom:1px solid #e6e8ed}
tr:nth-child(even) td{background:#f7f8fa}
td:first-child{font-weight:800}

/* ---- dimensions ---- */
.dims{display:flex;gap:.3in;margin:.1in 0 .05in}
.dims div{flex:1;background:%(grey)s;padding:.12in .16in}
.dims span{display:block;font-size:6.5pt;font-weight:800;color:%(orange)s;letter-spacing:.9px}
.dims b{font-size:11pt;font-weight:800}

/* ---- order logic ---- */
.sample{background:%(navy)s;padding:.16in .22in;margin:.1in 0 .16in}
.sample .lbl{color:#fff;font-size:6.5pt;font-weight:700;letter-spacing:1.2px;
  opacity:.85;margin-bottom:.06in}
.sample .code{font-size:21pt;font-weight:800;color:#fff;letter-spacing:.5px}
.sample .code em{color:%(orange)s;font-style:normal}
.sample .mark{color:%(orange)s;font-size:6.5pt;font-weight:700;margin-top:3px;
  letter-spacing:.8px}
.segs{display:flex;gap:.1in}
.seg{flex:1;background:%(grey)s}
.seg .h{background:%(orange)s;color:#fff;font-size:7.5pt;font-weight:800;
  letter-spacing:.5px;padding:.07in .1in}
.seg .o{padding:.08in .1in;font-size:8pt;line-height:1.35}
.seg .o b{display:block;font-weight:800}
.seg .o span{color:#5b6070}
.notes{text-align:right;font-style:italic;font-size:8pt;color:#5b6070;margin-top:.1in}

/* ---- pre-release ---- */
.prerel{background:#8a1c1c;color:#fff;padding:.1in .16in;margin:0 0 .14in}
.prerel b{font-size:9pt;letter-spacing:1.3px}
.prerel ul{margin:4px 0 0;padding-left:.16in;font-size:7pt;line-height:1.4}

/* ---- footer ---- */
.foot{position:absolute;left:0;right:0;bottom:0;height:.34in;background:%(navy)s;
  color:#fff;display:flex;align-items:center;padding:0 .45in;font-size:7pt;gap:.22in}
.foot em{color:%(orange)s;font-style:normal;font-weight:800;letter-spacing:.5px}
.foot .addr{margin-left:auto}
.page.cover .foot{left:.62in}
@media print{body{background:#fff}.page{margin:0;box-shadow:none;
  page-break-after:always}}
""" % {"navy": NAVY, "orange": ORANGE, "cream": CREAM, "grey": GREY_BG, "ink": INK}


def trace_svg():
    """The angular circuit-trace motif behind the cover photo."""
    seg = []
    for i, (y, w) in enumerate(((70, 300), (150, 210), (300, 250), (392, 320))):
        seg.append(
            "<path d='M0 %d H%d l40 -40 H%d l40 40 H820' fill='none' stroke='%s' "
            "stroke-width='1.6' opacity='.55'/>" % (y, w, w + 120, ORANGE))
        seg.append("<circle cx='%d' cy='%d' r='4.5' fill='%s' opacity='.85'/>"
                   % (w + 40, y - 40, ORANGE))
    return ("<svg class='trace' viewBox='0 0 820 470' preserveAspectRatio='none'>"
            + "".join(seg) + "</svg>")


LOGO = (
    "<svg viewBox='0 0 220 74' xmlns='http://www.w3.org/2000/svg'>"
    "<g fill='%(g)s'>"
    "<rect x='6' y='20' width='46' height='34' rx='3'/>"
    "<rect x='58' y='20' width='46' height='34' rx='3'/>"
    "<rect x='110' y='20' width='46' height='34' rx='3'/>"
    "</g>"
    "<path d='M160 30 L196 30 L196 12' fill='none' stroke='%(g)s' stroke-width='3'/>"
    "<circle cx='198' cy='10' r='4' fill='%(g)s'/>"
    "<text x='6' y='70' font-family='Segoe UI,Arial' font-size='13' font-weight='700' "
    "letter-spacing='3.4' fill='%(o)s'>CONNECTION</text></svg>"
)


import base64, os

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


def asset_uri(name):
    """Embed a PNG as a data URI so the sheet is one self-contained file that
    still renders after OneDrive moves it. Returns None if the asset is missing,
    so the caller can fall back rather than ship a broken image."""
    f = os.path.join(ASSETS, name)
    if not os.path.exists(f):
        return None
    return "data:image/png;base64," + base64.b64encode(open(f, "rb").read()).decode("ascii")


def logo(dark=True):
    """The real LED Connection logo, cropped from the reference sheet at 400 dpi.
    The hand-drawn SVG that used to live here looked nothing like it."""
    uri = asset_uri("logo_dark.png" if dark else "logo_light.png")
    if uri:
        return "<img class='logo' src='%s'>" % uri
    return LOGO % {"g": ("#3a4257" if dark else "#c9ccd4"), "o": ORANGE}
