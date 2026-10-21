# Independent checks on the built LC OPTIMUS PDF: page count, metadata, vendor words and patterns in
# text + metadata + file name + raw bytes, em dash / primes / commercial terms, image inventory, and
# a positive control that the guard fires.
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common as C
import pymupdf

pdf = os.path.join(C.OUT, "LC SPEC SHEET_OPTIMUS SERIES SLOT 2026.pdf")
d = pymupdf.open(pdf)
print("pages", len(d))
print("metadata", d.metadata)
print("xmp metadata length", len(d.get_xml_metadata() or ""))
txt = "".join(p.get_text() for p in d)
low = txt.lower()
print("text chars", len(txt), "| em dash", "—" in txt, "| en dash", "–" in txt,
      "| primes", any(ch in txt for ch in "′″“”’"))
print("pdf_text_check", C.pdf_text_check(pdf))
for pat in C.MONEY + [r"lead time", r"\bmoq\b"]:
    if re.search(pat, low):
        print("  COMMERCIAL HIT", pat)
for w in ("lc-slot-s-75w-nv-xx-50-80-ty03-f-bk", "dlc listing for led connection in progress (standard)",
          "sensor and photocell versions: contact led connection",
          "additional lens options will carry their own distribution code", "dlc-reported", "culus"):
    print("  %-66s %d" % (w, low.count(w)))
raw = open(pdf, "rb").read().lower()
longw = [w for w in C.VENDOR_WORDS if len(w) >= 5]
print("raw-byte vendor hits (words >= 5 chars)", [w for w in longw if w.lower().encode() in raw])
print("raw-byte short words", {w: raw.count(w.lower().encode()) for w in C.VENDOR_WORDS if len(w) < 5})
imgs = set()
for p in d:
    for im in p.get_images(full=True):
        imgs.add((im[2], im[3]))
print("images (w,h)", sorted(imgs))
print("file name", os.path.basename(pdf))
print("control (must FAIL):")
C.leak_check("control", "<p>AOK-75WoT-NVS-S5-DV-4080-T302 Seoul OT Series aokledlight</p>")
