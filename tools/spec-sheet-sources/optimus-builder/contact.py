# Contact sheet of every jpg in a folder, numbered, for picking photos.
# usage: py -3.12 -X utf8 contact.py FOLDER out.png
import os, sys
from PIL import Image, ImageDraw, ImageOps

src, out = sys.argv[1], sys.argv[2]
fs = sorted(f for f in os.listdir(src) if f.lower().endswith((".jpg", ".jpeg", ".png")))
T = 300
cols = 4
rows = (len(fs) + cols - 1) // cols
sheet = Image.new("RGB", (cols * T, rows * (T + 24)), "white")
dr = ImageDraw.Draw(sheet)
for i, f in enumerate(fs):
    im = Image.open(os.path.join(src, f))
    im = ImageOps.exif_transpose(im).convert("RGB")
    w, h = im.size
    im.thumbnail((T - 8, T - 8))
    x, y = (i % cols) * T, (i // cols) * (T + 24)
    sheet.paste(im, (x + 4, y + 4))
    dr.text((x + 6, y + T + 4), "%d %s %dx%d" % (i, f.encode("ascii", "replace").decode(), w, h), fill="black")
sheet.save(out)
for i, f in enumerate(fs):
    print(i, f)
