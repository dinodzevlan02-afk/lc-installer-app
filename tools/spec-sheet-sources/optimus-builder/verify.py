# Independent checks on the built PDF: page count, metadata, leak words in text +
# metadata + file name, em dashes, and a positive control that the guard does fire.
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common as C
import pymupdf

pdf = os.path.join(C.OUT, "LC SPEC SHEET_HOIST HST.pdf")
d = pymupdf.open(pdf)
print("pages", len(d))
print("metadata", d.metadata)
txt = "".join(p.get_text() for p in d)
print("text chars", len(txt), "em dash", "—" in txt, "en dash", "–" in txt)
print("pdf_text_check", C.pdf_text_check(pdf))
low = txt.lower()
for w in ("lc-hst-md-300w-nv-xxk", "lc-hst-hb-300w-nv-xxk", "lc-hst-md-450w-nv-xxk", "lc-hst-hb-450w-nv-xxk",
          "etl listed (multiple listing for led connection in progress)", "warranty", "dlc", "price", "moq", "lead time",
          "lm-79", "report", "control"):
    print("  %-62s %s" % (w, low.count(w)))
# raw bytes of the file: XMP or any stray string
raw = open(pdf, "rb").read().lower()
print("raw-byte vendor hits", [w for w in C.VENDOR_WORDS if w.lower().encode() in raw])
# positive control
print("control (must FAIL):")
C.leak_check("control", "<p>YouLumi MD300 Shenzhen YL-HB300</p>")
