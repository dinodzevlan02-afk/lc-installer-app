# Save a downscaled copy (or a crop) of one image for inspection.
# usage: py -3.12 -X utf8 look.py in.jpg out.png maxpx [x0 y0 x1 y1 as fractions]
import sys
from PIL import Image, ImageOps
im = ImageOps.exif_transpose(Image.open(sys.argv[1])).convert("RGB")
if len(sys.argv) > 4:
    w, h = im.size
    x0, y0, x1, y1 = map(float, sys.argv[4:8])
    im = im.crop((int(w * x0), int(h * y0), int(w * x1), int(h * y1)))
im.thumbnail((int(sys.argv[3]), int(sys.argv[3])))
im.save(sys.argv[2])
print(im.size)
