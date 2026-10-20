"""Cut the figures out of LED Connection's own Optimus installation manuals.

    python3 tools/guides/extract_figures.py            # every source/*.pdf -> content/figures/{code}-*.png
    python3 tools/guides/extract_figures.py --sheet    # also a contact sheet per manual, for checking

The manuals (source/Optimus-Installation-Manual-{code}-DNC1.pdf, DNC1 April
2024, from SharePoint Sales - D&E > Product > Spec Sheet > Active > Optimus)
are the content. The rebranded guides keep their drawings exactly as drawn,
so figures are rendered crops of the source pages, never redrawn:

  - parts.png      page 2 below "... Installation method": tools, the
                   exploded view and the numbered parts list
  - fig-{L}.png    each lettered figure (A, B, C ...) on the step and wiring
                   pages: from its letter down to the next letter, across
                   both columns when the other column is empty there. The
                   step text printed beside or under a drawing is blanked
                   out, because the guide sets that text again.
"""
import os, re, sys, glob
import fitz
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(HERE, "source"), os.path.join(HERE, "content", "figures")
DPI = 220
TOP, BOTTOM = 140, 738          # below the source's page header, above its footer
MID = 306                       # the source pages are two columns


def is_step(t):
    # "Step 2 - ...", and the pieces the source splits a step line into ("ep 2 - Pass ...")
    return re.search(r"(^|\s)S?t?ep\s*\d+\s*-", t) is not None


def step_rects(page):
    return [fitz.Rect(b[:4]) for b in page.get_text("blocks") if is_step(b[4])]


def crop(page, rect, path, blank=()):
    page.get_pixmap(dpi=DPI, clip=rect, alpha=False).save(path)
    k = DPI / 72.0
    hits = [b for b in blank if b.intersects(rect)]
    if not hits:
        trim(path)
        return
    if hits:
        im = Image.open(path)
        d = ImageDraw.Draw(im)
        for b in hits:
            b = (b + (-2, -2, 2, 2)) & rect
            d.rectangle([(b.x0 - rect.x0) * k, (b.y0 - rect.y0) * k, (b.x1 - rect.x0) * k, (b.y1 - rect.y0) * k], fill="white")
        im.save(path)
    trim(path)


def trim(path, pad=24):
    """Cut the white margin round the drawing, keeping a little air."""
    from PIL import ImageOps
    im = Image.open(path).convert("RGB")
    box = ImageOps.invert(im.convert("L")).point(lambda v: 255 if v > 24 else 0).getbbox()
    if box:
        x0, y0, x1, y1 = box
        im.crop((max(0, x0 - pad), max(0, y0 - pad), min(im.width, x1 + pad), min(im.height, y1 + pad))).save(path)


def drawn_in(page, rect, skip=()):
    """Union of everything drawn inside rect (vector paths, images, words),
    leaving out words inside the skip rectangles (the step text)."""
    boxes = [d["rect"] for d in page.get_drawings()]
    boxes += [page.get_image_bbox(i) for i in page.get_images(full=True)]
    boxes += [fitz.Rect(w[:4]) for w in page.get_text("words") if not any(fitz.Rect(w[:4]).intersects(s) for s in skip)]
    u = fitz.Rect()
    for b in boxes:
        b = fitz.Rect(b)
        if b.is_empty or b.is_infinite or b.width > 500:
            continue
        if rect.contains(b) or (rect.intersects(b) and (b & rect).get_area() > 0.6 * b.get_area()):
            u |= b
    return u


def figures(code, doc):
    out = []
    # parts / tools: page 2 from under the "Installation method" title
    p = doc[1]
    head = [b for b in p.get_text("blocks") if "installation method" in b[4].lower()]
    top = head[0][3] + 6 if head else 250
    r = drawn_in(p, fitz.Rect(30, top, 590, BOTTOM))
    out.append(("parts", p, r + (-8, -8, 8, 8)))

    for pi in range(2, doc.page_count):
        p = doc[pi]
        words = p.get_text("words")
        labels = [w for w in words if re.fullmatch(r"[A-I]", w[4]) and w[1] > TOP and (w[3] - w[1]) > 9]
        labels = [w for i, w in enumerate(labels) if not any(abs(w[0] - v[0]) < 3 and abs(w[1] - v[1]) < 3 for v in labels[:i])]
        steps = step_rects(p)
        left = lambda v: v[0] < MID
        for w in labels:
            # stop at the next figure below, in either column (a figure under the
            # other column can run under this one, as the wall hole sizes do)
            same = [l for l in labels if l is not w and l[1] > w[3] + 20]
            stop = min(l[1] for l in same) - 6 if same else BOTTOM
            # the other column is free over this span: let the drawing run into it
            other = [l for l in labels if left(l) != left(w) and l[1] < stop and l[3] + 60 > w[1] - 6]
            col = (30, MID - 4) if left(w) else (MID - 4, 590)
            if not other:
                col = (30, 590)
            cell = fitz.Rect(col[0], w[1] - 6, col[1], stop)
            r = drawn_in(p, cell, steps)
            if r.is_empty or r.height < 30:
                continue
            out.append(("fig-" + w[4], p, (r + (-6, -6, 6, 6)) & cell))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    for f in sorted(glob.glob(os.path.join(SRC, "*.pdf"))):
        code = re.search(r"Manual-([A-Z]+)-", f).group(1)
        doc = fitz.open(f)
        figs = figures(code, doc)
        for name, page, rect in figs:
            crop(page, rect, os.path.join(OUT, code + "-" + name + ".png"), step_rects(page))
        print(code, " ".join(n for n, _, _ in figs))
        if "--sheet" in sys.argv:
            sheet = fitz.open()
            for name, page, rect in figs:
                pg = sheet.new_page(width=rect.width + 20, height=rect.height + 40)
                pg.insert_text((10, 20), code + "-" + name, fontsize=12)
                pg.show_pdf_page(fitz.Rect(10, 30, rect.width + 10, rect.height + 30), doc, page.number, clip=rect)
            os.makedirs(os.path.join(HERE, "preview"), exist_ok=True)
            sheet.save(os.path.join(HERE, "preview", "figures-" + code + ".pdf"))


if __name__ == "__main__":
    main()
