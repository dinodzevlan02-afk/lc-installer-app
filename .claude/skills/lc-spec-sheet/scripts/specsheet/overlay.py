"""
Template-overlay renderer: the LC-TP PDF is the canvas.

    python specsheet/overlay.py <sheet.json>      (the dict rebrand.py builds)

Why this exists instead of the HTML renderer
--------------------------------------------
Two HTML/CSS attempts approximated the LC design and Dino rejected both. The
sheets he DID accept (his Sep-9 chat) were made the other way round: the
template PDF's own vector furniture - navy rail, wordmark, header strip,
section bars, callout boxes, footer - was kept exactly as drawn, the
Triproof-specific text and photos were redacted out of the content stream,
and new content was set into the same boxes in Poppins. Nothing is
approximated because nothing is redrawn that did not need redrawing.

How
---
1. Copy the template page into the new document as a vector XObject.
2. Before that, redact the regions holding Triproof content (text always;
   images and graphics only where the region is theirs, e.g. the cert
   badges, the product photo, the dimension drawings, the segment columns).
3. Insert our text into the same rectangles, same weights, same sizes.
4. Redraw only what is genuinely variable in shape: the order-logic segment
   columns (their count depends on our SKU) and the electrical table rows.

Coordinates are in PDF points on a 612 x 792 Letter page, measured off a
110-dpi render of the template (1 px = 0.6545 pt).
"""

import io, json, os, sys, tempfile, shutil, time

import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "assets", "template_LC-TP.pdf")
FONTS = os.path.join(HERE, "assets", "fonts")

NAVY = (0.102, 0.102, 0.180)      # #1A1A2E - side bar and footer
ORANGE = (0.957, 0.482, 0.125)    # #F47B20
GREY = (0.957, 0.957, 0.957)      # #F4F4F4 segment bodies
CREAM = (0.992, 0.941, 0.902)     # #FDF0E6 callouts
INK = (0.10, 0.10, 0.10)
MUTE = (0.36, 0.38, 0.44)
WHITE = (1, 1, 1)

PX = 612.0 / 935.0  # render-pixel -> point


def R(x0, y0, x1, y1):
    """Rect from 110-dpi render pixels."""
    return pymupdf.Rect(x0 * PX, y0 * PX, x1 * PX, y1 * PX)


# --------------------------------------------------------------------- fonts
class Fonts:
    """Poppins if a FULL family is present in assets/fonts/full/, otherwise
    Helvetica. The template's embedded Poppins is only a subset - it has the
    glyphs the Triproof sheet used and nothing else - so setting new copy in
    it would print .notdef boxes for any letter the template never needed."""

    def __init__(self, page):
        self.page = page
        full = os.path.join(FONTS, "full")
        want = {"black": "Poppins-Black.ttf", "bold": "Poppins-Bold.ttf",
                "semi": "Poppins-SemiBold.ttf", "med": "Poppins-Medium.ttf",
                "light": "Poppins-Light.ttf", "ital": "Poppins-LightItalic.ttf"}
        self.names = {}
        self.metrics = {}
        self.poppins = all(os.path.exists(os.path.join(full, f)) for f in want.values())
        if self.poppins:
            for k, f in want.items():
                page.insert_font(fontname="P" + k, fontfile=os.path.join(full, f))
                self.names[k] = "P" + k
                self.metrics[k] = pymupdf.Font(fontfile=os.path.join(full, f))
        else:
            fb = {"black": "hebo", "bold": "hebo", "semi": "hebo", "med": "helv",
                  "light": "helv", "ital": "heit"}
            self.names = fb
            for k, v in fb.items():
                self.metrics[k] = pymupdf.Font(fontname=v)

    def __getitem__(self, k):
        return self.names[k]


def drawn_bottom(page, rect, fallback):
    """Lowest glyph bottom actually rendered inside `rect`, in DESIGN pixels.

    Laying out below a block of text needs to know where that text really ended.
    Predicting it from the string is what went wrong twice here: first by
    counting characters (`165 if len(fam) > 18 else 172`), then by arithmetic on
    size x lineheight - which is wrong in this file because rects are design
    pixels scaled by PX while fontsize is passed through in points, so the two
    are not in the same unit. Measuring after the fact is immune to the wrap,
    to the shrink-to-fit in text(), and to that unit mismatch."""
    d = page.get_text("dict", clip=rect)
    ys = [s["bbox"][3] for b in d.get("blocks", [])
          for l in b.get("lines", []) for s in l.get("spans", [])]
    return (max(ys) / PX) if ys else fallback


def text(page, F, rect, s, weight="med", size=9, color=INK, align=0, lh=1.25):
    """Insert text into rect; shrink the size until it fits rather than
    overflow into a neighbour's box."""
    if not s:
        return
    # Step down gradually to a floor of 60% of the requested size. The first
    # version tried five steps and then dropped to 4.5pt - a 34pt title that
    # missed by a point came out as fine print.
    sz = float(size)
    floor = max(5.0, size * 0.6)
    while sz >= floor:
        rc = page.insert_textbox(rect, s, fontname=F[weight], fontsize=sz,
                                 color=color, align=align, lineheight=lh)
        if rc >= 0:
            return sz          # the size actually used, so callers can lay out below it
        sz -= 0.5
    page.insert_textbox(rect, s, fontname=F[weight], fontsize=floor, color=color,
                        align=align, lineheight=lh)
    return floor


def clear(page, rects, images=False, graphics=False):
    """Redact regions out of the content stream - not paint over them."""
    for r in rects:
        page.add_redact_annot(r)
    page.apply_redactions(images=1 if images else 0,
                          graphics=2 if graphics else 0,
                          text=0)  # text=0 -> remove text (pymupdf enum)


def import_page(tpl, pno, clears):
    """Return a fresh single-page doc holding the cleaned template page."""
    src = pymupdf.open(TEMPLATE)
    tp = src[pno]
    for rects, imgs, gfx in clears:
        clear(tp, rects, images=imgs, graphics=gfx)
    return src


# -------------------------------------------------------------------- badges
# The template's badge row (p2, y 325-380 px) is three designed pictograms, not
# rings with words in them. Where a feature matches one of them exactly, the
# template's own vector artwork is placed as a clip - identical to the
# reference by construction. Anything else is drawn in the same idiom: an
# orange ring, one large token in the middle, a tiny caps label beneath.
TEMPLATE_BADGES = {
    # (match test on the badge text)          -> clip rect on template page 2
    "dimming 1-10v": R(48, 322, 102, 384),
    "5 year":        R(106, 322, 162, 384),
    "sensor":        R(162, 318, 218, 388),
}


def draw_badges(page, F, badges, cy):
    tpl = pymupdf.open(TEMPLATE)
    for i, b in enumerate(badges):
        cx = (80 + i * 72)
        key = b.lower()
        hit = next((clip for k, clip in TEMPLATE_BADGES.items() if k in key), None)
        if hit:
            page.show_pdf_page(R(cx - 27, cy - 31, cx + 27, cy + 31), tpl, 1, clip=hit)
            continue

        c = pymupdf.Point(cx * PX, cy * PX)
        r = 26 * PX
        page.draw_circle(c, r, color=ORANGE, width=1.5)

        parts = b.split(None, 1)
        if parts and parts[0].isdigit():
            # "5 FINISHES" -> big 5, small FINISHES - the warranty rosette's idiom
            # number large and centred, label tucked directly beneath it - the
            # rosette's "5 / YEARS" spacing, not a digit floating at the top
            text(page, F, pymupdf.Rect(c.x - r, c.y - 11, c.x + r, c.y + 6),
                 parts[0], "black", 15, INK, 1, lh=1.0)
            text(page, F, pymupdf.Rect(c.x - r + 3, c.y + 5, c.x + r - 3, c.y + 13),
                 (parts[1] if len(parts) > 1 else "").upper(), "semi", 4.3, NAVY, 1)
        elif "recess" in key:
            # a recessed louvered face: frame + three louvre lines
            x0, y0 = c.x - 9, c.y - 9
            page.draw_rect(pymupdf.Rect(x0, y0, x0 + 18, y0 + 11), color=NAVY, width=0.9)
            for k in range(3):
                yy = y0 + 2.6 + k * 3.1
                page.draw_line(pymupdf.Point(x0 + 2.2, yy), pymupdf.Point(x0 + 15.8, yy),
                               color=ORANGE, width=0.9)
            text(page, F, pymupdf.Rect(c.x - r + 3, c.y + 4, c.x + r - 3, c.y + 13),
                 "RECESSED", "semi", 4.3, NAVY, 1)
        else:
            text(page, F, pymupdf.Rect(c.x - r + 4, c.y - 7, c.x + r - 4, c.y + 9),
                 b.upper(), "semi", 4.4, NAVY, 1, lh=1.1)


# --------------------------------------------------------------------- pages
def build(sheet, warn, out_path):
    fam = sheet["family"].upper()
    ptype = sheet["product_type"].upper()
    sku = sheet["lc_sku_prefix"]
    cv = sheet["cover"]
    doc = pymupdf.open()

    # ------------------------------------------------------------ COVER (p1)
    # keep: rail, wordmark top-right, circuit traces, orange title rule,
    #       callout box, "For custom solutions" line, footer bar + text
    # clear: rail text, hero photo (image), product type, family name,
    #        efficacy, subtitle, six spec values, callout text, cert badges
    tp = pymupdf.open(TEMPLATE)[0]
    clear(tp, [R(30, 800, 62, 1100)])                                   # rail text
    clear(tp, [R(110, 120, 935, 585)], images=True)                     # hero photo
    clear(tp, [R(112, 595, 700, 780), R(112, 805, 700, 895)])           # type/title/eff/sub
    clear(tp, [R(112, 920, 900, 1000)])                                 # spec strip values
    clear(tp, [R(135, 1035, 890, 1105)])                                # callout text
    clear(tp, [R(830, 590, 900, 760)], graphics=True)                   # TAA/FCC/UL marks

    page = doc.new_page(width=612, height=792)
    page.show_pdf_page(page.rect, tp.parent, 0)
    F = Fonts(page)

    # rail text (rotated) - draw with a matrix
    rail = "LED CONNECTION - %s" % fam
    page.insert_text(pymupdf.Point(52 * PX, 1090 * PX), rail, fontname=F["bold"],
                     fontsize=6.3, color=ORANGE, rotate=90)

    # hero
    hero = sheet.get("hero_png")
    if hero and os.path.exists(hero):
        # stops short of the pre-release band, which sits at 470-585 when present;
        # with no band (Dino, 2026-10-21: "remove this red banner") it takes that room too
        page.insert_image(R(230, 150, 800, 455 if warn else 575), filename=hero, keep_proportion=True)
    else:
        text(page, F, R(300, 330, 740, 360), "PRODUCT PHOTOGRAPH", "semi", 8, (.78, .8, .84), 1)

    text(page, F, R(120, 598, 700, 628), ptype, "med", 12.5, MUTE)
    # the template's title slot is two lines tall; a one-line family name sits
    # low in it so it lands just above the orange rule, as the reference does
    ty = 632 if len(fam) > 18 else 700
    text(page, F, R(118, ty, 780, 780), fam, "black", 40, INK, lh=0.92)
    # `headline` is the category-neutral key: LM/W on a luminaire, nits or
    # transparency on a display. headline_efficacy stays valid for old sheets.
    eff = cv.get("headline") or cv.get("headline_efficacy")
    if eff and eff != "-":
        text(page, F, R(120, 808, 600, 852), eff, "black", 21, ORANGE)
    sub = cv.get("subtitle") or cv.get("tagline") or ""
    text(page, F, R(120, 862, 880, 888), sub.upper(), "med", 8.6, MUTE)

    # six spec columns - labels sit at y~930, values at y~955 in the template
    xs = [120, 246, 372, 498, 622, 748]
    keys = list(cv["chips"].items())[:6]
    for (k, v), x in zip(keys, xs):
        text(page, F, R(x, 926, x + 118, 940), k.upper(), "semi", 6.2, ORANGE)
        text(page, F, R(x, 946, x + 118, 992), str(v), "bold", 12.5, INK)

    text(page, F, R(148, 1042, 880, 1058), cv["tagline"].upper(), "bold", 9.4, INK)
    text(page, F, R(148, 1062, 880, 1102), cv["positioning"], "light", 8.8, INK, lh=1.3)

    # pre-release band sits over the hero's lower third, deliberately visible
    if warn:
        band = R(130, 470, 900, 585)
        page.draw_rect(band, color=None, fill=(0.54, 0.11, 0.11))
        text(page, F, R(145, 478, 890, 494), "PRE-RELEASE - NOT FOR DISTRIBUTION", "bold", 8.6, WHITE)
        text(page, F, R(145, 496, 890, 582), "\n".join("- " + w for w in warn), "light", 6.2, WHITE, lh=1.25)

    # ------------------------------------------------------- PAGE 2 (p2)
    tp = pymupdf.open(TEMPLATE)[1]
    clear(tp, [R(50, 45, 300, 70)])                                     # header title + sku
    clear(tp, [R(50, 135, 470, 300)])                                   # type / title / sku
    clear(tp, [R(45, 315, 230, 390)], graphics=True)                    # feature icons
    clear(tp, [R(540, 140, 900, 340)], images=True)                     # product photo
    clear(tp, [R(70, 430, 880, 475)])                                   # callout text
    clear(tp, [R(50, 555, 890, 670)])                                   # description
    clear(tp, [R(50, 730, 700, 945)])                                   # bullets
    clear(tp, [R(60, 1000, 900, 1140)], graphics=True)                  # dimension drawings
    page = doc.new_page(width=612, height=792)
    page.show_pdf_page(page.rect, tp.parent, 1)
    F = Fonts(page)

    head = "%s - %s" % (ptype, fam)
    text(page, F, R(55, 50, 240, 64), head, "bold", 6.6, ORANGE)
    text(page, F, R(255, 50, 400, 64), sku, "light", 6.6, MUTE)
    text(page, F, R(55, 140, 470, 162), ptype, "med", 10.5, MUTE)
    # Poppins Black needs ~46pt of box for a 34pt line; 60px was Helvetica-sized
    title_rect = R(53, 165, 560, 315)
    text(page, F, title_rect, fam, "black", 34, INK, lh=0.92)
    # SKU sits below the title's REAL last line, measured off the page. A
    # three-word family wraps to two lines and the old character-count rule
    # printed the orange SKU straight through the second one.
    tb = drawn_bottom(page, title_rect, 224)
    sku_rect = R(55, tb + 10, 400, tb + 38)
    text(page, F, sku_rect, sku, "black", 12.5, ORANGE)

    # Badges hang off the SKU's measured bottom, keep the template's own row as a
    # floor, and are NEVER allowed to run into the cream callout below - its top
    # edge is at design y 424.7, read off the template rather than guessed.
    # A badge is 31 design px each side of its centre.
    sb = drawn_bottom(page, sku_rect, tb + 30)
    CALLOUT_TOP, BADGE_R = 424.7, 31.0
    cy = max(sb + 12 + BADGE_R, 302)
    if cy + BADGE_R <= CALLOUT_TOP - 8:
        draw_badges(page, F, sheet.get("badges", [])[:4], cy=cy)
    elif sheet.get("badges"):
        # No room. Drop the row rather than overlap it: this is an output skill,
        # and a badge sitting on top of the callout is exactly the kind of thing
        # that looks finished and is wrong. Happens when the family name wraps to
        # three lines, which a real LC family name does not.
        print("   note: badge row omitted on page 2 - the family name wraps to "
              "%d lines and leaves no clear space above the callout." %
              max(1, round((tb - 165) / 46)))

    hero = sheet.get("hero_png")
    if hero and os.path.exists(hero):
        page.insert_image(R(600, 150, 885, 315), filename=hero, keep_proportion=True)

    text(page, F, R(77, 434, 870, 449), "QUALITY DEFENDER", "bold", 9.4, INK)
    text(page, F, R(77, 452, 870, 474), sheet.get("quality_line") or cv["positioning"], "light", 8.6, INK)

    text(page, F, R(55, 560, 887, 668), sheet["description"], "light", 8.7, INK, 3, lh=1.32)
    # Bullets are DRAWN, not typed: the template uses small orange squares, and
    # Base14 Helvetica printed "?" for both U+25AA and U+2022 anyway.
    for i, line in enumerate(sheet.get("overview", [])[:10]):
        y0 = 735 + i * 21
        page.draw_rect(R(56, y0 + 7, 60, y0 + 11), color=None, fill=ORANGE)
        text(page, F, R(70, y0, 887, y0 + 21), line, "light", 8.7, INK)

    dims = sheet.get("dimensions") or {}
    if dims:
        xs = [60, 340, 620]
        for (k, v), x in zip(list(dims.items())[:3], xs):
            page.draw_rect(R(x, 1010, x + 260, 1090), color=None, fill=GREY)
            text(page, F, R(x + 14, 1020, x + 250, 1034), k.upper(), "semi", 6.2, ORANGE)
            text(page, F, R(x + 14, 1040, x + 250, 1084), str(v), "bold", 10.5, INK)

    # ------------------------------------------------------- PAGE 3 (p3)
    tp = pymupdf.open(TEMPLATE)[2]
    clear(tp, [R(50, 45, 300, 70)])                                     # header
    clear(tp, [R(50, 140, 890, 160)])                                   # "Build a ... SKU" line
    clear(tp, [R(70, 185, 880, 250)])                                   # sample code text
    # Everything below the sample-code panel is laid out in FLOW. The template
    # fixes the NOTE box, ELECTRICAL DATA bar, table and lumen callout at heights
    # sized for four tall option columns; with two short ones they left a void,
    # and a longer table ran straight through the lumen box. So the region is
    # cleared - graphics included - and redrawn from the columns downward.
    clear(tp, [R(50, 280, 890, 1075)], graphics=True)
    page = doc.new_page(width=612, height=792)
    page.show_pdf_page(page.rect, tp.parent, 2)
    F = Fonts(page)

    text(page, F, R(55, 50, 240, 64), head, "bold", 6.6, ORANGE)
    text(page, F, R(255, 50, 400, 64), sku, "light", 6.6, MUTE)
    text(page, F, R(55, 141, 887, 160), "Build a %s SKU by selecting one option from each segment."
         % sheet["family"], "light", 9.4, INK)

    ol = sheet.get("order_logic") or {}
    code = ol.get("sample_code", "")
    first, rest = (code.split(" - ", 1) + [""])[:2]
    text(page, F, R(75, 186, 400, 198), "SAMPLE CODE", "med", 6.2, WHITE)
    # brand+series in orange, remainder in white
    p1 = pymupdf.Point(75 * PX, 228 * PX)
    # get_text_length only knows Base14 names; a custom-inserted font must be
    # measured from its file.
    if F.poppins:
        # get_text_length() has no fontfile parameter; a custom font is measured
        # through a Font object.
        w1 = pymupdf.Font(fontfile=os.path.join(FONTS, "full", "Poppins-Black.ttf")
                          ).text_length(first + " - ", fontsize=21)
    else:
        w1 = pymupdf.get_text_length(first + " - ", fontname="hebo", fontsize=21)
    page.insert_text(p1, first + " - ", fontname=F["black"], fontsize=21, color=ORANGE)
    page.insert_text(pymupdf.Point(p1.x + w1, p1.y), rest, fontname=F["black"], fontsize=21, color=WHITE)
    marks = "[BRAND]   " + "   ".join("[%s]" % s["n"] for s in ol.get("segments", []) if s["n"] != "01")
    text(page, F, R(75, 233, 700, 246), marks, "med", 6.2, ORANGE)

    segs = [s for s in ol.get("segments", []) if s["n"] != "01"]
    n = max(1, len(segs))
    colw = (835 - 55 - (n - 1) * 8) / n
    # columns are as tall as their longest option list, not the template's
    # fixed 290 px - two options in a full-height column read as an error
    hmax = max([len(s["options"]) for s in segs] or [1])
    bottom = min(572, 322 + hmax * 30 + 14)
    for i, s in enumerate(segs):
        x0 = 55 + i * (colw + 8)
        page.draw_rect(R(x0, 285, x0 + colw, 312), color=None, fill=ORANGE)
        page.draw_rect(R(x0, 312, x0 + colw, bottom), color=None, fill=GREY)
        text(page, F, R(x0 + 10, 291, x0 + colw - 6, 307), "%s %s" % (s["n"], s["name"].upper()), "bold", 7.4, WHITE)
        y = 322
        for code_, desc in s["options"][:9]:
            text(page, F, R(x0 + 10, y, x0 + colw - 6, y + 14), code_, "bold", 7.6, INK)
            text(page, F, R(x0 + 10, y + 13, x0 + colw - 6, y + 27), desc, "light", 7.4, INK)
            y += 30
    text(page, F, R(300, bottom + 16, 887, bottom + 32), "For custom solutions please contact our sales representative.", "ital", 8.2, MUTE, 2)

    e = sheet.get("electrical") or {}

    def secbar(y, label):
        """A section header the way the template draws it: navy bar, white caps,
        thin orange rule running to the right margin."""
        page.draw_rect(R(55, y, 440, y + 30), color=None, fill=NAVY)
        page.draw_rect(R(440, y + 14, 887, y + 16), color=None, fill=ORANGE)
        text(page, F, R(75, y + 8, 430, y + 27), label, "bold", 10.2, WHITE)

    def callout(y, h, title, body, body_weight="light", upper=False):
        page.draw_rect(R(55, y, 887, y + h), color=None, fill=CREAM)
        page.draw_rect(R(55, y, 60, y + h), color=None, fill=ORANGE)
        text(page, F, R(78, y + 8, 870, y + 24), title, "bold", 9.4, INK)
        text(page, F, R(78, y + 26, 870, y + h - 4), body.upper() if upper else body,
             body_weight, 8.3, INK, 0 if upper else 3, lh=1.3)

    y = bottom + 50
    callout(y, 60, "NOTE:", e.get("note") or "", body_weight="med", upper=True)
    y += 60 + 34
    secbar(y, e.get("title") or "ELECTRICAL DATA")
    y += 30 + 22

    cols = e.get("columns", [])
    # Was a flat [:8]. A display's technical table runs to 13 rows and the cut
    # silently dropped peak and average power - the figures LC needs as the
    # electrical contractor. Fit to the space actually available instead, which
    # is larger on a display sheet because the closing callout is skipped.
    room = int((1095 - (y + 32 + 24) - (66 if (sheet.get("callout_body") or
                                               sheet.get("lumen_maintenance") or "").strip() else 0)) / 22)
    rows = e.get("rows", [])[:max(6, room)]
    if cols:
        cw = (880 - 55) / len(cols)
        page.draw_rect(R(55, y, 880, y + 32), color=None, fill=NAVY)
        for j, c in enumerate(cols):
            text(page, F, R(55 + j * cw + 8, y + 7, 55 + (j + 1) * cw, y + 27), c.upper(), "bold", 6.8, WHITE)
        y += 32
        for i, r in enumerate(rows):
            if i % 2:
                page.draw_rect(R(55, y, 880, y + 22), color=None, fill=(0.97, 0.97, 0.98))
            for j, c in enumerate(r):
                text(page, F, R(55 + j * cw + 8, y + 5, 55 + (j + 1) * cw, y + 21), str(c),
                     "bold" if j == 0 else "light", 7.4, INK)
            y += 22

    # Closing callout. On a luminaire this is LUMEN MAINTENANCE; a display has no
    # such thing, so both the title and the body are data-driven and the box is
    # SKIPPED ENTIRELY when there is no body. Drawing an empty "LUMEN MAINTENANCE"
    # panel on a screen sheet is exactly the failure AGENT.md 5 warns about - it
    # looks finished and is wrong.
    foot_title = sheet.get("callout_title") or "LUMEN MAINTENANCE"
    foot_body = sheet.get("callout_body") or sheet.get("lumen_maintenance") or ""
    if foot_body.strip():
        y += 24
        if y + 66 > 1095:          # never run into the footer bar
            y = 1095 - 66
        callout(y, 66, foot_title, foot_body)

    # ------------------------------------------------------------ write
    doc.set_metadata({"title": "%s %s - LED Connection" % (sheet["family"], sheet["product_type"]),
                      "author": "LED Connection", "producer": "LC spec sheet skill"})
    tmp = os.path.join(tempfile.mkdtemp(prefix="lc-ov-"), "sheet.pdf")
    doc.save(tmp, garbage=3, deflate=True)
    for _ in range(6):
        try:
            shutil.copy2(tmp, out_path)
            return out_path, F.poppins
        except Exception:
            time.sleep(1.5)
    alt = "%s_%s.pdf" % (os.path.splitext(out_path)[0], time.strftime("%H%M%S"))
    shutil.copy2(tmp, alt)
    return alt, F.poppins


def main():
    if len(sys.argv) < 2:
        print("usage: overlay.py <sheet.json> [out.pdf]"); sys.exit(1)
    sheet = json.load(io.open(sys.argv[1], encoding="utf-8"))
    sys.path.insert(0, HERE)
    import build as builder
    blocking, warn = builder.check(sheet)
    if blocking:
        for b in blocking:
            print("  BLOCK: %s" % b)
        sys.exit(2)
    if not os.path.exists(TEMPLATE):
        print("REFUSED: template not found at %s" % TEMPLATE); sys.exit(2)
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        builder.OUT, "%s_%s_SpecSheet_%s.pdf" % (sheet["family"].replace(" ", ""),
                                                 sheet["product_type"].split()[0],
                                                 sheet["lc_sku_prefix"]))
    path, poppins = build(sheet, warn, out)
    print("  built : %s" % path)
    print("  font  : %s" % ("Poppins (full family)" if poppins else
                            "Helvetica FALLBACK - full Poppins not in assets/fonts/full/"))
    if warn:
        print("  band  : PRE-RELEASE (%d item%s pending)" % (len(warn), "" if len(warn) == 1 else "s"))


if __name__ == "__main__":
    main()
