# Trim the chosen white-background product photos and save them into assets/ under LC names.
# usage: py -3.12 -X utf8 prep_images.py PHOTOS_DIR   (the factory Photos\200300027HZH-002 folder)
# Choices (2026-10-16, looked at every photo in MD300 and HB300):
#   MD300\MD (31)-2.jpg  disk on the crank tripod, plain white      -> assets/hst_md_stand.png
#   MD300\MD (32).jpg    disk on the post adapter with cord, white  -> assets/hst_md_head.png
#                        (a small barcode label shows through one vent: blurred out)
#   HB300\MD (7).jpg     high bay 3/4 view, hook, cord and plug     -> assets/hst_hb.png
#   HB300\MD (6).jpg     high bay side view, hook and cord          -> assets/hst_hb_side.png
# Rejected: every photo with callouts, dimension text, energy labels, scenes or banners.
import os, sys
from PIL import Image, ImageOps, ImageFilter, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1]
DST = os.path.join(HERE, "assets")


def trim(im, pad=0.03, thr=244):
    g = im.convert("L").point(lambda v: 255 if v < thr else 0)
    box = g.getbbox()
    im = im.crop(box)
    w, h = im.size
    p = int(max(w, h) * pad)
    out = Image.new("RGB", (w + 2 * p, h + 2 * p), "white")
    out.paste(im, (p, p))
    return out


def whiten(im, thr=242):
    """Push the near-white studio background to pure white so it sits on the page."""
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            if r >= thr and g >= thr and b >= thr:
                px[x, y] = (255, 255, 255)
    return im


def load(rel, maxpx):
    im = ImageOps.exif_transpose(Image.open(os.path.join(SRC, rel))).convert("RGB")
    im.thumbnail((maxpx, maxpx), Image.LANCZOS)
    return im


jobs = []
im = load(r"MD300\MD (31)-2.jpg", 2000)
jobs.append(("hst_md_stand.png", im))

im = load(r"MD300\MD (32).jpg", 1600)
w, h = im.size
# barcode label seen through a vent at about x 0.485-0.51, y 0.325-0.365 of the frame:
# paint it with the dark interior colour sampled beside it, feathered, so no block shows.
box = (int(w * 0.476), int(h * 0.322), int(w * 0.506), int(h * 0.354))
sample = im.crop((int(w * 0.506), int(h * 0.356), int(w * 0.512), int(h * 0.366)))
col = tuple(int(sum(c) / len(c)) for c in zip(*sample.getdata()))
patch = Image.new("RGB", (box[2] - box[0], box[3] - box[1]), col)
mask = Image.new("L", patch.size, 0)
from PIL import ImageDraw
ImageDraw.Draw(mask).rectangle((3, 3, patch.size[0] - 4, patch.size[1] - 4), fill=255)
mask = mask.filter(ImageFilter.GaussianBlur(3))
im.paste(patch, box, mask)
jobs.append(("hst_md_head.png", im))

jobs.append(("hst_hb.png", load(r"HB300\MD (7).jpg", 2000)))
jobs.append(("hst_hb_side.png", load(r"HB300\MD (6).jpg", 2000)))

for name, im in jobs:
    im = whiten(trim(im))
    im.save(os.path.join(DST, name), optimize=True)
    print(name, im.size)
