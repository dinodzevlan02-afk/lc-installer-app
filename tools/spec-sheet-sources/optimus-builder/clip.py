# Render a clip of one PDF page at high dpi for reading.
# usage: py -3.12 -X utf8 clip.py in.pdf page x0 y0 x1 y1 (fractions 0..1) out.png [dpi]
import sys
import pymupdf
p, pg, x0, y0, x1, y1, out = sys.argv[1], int(sys.argv[2]), *map(float, sys.argv[3:7]), sys.argv[7]
dpi = int(sys.argv[8]) if len(sys.argv) > 8 else 250
d = pymupdf.open(p)
page = d[pg - 1]
r = page.rect
clip = pymupdf.Rect(r.x0 + r.width * x0, r.y0 + r.height * y0, r.x0 + r.width * x1, r.y0 + r.height * y1)
page.get_pixmap(dpi=dpi, clip=clip).save(out)
print(out)
