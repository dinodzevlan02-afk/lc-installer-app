"""LED Connection installation guides for the Optimus area light, one per bracket.

    python3 tools/guides/build_guides.py            # every content/*.json -> app/guides/optimus/
    python3 tools/guides/build_guides.py --preview  # content/_preview.json -> the design preview only

Why this exists (Dino, 2026-10-20): the Optimus is supplied with the
supplier's own bracket guides (A-G). LED Connection issues its own: same
installation content, LED Connection's look, its part numbers, its support
line, and never the supplier's name or codes.

Rules for content/*.json (one file per bracket):
  - Steps, parts, torque, drilling and wiring are taken ONLY from the
    supplier's guide for that bracket, word for word in meaning. Nothing is
    added from memory. Figures are the supplier's drawings, cleaned of
    supplier marks (content/figures/).
  - "source" names the supplier document the content came from. It is
    kept for traceability and is NEVER printed.
  - The bracket code is the order-logic code (lc-catalog/lc-skb.js
    OPTIMUS_OPTS.bracket): F slipfitter, R adjustable arm, U yoke,
    SS straight square arm, SR straight round arm, T trunnion.

Look: white pages that print well, a dark LED Connection cover and header
band (the logo is white and orange), Outfit for text, Orbitron for the
display lines, JetBrains Mono for codes, orange #f37021 and cyan #22d3ee.
Fonts are SIL OFL (Outfit, Orbitron, JetBrains Mono) and live in fonts/.
"""
import json, os, sys, glob, datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, white
from reportlab.lib.utils import ImageReader, simpleSplit

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
LOGO = os.path.join(ROOT, "app", "lc-logo.png")
OUT = os.path.join(ROOT, "app", "guides", "optimus")

for name in ["Outfit-Regular", "Outfit-Medium", "Outfit-SemiBold", "Outfit-Bold", "Outfit-ExtraBold",
             "Orbitron-Bold", "Orbitron-Black", "JetBrainsMono-Regular", "JetBrainsMono-Bold"]:
    pdfmetrics.registerFont(TTFont(name, os.path.join(HERE, "fonts", name + ".ttf")))

NAVY, NAVY2 = HexColor("#0a0e1a"), HexColor("#131a2c")
ORANGE, CYAN = HexColor("#f37021"), HexColor("#22d3ee")
INK, INK2, INK3 = HexColor("#111827"), HexColor("#4b5563"), HexColor("#9ca3af")
LINE, SOFT, WARN_BG = HexColor("#e5e7eb"), HexColor("#f6f7f9"), HexColor("#fff4ec")
W, H = letter
M = 50                      # page margin
COMPANY = {"name": "LED Connection", "phone": "702.847.7680", "web": "ledconnection.com",
           "email": "dinod@ledconnection.com", "addr": "915 E Dale Ave Ste 110, Henderson, NV 89044"}
PN = ["LC", "SLOT", "{watt}W", "{volt}", "L5", "{sensor}", "{cct}", "{cri}", "{optic}", "{BRACKET}", "{color}"]


class Guide:
    def __init__(self, data, path, preview=False):
        self.d, self.preview, self.page = data, preview, 0
        self.c = canvas.Canvas(path, pagesize=letter)
        self.c.setTitle("Optimus Installation Guide - " + data["bracket"])
        self.c.setAuthor(COMPANY["name"])
        self.c.setSubject(data["doc"] + " rev " + data["rev"])
        self.c.setCreator("LED Connection")

    # ── helpers ──────────────────────────────────────────────────────────
    def text(self, x, y, s, font="Outfit-Regular", size=10.5, color=INK, align="l", spacing=0):
        c = self.c
        c.setFillColor(color)
        t = c.beginText()
        t.setFont(font, size)
        t.setCharSpace(spacing)
        w = pdfmetrics.stringWidth(s, font, size) + spacing * max(len(s) - 1, 0)
        t.setTextOrigin(x - (w if align == "r" else w / 2 if align == "c" else 0), y)
        t.textOut(s)
        c.drawText(t)
        return w

    def para(self, x, y, s, width, font="Outfit-Regular", size=10.5, lead=14.5, color=INK):
        lines = simpleSplit(s, font, size, width)
        for i, ln in enumerate(lines):
            self.text(x, y - i * lead, ln, font, size, color)
        return y - len(lines) * lead

    def logo(self, x, y, h):
        img = ImageReader(LOGO)
        iw, ih = img.getSize()
        self.c.drawImage(img, x, y, width=h * iw / ih, height=h, mask="auto")

    def footer(self):
        c, d = self.c, self.d
        c.setStrokeColor(LINE); c.setLineWidth(0.6); c.line(M, 38, W - M, 38)
        self.text(M, 26, COMPANY["name"] + "  ·  " + COMPANY["phone"] + "  ·  " + COMPANY["web"], "Outfit-Medium", 8, INK2)
        self.text(W - M, 26, d["doc"] + "  ·  rev " + d["rev"] + "  ·  " + str(self.page), "JetBrainsMono-Regular", 7.5, INK3, "r")
        if self.preview:
            c.saveState(); c.setFillColor(HexColor("#f37021")); c.setFillAlpha(0.08)
            c.translate(W / 2, H / 2); c.rotate(35); c.setFont("Orbitron-Black", 70)
            c.drawCentredString(0, 0, "PREVIEW"); c.restoreState()

    def header(self):
        c, d = self.c, self.d
        c.setFillColor(NAVY); c.rect(0, H - 54, W, 54, stroke=0, fill=1)
        c.setFillColor(ORANGE); c.rect(0, H - 57, W, 3, stroke=0, fill=1)
        self.logo(M, H - 45, 34)
        w1 = self.text(M + 62, H - 26, "OPTIMUS", "Orbitron-Bold", 9.5, white, spacing=1.2)
        c.setFillColor(ORANGE); c.rect(M + 62 + w1 + 8, H - 24, 4, 4, stroke=0, fill=1)   # Orbitron has no middle dot
        self.text(M + 62 + w1 + 20, H - 26, "INSTALLATION GUIDE", "Orbitron-Bold", 9.5, white, spacing=1.2)
        self.text(M + 62, H - 40, d["bracket"].upper() + "  (" + d["code"] + ")", "JetBrainsMono-Bold", 8, CYAN, spacing=0.6)
        self.text(W - M, H - 33, d["doc"], "JetBrainsMono-Regular", 8, INK3, "r")

    def new_page(self):
        if self.page:
            self.footer(); self.c.showPage()
        self.page += 1

    def section(self, y, title):
        self.c.setFillColor(ORANGE); self.c.rect(M, y - 2, 4, 15, stroke=0, fill=1)
        self.text(M + 12, y, title.upper(), "Orbitron-Bold", 11, INK, spacing=1.0)
        return y - 26

    # ── pages ────────────────────────────────────────────────────────────
    def cover(self):
        c, d = self.c, self.d
        self.new_page()
        top = H * 0.46
        c.setFillColor(NAVY); c.rect(0, top, W, H - top, stroke=0, fill=1)
        c.setStrokeColor(NAVY2); c.setLineWidth(0.6)            # the HUD grid
        for gx in range(0, int(W) + 1, 28): c.line(gx, top, gx, H)
        for gy in range(int(top), int(H) + 1, 28): c.line(0, gy, W, gy)
        c.setFillColor(ORANGE); c.rect(0, top - 6, W, 6, stroke=0, fill=1)
        self.logo(M, H - 118, 72)
        self.text(M, H - 168, "INSTALLATION GUIDE", "JetBrainsMono-Bold", 10, CYAN, spacing=3)
        self.text(M, H - 226, "OPTIMUS", "Orbitron-Black", 58, white, spacing=2)
        self.text(M, H - 252, "LED area light  ·  75 W to 420 W  ·  LC-SLOT", "Outfit-Medium", 13, HexColor("#cbd5e1"))
        # the bracket, as a chip
        bw = pdfmetrics.stringWidth(d["bracket"].upper(), "Orbitron-Bold", 15) + 98
        c.setFillColor(ORANGE); c.roundRect(M, top + 34, bw, 46, 8, stroke=0, fill=1)
        c.setFillColor(NAVY); c.roundRect(M + 8, top + 42, 58, 30, 5, stroke=0, fill=1)
        self.text(M + 37, top + 51, d["code"], "JetBrainsMono-Bold", 15, ORANGE, "c")
        self.text(M + 78, top + 51, d["bracket"].upper(), "Orbitron-Bold", 15, NAVY, spacing=0.5)

        # lower half: which part numbers, at a glance, safety
        y = top - 50
        self.text(M, y, "THIS GUIDE COVERS EVERY OPTIMUS PART NUMBER WITH BRACKET " + d["code"], "JetBrainsMono-Bold", 8.5, INK2, spacing=0.8)
        y -= 34
        x = M
        for seg in PN:
            hot = seg == "{BRACKET}"
            label = d["code"] if hot else seg.replace("{", "").replace("}", "")
            f, sz = ("JetBrainsMono-Bold", 12) if hot else ("JetBrainsMono-Regular", 10)
            sw = max(pdfmetrics.stringWidth(label, f, sz) + 14, 26)
            c.setFillColor(ORANGE if hot else SOFT); c.setStrokeColor(ORANGE if hot else LINE)
            c.roundRect(x, y - 7, sw, 24, 4, stroke=1, fill=1)
            self.text(x + sw / 2, y + 1, label, f, sz, white if hot else INK2, "c")
            x += sw + 4
        self.text(M, y - 26, "e.g. " + d.get("example", "LC-SLOT-300W-HV-L5-XX-50-70-T5S-" + d["code"] + "-BK"), "JetBrainsMono-Regular", 9, INK3)
        y -= 66
        g = d.get("glance", {})
        boxes = [("TIME", g.get("time") or "-"), ("PEOPLE", g.get("people") or "-"), ("TOOLS", ", ".join(g.get("tools", [])) or "-")]
        bw3 = (W - 2 * M - 24) / 3
        for i, (k, v) in enumerate(boxes):
            bx = M + i * (bw3 + 12)
            c.setFillColor(SOFT); c.setStrokeColor(LINE); c.roundRect(bx, y - 52, bw3, 66, 8, stroke=1, fill=1)
            self.text(bx + 14, y - 4, k, "JetBrainsMono-Bold", 8, ORANGE, spacing=1.5)
            self.para(bx + 14, y - 22, v, bw3 - 28, "Outfit-SemiBold", 11, 13.5, INK)
        y -= 92
        self.warn(y, "Electrical work by a qualified electrician, to the NEC and local code. Switch the circuit off at the panel, "
                     "lock it out and prove it dead before you open the fixture or the pole.")

    def warn(self, y, s, title="SAFETY FIRST"):
        c = self.c
        lines = simpleSplit(s, "Outfit-Medium", 10.5, W - 2 * M - 70)
        h = 30 + len(lines) * 14
        c.setFillColor(WARN_BG); c.setStrokeColor(ORANGE); c.setLineWidth(1)
        c.roundRect(M, y - h + 14, W - 2 * M, h, 8, stroke=1, fill=1)
        c.setFillColor(ORANGE); c.circle(M + 26, y - h / 2 + 14, 13, stroke=0, fill=1)
        self.text(M + 26, y - h / 2 + 9, "!", "Orbitron-Black", 14, white, "c")
        self.text(M + 50, y - 2, title, "JetBrainsMono-Bold", 8.5, ORANGE, spacing=1.5)
        self.para(M + 50, y - 18, s, W - 2 * M - 70, "Outfit-Medium", 10.5, 14, INK)
        return y - h - 6

    def parts_page(self):
        d = self.d
        self.new_page(); self.header()
        y = self.section(H - 96, "In the box")
        parts = d.get("parts", [])
        for i, p in enumerate(parts):
            ry = y - i * 26
            self.c.setFillColor(SOFT if i % 2 == 0 else white); self.c.rect(M, ry - 8, W - 2 * M, 26, stroke=0, fill=1)
            self.text(M + 12, ry, p.get("ref", chr(65 + i)), "JetBrainsMono-Bold", 10, ORANGE)
            self.text(M + 44, ry, p["name"], "Outfit-Medium", 10.5, INK)
            self.text(W - M - 12, ry, "× " + str(p.get("qty", "")), "JetBrainsMono-Bold", 10, INK2, "r")
        y -= max(len(parts), 1) * 26 + 24
        y = self.section(y, "Tools")
        y = self.para(M, y, ", ".join(d.get("glance", {}).get("tools", [])) or "-", W - 2 * M) - 18
        if d.get("specs"):
            y = self.section(y, "Key figures")
            for k, v in d["specs"]:
                self.text(M, y, k, "Outfit-Regular", 10.5, INK2)
                self.text(M + 220, y, v, "JetBrainsMono-Bold", 10.5, INK)
                y -= 18
        return y

    def steps(self):
        d = self.d
        steps = d.get("steps", [])
        y = None
        for n, st in enumerate(steps, 1):
            fig = st.get("figure")
            need = 120 + (210 if fig else 0) + len(simpleSplit(st.get("text", ""), "Outfit-Regular", 10.5, W - 2 * M - 60)) * 14.5
            if y is None or y - need < 60:
                self.new_page(); self.header()
                y = self.section(H - 96, "Installation" if n == 1 else "Installation, continued")
            c = self.c
            c.setFillColor(ORANGE); c.circle(M + 18, y - 4, 18, stroke=0, fill=1)
            self.text(M + 18, y - 11, str(n), "Orbitron-Black", 16, white, "c")
            self.text(M + 50, y - 9, st["title"], "Outfit-Bold", 14, INK)
            y = self.para(M + 50, y - 30, st.get("text", ""), W - 2 * M - 60) - 6
            if st.get("warn"):
                y = self.warn(y - 4, st["warn"], "CAUTION")
            if fig:
                fh = 200
                c.setStrokeColor(CYAN); c.setLineWidth(1); c.setFillColor(white)
                c.roundRect(M + 50, y - fh, W - 2 * M - 50, fh, 8, stroke=1, fill=1)
                path = os.path.join(HERE, "content", fig)
                if os.path.exists(path):
                    img = ImageReader(path); iw, ih = img.getSize()
                    k = min((W - 2 * M - 70) / iw, (fh - 20) / ih)
                    c.drawImage(img, M + 50 + (W - 2 * M - 50 - iw * k) / 2, y - fh + (fh - ih * k) / 2, iw * k, ih * k, mask="auto")
                else:
                    self.text(M + 50 + (W - 2 * M - 50) / 2, y - fh / 2, "FIGURE · " + fig, "JetBrainsMono-Regular", 9, INK3, "c")
                y -= fh + 22
            y -= 18

    def back(self):
        d = self.d
        self.new_page(); self.header()
        y = self.section(H - 96, "Before you leave the pole")
        for s in d.get("finish", []) + [
            "Restore power and check every head on the pole lights, with no flicker.",
            "In the LC Installer App: open the pin, take a photo of the installed fixture (and its label), SAVE AS INSTALLED. Every head is its own pin.",
            "Anything not as designed (bracket, height, aim): write it in the pin's note."]:
            self.c.setFillColor(CYAN); self.c.circle(M + 6, y + 3.5, 3.5, stroke=0, fill=1)
            y = self.para(M + 18, y, s, W - 2 * M - 18) - 8
        y -= 20
        y = self.section(y, "Questions on site")
        c = self.c
        c.setFillColor(NAVY); c.roundRect(M, y - 92, W - 2 * M, 104, 10, stroke=0, fill=1)
        self.logo(M + 20, y - 62, 50)
        self.text(M + 100, y - 18, COMPANY["name"].upper(), "Orbitron-Bold", 13, white, spacing=1)
        self.text(M + 100, y - 40, COMPANY["phone"], "JetBrainsMono-Bold", 15, ORANGE)
        self.text(M + 100, y - 60, COMPANY["email"] + "  ·  " + COMPANY["web"], "Outfit-Medium", 10.5, HexColor("#cbd5e1"))
        self.text(M + 100, y - 78, COMPANY["addr"], "Outfit-Regular", 9, INK3)

    def build(self):
        self.cover(); self.parts_page(); self.steps(); self.back()
        self.footer(); self.c.save()


def main():
    preview = "--preview" in sys.argv
    files = [os.path.join(HERE, "content", "_preview.json")] if preview else \
        sorted(f for f in glob.glob(os.path.join(HERE, "content", "*.json")) if not os.path.basename(f).startswith("_"))
    out = os.path.join(HERE, "preview") if preview else OUT
    os.makedirs(out, exist_ok=True)
    for f in files:
        d = json.load(open(f))
        name = "LC-Optimus-Installation-Guide-" + d["code"] + ".pdf"
        Guide(d, os.path.join(out, name), preview).build()
        print("built", os.path.relpath(os.path.join(out, name), ROOT))


if __name__ == "__main__":
    main()
