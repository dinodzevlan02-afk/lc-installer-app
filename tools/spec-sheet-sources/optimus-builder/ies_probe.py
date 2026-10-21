# Probe IES files: header keywords, watts, lumens, peak, beam/field.
# usage: py -3.12 -X utf8 ies_probe.py file1.ies [file2.ies ...]
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ies


def angles(d):
    out = []
    planes = range(d["nh"] - 1) if d["nh"] > 1 else range(1)
    for ih in planes:
        c = d["cd"][ih]; va = d["vang"]; pk = max(c); row = []
        for frac in (0.5, 0.1):
            t = pk * frac
            ang = None
            for i in range(c.index(pk) + 1, len(c)):
                if c[i] < t <= c[i - 1]:
                    ang = 2 * (va[i - 1] + (c[i - 1] - t) / (c[i - 1] - c[i]) * (va[i] - va[i - 1]))
                    break
            row.append(ang)
        out.append(row)
    ok = [r for r in out if r[0] is not None and r[1] is not None]
    return (sum(r[0] for r in ok) / len(ok) if ok else None, sum(r[1] for r in ok) / len(ok) if ok else None)


for p in sys.argv[1:]:
    d = ies.read(p)
    print("=" * 70)
    print(os.path.basename(p))
    for k, v in d["kw"].items():
        print("  [%s] %s" % (k, " | ".join(v)))
    print("  nlamp %d lum %g mult %g nv %d nh %d ptype %d units %d size %s watts %g"
          % (d["nlamp"], d["lum"], d["mult"], d["nv"], d["nh"], d["ptype"], d["units"], d["size"], d["watts"]))
    print("  vang %g..%g  hang %g..%g" % (d["vang"][0], d["vang"][-1], d["hang"][0], d["hang"][-1]))
    lm = ies.total_lumens(d)
    pk = ies.max_cd(d)
    b, f = angles(d)
    print("  lumens %.0f  lm/W %.1f  peak %.0f cd at v%g h%g  beam %s field %s"
          % (lm, lm / d["watts"], pk[0], pk[1], pk[2], b, f))
    z = ies.zonal_table(d)
    print("  zonal:", ", ".join("%d-%d:%.0f" % t for t in z))
