"""LED Connection installation guides for the Optimus area light, one per bracket.

    python3 tools/guides/extract_figures.py   # figures from source/*.pdf -> content/figures/
    python3 tools/guides/build_guides.py      # content/{code}.json -> app/guides/optimus/LC-Optimus-Installation-Guide-{code}.pdf

The content is LED Connection's own Optimus installation manuals (source/,
DNC1 April 2024, one per bracket: F, R, SR, SS, T, U). Dino, 2026-10-20:
"rebrand in the new format LC, not like a spec sheet". These guides set the
same content in the new look; nothing is added from memory:
  - every step, part, tool, torque and dimension is the manual's own
    (content/{code}.json; "source" names the manual and is never printed),
  - figures are crops of the manual's own drawings (extract_figures.py),
  - the safety, electrical and grounding text is the manuals' shared page 1
    (content/_common.json),
  - the supplier's bracket letters, which the manuals print in "connect the
    cable in the E holder", are left out ("the bracket holder").

Look: a dark LED Connection cover (HUD grid, orange band), white pages that
print well, Outfit for text, Orbitron for display lines, JetBrains Mono for
codes, orange #f37021 and cyan #22d3ee. Fonts are SIL OFL, in fonts/.
"""
import json, os, sys, glob
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, white
from reportlab.lib.utils import ImageReader, simpleSplit

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
CONTENT = os.path.join(HERE, "content")
LOGO = os.path.join(ROOT, "app", "lc-logo.png")
OUT = os.path.join(ROOT, "app", "guides")

for name in ["Outfit-Regular", "Outfit-Medium", "Outfit-SemiBold", "Outfit-Bold", "Outfit-ExtraBold",
             "Orbitron-Bold", "Orbitron-Black", "JetBrainsMono-Regular", "JetBrainsMono-Bold"]:
    pdfmetrics.registerFont(TTFont(name, os.path.join(HERE, "fonts", name + ".ttf")))

NAVY, NAVY2 = HexColor("#0a0e1a"), HexColor("#131a2c")
ORANGE, CYAN = HexColor("#f37021"), HexColor("#22d3ee")
INK, INK2, INK3 = HexColor("#111827"), HexColor("#4b5563"), HexColor("#9ca3af")
LINE, SOFT, WARN_BG, CYAN_BG = HexColor("#e5e7eb"), HexColor("#f6f7f9"), HexColor("#fff4ec"), HexColor("#ecfeff")
W, H = letter
M = 48                      # page margin
TOPY = H - 96               # first line under the page header
# Contact as printed on the manuals themselves.
COMPANY = {"name": "LED Connection", "phone": "702.847.7680", "web": "www.ledconnection.com", "email": "info@ledconnection.com"}
PN = ["LC", "SLOT", "{watt}W", "{volt}", "L5", "{sensor}", "{cct}", "{cri}", "{optic}", "{BRACKET}", "{color}"]


# A guide for another product names itself in "product" (content/{code}.json);
# without it a guide is an Optimus bracket guide, exactly as before.
OPTIMUS = {"name": "OPTIMUS", "line": "Ultra area luminaire  ·  LC-SLOT", "pn": PN,
           "for": "FOR EVERY OPTIMUS PART NUMBER WITH BRACKET {code}", "chip": "{bracket} BRACKET",
           "title": "Optimus Installation Guide - {bracket} bracket ({code})",
           "file": "optimus/LC-Optimus-Installation-Guide-{code}.pdf"}


class Guide:
    def __init__(self, data, common, path):
        self.p = dict(OPTIMUS, **data.get("product", {}))
        self.d, self.k, self.page = data, dict(common, **data.get("common", {})), 0
        self.c = canvas.Canvas(path, pagesize=letter)
        self.c.setTitle(self.f(self.p["title"]))
        self.c.setAuthor(COMPANY["name"])
        self.c.setSubject(data["doc"] + " rev " + data["rev"])
        self.c.setCreator(COMPANY["name"])

    # ── helpers ──────────────────────────────────────────────────────────
    def f(self, s):
        return s.format(code=self.d["code"], bracket=self.d.get("bracket", ""))

    def text(self, x, y, s, font="Outfit-Regular", size=10.5, color=INK, align="l", spacing=0):
        t = self.c.beginText()
        t.setFont(font, size)
        t.setCharSpace(spacing)
        w = pdfmetrics.stringWidth(s, font, size) + spacing * max(len(s) - 1, 0)
        t.setTextOrigin(x - (w if align == "r" else w / 2 if align == "c" else 0), y)
        t.setFillColor(color)
        t.textOut(s)
        self.c.drawText(t)
        return w

    def para(self, x, y, s, width, font="Outfit-Regular", size=10.5, lead=14.5, color=INK):
        for i, ln in enumerate(simpleSplit(s, font, size, width)):
            self.text(x, y - i * lead, ln, font, size, color)
        return y - len(simpleSplit(s, font, size, width)) * lead

    def bullets(self, x, y, items, width, dot=CYAN, size=10.5):
        for s in items:
            self.c.setFillColor(dot); self.c.circle(x + 3.5, y + 3.5, 3, stroke=0, fill=1)
            y = self.para(x + 14, y, s, width - 14, size=size) - 6
        return y

    def logo(self, x, y, h):
        img = ImageReader(LOGO)
        iw, ih = img.getSize()
        self.c.drawImage(img, x, y, width=h * iw / ih, height=h, mask="auto")

    def footer(self):
        c, d = self.c, self.d
        c.setStrokeColor(LINE); c.setLineWidth(0.6); c.line(M, 38, W - M, 38)
        self.text(M, 26, COMPANY["name"] + "  ·  " + COMPANY["phone"] + "  ·  " + COMPANY["web"], "Outfit-Medium", 8, INK2)
        self.text(W - M, 26, d["doc"] + "  ·  rev " + d["rev"] + "  ·  page " + str(self.page), "JetBrainsMono-Regular", 7.5, INK3, "r")

    def header(self):
        c, d = self.c, self.d
        c.setFillColor(NAVY); c.rect(0, H - 54, W, 54, stroke=0, fill=1)
        c.setFillColor(ORANGE); c.rect(0, H - 57, W, 3, stroke=0, fill=1)
        self.logo(M, H - 45, 34)
        w1 = self.text(M + 62, H - 26, self.p["name"], "Orbitron-Bold", 9.5, white, spacing=1.2)
        c.setFillColor(ORANGE); c.rect(M + 62 + w1 + 8, H - 24, 4, 4, stroke=0, fill=1)   # Orbitron has no middle dot
        self.text(M + 62 + w1 + 20, H - 26, "INSTALLATION GUIDE", "Orbitron-Bold", 9.5, white, spacing=1.2)
        self.text(M + 62, H - 40, self.f(self.p["chip"]).upper() + "  (" + d["code"] + ")", "JetBrainsMono-Bold", 8, CYAN, spacing=0.6)
        self.text(W - M, H - 33, d["doc"], "JetBrainsMono-Regular", 8, INK3, "r")

    def new_page(self, header=True):
        if self.page:
            self.footer(); self.c.showPage()
        self.page += 1
        if header:
            self.header()

    def section(self, y, title):
        self.c.setFillColor(ORANGE); self.c.rect(M, y - 2, 4, 15, stroke=0, fill=1)
        self.text(M + 12, y, title.upper(), "Orbitron-Bold", 11, INK, spacing=1.0)
        return y - 26

    def box_h(self, lines, bw=W - 2 * M, size=10.5):
        w = bw - 70
        n = sum(len(simpleSplit(s, "Outfit-Medium", size, w)) for s in lines)
        return 34 + n * (size + 3.5) + (len(lines) - 1) * 4

    def box(self, y, title, lines, color=ORANGE, bg=WARN_BG, mark="!", x=M, bw=W - 2 * M, size=10.5):
        """A tinted callout; lines is a list of paragraphs. Returns the y under it."""
        c, w = self.c, bw - 70
        h = self.box_h(lines, bw, size)
        c.setFillColor(bg); c.setStrokeColor(color); c.setLineWidth(1)
        c.roundRect(x, y - h + 14, bw, h, 8, stroke=1, fill=1)
        c.setFillColor(color); c.circle(x + 26, y - h / 2 + 14, 13, stroke=0, fill=1)
        self.text(x + 26, y - h / 2 + 9, mark, "Orbitron-Black", 13, white, "c")
        self.text(x + 50, y - 2, title, "JetBrainsMono-Bold", 8.5, color, spacing=1.5)
        yy = y - 18
        for s in lines:
            yy = self.para(x + 50, yy, s, w, "Outfit-Medium", size, size + 3.5, INK) - 4
        return y - h - 8

    def figure(self, x, y, w, path, max_h, frame_h=None):
        """Draw a figure in a cyan frame, as large as fits; returns its height."""
        img = ImageReader(os.path.join(CONTENT, "figures", path))
        iw, ih = img.getSize()
        k = min((w - 20) / iw, (max_h - 20) / ih)
        fh = frame_h or ih * k + 20
        c = self.c
        c.setStrokeColor(CYAN); c.setLineWidth(1); c.setFillColor(white)
        c.roundRect(x, y - fh, w, fh, 8, stroke=1, fill=1)
        c.drawImage(img, x + (w - iw * k) / 2, y - fh + (fh - ih * k) / 2, iw * k, ih * k)
        return fh

    def fig_height(self, w, path, max_h):
        iw, ih = ImageReader(os.path.join(CONTENT, "figures", path)).getSize()
        return ih * min((w - 20) / iw, (max_h - 20) / ih) + 20

    # ── pages ────────────────────────────────────────────────────────────
    def cover(self):
        c, d = self.c, self.d
        self.new_page(header=False)
        top = H * 0.47
        c.setFillColor(NAVY); c.rect(0, top, W, H - top, stroke=0, fill=1)
        c.setStrokeColor(NAVY2); c.setLineWidth(0.6)            # the HUD grid
        for gx in range(0, int(W) + 1, 28): c.line(gx, top, gx, H)
        for gy in range(int(top), int(H) + 1, 28): c.line(0, gy, W, gy)
        c.setFillColor(ORANGE); c.rect(0, top - 6, W, 6, stroke=0, fill=1)
        self.logo(M, H - 118, 72)
        self.text(M, H - 166, "INSTALLATION GUIDE", "JetBrainsMono-Bold", 10, CYAN, spacing=3)
        name = self.p["name"]
        size = 58 if pdfmetrics.stringWidth(name, "Orbitron-Black", 58) + 2 * len(name) < W - 2 * M else 40
        self.text(M, H - 224, name, "Orbitron-Black", size, white, spacing=2)
        self.text(M, H - 250, self.p["line"], "Outfit-Medium", 13, HexColor("#cbd5e1"))
        label = self.f(self.p["chip"]).upper()
        bw = pdfmetrics.stringWidth(label, "Orbitron-Bold", 15) + 0.5 * (len(label) - 1) + 98
        c.setFillColor(ORANGE); c.roundRect(M, top + 34, bw, 46, 8, stroke=0, fill=1)
        c.setFillColor(NAVY); c.roundRect(M + 8, top + 42, 58, 30, 5, stroke=0, fill=1)
        self.text(M + 37, top + 51, d["code"], "JetBrainsMono-Bold", 15, ORANGE, "c")
        self.text(M + 78, top + 51, label, "Orbitron-Bold", 15, NAVY, spacing=0.5)

        y = top - 46
        self.text(M, y, self.f(self.p["for"]), "JetBrainsMono-Bold", 8.5, INK2, spacing=0.8)
        y -= 32
        x = M
        for seg in self.p["pn"]:
            hot = seg == "{BRACKET}" or seg.startswith("*")
            lab = (d["code"] if seg == "{BRACKET}" else seg.lstrip("*")) if hot else seg.replace("{", "").replace("}", "")
            f, sz = ("JetBrainsMono-Bold", 12) if hot else ("JetBrainsMono-Regular", 9.5)
            sw = max(pdfmetrics.stringWidth(lab, f, sz) + 12, 24)
            c.setFillColor(ORANGE if hot else SOFT); c.setStrokeColor(ORANGE if hot else LINE)
            c.roundRect(x, y - 7, sw, 24, 4, stroke=1, fill=1)
            self.text(x + sw / 2, y + 1, lab, f, sz, white if hot else INK2, "c")
            x += sw + 4
        y -= 44
        # at a glance: tools, torque, parts in the box
        torques = sorted({s["torque"] for s in d["steps"] if s.get("torque")})
        inbox = d.get("inbox") or [str(len(d["parts"])) + " kinds of parts, " + str(sum(int(p["qty"]) for p in d["parts"])) + " pieces", "Numbered list and drawing on page 3"]
        boxes = [("TOOLS", d["tools"]), (d.get("glance2", ["TORQUE"])[0], d.get("glance2", [None, None])[1] or torques or ["-"]),
                 (d.get("glance3", "IN THE BOX"), inbox)]
        bw3 = (W - 2 * M - 24) / 3
        for i, (k, vals) in enumerate(boxes):
            bx = M + i * (bw3 + 12)
            c.setFillColor(SOFT); c.setStrokeColor(LINE); c.roundRect(bx, y - 70, bw3, 84, 8, stroke=1, fill=1)
            self.text(bx + 14, y - 4, k, "JetBrainsMono-Bold", 8, ORANGE, spacing=1.5)
            yy = y - 21
            for v in vals:
                yy = self.para(bx + 14, yy, v, bw3 - 28, "Outfit-SemiBold", 10.5, 13, INK) - 2
        y -= 104
        self.box(y, "BEFORE YOU BEGIN", ["Read and follow the safety instructions on the next page. Save these instructions."])

    def safety(self):
        k = self.k
        self.new_page()
        y = self.box(TOPY + 10, "WARNING  ·  RISK OF FIRE, EXPLOSION AND ELECTRIC SHOCK", k["warning"])
        y = self.section(y - 12, "Electrical requirements")
        y = self.para(M, y, k["electrical"], W - 2 * M) - 16
        y = self.section(y, "Grounding")
        y = self.para(M, y, k["grounding"], W - 2 * M) - 16
        y = self.section(y, "Before starting")
        self.bullets(M, y, k["before"], W - 2 * M)

    def parts_page(self):
        d, c = self.d, self.c
        self.new_page()
        y = self.section(TOPY, "Tools")
        x = M
        for t in d["tools"]:
            tw = pdfmetrics.stringWidth(t, "Outfit-SemiBold", 10.5) + 22
            c.setFillColor(CYAN_BG); c.setStrokeColor(CYAN); c.roundRect(x, y - 7, tw, 22, 11, stroke=1, fill=1)
            self.text(x + 11, y, t, "Outfit-SemiBold", 10.5, INK)
            x += tw + 8
        self.text(M, y - 26, self.k["toolsNote"], "Outfit-Regular", 9.5, INK2)
        y -= 56
        y = self.section(y, "In the box")
        rows = d["parts"]
        half = (len(rows) + 1) // 2
        cw = (W - 2 * M - 12) / 2
        for i, p in enumerate(rows):
            col, row = (0, i) if i < half else (1, i - half)
            rx, ry = M + col * (cw + 12), y - row * 24
            c.setFillColor(SOFT if row % 2 == 0 else white); c.rect(rx, ry - 8, cw, 24, stroke=0, fill=1)
            c.setFillColor(ORANGE); c.circle(rx + 14, ry + 3.5, 8, stroke=0, fill=1)
            self.text(rx + 14, ry, p["ref"], "JetBrainsMono-Bold", 9, white, "c")
            self.text(rx + 30, ry, p["name"], "Outfit-Medium", 10.5, INK)
            self.text(rx + cw - 10, ry, "× " + str(p["qty"]), "JetBrainsMono-Bold", 10, INK2, "r")
        y -= half * 24 + 12
        if os.path.exists(os.path.join(CONTENT, "figures", d["code"] + "-parts.png")):
            self.figure(M, y, W - 2 * M, d["code"] + "-parts.png", y - 60)
        for t in d.get("parts_notes", []):
            y = self.box(y, t["title"], t["lines"], CYAN, CYAN_BG, "i") - 6

    def card(self, x, y, cw, n, st, draw=True, fmax1=215):
        """One step as a card in the two-column grid; returns its height."""
        c = self.c
        figs = st.get("figures", [])
        note = self.k["waterproof"] if st.get("note") == "WATERPROOF" else st.get("note")
        tw = cw - 46
        title = simpleSplit(st["title"], "Outfit-Bold", 11.5, tw)
        fmax = fmax1
        # several drawings sit side by side, each as wide as its shape needs
        # so they come out the same height (a wide dimension drawing gets
        # most of the row)
        asp = [(lambda s: s[0] / s[1])(ImageReader(os.path.join(CONTENT, "figures", f)).getSize()) for f in figs]
        widths = [(cw - 12 * (len(figs) - 1)) * a / sum(asp) for a in asp] if figs else []
        h = 8 + max(len(title) * 15, 30) + 6
        if st.get("torque"):
            h += 28
        h += max([self.fig_height(w, f, fmax) for w, f in zip(widths, figs)] or [0]) + 8
        if note:
            h += self.box_h([note], cw, 9) + 2
        if not draw:
            return h
        c.setFillColor(ORANGE); c.circle(x + 15, y - 11, 15, stroke=0, fill=1)
        self.text(x + 15, y - 17, str(n), "Orbitron-Black", 14, white, "c")
        yy = y - 8
        for i, ln in enumerate(title):
            self.text(x + 40, yy - 8 - i * 15, ln, "Outfit-Bold", 11.5, INK)
        yy -= max(len(title) * 15, 30) + 6
        if st.get("torque"):
            lab = "TORQUE  " + st["torque"]
            lw = pdfmetrics.stringWidth(lab, "JetBrainsMono-Bold", 8.5) + 18
            c.setFillColor(NAVY); c.roundRect(x, yy - 16, lw, 20, 5, stroke=0, fill=1)
            self.text(x + 9, yy - 10, lab, "JetBrainsMono-Bold", 8.5, ORANGE)
            yy -= 28
        if figs:
            hs = [self.fig_height(w, f, fmax) for w, f in zip(widths, figs)]
            fx = x
            for w, f in zip(widths, figs):
                self.figure(fx, yy, w, f, fmax, max(hs))
                fx += w + 12
            yy -= max(hs) + 8
        if note:
            self.box(yy, "NOTE", [note], CYAN, CYAN_BG, "i", x, cw, 9)
        return h

    def steps(self):
        steps = self.d["steps"]
        rows, i = [], 0
        while i < len(steps):
            if len(steps[i].get("figures", [])) > 1 or i + 1 == len(steps) or len(steps[i + 1].get("figures", [])) > 1:
                rows.append((i, steps[i:i + 1])); i += 1
            else:
                rows.append((i, steps[i:i + 2])); i += 2
        y = None
        for r, row in rows:
            cw = (W - 2 * M - 18) / 2 if len(row) == 2 or len(row[0].get("figures", [])) < 2 else W - 2 * M
            # shrink the drawings a little to keep a row on this page, rather
            # than leave half a page empty
            fit = None
            if y is not None:
                for fm in (215, 195, 175, 155, 140):
                    if y - max(self.card(0, 0, cw, 0, st, False, fm) for st in row) >= 56:
                        fit = fm
                        break
            if fit is None:
                self.new_page()
                y = self.section(TOPY, "Installation" if r == 0 else "Installation, continued")
                fit = 215
            rh = max(self.card(0, 0, cw, 0, st, False, fit) for st in row)
            for i, st in enumerate(row):
                self.card(M + i * (cw + 18), y, cw, r + i + 1, st, True, fit)
            y -= rh + 22
        self.y = y

    def room(self, need, title):
        """Carry on down this page when need fits, else start a new one."""
        if self.y - need < 56:
            self.new_page()
            self.y = TOPY
        else:
            self.y -= 6
        self.y = self.section(self.y, title)

    def wiring(self):
        d, fw = self.d, W - 2 * M
        if not d.get("wiring"):
            self.wmax = 230
            return self.extras()
        labels = d.get("wiring_labels", ["STANDARD WIRING", "0-10V DIM WIRING"])
        intro = len(simpleSplit(self.k["wiring"], "Outfit-Regular", 10.5, fw)) * 14.5 + 14
        head = 6 + 26 + intro + self.box_h([self.k["waterproof"]]) + 8 + 6 + 36
        # the first diagram follows the steps on their page when it fits, a
        # little smaller if need be; never the heading alone at a page foot
        avail = self.y - head - 56
        self.wmax = 230
        if avail < self.fig_height(fw, d["wiring"][0], 230):
            fits = [m for m in (200, 170, 145) if avail >= self.fig_height(fw, d["wiring"][0], m)]
            self.wmax = fits[0] if fits else 230
        self.room(head - 32 + self.fig_height(fw, d["wiring"][0], self.wmax) + 36, "Wiring")
        self.y = self.para(M, self.y, self.k["wiring"], fw) - 14
        self.y = self.box(self.y, "NOTE", [self.k["waterproof"]], CYAN, CYAN_BG, "i") - 6
        for i, f in enumerate(d["wiring"]):
            if self.y - (self.fig_height(fw, f, self.wmax) + 36) < 56:
                self.new_page()
                self.y = self.section(TOPY, "Wiring, continued")
                self.wmax = 230
            self.text(M, self.y, labels[i] if i < len(labels) else "", "JetBrainsMono-Bold", 8.5, ORANGE, spacing=1.2)
            self.y -= 10 + self.figure(M, self.y - 8, fw, f, self.wmax) + 18
        self.extras()

    def extras(self):
        d, fw = self.d, W - 2 * M
        if d.get("extra"):
            for f in d["extra"]["figures"]:
                self.room(self.fig_height(fw, f, 360) + 40, d["extra"]["title"])
                self.y -= self.figure(M, self.y, fw, f, 360) + 12
        for sec in d.get("sections", []):              # e.g. the step-down, the goof ring
            lines = sec.get("lines", [])
            need = 40 + sum(len(simpleSplit(t, "Outfit-Regular", 10.5, fw - 14)) * 14.5 + 6 for t in lines)
            need += sum(self.fig_height(fw, f, 260) + 12 for f in sec.get("figures", []))
            self.room(min(need, 520), sec["title"])
            if sec.get("intro"):
                self.y = self.para(M, self.y, sec["intro"], fw) - 10
            if lines:
                self.y = self.bullets(M, self.y, lines, fw) - 6
            if sec.get("box"):
                self.y = self.box(self.y, sec["box"]["title"], sec["box"]["lines"]) - 6
            for f in sec.get("figures", []):
                if self.y - self.fig_height(fw, f, 260) < 56:
                    self.new_page(); self.y = self.section(TOPY, sec["title"] + ", continued")
                self.y -= self.figure(M, self.y, fw, f, 260) + 12

    def back(self):
        c, d = self.c, self.d
        self.room(250, "Record the install")
        y = self.bullets(M, self.y, [
            "In the LC Installer App, open the fixture's pin, take a photo of the installed fixture (and its label if you can), and SAVE AS INSTALLED. Every head is its own pin.",
            d.get("record_note", "Anything not as designed (bracket, height, aim): write it in the pin's note.")], W - 2 * M) - 24
        y = self.section(y, "Questions on site")
        c.setFillColor(NAVY); c.roundRect(M, y - 92, W - 2 * M, 104, 10, stroke=0, fill=1)
        self.logo(M + 20, y - 62, 50)
        self.text(M + 100, y - 18, COMPANY["name"].upper(), "Orbitron-Bold", 13, white, spacing=1)
        self.text(M + 100, y - 42, COMPANY["phone"], "JetBrainsMono-Bold", 16, ORANGE)
        self.text(M + 100, y - 64, COMPANY["email"] + "  ·  " + COMPANY["web"], "Outfit-Medium", 10.5, HexColor("#cbd5e1"))

    def build(self):
        self.cover(); self.safety()
        if self.d.get("parts"):
            self.parts_page()
        self.steps()
        if self.d.get("wiring") or self.d.get("sections") or self.d.get("extra"):
            self.wiring()
        self.back()
        self.footer(); self.c.save()


def main(argv):
    common = json.load(open(os.path.join(CONTENT, "_common.json")))
    files = sorted(f for f in glob.glob(os.path.join(CONTENT, "*.json")) if not os.path.basename(f).startswith("_"))
    only = [a for a in argv if not a.startswith("-")]
    out = os.path.join(HERE, "preview") if "--preview" in argv else OUT
    os.makedirs(out, exist_ok=True)
    for f in files:
        d = json.load(open(f))
        if only and d["code"] not in only:
            continue
        name = dict(OPTIMUS, **d.get("product", {}))["file"].format(code=d["code"], bracket=d.get("bracket", ""))
        path = os.path.join(out, os.path.basename(name) if out.endswith("preview") else name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        Guide(d, common, path).build()
        print("built", os.path.relpath(path, ROOT))


if __name__ == "__main__":
    main(sys.argv[1:])
