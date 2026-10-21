# Dump the text layer of vendor PDFs (data only) and render page images for reading.
# usage: py -3.12 -X utf8 extract_text.py OUTDIR file1.pdf [file2.pdf ...]
import os, sys
import pymupdf

out = sys.argv[1]
os.makedirs(out, exist_ok=True)
for i, p in enumerate(sys.argv[2:]):
    d = pymupdf.open(p)
    tag = "doc%d" % i
    print("=" * 80)
    print(tag, os.path.basename(p), "pages:", len(d))
    for n, pg in enumerate(d):
        print("--- page", n + 1)
        print(pg.get_text())
        pg.get_pixmap(dpi=100).save(os.path.join(out, "%s_p%d.png" % (tag, n + 1)))
