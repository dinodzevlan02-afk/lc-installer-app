"""
Lift the product photo off a vendor datasheet.

Why this is not just "extract the biggest embedded image": on the Torshare
troffer sheet the cover photo is **tiled** - the fixture is sliced across ~18
separate 860x834 JPEGs, and the largest single one is a featureless corner of
the diffuser. Extraction returns a fragment that looks like nothing.

So the page is re-rendered and cropped instead. That reassembles whatever the
PDF did, however it did it, and works equally for a single placed image.

The crop is a projection profile: find the rows that carry ink, take the tallest
contiguous band, then its horizontal extent. The vendor's logo band at the top
and the address footer at the bottom are excluded by position before profiling -
they are the two things guaranteed to be on a datasheet cover and guaranteed not
to be the product.

AGENT.md 6 allows a vendor photo as our hero when it carries no badge or
watermark. That judgement is a HUMAN's - this returns a candidate and the caller
says so on the sheet.
"""

import os

TOP_SKIP = 0.10      # logo band
BOT_SKIP = 0.12      # address / page footer
NEAR_WHITE = 244


def find(pdf_path, out_png, page_no=0, dpi=200):
    import pymupdf
    doc = pymupdf.open(pdf_path)
    if page_no >= doc.page_count:
        return None
    page = doc[page_no]

    pm = page.get_pixmap(dpi=90)
    w, h, n = pm.width, pm.height, pm.n
    buf = pm.samples

    y0 = int(h * TOP_SKIP)
    y1 = int(h * (1 - BOT_SKIP))

    def ink_in_row(y):
        c = 0
        base = y * pm.stride
        for x in range(0, w, 2):                     # every other pixel is plenty
            i = base + x * n
            if buf[i] < NEAR_WHITE or buf[i + 1] < NEAR_WHITE or buf[i + 2] < NEAR_WHITE:
                c += 1
        return c

    thresh = (w // 2) * 0.06
    rows = [y for y in range(y0, y1) if ink_in_row(y) > thresh]
    if not rows:
        return None

    # tallest contiguous band, allowing small gaps (a caption line inside a photo)
    bands, start, prev = [], rows[0], rows[0]
    for y in rows[1:]:
        if y - prev > 6:
            bands.append((start, prev))
            start = y
        prev = y
    bands.append((start, prev))
    top, bot = max(bands, key=lambda b: b[1] - b[0])
    if bot - top < h * 0.12:
        return None

    cols = []
    for x in range(0, w, 2):
        c = 0
        for y in range(top, bot, 2):
            i = y * pm.stride + x * n
            if buf[i] < NEAR_WHITE or buf[i + 1] < NEAR_WHITE or buf[i + 2] < NEAR_WHITE:
                c += 1
        if c > ((bot - top) // 2) * 0.06:
            cols.append(x)
    if not cols:
        return None
    left, right = cols[0], cols[-1]
    if right - left < w * 0.25:
        return None

    # back to PDF points, then re-render just that box at print resolution
    sx, sy = page.rect.width / w, page.rect.height / h
    clip = pymupdf.Rect(left * sx, top * sy, right * sx, bot * sy)
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    page.get_pixmap(dpi=dpi, clip=clip).save(out_png)
    doc.close()
    return out_png
