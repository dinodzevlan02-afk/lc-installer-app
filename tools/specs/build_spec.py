"""LED Connection spec sheets for products the catalog has no LC sheet for.

    python3 tools/specs/build_spec.py LC-FL-WS-3CCT            # -> tools/specs/preview/{part}.pdf
    python3 tools/specs/build_spec.py LC-FL-WS-3CCT --publish  # -> app/specs/{file} (after Dino approves)

content/{part}.json holds every line the sheet prints, each with the source it
came from ("src", never printed): the supplier's own spec sheet and quote,
and LED Connection's item description. Nothing is added from memory, and the
supplier's name and model codes never appear on the sheet.

Same look as the installation guides (tools/guides): dark header band with the
LED Connection logo, orange #f37021 and cyan #22d3ee, Outfit for text, Orbitron
for display lines, JetBrains Mono for codes; white pages that print well. A
sheet whose content says "draft": true carries a DRAFT mark on every page.
"""
import json, os, sys
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, white
from reportlab.lib.utils import ImageReader, simpleSplit

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
FONTS = os.path.join(ROOT, "tools", "guides", "fonts")
LOGO = os.path.join(ROOT, "app", "lc-logo.png")

for name in ["Outfit-Regular", "Outfit-Medium", "Outfit-SemiBold", "Outfit-Bold",
             "Orbitron-Bold", "Orbitron-Black", "JetBrainsMono-Regular", "JetBrainsMono-Bold"]:
    pdfmetrics.registerFont(TTFont(name, os.path.join(FONTS, name + ".ttf")))

NAVY, NAVY2 = HexColor("#0a0e1a"), HexColor("#131a2c")
ORANGE, CYAN = HexColor("#f37021"), HexColor("#22d3ee")
INK, INK2, INK3 = HexColor("#111827"), HexColor("#4b5563"), HexColor("#9ca3af")
LINE, SOFT, WARN_BG = HexColor("#e5e7eb"), HexColor("#f6f7f9"), HexColor("#fff4ec")
W, H = letter
M = 44
COMPANY = {"name": "LED Connection", "phone": "702.847.7680", "web": "www.ledconnection.com"}


class Sheet:
    def __init__(self, d, path):
        self.d, self.page = d, 0
        self.c = canvas.Canvas(path, pagesize=letter)
        self.c.setTitle(d["part"] + " " + d["name"] + " - Spec Sheet")
        self.c.setAuthor(COMPANY["name"]); self.c.setCreator(COMPANY["name"])
        self.c.setSubject(d["doc"] + " rev " + d["rev"])

    # ── helpers ──────────────────────────────────────────────────────────
    def text(self, x, y, s, font="Outfit-Regular", size=10, color=INK, align="l", spacing=0):
        w = pdfmetrics.stringWidth(s, font, size) + spacing * max(len(s) - 1, 0)
        t = self.c.beginText()
        t.setFont(font, size); t.setCharSpace(spacing); t.setFillColor(color)
        t.setTextOrigin(x - (w if align == "r" else w / 2 if align == "c" else 0), y)
        t.textOut(s); self.c.drawText(t)
        return w

    def para(self, x, y, s, width, font="Outfit-Regular", size=10, lead=14, color=INK):
        lines = simpleSplit(s, font, size, width)
        for i, ln in enumerate(lines):
            self.text(x, y - i * lead, ln, font, size, color)
        return y - len(lines) * lead

    def logo(self, x, y, h):
        img = ImageReader(LOGO); iw, ih = img.getSize()
        self.c.drawImage(img, x, y, width=h * iw / ih, height=h, mask="auto")

    def section(self, x, y, title):
        self.c.setFillColor(ORANGE); self.c.rect(x, y - 2, 4, 14, stroke=0, fill=1)
        self.text(x + 11, y, title.upper(), "Orbitron-Bold", 10, INK, spacing=1.0)
        return y - 22

    def chip(self, x, y, s, bg=ORANGE, fg=white, font="JetBrainsMono-Bold", size=8.5):
        w = pdfmetrics.stringWidth(s, font, size) + 0.6 * (len(s) - 1) + 16
        self.c.setFillColor(bg); self.c.roundRect(x, y - 5, w, 18, 4, stroke=0, fill=1)
        self.text(x + 8, y, s, font, size, fg, spacing=0.6)
        return w

    # ── frame ────────────────────────────────────────────────────────────
    def header(self):
        c, d = self.c, self.d
        c.setFillColor(NAVY); c.rect(0, H - 92, W, 92, stroke=0, fill=1)
        c.setStrokeColor(NAVY2); c.setLineWidth(0.5)               # the HUD grid
        for gx in range(0, int(W) + 1, 24): c.line(gx, H - 92, gx, H)
        for gy in range(int(H - 92), int(H) + 1, 24): c.line(0, gy, W, gy)
        c.setFillColor(ORANGE); c.rect(0, H - 96, W, 4, stroke=0, fill=1)
        self.logo(M, H - 70, 46)
        self.text(M + 112, H - 38, d["name"].upper(), "Orbitron-Black", 17, white, spacing=1.0)
        self.text(M + 112, H - 60, d["part"] + "-SF  /  " + d["part"] + "-Y", "JetBrainsMono-Bold", 10, CYAN, spacing=0.6)
        self.text(W - M, H - 36, "SPEC SHEET", "Orbitron-Bold", 10, white, "r", spacing=2)
        if d.get("draft"):
            w = pdfmetrics.stringWidth("DRAFT  ·  NOT FOR RELEASE", "JetBrainsMono-Bold", 8) + 0.6 * 24 + 16
            self.chip(W - M - w, H - 62, "DRAFT  ·  NOT FOR RELEASE")

    def footer(self):
        c, d = self.c, self.d
        c.setStrokeColor(LINE); c.setLineWidth(0.6); c.line(M, 40, W - M, 40)
        self.text(M, 28, COMPANY["name"] + "  ·  " + COMPANY["phone"] + "  ·  " + COMPANY["web"], "Outfit-Medium", 8, INK2)
        self.text(M, 17, "Specifications subject to change without notice.", "Outfit-Regular", 7, INK3)
        self.text(W - M, 28, d["doc"] + "  ·  rev " + d["rev"] + "  ·  page " + str(self.page), "JetBrainsMono-Regular", 7.5, INK3, "r")

    def new_page(self):
        if self.page:
            self.footer(); self.c.showPage()
        self.page += 1
        self.header()

    # ── page 1: what it is ───────────────────────────────────────────────
    def page1(self):
        c, d = self.c, self.d
        self.new_page()
        y, lw = H - 126, 300
        y = self.section(M, y, "Product description")
        for p in d["description"]:
            y = self.para(M, y, p["t"], lw, "Outfit-Regular", 10.5, 15) - 6
        y = self.section(M, y - 8, "Overview")
        for p in d["overview"]:
            c.setFillColor(CYAN); c.circle(M + 3.5, y + 3.5, 2.8, stroke=0, fill=1)
            y = self.para(M + 13, y, p["t"], lw - 13, "Outfit-Regular", 10, 13.5) - 4
        # photo frame: no supplier image is used until LC has its own product photo
        px, pw, ptop = M + lw + 24, W - 2 * M - lw - 24, H - 122
        ph = 210
        c.setStrokeColor(CYAN); c.setLineWidth(1); c.setDash(4, 3); c.setFillColor(SOFT)
        c.roundRect(px, ptop - ph, pw, ph, 8, stroke=1, fill=1); c.setDash()
        self.text(px + pw / 2, ptop - ph / 2 + 6, "PRODUCT PHOTO", "Orbitron-Bold", 9, INK3, "c", spacing=1.5)
        self.text(px + pw / 2, ptop - ph / 2 - 10, "LC photo to be added", "Outfit-Regular", 8.5, INK3, "c")
        cy = ptop - ph - 26
        for label, val in [("WATTAGE", "40 / 60 / 80 W"), ("CCT", "3000 / 4000 / 5000 K"), ("VOLTAGE", "120-277 V")]:
            self.text(px, cy, label, "JetBrainsMono-Bold", 7.5, ORANGE, spacing=1)
            self.text(px + pw, cy, val, "Outfit-SemiBold", 10, INK, "r")
            c.setStrokeColor(LINE); c.setLineWidth(0.5); c.line(px, cy - 7, px + pw, cy - 7)
            cy -= 22
        y = min(y, cy) - 14
        # specification table
        y = self.section(M, y, "Specifications")
        kw, rh = 150, 19
        for i, (k, v, _src) in enumerate(d["specs"]):
            if i % 2 == 0:
                c.setFillColor(SOFT); c.rect(M, y - 6, W - 2 * M, rh, stroke=0, fill=1)
            self.text(M + 8, y, k, "Outfit-SemiBold", 9.5, INK2)
            self.text(M + 8 + kw, y, v, "Outfit-Regular", 9.5, INK)
            y -= rh
        return y

    # ── page 2: ordering, connections, set-up ────────────────────────────
    def page2(self):
        c, d = self.c, self.d
        self.new_page()
        y = self.section(M, H - 126, "Ordering information")
        cols = d["ordering"]["columns"]
        cw = (W - 2 * M) / len(cols)
        c.setFillColor(NAVY); c.rect(M, y - 6, W - 2 * M, 20, stroke=0, fill=1)
        for i, col in enumerate(cols):
            self.text(M + i * cw + 8, y, col["h"].upper(), "JetBrainsMono-Bold", 8, CYAN, spacing=1)
        y -= 26
        rows = max(len(col["rows"]) for col in cols)
        top = y
        for i, col in enumerate(cols):
            yy = top
            for code, txt in col["rows"]:
                if code:
                    self.text(M + i * cw + 8, yy, code, "JetBrainsMono-Bold", 11, ORANGE)
                yy = self.para(M + i * cw + 8, yy - (14 if code else 0), txt, cw - 14, "Outfit-Regular", 9, 12, INK) - 8
        y = top - rows * 36 - 6
        c.setStrokeColor(LINE); c.setLineWidth(0.6); c.line(M, y + 10, W - M, y + 10)
        w = self.text(M, y - 6, "EXAMPLE", "JetBrainsMono-Bold", 8, INK3, spacing=1)
        self.chip(M + w + 12, y - 6, d["ordering"]["example"], NAVY, CYAN, size=9)
        y -= 34
        for pn, txt in d["ordering"]["parts"]:
            self.text(M + 8, y, pn, "JetBrainsMono-Bold", 9.5, INK)
            self.text(M + 168, y, txt, "Outfit-Regular", 9.5, INK2)
            y -= 17
        y -= 14
        # two columns: connections | field set-up
        lx, rx, colw = M, W / 2 + 10, W / 2 - M - 10
        y0 = y
        y = self.section(lx, y0, "Electrical connections")
        for i, (wire, fn) in enumerate(d["wiring"]):
            if i % 2 == 0:
                c.setFillColor(SOFT); c.rect(lx, y - 6, colw, 19, stroke=0, fill=1)
            self.text(lx + 8, y, wire, "Outfit-SemiBold", 9.5, INK)
            self.text(lx + 90, y, fn, "Outfit-Regular", 9.5, INK2)
            y -= 19
        yl = y
        y = self.section(rx, y0, "Field set-up: wattage and CCT")
        for n, p in enumerate(d["setup"], 1):
            c.setFillColor(ORANGE); c.circle(rx + 8, y + 3.5, 8, stroke=0, fill=1)
            self.text(rx + 8, y, str(n), "Orbitron-Bold", 8.5, white, "c")
            y = self.para(rx + 24, y, p["t"], colw - 24, "Outfit-Regular", 9.5, 13) - 8
        y = min(yl, y) - 16
        # notes
        y = self.section(M, y, "Notes")
        for p in d["notes"]:
            c.setFillColor(CYAN); c.circle(M + 3.5, y + 3.5, 2.8, stroke=0, fill=1)
            y = self.para(M + 13, y, p["t"], W - 2 * M - 13, "Outfit-Regular", 9.5, 13) - 4
        if d.get("draft"):
            y -= 14
            lines = ["Draft for LED Connection review. Not for customers until approved: "
                     "certifications (UL/ETL, DLC), delivered lumens, photometry and warranty are added once the documents are on file."]
            h = 20 + len(simpleSplit(lines[0], "Outfit-Medium", 9.5, W - 2 * M - 30)) * 13
            c.setFillColor(WARN_BG); c.setStrokeColor(ORANGE); c.setLineWidth(1)
            c.roundRect(M, y - h + 12, W - 2 * M, h, 6, stroke=1, fill=1)
            self.text(M + 14, y - 2, "DRAFT", "JetBrainsMono-Bold", 8, ORANGE, spacing=1.5)
            self.para(M + 14, y - 16, lines[0], W - 2 * M - 30, "Outfit-Medium", 9.5, 13)
        self.footer(); self.c.save()


def main(argv):
    part = argv[1] if len(argv) > 1 else "LC-FL-WS-3CCT"
    d = json.load(open(os.path.join(HERE, "content", part + ".json")))
    if "--publish" in argv:
        if d.get("draft"):
            sys.exit(part + " is still a draft: set \"draft\": false after Dino approves it")
        out = os.path.join(ROOT, "app", "specs", d.get("file", "LC-" + part + ".pdf"))
    else:
        out = os.path.join(HERE, "preview", part + ".pdf")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    s = Sheet(d, out); s.page1(); s.page2()
    print(out)


if __name__ == "__main__":
    main(sys.argv)
