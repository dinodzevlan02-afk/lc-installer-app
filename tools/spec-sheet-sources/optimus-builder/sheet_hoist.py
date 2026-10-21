# LC HOIST (series HST), portable 300 W LED area lights. Built 2026-10-16 for Dave's
# spec-sheet request; modelled on sheet_kestrel.py (LC-XCPA layout). Two models:
#   LC-HST-MD-300W-NV-XXK  mobile LED disk on a telescoping (crank) tripod stand
#   LC-HST-HB-300W-NV-XXK  portable high bay, hook and plug
# Pending, not in the main table: LC-HST-MD-450W-NV-XXK, LC-HST-HB-450W-NV-XXK.
# Code segments: LC / HST series / MD or HB type / 300W / NV = 100-277 VAC / XXK = CCT,
# two digits + K (50K = 5000K). The factory is named ZERO times on the sheet.
#
# PROVENANCE (every number on this sheet). Factory document set received 2026-10-16,
# folder "Youlumi ETL documents 2026-10-16\extracted\...". All one-page datasheets.
#  [MDS] Spec/200300027HZH-002, MD (mobile disk) 300 W product datasheet, p1:
#        300 W; 100-277 VAC 50/60 Hz; THD < 20%; efficacy 130 lm/W; CCT 2700-6500K;
#        CRI > 80 Ra; working temp -40 to 50 C; IP65; IK08 (5 J); lifespan 50,000 h;
#        material aluminum; lamp cover opal; installation vertical stand; US cord SJTW
#        3 x 0.824 mm2 (18 AWG) 105 C 300 V, 5 m (16.40 ft); vertical stand 4 m (13.12 ft);
#        overall 4.24 m (13.91 ft); leg spread dia. 1.3-1.8 m; stand weight 15.55 kg
#        (34.28 lb); disk dia. 400 mm; disk height 160 mm; height with post 313 mm; tube
#        dia. 35.5 mm; spec table 39,000 lm, PF >= 0.9, certificate ETL. Accessories:
#        standard = hook (hanging), safety chain, stand adapter, hand bag; optional =
#        safety cable (tripod guying), 13 ft tripod vertical stand, carrying case.
#        (A 24 V DC version in the same table is not part of this family; not printed.)
#  [HBS] Spec/200300027HZH-002, HB (portable high bay) 300 W product datasheet, p1:
#        300 W; 100-277 VAC 50/60 Hz; THD < 20%; 130 lm/W; 2700-6500K; CRI > 80 Ra;
#        -40 to 50 C; IP65; IK08 (5 J); 50,000 h; spec table 39,000 lm, PF >= 0.9, ETL;
#        dia. 400 mm; body height 153 mm; overall with hook 273 mm. Cable drawing: STW
#        (SOOW) 14 AWG / 3C 105 C / 600 V; M19 three-core waterproof connectors; plug lead
#        1 ft (304.8 mm) three-pin plug to M19 female; tee lead 5 ft (1524 mm) run with
#        3 ft (914.4 mm) drop; extension 20 ft (6096 mm); outlet lead 1 ft (304.8 mm)
#        M19 male to three-pin receptacle. Code key: CCT XXK = 65K (6500K).
#  [HBM] Installation/200300027HZH-002, HB installation manual V3.3 (2023-09-11), p1:
#        AC 100-277 V; 300 W; suitable for wet locations; housing aluminum + PC; weight
#        7.80 kg (17.20 lb); support to carry >= 15.6 kg; safety chain 1 m (3.28 ft);
#        packing list disk, hook, safety chain, bag, manual; hanging chains and ceiling
#        hooks not included; plug-in. (States a 5 year warranty: NOT printed, the
#        datasheet states none.)
#  [MDM] Installation/200300027HZH-002, MD operation manual, p1-p3: crank tripod,
#        H max 4 m, D (leg spread) 1.8 m, tripod 14 kg, max load 30 kg; packing list
#        crank tripod, fixing bolts, wire rope, ground stakes, carabiners, disk, hook;
#        hand crank raises and lowers the column; guy with the safety cables; p3 indoor
#        and outdoor, temperature -20 to +40 C.
#  [IES] IES files/200300027HZH-002/MD300 MD450, the MD 300 W 5000K file (IESNA 2002,
#        the non-EU file) and its factory photometric test report p1: 37,763 lm at
#        284.6 W, 216.5 V, PF 0.981, average beam 106.5 deg (50%), up 3.7% / down 96.3%,
#        test 2024-08-16 at 25.3 C. Computed here from the file: 37,761 lm, peak 13,199 cd,
#        nadir 13,063 cd (mean of 12 planes), beam 106.3 deg, 96.2 pct down. Lumens, beam, candela and illuminance are computed
#        below from the IES file in code. The EU file (38,477 lm) was not used.
#
# CONFLICTS RESOLVED (more conservative value printed)
#  - MD lumens: [MDS] 39,000 lm vs [IES] 37,763 lm tested: printed the tested value,
#    rounded down to 37,760 lm. HB: no photometric file; printed [HBS] 39,000 lm, rated.
#  - Efficacy: [MDS]/[HBS] 130 lm/W vs [IES] 132.7 lm/W measured: printed 130 lm/W.
#  - Operating ambient: datasheets -40 to 50 C vs [MDM p3] -20 to +40 C: printed
#    -20 to 40 C for both models (the HB manual calls the HB a hanging mobile LED disk).
#  - Tripod weight: [MDS] 15.55 kg vs [MDM] 14 kg: printed the heavier 15.55 kg.
#  - Tripod supplied: [MDS] lists the 13 ft tripod as optional; [MDM] packing list
#    includes it: printed as an option.
#
# DROPPED / GAPS (not in the documents, or not ours to print)
#  - Warranty (only in [HBM], not on a datasheet), ETL report and control numbers, DLC.
#  - MD luminaire weight (only the stand weight is stated), HB beam / candela (no IES),
#    discrete CCT steps (only the 2700-6500K range), R9, SDCM, dimming (none stated),
#    surge rating, US plug configuration name, HB lens material.
#  - IES test voltage 216.5 V: stated on the sheet as the test condition.
import math, os, sys
from decimal import Decimal, ROUND_HALF_UP
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common as C
import ies

NAME = "LC HOIST"
SERIES = "LC-HST"
MD_CODE = "LC-HST-MD-300W-NV-XXK"
HB_CODE = "LC-HST-HB-300W-NV-XXK"
PENDING = ("LC-HST-MD-450W-NV-XXK", "LC-HST-HB-450W-NV-XXK")
TITLE = "PORTABLE 300 W LED AREA LIGHT &middot; " + NAME
PDF_NAME = "LC SPEC SHEET_HOIST HST.pdf"
PROJ = "PORTABLE LED AREA LIGHTING &nbsp;&middot;&nbsp; 300 W &nbsp;&middot;&nbsp; ISSUED 2026-10-16"
IES_MD = sys.argv[1] if len(sys.argv) > 1 else None


# ---------------------------------------------------------------- units (US first)
def _q(v, nd=1):
    return (Decimal(str(v))).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP)


def inch(mm):
    """'15.7 in' from mm, nearest 0.1 in (1 in = 25.4 mm)."""
    return "%s in" % _q(Decimal(str(mm)) / Decimal("25.4"))


def in_mm(mm):
    return '%s <span class="mm">(%s mm)</span>' % (inch(mm), ("%g" % mm))


def ftin(mm):
    """'13 ft 1.5 in' from mm, nearest 0.1 in."""
    tot = _q(Decimal(str(mm)) / Decimal("25.4"))
    ft = int(tot // 12)
    rest = tot - 12 * ft
    return "%d ft %s in" % (ft, rest) if ft else "%s in" % rest


def ftin_m(mm, m_label):
    return '%s <span class="mm">(%s m)</span>' % (ftin(mm), m_label)


def lb(kg):
    return "%s lb" % _q(Decimal(str(kg)) / Decimal("0.45359237"))


def lb_kg(kg):
    return '%s <span class="mm">(%s kg)</span>' % (lb(kg), ("%g" % kg))


def ft(mm):
    return "%s ft" % _q(Decimal(str(mm)) / Decimal("304.8"))


def ft_m(mm):
    return '%s <span class="mm">(%.1f m)</span>' % (ft(mm), mm / 1000.0)


def f_c(c):
    return '%d F <span class="mm">(%d C)</span>' % (round(c * 9 / 5.0 + 32), c)


# ---------------------------------------------------------------- data
W = 300                                            # [MDS][HBS]
LPW = 130                                          # [MDS][HBS] (test 132.7, conservative)
LM_RATED = 39000                                   # [MDS][HBS]
MD_D, MD_HDISK, MD_HTOT, MD_TUBE = 400, 160, 313, 35.5      # [MDS] mm
ST_H, ST_TOT, ST_S0, ST_S1 = 4000, 4240, 1300, 1800        # [MDS][MDM] mm
ST_KG, ST_LOAD = 15.55, 30                                 # [MDS] / [MDM]
HB_D, HB_HBODY, HB_HTOT, HB_KG = 400, 153, 273, 7.80       # [HBS] / [HBM]
HB_SUPPORT_KG, CHAIN_MM = 15.6, 1000                       # [HBM]
MD_CORD_MM = 5000                                          # [MDS]
AMB = (-20, 40)                                            # [MDM p3], conservative

D = ies.read(IES_MD) if IES_MD else None


def _angles(d):
    out = []
    for ih in range(d["nh"] - 1):
        c = d["cd"][ih]; va = d["vang"]; pk = max(c); row = []
        for frac in (0.5, 0.1):
            t = pk * frac
            for i in range(c.index(pk) + 1, len(c)):
                if c[i] < t <= c[i - 1]:
                    row.append(2 * (va[i - 1] + (c[i - 1] - t) / (c[i - 1] - c[i]) * (va[i] - va[i - 1])))
                    break
        out.append(row)
    return (sum(r[0] for r in out) / len(out), sum(r[1] for r in out) / len(out))


if D:
    assert abs(D["watts"] - 284.6) < 0.05, D["watts"]
    LM_TEST = ies.total_lumens(D)
    assert 37700 < LM_TEST < 37800, LM_TEST
    LM_MD = int(LM_TEST // 10 * 10)                 # conservative: round down to 10 lm
    BEAM, FIELD = _angles(D)
    I0 = sum(D["cd"][ih][0] for ih in range(D["nh"] - 1)) / (D["nh"] - 1)   # nadir cd
    PEAK = ies.max_cd(D)[0]
    Z = ies.zonal_table(D)
    DOWN = sum(s for z0, z1, s in Z if z1 <= 90) / LM_TEST * 100.0
    UP = 100.0 - DOWN
else:
    raise SystemExit("pass the MD 300 W 5000K IES file as the first argument")


def polar():
    rel = dict(D)
    rel["cd"] = [[x / PEAK * 100.0 for x in row] for row in D["cd"]]
    return ies.polar_svg(rel, [(0, "#f37021", "0-180 deg plane"), (90, "#1A1A2E", "90-270 deg plane")],
                         "RELATIVE INTENSITY, PERCENT OF PEAK", size=330, rel=True)


def illum_rows():
    rows = []
    for h_ft in (8, 10, 13, 16, 20, 25):
        fc = I0 / float(h_ft * h_ft)
        lux = fc * 10.7639
        dia_ft = 2 * h_ft * math.tan(math.radians(BEAM / 2.0))
        rows.append('<tr><td class="k">%d ft <span class="mm">(%.1f m)</span></td>'
                    '<td class="c">%s fc <span class="mm">(%s lx)</span></td>'
                    '<td class="c">%.1f ft <span class="mm">(%.1f m)</span></td></tr>'
                    % (h_ft, h_ft * 0.3048, "{:,.0f}".format(fc) if fc >= 10 else "%.1f" % fc,
                       "{:,.0f}".format(lux), dia_ft, dia_ft * 0.3048))
    return "\n".join(rows)


# ---------------------------------------------------------------- LC-drawn schematic
def dims_svg():
    """Schematic from the dimension values in [MDS]/[HBS]; not the factory drawing.
    Disk and HB at 0.375 px/mm; the tripod panel at its own smaller scale."""
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 560 256" width="100%">',
         '<defs><marker id="a" viewBox="0 0 6 6" refX="3" refY="3" markerWidth="5" markerHeight="5" '
         'orient="auto-start-reverse"><path d="M0,0 L6,3 L0,6 z" fill="#1A1A2E"/></marker></defs>']
    st = 'fill="#e9eaee" stroke="#1A1A2E" stroke-width="0.9"'
    fin = 'fill="#3b3f52" stroke="#1A1A2E" stroke-width="0.8"'
    lens = 'fill="#ffffff" stroke="#1A1A2E" stroke-width="0.8"'
    tx = 'font-family="Poppins" font-size="9" font-weight="700" fill="#f37021"'
    cap = 'font-family="Poppins" font-size="7" font-weight="600" fill="#7a7e8c" text-anchor="middle"'
    ar = 'stroke="#1A1A2E" stroke-width="0.7" marker-start="url(#a)" marker-end="url(#a)"'
    ext = 'stroke="#9aa0ae" stroke-width="0.5" stroke-dasharray="2 2"'

    def disk(cx, y_top, s, d_mm, h_mm):
        """Side profile: dome (48 pct), fin band (30 pct), opal bowl (22 pct). Returns lens-bottom y."""
        r = d_mm * s / 2.0
        h = h_mm * s
        dome, band, bowl = h * 0.48, h * 0.30, h * 0.22
        y_band = y_top + dome
        y_bowl = y_band + band
        y_bot = y_bowl + bowl
        k = 4.0 / 3.0                                     # cubic control so the curve reaches the extreme
        o.append('<path d="M%g,%g C%g,%g %g,%g %g,%g Z" %s/>'
                 % (cx - r * 0.97, y_bowl, cx - r * 0.55, y_bowl + bowl * k, cx + r * 0.55, y_bowl + bowl * k,
                    cx + r * 0.97, y_bowl, lens))
        o.append('<rect x="%g" y="%g" width="%g" height="%g" %s/>' % (cx - r, y_band, 2 * r, band, fin))
        o.append('<path d="M%g,%g C%g,%g %g,%g %g,%g Z" %s/>'
                 % (cx - r * 0.93, y_band, cx - r * 0.55, y_band - dome * k, cx + r * 0.55, y_band - dome * k,
                    cx + r * 0.93, y_band, st))
        return y_bot

    def vdim(x, y0, y1, lab, side=1):
        o.append('<line x1="%g" y1="%g" x2="%g" y2="%g" %s/>' % (x, y0, x, y1, ar))
        o.append('<text x="%g" y="%g" %s text-anchor="%s">%s</text>'
                 % (x + 5 * side, (y0 + y1) / 2 + 3, tx, "start" if side > 0 else "end", lab))

    def hdim(x0, x1, y, lab):
        o.append('<line x1="%g" y1="%g" x2="%g" y2="%g" %s/>' % (x0, y, x1, y, ar))
        o.append('<text x="%g" y="%g" %s text-anchor="middle">%s</text>' % ((x0 + x1) / 2, y + 12, tx, lab))

    s = 0.375
    # --- panel 1: MD disk on its post adapter
    cx, top = 92, 52
    bot = disk(cx, top, s, MD_D, MD_HDISK)
    post_bot = top + MD_HTOT * s
    tw = MD_TUBE * s
    o.append('<rect x="%g" y="%g" width="%g" height="%g" %s/>' % (cx - tw / 2 - 2, bot - 2, tw + 4, post_bot - bot + 2, st))
    r = MD_D * s / 2.0
    for y in (top, bot):
        o.append('<line x1="%g" y1="%g" x2="%g" y2="%g" %s/>' % (cx + r * 0.3, y, cx + r + 16, y, ext))
    o.append('<line x1="%g" y1="%g" x2="%g" y2="%g" %s/>' % (cx + tw / 2 + 3, post_bot, cx + r + 36, post_bot, ext))
    vdim(cx + r + 12, top, bot, "B")
    vdim(cx + r + 32, top, post_bot, "C")
    hdim(cx - r, cx + r, post_bot + 14, "A")
    o.append('<text x="%g" y="251" %s>MD, DISK ON POST ADAPTER</text>' % (cx + 14, cap))

    # --- panel 2: HB with hook
    cx2 = 290
    hook_top = 52
    body_top = hook_top + (HB_HTOT - HB_HBODY) * s
    bot2 = disk(cx2, body_top, s, HB_D, HB_HBODY)
    o.append('<rect x="%g" y="%g" width="%g" height="%g" %s/>' % (cx2 - 5, body_top - 14, 10, 15, st))
    hr = 9
    o.append('<path d="M%g,%g L%g,%g A%g,%g 0 1 1 %g,%g" fill="none" stroke="#1A1A2E" stroke-width="2.4" stroke-linecap="round"/>'
             % (cx2, body_top - 14, cx2, hook_top + hr, hr, hr, cx2 + hr * 1.6, hook_top + hr * 1.3))
    r2 = HB_D * s / 2.0
    for y in (hook_top, body_top, bot2):
        o.append('<line x1="%g" y1="%g" x2="%g" y2="%g" %s/>' % (cx2 + (r2 * 0.3 if y != hook_top else 14), y, cx2 + r2 + 36, y, ext))
    vdim(cx2 + r2 + 12, body_top, bot2, "E")
    vdim(cx2 + r2 + 32, hook_top, bot2, "F")
    hdim(cx2 - r2, cx2 + r2, bot2 + 18, "D")
    o.append('<text x="%g" y="251" %s>HB, WITH HOOK</text>' % (cx2 + 14, cap))

    # --- panel 3: the crank tripod, own scale
    t = 0.0445
    cx3, ground = 478, 222
    st_top = ground - ST_H * t
    dsk_top = ground - ST_TOT * t
    sp = ST_S1 * t / 2.0
    knee = ground - 58
    o.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#9aa0ae" stroke-width="1"/>' % (cx3 - 62, ground, cx3 + 52, ground))
    o.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#1A1A2E" stroke-width="4.5"/>' % (cx3, ground - 2, cx3, ground - ST_H * t * 0.5))
    o.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#1A1A2E" stroke-width="2.4"/>' % (cx3, ground - ST_H * t * 0.5, cx3, st_top))
    for dx in (-sp, sp):
        o.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#1A1A2E" stroke-width="2"/>' % (cx3, knee, cx3 + dx, ground))
    td = disk(cx3, dsk_top, t * 1.4, MD_D, MD_HDISK)        # disk drawn 1.4x so it reads; still clears G
    o.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#1A1A2E" stroke-width="2"/>' % (cx3, td, cx3, st_top))
    o.append('<line x1="%g" y1="%g" x2="%g" y2="%g" %s/>' % (cx3 - 50, dsk_top, cx3 - 12, dsk_top, ext))
    o.append('<line x1="%g" y1="%g" x2="%g" y2="%g" %s/>' % (cx3 + 3, st_top, cx3 + 52, st_top, ext))
    vdim(cx3 + 48, st_top, ground, "G")
    vdim(cx3 - 46, dsk_top, ground, "H", side=-1)
    hdim(cx3 - sp, cx3 + sp, ground + 8, "J")
    o.append('<text x="%g" y="251" %s>MD ON THE CRANK TRIPOD</text>' % (cx3 - 6, cap))
    o.append("</svg>")
    return "\n".join(o)


# ---------------------------------------------------------------- shared values
V = dict(
    name=NAME, md=MD_CODE, hb=HB_CODE, pend0=PENDING[0], pend1=PENDING[1],
    foot=C.FOOT, custom=C.CUSTOM, proj=PROJ, hdr=C.hdr(TITLE, SERIES),
    w=W, lpw=LPW, lm_md="{:,}".format(LM_MD), lm_hb="{:,}".format(LM_RATED),
    beam="%.0f" % BEAM, i0="{:,.0f}".format(I0), peak="{:,.0f}".format(PEAK),
    up="%.1f" % UP, down="%.1f" % DOWN, wtest="%.1f" % D["watts"],
    amb="%s to %s" % (f_c(AMB[0]), f_c(AMB[1])),
    md_d=in_mm(MD_D), md_hd=in_mm(MD_HDISK), md_ht=in_mm(MD_HTOT), md_tube=in_mm(MD_TUBE),
    hb_d=in_mm(HB_D), hb_hb=in_mm(HB_HBODY), hb_ht=in_mm(HB_HTOT), hb_w=lb_kg(HB_KG),
    st_h=ftin_m(ST_H, "4"), st_tot=ftin_m(ST_TOT, "4.24"),
    st_sp='%s to %s<br><span class="mm">(1.3 to 1.8 m)</span>' % (ftin(ST_S0), ftin(ST_S1)),
    st_w=lb_kg(ST_KG), st_load=lb_kg(ST_LOAD), hb_sup=lb_kg(HB_SUPPORT_KG), chain=ft_m(CHAIN_MM),
    md_cord=ft_m(MD_CORD_MM), st_h_short=ftin(ST_H),
    d_short=inch(MD_D),
    c1=ft_m(304.8), c5=ft_m(1524), c3=ft_m(914.4), c20=ft_m(6096),
    ies_date="2024-08-16",
)

# ---------------------------------------------------------------- page 1  cover
P1 = """
<section class="page">
  <div class="side"><div class="vt">LED CONNECTION &nbsp;&middot;&nbsp; PORTABLE LED AREA LIGHT &nbsp;&middot;&nbsp; 300 W</div><img src="assets/logo_side_w.png" alt=""></div>
  <div class="proj">%(proj)s</div>
  <img src="assets/hst_md_stand.png" alt="LC HOIST MD on the crank tripod" style="position:absolute;left:1.55in;top:.55in;height:4.45in;width:auto">
  <img src="assets/hst_hb.png" alt="LC HOIST HB portable high bay" style="position:absolute;left:3.95in;top:2.05in;width:3.15in;height:auto">
  <div style="position:absolute;left:1.25in;right:1.3in;top:5.1in;text-align:center;font-size:6.8pt;color:#7a7e8c">Left: LC-HST-MD on the optional 13 ft crank tripod. Right: LC-HST-HB portable high bay with hook and plug.</div>
  <div class="badges" style="top:1.05in">
    <div class="tbadge">ETL<br>LISTED<i>SEE LISTING NOTE</i></div>
    <div class="tbadge">IP65<i>INDOOR + OUTDOOR</i></div>
    <div class="tbadge">IK08<i>5 JOULE IMPACT</i></div>
    <div class="tbadge">100-277<br>VAC<i>50/60 HZ</i></div>
    <div class="tbadge">2700K TO<br>6500K<i>CRI 80+</i></div>
  </div>
  <div class="cv">
    <div class="kick">PORTABLE 300 W LED AREA LIGHT &middot; STAND OR HOOK</div>
    <div class="big">%(name)s</div>
    <div class="rule"></div>
    <div class="lpw">300 W &middot; %(lpw)d LM/W &middot; IP65</div>
    <div class="tag">MOBILE DISK ON A 13 FT CRANK TRIPOD OR HOOK-HUNG HIGH BAY &middot; 100-277 VAC &middot; PLUG-IN &middot; ALUMINUM HOUSING &middot; IK08</div>
    <div class="strip">
      <div><small>WATTAGE</small><span>300 W</span></div>
      <div><small>LUMENS, MD</small><span>%(lm_md)s lm<br><em class="sm">tested, 5000K</em></span></div>
      <div><small>LUMENS, HB</small><span>%(lm_hb)s lm<br><em class="sm">rated</em></span></div>
      <div><small>CCT</small><span>2700K to<br>6500K</span></div>
      <div><small>DISK</small><span>%(d_short)s<br><em class="sm">(400 mm) dia.</em></span></div>
      <div><small>STAND</small><span>to %(st_h_short)s<br><em class="sm">(4 m), MD</em></span></div>
    </div>
    <div class="pn">ORDERING CODES &nbsp;<b>%(md)s</b> &nbsp;&middot;&nbsp; <b>%(hb)s</b></div>
    <div class="callout">
      <h4>ONE 300 W DISK, TWO WAYS TO SET IT UP</h4>
      <p>A 15.7 in round aluminum LED disk for light that has to move with the job. The MD rides a hand-crank tripod up to
         13 ft; the HB hangs from its hook like a high bay. Both plug in, run on 100-277 VAC and are rated IP65 for
         indoor and outdoor use.</p>
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
    <img class="hero2" src="assets/hst_md_head.png" alt="" style="width:2.35in;height:auto;top:.15in;right:0">
    <div class="wrapn">
      <div class="h1">PORTABLE 300 W LED AREA LIGHT &middot; STAND OR HOOK</div>
      <div class="big" style="font-size:28pt">%(name)s</div>
      <div class="code">%(md)s<small>Mobile LED disk, crank tripod or hook &middot; 300 W &middot; %(lm_md)s lm tested at 5000K</small></div>
      <div class="code" style="margin-top:.06in">%(hb)s<small>Portable high bay, hook and plug &middot; 300 W &middot; %(lm_hb)s lm rated</small></div>
      <div class="icons">
        <div class="dim0"><span>POWER</span><span>300 W</span></div>
        <div class="dim0"><span>RATING</span><span>IP65</span></div>
        <div class="dim0"><span>IMPACT</span><span>IK08</span></div>
        <div class="dim0"><span>CRI</span><span>80+</span></div>
        <div class="dim0"><span>INPUT</span><span>100-277</span><span>VAC</span></div>
      </div>
    </div>
    <div class="hl"><h4>BUILT TO BE MOVED</h4>
      <p>Set the MD on its tripod, crank it up to 13 ft and plug it in. Need it overhead instead? The HB hangs from a
         ceiling hook or chain and plugs into an outlet. No hardwiring either way.</p></div>

    <div class="sec"><h3>PRODUCT DESCRIPTION</h3></div>
    <p class="txt">LC HOIST is a portable 300 W LED area light for sites where the lighting moves with the work. The light
      engine sits in a 15.7 in (400 mm) round, passively cooled aluminum disk, sealed to IP65 and rated IK08 against
      impact. It comes in two set-ups: the MD mounts on a post adapter and a hand-crank tripod for
      free-standing area light, and the HB hangs from its hook as a temporary high bay. Both run on 100-277 VAC and are
      ordered in one colour temperature from 2700K to 6500K.</p>

    <div class="sec"><h3>OVERVIEW</h3></div>
    <ul class="ov two">
      <li>300 W; %(lm_md)s lm tested (MD, 5000K)</li>
      <li>%(lpw)d lm/W rated</li>
      <li>100-277 VAC, 50/60 Hz; power factor 0.9 or higher</li>
      <li>THD below 20 percent</li>
      <li>CCT 2700K to 6500K, CRI 80+</li>
      <li>Wide %(beam)s&deg; distribution (MD, tested)</li>
      <li>IP65; IK08 (5 J); indoor and outdoor</li>
      <li>Operating ambient %(amb)s</li>
      <li>Rated life 50,000 h</li>
      <li>Aluminum housing; plug-in power</li>
      <li>MD: crank tripod to %(st_h)s</li>
      <li>HB: hook with safety chain, %(hb_w)s</li>
    </ul>

    <div class="sec"><h3>APPLICATIONS</h3></div>
    <ul class="ov two">
      <li>Construction and building sites</li>
      <li>Plant shutdowns and maintenance work</li>
      <li>Warehouses and workshops, temporary high bay</li>
      <li>Events, staging and outdoor venues</li>
      <li>Emergency response and rescue staging areas</li>
      <li>Industrial and utility work at night</li>
    </ul>

    <div class="sec"><h3>TWO SET-UPS</h3></div>
    <div class="twocol">
      <div class="pcard" style="display:flex;gap:.12in;align-items:center">
        <img src="assets/hst_md_stand.png" alt="" style="height:1.55in;width:auto">
        <div><h6>LC-HST-MD &middot; MOBILE DISK</h6><div class="sub" style="font-size:6.9pt;line-height:1.45;color:#454857">Post adapter
          supplied for stand mounting; hook and safety chain supplied for hanging. Optional 13 ft hand-crank tripod with guy cables,
          and a rolling carrying case.</div></div>
      </div>
      <div class="pcard" style="display:flex;gap:.12in;align-items:center">
        <img src="assets/hst_hb_side.png" alt="" style="width:1.6in;height:auto">
        <div><h6>LC-HST-HB &middot; PORTABLE HIGH BAY</h6><div class="sub" style="font-size:6.9pt;line-height:1.45;color:#454857">Hook,
          safety chain and bag supplied. Hangs from a hook or support rated for %(hb_sup)s or more; plugs into an outlet.</div></div>
      </div>
    </div>
  </div>
  %(foot)s
</section>
"""

# ---------------------------------------------------------------- page 3  order + specifications
P3 = """
<section class="page">
  %(hdr)s
  <div class="body" style="top:.85in">
    <div class="sec" style="margin-top:.1in"><h3>ORDER LOGIC</h3></div>
    <div class="olx">The LED Connection ordering code. Segment 01 is always LC. Choose one colour temperature for segment 06.</div>
    <div class="sample"><small>SAMPLE CODE</small>
      <div class="segs">
        <div class="sg"><span class="o">LC</span><i>[01]</i></div><span class="dash">-</span>
        <div class="sg"><span class="o">HST</span><i>[02]</i></div><span class="dash">-</span>
        <div class="sg"><span>MD</span><i>[03]</i></div><span class="dash">-</span>
        <div class="sg"><span>300W</span><i>[04]</i></div><span class="dash">-</span>
        <div class="sg"><span>NV</span><i>[05]</i></div><span class="dash">-</span>
        <div class="sg"><span class="o">50K</span><i>[06]</i></div>
      </div>
    </div>
    <div class="cards" style="grid-template-columns:repeat(6,1fr)">
      <div class="card"><h5>01 BRAND</h5><div><b>LC</b>LED Connection</div></div>
      <div class="card"><h5>02 SERIES</h5><div><b>HST</b>LC HOIST portable area light</div></div>
      <div class="card"><h5>03 TYPE</h5><div><b>MD</b>Mobile disk, stand or hook<div class="op"><b>HB</b>Portable high bay, hook</div></div></div>
      <div class="card"><h5>04 WATTS</h5><div><b>300W</b>300 W<div class="op"><b>450W</b>Pending, see note</div></div></div>
      <div class="card"><h5>05 VOLTAGE</h5><div><b>NV</b>100-277 VAC, 50/60 Hz</div></div>
      <div class="card"><h5>06 CCT (XXK)</h5><div><b>27K to 65K</b>Two digits + K: 27K = 2700K, 50K = 5000K, 65K = 6500K. Range 2700K to 6500K.</div></div>
    </div>

    <div class="sec"><h3>ORDERING CODES</h3></div>
    <table class="ord">
      <tr><th style="width:29%%">ORDERING CODE</th><th>TYPE</th><th>MOUNTING</th><th class="c">POWER</th><th class="c">LUMENS</th><th class="c">CCT</th></tr>
      <tr><td class="k">%(md)s</td><td>Mobile LED disk</td><td>Tripod stand or hook</td><td class="c">300 W</td><td class="c">%(lm_md)s lm, tested</td><td class="c">2700K to 6500K</td></tr>
      <tr><td class="k">%(hb)s</td><td>Portable high bay</td><td>Hook and safety chain</td><td class="c">300 W</td><td class="c">%(lm_hb)s lm, rated</td><td class="c">2700K to 6500K</td></tr>
    </table>
    <div class="note"><b>Pending, not yet released:</b> %(pend0)s and %(pend1)s, the 450 W versions. Data for them is issued separately.</div>

    <div class="sec"><h3>SPECIFICATIONS</h3></div>
    <table class="spec">
      <tr><th style="width:24%%">ITEM</th><th style="width:38%%">LC-HST-MD &middot; MOBILE DISK</th><th>LC-HST-HB &middot; PORTABLE HIGH BAY</th></tr>
      <tr class="grp"><td colspan="3">PERFORMANCE</td></tr>
      <tr><td class="k">Input power</td><td>300 W</td><td>300 W</td></tr>
      <tr><td class="k">Delivered lumens</td><td>%(lm_md)s lm, factory photometric test at 5000K</td><td>%(lm_hb)s lm, rated</td></tr>
      <tr><td class="k">Efficacy</td><td colspan="2">%(lpw)d lm/W, rated</td></tr>
      <tr><td class="k">Colour temperature</td><td colspan="2">2700K to 6500K, one CCT per order (segment 06)</td></tr>
      <tr><td class="k">CRI</td><td colspan="2">80+</td></tr>
      <tr><td class="k">Beam angle</td><td>%(beam)s&deg; (50 percent of peak), tested</td><td>Not tested</td></tr>
      <tr><td class="k">Rated life</td><td colspan="2">50,000 h</td></tr>
      <tr class="grp"><td colspan="3">ELECTRICAL</td></tr>
      <tr><td class="k">Input voltage</td><td colspan="2">100-277 VAC, 50/60 Hz (NV)</td></tr>
      <tr><td class="k">Power factor</td><td colspan="2">0.9 or higher</td></tr>
      <tr><td class="k">THD</td><td colspan="2">Below 20 percent</td></tr>
      <tr><td class="k">Power connection</td><td>%(md_cord)s SJTW 18 AWG 3-conductor cord, 105 C, 300 V, with US plug</td>
          <td>STW (SOOW) 14 AWG 3-conductor cable, 105 C, 600 V; M19 waterproof connectors; three-pin plug; leads on page 4</td></tr>
      <tr class="grp"><td colspan="3">PHYSICAL AND ENVIRONMENT</td></tr>
      <tr><td class="k">Housing</td><td>Aluminum; opal lens</td><td>Aluminum and PC</td></tr>
      <tr><td class="k">Mounting</td><td>Post adapter on tripod stand, or hook</td><td>Hook, with safety chain</td></tr>
      <tr><td class="k">Ingress / impact</td><td colspan="2">IP65 / IK08 (5 J)</td></tr>
      <tr><td class="k">Location</td><td>Indoor and outdoor</td><td>Wet location</td></tr>
      <tr><td class="k">Operating ambient</td><td colspan="2">%(amb)s</td></tr>
      <tr><td class="k">Listing</td><td colspan="2">ETL listed (multiple listing for LED Connection in progress)</td></tr>
    </table>
  </div>
  %(foot)s
</section>
"""

# ---------------------------------------------------------------- page 4  dimensions, accessories, cables
P4 = """
<section class="page">
  %(hdr)s
  <div class="body" style="top:.85in">
    <div class="sec" style="margin-top:.1in"><h3>DIMENSIONS</h3></div>
    <div style="width:6.3in;margin:0 auto">%(dims)s</div>
    <div class="note" style="text-align:right;margin-top:0">Drawing is schematic, not to one scale; dimensions govern.</div>
    <div class="twocol" style="margin-top:.06in;align-items:start">
      <table>
        <tr><th style="width:11%%">REF</th><th style="width:45%%">LC-HST-MD</th><th class="c">US (METRIC)</th></tr>
        <tr><td class="k">A</td><td>Disk diameter</td><td class="c">%(md_d)s</td></tr>
        <tr><td class="k">B</td><td>Disk height</td><td class="c">%(md_hd)s</td></tr>
        <tr><td class="k">C</td><td>Height on post adapter</td><td class="c">%(md_ht)s</td></tr>
        <tr><td class="k">-</td><td>Mounting tube diameter</td><td class="c">%(md_tube)s</td></tr>
        <tr><td class="k">G</td><td>Tripod, maximum height</td><td class="c">%(st_h)s</td></tr>
        <tr><td class="k">H</td><td>Overall, disk on tripod</td><td class="c">%(st_tot)s</td></tr>
        <tr><td class="k">J</td><td>Tripod leg spread</td><td class="c">%(st_sp)s</td></tr>
        <tr><td class="k">-</td><td>Tripod weight</td><td class="c">%(st_w)s</td></tr>
        <tr><td class="k">-</td><td>Tripod maximum load</td><td class="c">%(st_load)s</td></tr>
      </table>
      <table>
        <tr><th style="width:11%%">REF</th><th style="width:45%%">LC-HST-HB</th><th class="c">US (METRIC)</th></tr>
        <tr><td class="k">D</td><td>Disk diameter</td><td class="c">%(hb_d)s</td></tr>
        <tr><td class="k">E</td><td>Body height</td><td class="c">%(hb_hb)s</td></tr>
        <tr><td class="k">F</td><td>Overall height with hook</td><td class="c">%(hb_ht)s</td></tr>
        <tr><td class="k">-</td><td>Weight</td><td class="c">%(hb_w)s</td></tr>
        <tr><td class="k">-</td><td>Support to carry at least</td><td class="c">%(hb_sup)s</td></tr>
        <tr><td class="k">-</td><td>Safety chain</td><td class="c">%(chain)s</td></tr>
      </table>
    </div>

    <div class="twocol">
      <div>
        <div class="sec"><h3 style="min-width:0;width:100%%">ACCESSORIES</h3></div>
        <table>
          <tr><th style="width:52%%">ITEM</th><th class="c">MD</th><th class="c">HB</th></tr>
          <tr><td class="k">Hook, for hanging</td><td class="c">Supplied</td><td class="c">Supplied</td></tr>
          <tr><td class="k">Safety chain</td><td class="c">Supplied</td><td class="c">Supplied</td></tr>
          <tr><td class="k">Post adapter, for stand mounting</td><td class="c">Supplied</td><td class="c">-</td></tr>
          <tr><td class="k">Carry bag</td><td class="c">Supplied</td><td class="c">Supplied</td></tr>
          <tr><td class="k">13 ft hand-crank tripod</td><td class="c">Option</td><td class="c">-</td></tr>
          <tr><td class="k">Tripod guy cable set</td><td class="c">Option</td><td class="c">-</td></tr>
          <tr><td class="k">Rolling carrying case</td><td class="c">Option</td><td class="c">-</td></tr>
        </table>
        <div class="note">Ceiling hooks and hanging chains for the HB are not included. Supplied items are confirmed on the order
          acknowledgement.</div>
      </div>
      <div>
        <div class="sec"><h3 style="min-width:0;width:100%%">HB CABLE SYSTEM</h3></div>
        <table class="cab">
          <tr><th style="width:27%%">LEAD</th><th>ENDS</th><th class="c" style="width:27%%">LENGTH</th></tr>
          <tr><td class="k">Plug lead</td><td>Three-pin plug to M19 female</td><td class="c">%(c1)s</td></tr>
          <tr><td class="k">Tee lead, linking</td><td>M19 male to M19 female, drop to M19 female</td><td class="c">%(c5)s<br>drop %(c3)s</td></tr>
          <tr><td class="k">Extension lead</td><td>M19 male to M19 female</td><td class="c">%(c20)s</td></tr>
          <tr><td class="k">Outlet lead</td><td>M19 male to three-pin receptacle</td><td class="c">%(c1)s</td></tr>
        </table>
        <div class="note">All leads STW (SOOW) 14 AWG, 3-conductor, 105 C, 600 V, with M19 three-core waterproof connectors.</div>
      </div>
    </div>
  </div>
  %(foot)s
</section>
"""

# ---------------------------------------------------------------- page 5  photometry, set-up, notes
P5 = """
<section class="page">
  %(hdr)s
  <div class="body" style="top:.85in">
    <div class="sec" style="margin-top:.1in"><h3>PHOTOMETRY &middot; LC-HST-MD</h3></div>
    <div class="band" style="margin-top:0"><b>Factory photometric test of the MD at 5000K,</b> %(ies_date)s, test voltage 216.5 VAC,
      %(wtest)s W measured. %(lm_md)s lm delivered; %(down)s percent of the light goes down, %(up)s percent up.
      Values for other colour temperatures, and for the HB, have not been tested.</div>
    <div class="twocol" style="margin-top:.1in;grid-template-columns:1fr 1.15fr">
      <div class="pcard"><h6>POLAR DISTRIBUTION</h6><div class="sub">0-180 and 90-270 deg planes, nadir at bottom; 100 percent = %(peak)s cd</div><div class="pw" style="height:2.75in">%(polar)s</div></div>
      <div>
        <table>
          <tr><th style="width:30%%">MOUNTING HEIGHT</th><th class="c">CENTRE ILLUMINANCE</th><th class="c">BEAM DIAMETER, %(beam)s&deg;</th></tr>
          %(illum)s
        </table>
        <div class="note">Centre illuminance directly below the disk, from the nadir intensity (%(i0)s cd) of the test file,
          disk level and aimed straight down. Beam diameter is where the light falls to 50 percent of peak. Mounting height is
          measured to the lens; on the tripod the lens sits below the overall height H.</div>
      </div>
    </div>

    <div class="twocol">
      <div>
        <div class="sec"><h3 style="min-width:0;width:100%%">SET-UP, MD ON THE TRIPOD</h3></div>
        <ul class="ov">
          <li>Open the legs fully on level ground and lock every wing nut.</li>
          <li>Fit the disk on the post adapter at the top of the column and lock it.</li>
          <li>Turn the crank clockwise to raise the column, counterclockwise to lower it; lock at height.</li>
          <li>Guy the tripod with the safety cables to the ground stakes, always, outdoors or in wind.</li>
          <li>Keep the load within %(st_load)s.</li>
        </ul>
        <div class="sec"><h3 style="min-width:0;width:100%%">SET-UP, HB</h3></div>
        <ul class="ov">
          <li>Screw the lifting hook firmly into the disk.</li>
          <li>Hang from a hook or support rated for %(hb_sup)s or more and close the spring clip.</li>
          <li>Fit the safety chain as a second support, then plug in.</li>
        </ul>
      </div>
      <div>
        <div class="sec"><h3 style="min-width:0;width:100%%">CERTIFICATION</h3></div>
        <table>
          <tr><td class="k" style="width:38%%">Safety listing</td><td>ETL listed (multiple listing for LED Connection in progress)</td></tr>
          <tr><td class="k">Ingress</td><td>IP65</td></tr>
          <tr><td class="k">Impact</td><td>IK08 (5 J)</td></tr>
          <tr><td class="k">Location</td><td>MD indoor and outdoor; HB wet location</td></tr>
        </table>
        <div class="sec"><h3 style="min-width:0;width:100%%">NOTES</h3></div>
        <ul class="ov">
          <li>Installation and servicing by qualified personnel. Power off before maintenance.</li>
          <li>Proper grounding is required; use a grounded outlet.</li>
          <li>Clean the lens regularly; no harsh solvents.</li>
          <li>Specifications may change without notice.</li>
        </ul>
      </div>
    </div>
  </div>
  %(custom)s
  %(foot)s
</section>
"""

EXTRA_CSS = """
.mm { font-size:.86em; color:#7a7e8c; font-weight:400; }
em.sm { font-style:normal; font-weight:500; font-size:6.8pt; color:#5d6170; }
table.spec tr.grp td { background:#fdeee5; color:var(--ink); font-weight:800; font-size:6.6pt; letter-spacing:.06em; padding:.035in .08in; }
table.spec td { padding:.022in .08in; line-height:1.3; }
table.spec tr.grp td { padding:.025in .08in; }
table.ord td { white-space:nowrap; }
table.cab td.c { white-space:nowrap; }
"""


def build():
    v = dict(V)
    v.update(dims=dims_svg(), polar=polar(), illum=illum_rows())
    v["custom"] = C.CUSTOM
    pages = [P1 % v, P2 % v, P3 % v, P4 % v, P5 % v]
    C.CSS = C.CSS + EXTRA_CSS
    html = C.doc("LED Connection spec sheet LC-HST", pages)
    path = os.path.join(HERE, "hoist.html")
    open(path, "w", encoding="utf-8").write(html)
    hits = C.leak_check("LC-HST", html)
    pdf = C.to_pdf(path, PDF_NAME)
    C.strip_metadata(pdf, "LED Connection Spec Sheet LC-HST", "LED Connection LC HOIST portable LED area light specification")
    return pdf, hits


if __name__ == "__main__":
    print("IES MD 5000K: %.1f W, %.0f lm (sheet %d), peak %.0f cd, nadir %.0f cd, beam %.1f, field %.1f, down %.1f%%"
          % (D["watts"], LM_TEST, LM_MD, PEAK, I0, BEAM, FIELD, DOWN))
    pdf, hits = build()
    print(pdf, hits)
    print("pdf_text_check:", C.pdf_text_check(pdf))
    for f in C.preview(pdf):
        print(f)
