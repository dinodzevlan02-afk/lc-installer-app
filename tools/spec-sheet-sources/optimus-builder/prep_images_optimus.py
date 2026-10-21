# Build the LC OPTIMUS assets from OUR OWN 2023 LC sheet (LC SPEC SHEET_Optimus Series Ultra
# Area Luminaire_V202304.pdf). Every image here comes out of that LC document; nothing is taken
# from the factory catalogue. Images are re-encoded through PIL, so no source metadata survives.
# usage: py -3.12 -X utf8 prep_images_optimus.py OLD_LC_SHEET.pdf
#   p1 Im0 (xref 295 + soft mask 294)  luminaire render on a square pole, transparent  -> slot_hero.png, slot_head.png
#   p6 xref 78/73/76/79/80              bracket line drawings S, R, F, U, T              -> br_S/R/F/U/T.png
# Rejected: p1 xref 285 (front/back/side photo: shows a sensor, which the Standard version does
# not have), p3 photometry plots (160 W L1 model, not on this listing), p7 pole page.
import os, sys
import pymupdf
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
DST = os.path.join(HERE, "assets")
d = pymupdf.open(sys.argv[1])


def pix(xref, smask=0):
    base = pymupdf.Pixmap(d, xref)
    if base.n - base.alpha > 3:
        base = pymupdf.Pixmap(pymupdf.csRGB, base)
    if smask:
        base = pymupdf.Pixmap(base, pymupdf.Pixmap(d, smask))
    mode = "RGBA" if base.alpha else "RGB"
    im = Image.frombytes(mode, (base.width, base.height), base.samples)
    if mode == "RGBA":
        bg = Image.new("RGB", im.size, "white")
        bg.paste(im, mask=im.split()[3])
        im = bg
    return im


def trim(im, pad=0.02, thr=246):
    g = im.convert("L").point(lambda v: 255 if v < thr else 0)
    im = im.crop(g.getbbox())
    w, h = im.size
    p = int(max(w, h) * pad)
    out = Image.new("RGB", (w + 2 * p, h + 2 * p), "white")
    out.paste(im, (p, p))
    return out


hero = pix(295, 294)
# The render carries faint white flecks on its transparent background (y 600-760 px); on white
# they vanish. Trim, then save the full pole view and a crop of the luminaire head.
#  - Two tiny marking plates on the LED board (illegible at any size, but they could be a maker's
#    plate) are blurred out. Boxes measured on slot_head.png, mapped back to raw-render pixels.
#  - Faint white flecks left of the pole (from the transparent render) are pushed to pure white.
from PIL import ImageFilter, ImageDraw
w0, h0 = hero.size
_crop = hero.crop((0, 0, w0, int(h0 * 0.27)))
_bb = _crop.convert("L").point(lambda v: 255 if v < 246 else 0).getbbox()
_p = int(max(_bb[2] - _bb[0], _bb[3] - _bb[1]) * 0.02)
for (x0, y0, x1, y1) in ((540, 182, 606, 194), (738, 164, 770, 174)):
    box = (x0 - _p + _bb[0], y0 - _p + _bb[1], x1 - _p + _bb[0], y1 - _p + _bb[1])
    reg = hero.crop(box).filter(ImageFilter.MinFilter(7)).filter(ImageFilter.GaussianBlur(1.2))
    mask = Image.new("L", reg.size, 0)
    ImageDraw.Draw(mask).rectangle((2, 2, reg.size[0] - 3, reg.size[1] - 3), fill=255)
    hero.paste(reg, box, mask.filter(ImageFilter.GaussianBlur(1.5)))
px = hero.load()
for y in range(int(h0 * 0.25), h0):
    for x in range(0, int(w0 * 0.68)):
        r, g, b = px[x, y]
        if r > 200 and g > 200 and b > 200:
            px[x, y] = (255, 255, 255)
hero_t = trim(hero)
hero_t.save(os.path.join(DST, "slot_hero.png"), optimize=True)
w, h = hero.size
head = trim(hero.crop((0, 0, w, int(h * 0.27))))
head.save(os.path.join(DST, "slot_head.png"), optimize=True)
print("slot_hero.png", hero_t.size, "slot_head.png", head.size)

for code, x, sm in (("S", 78, 0), ("R", 73, 0), ("F", 76, 0), ("U", 79, 0), ("T", 80, 0)):
    im = trim(pix(x, sm), pad=0.03)
    im.save(os.path.join(DST, "br_%s.png" % code), optimize=True)
    print("br_%s.png" % code, im.size)
