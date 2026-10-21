# IESNA LM-63 reader + polar candela plot (SVG), nadir (0 deg) at the bottom. No curve is ever drawn from anything
# but a real IES file: AGENT.md section 3.
import io, math, re


def read(path):
    raw = io.open(path, encoding="latin-1").read().splitlines()
    kw = {}
    i = 0
    while i < len(raw) and not raw[i].strip().upper().startswith("TILT"):
        m = re.match(r"\[([A-Z0-9_]+)\]\s*(.*)", raw[i].strip(), re.I)
        if m:
            kw.setdefault(m.group(1).upper(), []).append(m.group(2))
        i += 1
    tilt = raw[i].strip()
    i += 1
    if tilt.upper() != "TILT=NONE":
        raise SystemExit("TILT data present, not handled: " + path)
    nums = []
    for ln in raw[i:]:
        nums += [float(x) for x in ln.replace(",", " ").split()]
    nlamp = int(nums[0]); lum = nums[1]; mult = nums[2]
    nv = int(nums[3]); nh = int(nums[4])
    ptype = int(nums[5]); units = int(nums[6])
    w, l, h = nums[7], nums[8], nums[9]
    ballast = nums[10]; watts = nums[12]
    p = 13
    vang = nums[p:p + nv]; p += nv
    hang = nums[p:p + nh]; p += nh
    cd = []
    for _ in range(nh):
        cd.append([v * mult * ballast for v in nums[p:p + nv]]); p += nv
    return dict(kw=kw, nlamp=nlamp, lum=lum, mult=mult, nv=nv, nh=nh, ptype=ptype,
                units=units, size=(w, l, h), watts=watts, vang=vang, hang=hang, cd=cd)


def plane(d, h):
    """Candela values on the horizontal plane nearest h degrees."""
    j = min(range(d["nh"]), key=lambda k: abs(d["hang"][k] - h))
    return d["hang"][j], d["cd"][j]


def _h_average(d, iv):
    """Mean candela around the full 360 deg at one vertical angle, respecting the
    LM-63 symmetry convention. 0..180 in the file means mirror it; 0..360 means the
    last plane repeats the first. Getting this wrong inflated the flux by 8 percent."""
    nh = d["nh"]; ha = d["hang"]; cd = d["cd"]
    if nh == 1:
        return cd[0][iv]
    span = ha[-1] - ha[0]
    if abs(span - 360.0) < 1e-6:                       # 0..360, last == first
        return sum(cd[ih][iv] for ih in range(nh - 1)) / (nh - 1)
    if abs(span - 180.0) < 1e-6:                       # 0..180, mirrored
        s = cd[0][iv] + cd[nh - 1][iv] + 2 * sum(cd[ih][iv] for ih in range(1, nh - 1))
        return s / (2 * (nh - 1))
    if abs(span - 90.0) < 1e-6:                        # 0..90, quadrant symmetry
        s = cd[0][iv] + cd[nh - 1][iv] + 2 * sum(cd[ih][iv] for ih in range(1, nh - 1))
        return s / (2 * (nh - 1))
    return sum(cd[ih][iv] for ih in range(nh)) / nh


def total_lumens(d):
    """Zonal integration of the candela table (IES LM-63 standard method)."""
    nv = d["nv"]; va = d["vang"]
    tot = 0.0
    for iv in range(nv):
        lo = va[0] if iv == 0 else (va[iv] + va[iv - 1]) / 2.0
        hi = va[-1] if iv == nv - 1 else (va[iv] + va[iv + 1]) / 2.0
        zone = 2 * math.pi * (math.cos(math.radians(lo)) - math.cos(math.radians(hi)))
        tot += _h_average(d, iv) * zone
    return tot


def zonal_table(d):
    """Flux in each 10 degree vertical zone, same method as total_lumens."""
    out = []
    nv = d["nv"]; va = d["vang"]
    per = [0.0] * nv
    for iv in range(nv):
        lo = va[0] if iv == 0 else (va[iv] + va[iv - 1]) / 2.0
        hi = va[-1] if iv == nv - 1 else (va[iv] + va[iv + 1]) / 2.0
        per[iv] = _h_average(d, iv) * 2 * math.pi * (
            math.cos(math.radians(lo)) - math.cos(math.radians(hi)))
    top = int(va[-1])
    for z0 in range(0, top, 10):
        z1 = z0 + 10
        s = sum(per[iv] for iv in range(nv) if z0 <= va[iv] < z1 or (z1 == top and va[iv] == top))
        out.append((z0, z1, s))
    return out


def max_cd(d):
    best = (0.0, 0.0, 0.0)
    for ih in range(d["nh"]):
        for iv in range(d["nv"]):
            if d["cd"][ih][iv] > best[0]:
                best = (d["cd"][ih][iv], d["vang"][iv], d["hang"][ih])
    return best


NAVY = "#1b1d2b"; ORANGE = "#f37021"; GREY = "#8a8d99"; LINE = "#d9dbe1"


def polar_svg(d, planes, title, size=360, half=False, rel=False):
    """planes: list of (h_degrees, colour, label). half=True plots 0..90 only (mirrored).
    rel=True (added 2026-10-12): candela already normalised to percent of peak; rings at 25 percent."""
    cx = size / 2.0; cy = size / 2.0 if not half else size * 0.14
    R = size * 0.40 if not half else size * 0.78
    peak = max(max(v for v in d["cd"][ih]) for ih in range(d["nh"]))
    step = 10 ** math.floor(math.log10(peak)) if peak > 0 else 1
    for m in (1, 2, 2.5, 5, 10):
        if step * m >= peak / 3.0:
            step = step * m; break
    if rel:
        step = 25.0
    rings = int(math.ceil(peak / step))
    rmax = rings * step
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %g %g" width="100%%">' % (size, size * (0.95 if half else 1.05))]
    out.append('<rect width="100%" height="100%" fill="#ffffff"/>')
    for k in range(1, rings + 1):
        r = R * k / rings
        out.append('<circle cx="%g" cy="%g" r="%g" fill="none" stroke="%s" stroke-width="0.6"/>' % (cx, cy, r, LINE))
        out.append('<text x="%g" y="%g" font-family="Poppins" font-size="6" fill="%s">%s</text>'
                   % (cx + 2, cy - r + 7, GREY, ("%d%%" % (step * k)) if rel else "{:,.0f}".format(step * k)))
    for ang in range(0, 180 if half else 360, 15):
        a = math.radians(ang + 90)
        x2 = cx + R * math.cos(a); y2 = cy + R * math.sin(a)
        out.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" stroke-width="0.4"/>' % (cx, cy, x2, y2, LINE))
    for ang in range(0, 181, 30):
        a = math.radians(ang + 90)
        lx = cx + (R + 11) * math.cos(a); ly = cy + (R + 11) * math.sin(a) + 2
        out.append('<text x="%g" y="%g" font-family="Poppins" font-size="6.5" fill="%s" text-anchor="middle">%d</text>'
                   % (lx, ly, GREY, ang))
        if not half and ang not in (0, 180):
            a2 = math.radians(-ang + 90)
            out.append('<text x="%g" y="%g" font-family="Poppins" font-size="6.5" fill="%s" text-anchor="middle">%d</text>'
                       % (cx + (R + 11) * math.cos(a2), cy + (R + 11) * math.sin(a2) + 2, GREY, ang))
    for h, col, lab in planes:
        ha, vals = plane(d, h)
        pts = []
        for s in (1, -1):
            seq = range(d["nv"]) if s == 1 else range(d["nv"] - 1, -1, -1)
            hh = ha if s == 1 else (ha + 180) % 360
            jv = plane(d, hh)[1] if s == -1 else vals
            for iv in seq:
                v = d["vang"][iv]
                r = R * min(jv[iv], rmax) / rmax
                a = math.radians(s * v + 90)
                pts.append("%g,%g" % (cx + r * math.cos(a), cy + r * math.sin(a)))
        out.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="1.6" stroke-linejoin="round"/>'
                   % (" ".join(pts), col))
    ly = size * 1.03 if not half else size * 0.90
    lx = 6
    for h, col, lab in planes:
        out.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" stroke-width="2"/>' % (lx, ly - 2.5, lx + 12, ly - 2.5, col))
        out.append('<text x="%g" y="%g" font-family="Poppins" font-size="7" fill="%s">%s</text>' % (lx + 15, ly, NAVY, lab))
        lx += 15 + 6.2 * len(lab) + 10
    out.append('<text x="%g" y="10" font-family="Poppins" font-size="7.5" font-weight="700" fill="%s" text-anchor="middle">%s</text>'
               % (cx, NAVY, title))
    out.append("</svg>")
    return "\n".join(out)
