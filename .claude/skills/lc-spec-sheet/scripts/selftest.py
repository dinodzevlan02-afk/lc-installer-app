"""Rebuild the worked example and compare it with the desk's own output.

    python3 .claude/skills/lc-spec-sheet/scripts/selftest.py

Pages 2 and 3 must match the reference render pixel for pixel (within 0.5% of
pixels). Page 1 is compared only above the hero, because the reference still
carries the red PRE-RELEASE banner that Dino removed on 2026-10-21.
"""
import os, subprocess, sys, tempfile
import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
SK = os.path.dirname(HERE)
ex = os.path.join(SK, "examples", "LC-FL-WS-3CCT.json")
out = os.path.join(tempfile.mkdtemp(prefix="lcss-"), "test.pdf")
r = subprocess.run([sys.executable, os.path.join(HERE, "make_sheet.py"), ex, "--out", out], capture_output=True, text=True)
if r.returncode:
    sys.exit("build failed:\n" + r.stdout + r.stderr)
ref = pymupdf.open(os.path.join(SK, "examples", "LC-FL-WS-3CCT.reference.pdf"))
new = pymupdf.open(out)
assert len(ref) == len(new), "page count %d vs %d" % (len(new), len(ref))

def diff(a, b, clip=None):
    pa, pb = a.get_pixmap(dpi=60, clip=clip), b.get_pixmap(dpi=60, clip=clip)
    sa, sb = pa.samples, pb.samples
    bad = sum(1 for i in range(0, len(sa), pa.n) if abs(sa[i] - sb[i]) > 24)
    return bad / (pa.width * pa.height)

ok = True
for i in range(len(ref)):
    clip = pymupdf.Rect(0, 0, 612, 90) if i == 0 else None
    d = diff(ref[i], new[i], clip)
    print("page %d: %.3f%% pixels differ%s" % (i + 1, 100 * d, " (header only)" if clip else ""))
    ok &= d < 0.005
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
