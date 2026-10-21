"""Clean a product photo for the LC sheet: lift it off the supplier's coloured
background onto white, upscale, sharpen a touch.

    python3 .claude/skills/lc-spec-sheet/scripts/clean_photo.py <src.pdf> <xref,xref,...> <out.png>
    python3 .claude/skills/lc-spec-sheet/scripts/clean_photo.py <src.png> - <out.png> [scale]

scale (default 4) is a plain LANCZOS upscale. For a photo-quality hero, run
esrgan_np.py (Real-ESRGAN x4, numpy only) on the small photo first and pass
its output with scale 1.

Xrefs are image objects in the PDF (pymupdf page.get_images), stacked top to
bottom: supplier sheets often slice one photo into strips. The background is
found by flooding in from the edges over light, bluish pixels; a neutral lens
or white housing is never bluish, so it stays. Look at the result: a product
photographed on a neutral grey or white needs a different test.
Use it as "hero": {"png": "..."} in the product file.
"""
import sys
from collections import deque
from PIL import Image, ImageFilter, ImageEnhance
import pymupdf


def load(src, xrefs):
    if xrefs == "-":
        return Image.open(src).convert("RGB")
    d = pymupdf.open(src)
    parts = []
    for x in map(int, xrefs.split(",")):
        p = pymupdf.Pixmap(d, x)
        if p.n - p.alpha > 3:
            p = pymupdf.Pixmap(pymupdf.csRGB, p)
        if p.alpha:
            p = pymupdf.Pixmap(p, 0)
        parts.append(Image.frombytes("RGB", (p.width, p.height), p.samples))
    im = Image.new("RGB", (max(p.width for p in parts), sum(p.height for p in parts)), "white")
    y = 0
    for p in parts:
        im.paste(p, (0, y)); y += p.height
    return im


src, xrefs, out = sys.argv[1], sys.argv[2], sys.argv[3]
S = int(sys.argv[4]) if len(sys.argv) > 4 else 4
im = load(src, xrefs); W, H = im.size; px = im.load()
bg = [[False]*W for _ in range(H)]
q = deque()
light = lambda c: sum(c) / 3 > 150 and c[2] - c[0] >= 2   # the background is bluish, the lens neutral
for x in range(W):
    for y in (0, H-1): q.append((x, y))
for y in range(H):
    for x in (0, W-1): q.append((x, y))
for x, y in q: bg[y][x] = light(px[x, y])
q = deque(p for p in q if bg[p[1]][p[0]])
while q:
    x, y = q.popleft(); c = px[x, y]
    for nx, ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
        if 0 <= nx < W and 0 <= ny < H and not bg[ny][nx]:
            n = px[nx, ny]
            if light(n) and max(abs(a-b) for a, b in zip(c, n)) < 14:
                bg[ny][nx] = True; q.append((nx, ny))
mask = Image.new("L", (W, H), 0); m = mask.load()
for y in range(H):
    for x in range(W):
        m[x, y] = 0 if bg[y][x] else 255
mask = mask.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8 * max(1, 4 // S) if S > 1 else 2.4))
big = im.resize((W*S, H*S), Image.LANCZOS) if S > 1 else im
if S > 1:
    big = big.filter(ImageFilter.UnsharpMask(radius=2, percent=90, threshold=2))
big = ImageEnhance.Contrast(big).enhance(1.06)
bmask = mask.resize((W*S, H*S), Image.LANCZOS)
white = Image.new("RGB", big.size, "white")
res = Image.composite(big, white, bmask)
bbox = bmask.point(lambda v: 255 if v > 20 else 0).getbbox()
pad = 24 if S > 1 else 40
res = res.crop((max(0,bbox[0]-pad), max(0,bbox[1]-pad), min(W*S,bbox[2]+pad), min(H*S,bbox[3]+pad)))
res.save(out); print(res.size)
