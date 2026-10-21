"""Crop the step drawings for the Kroger 345 guides out of the supplier documents.

    python3 tools/guides/kroger345/extract_figures.py [--sheet]

Each crop is the drawing only: never the supplier's header, logo, footer or the
English caption printed in the box (the guide writes its own step text).
Clips are in PDF points, measured off renders of the source pages.
"""
import os, sys
import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
FIG = os.path.join(ROOT, "tools", "guides", "content", "figures")
SRC = {
    "flood": os.path.join(ROOT, "tools", "specs", "sources", "LC-FL-WS-3CCT", "vendor-datasheet.pdf"),
    "wallpack": os.path.join(ROOT, "tools", "specs", "sources", "LC-FWP-WS-3CCT", "fcw-spec-install.pdf"),
    # downlight: the goof ring instruction's drawings (a spring-clip downlight with its
    # junction box on a whip, as LC-UDL-8-A) and LC's own Universal Downlight sheet
    "ring": os.path.join(ROOT, "tools", "guides", "source", "kroger345", "downlight", "litetronics-goof-ring.pdf"),
    "udl": os.path.join(ROOT, "tools", "specs", "lc-existing", "LC SPEC SHEET_Universal Downlight Series.pdf"),
}
# name: (source, page index, clip x0, y0, x1, y1)
CROPS = {
    # flood, yoke
    "FLY-fig-A": ("flood", 4, 26, 588, 192, 686),
    "FLY-fig-B": ("flood", 4, 209, 588, 382, 686),
    "FLY-fig-C": ("flood", 4, 396, 588, 569, 686),
    "FLY-fig-D": ("flood", 5, 26, 172, 192, 260),
    "FLY-fig-E": ("flood", 5, 209, 172, 382, 260),
    "FLY-fig-F": ("flood", 5, 396, 172, 569, 260),
    "FLY-fig-G": ("flood", 5, 26, 312, 192, 430),
    # flood, slip-fitter
    "FLS-fig-A": ("flood", 3, 37, 174, 210, 254),
    "FLS-fig-B": ("flood", 3, 219, 162, 381, 254),
    "FLS-fig-C": ("flood", 3, 390, 162, 566, 254),
    "FLS-fig-D": ("flood", 3, 37, 288, 210, 404),
    "FLS-fig-E": ("flood", 3, 219, 304, 381, 400),
    # flood, wattage / CCT selector (both mountings)
    "FL-set-A": ("flood", 5, 41, 584, 282, 686),
    "FL-set-B": ("flood", 5, 308, 584, 575, 686),
    "FL-set-C": ("flood", 6, 41, 212, 282, 360),
    "FL-set-D": ("flood", 6, 308, 212, 562, 360),
    # wall pack
    "FWP-fig-A": ("wallpack", 4, 42, 628, 279, 732),
    "FWP-fig-B": ("wallpack", 4, 301, 628, 563, 732),
    "FWP-fig-C": ("wallpack", 5, 62, 168, 292, 288),
    "FWP-fig-D": ("wallpack", 5, 304, 168, 569, 288),
    "FWP-fig-E": ("wallpack", 5, 62, 350, 292, 463),
    "FWP-fig-F": ("wallpack", 5, 304, 350, 569, 472),
    "FWP-fig-G": ("wallpack", 5, 62, 508, 292, 613),
    "FWP-set-A": ("wallpack", 4, 140, 174, 352, 288),
    # downlight with goof ring
    "UDL-fig-A": ("ring", 1, 100, 131, 218, 238),
    "UDL-fig-B": ("ring", 1, 100, 274, 218, 382),
    "UDL-fig-C": ("ring", 1, 368, 48, 506, 141),
    "UDL-dims": ("udl", 0, 17, 349.6, 245, 418),
}
# white-out inside a crop (pixels of the 4x render): a corner of the sheet's photo above the drawing
WHITE = {"UDL-dims": [(560, 0, 820, 14)]}


def main(argv):
    docs = {k: pymupdf.open(v) for k, v in SRC.items() if os.path.exists(v)}
    z = pymupdf.Matrix(4, 4)
    for name, (src, pg, *clip) in CROPS.items():
        pix = docs[src][pg].get_pixmap(matrix=z, clip=pymupdf.Rect(*clip))
        for r in WHITE.get(name, []):
            pix.set_rect(pymupdf.IRect(*r) + (pix.x, pix.y, pix.x, pix.y), (255, 255, 255))
        pix.save(os.path.join(FIG, name + ".png"))
        print(name)
    if "--sheet" in argv:                       # contact sheet to check the crops by eye
        out = pymupdf.open()
        pg = out.new_page(width=612, height=792)
        for i, name in enumerate(CROPS):
            r = pymupdf.Rect(10 + (i % 4) * 150, 10 + (i // 4) * 120, 155 + (i % 4) * 150, 120 + (i // 4) * 120)
            pg.insert_image(r, filename=os.path.join(FIG, name + ".png"))
            pg.insert_text((r.x0, r.y1 + 8), name, fontsize=6)
        out.save(argv[argv.index("--sheet") + 1])


if __name__ == "__main__":
    main(sys.argv)
