"""
Turn an extracted vendor draft into an LED Connection spec sheet.

    python specsheet/rebrand.py <draft.json> --family "Omnitron Series" \
        --type "Linear High Bay" --sku LC-LHB-OLH

This is the step where a vendor's document becomes OUR product. The single
most important thing it does is DROP things:

  * the vendor's name, filename, model numbers and copy
  * anything commercial
  * every certification number, unless a human marked it verified

What survives is the physics - wattage, voltage, CCT, CRI, IP, pitch, nits -
because those describe the product we are buying, not the company selling it.

Everything carried over is unverified by construction, so the sheet renders
with its PRE-RELEASE band until a human confirms the numbers.
"""

import argparse, io, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build as builder  # noqa: E402


def pick(draft, field):
    """First candidate for a field, or None. First is not 'best' - it is a
    starting point a human edits. Pretending otherwise would be the whole
    mistake this pipeline exists to avoid."""
    e = (draft.get("extracted") or {}).get(field)
    if not e:
        return None
    c = e.get("candidates") or []
    return c[0] if c else None


def all_of(draft, field):
    e = (draft.get("extracted") or {}).get(field)
    return (e.get("candidates") or []) if e else []


def describe(draft, family, ptype, is_display=False):
    """Spec-sheet prose assembled only from facts read off the source. Reads
    like a product description; contains nothing we did not see."""
    if is_display:
        # A display has no wattage options and no CCT. The lighting sentence
        # here once produced "is a led troffer. Offered in 60W LED options."
        # on a transparent screen, off a marketing line reading "averaging
        # 60W/m2 per hour".
        pitch, nits = pick(draft, "pitch"), pick(draft, "nits")
        trans, cab = pick(draft, "transparency"), pick(draft, "cabinet_size")
        s = "The %s is a %s." % (family, ptype.lower())
        bits = []
        if pitch:
            bits.append("pixel pitch %s mm" % pitch if "mm" not in pitch.lower() else "pixel pitch %s" % pitch)
        if nits:
            bits.append("%s nits" % nits if "nit" not in nits.lower() else nits)
        if trans:
            bits.append("%s transparency" % (trans if trans.endswith("%") else trans + "%"))
        if bits:
            s += " " + ("Specified at " + ", ".join(bits) + ".")
        if cab:
            s += " Cabinet %s mm." % cab.replace("*", " x ")
        return s

    m, mat, lens = pick(draft, "mounting"), pick(draft, "material"), pick(draft, "lens")
    w, v, c, fin = (all_of(draft, "wattage"), all_of(draft, "voltage"),
                    all_of(draft, "cct"), all_of(draft, "finish"))
    # don't say "recessed recessed step light" when the type already carries it
    lead = (m.lower() + " ") if (m and m.lower() not in ptype.lower()) else ""
    s = "The %s is a %s%s" % (family, lead, ptype.lower())
    if mat:
        s += " in %s" % mat.lower()
    if lens:
        s += " with a %s lens" % lens.lower()
    s += "."
    t = ""
    if w:
        t = "Offered in %s LED options" % " / ".join(w)
    if v:
        t += (" across %s inputs" % " and ".join(v)) if t else "Available for %s inputs" % " and ".join(v)
    if c:
        t += ", in %s" % " or ".join(x.lower() for x in c)
    if t:
        s += " " + t + "."
    if len(fin) > 1:
        s += " Finished in %s or %s." % (", ".join(fin[:-1]), fin[-1])
    elif fin:
        s += " Finished in %s." % fin[0]
    return s


def to_sheet(draft, family, ptype, sku, hero_uri=None):
    ex = draft.get("extracted") or {}
    # intake records the category explicitly now. The old heuristic stays as the
    # fallback for drafts written before that, and for hand-written ones.
    cat = draft.get("_category")
    is_display = (cat == "display") if cat else bool(
        ex.get("pitch") or ex.get("nits") or ex.get("transparency"))

    if is_display:
        # These six are fixed by Dino, 2026-09-11. Not a free choice - they are
        # the sheet. A missing one shows as "-" rather than being swapped for
        # whatever else happened to be extracted.
        def _nits(v):
            return (v + " nits") if v and not v.lower().endswith("nits") else (v or "-")

        def _pct(v):
            return (v if (v or "").endswith("%") else (v + "%")) if v else "-"

        chips = {
            "PITCH":        pick(draft, "pitch") or "-",
            "BRIGHTNESS":   _nits(pick(draft, "nits")),
            "TRANSPARENCY": _pct(pick(draft, "transparency")),
            "REFRESH":      pick(draft, "refresh") or "-",
            "IP":           pick(draft, "ip_rating") or "-",
            "WARRANTY":     pick(draft, "warranty") or "-",
        }
        headline = chips["BRIGHTNESS"] if chips["BRIGHTNESS"] != "-" else "-"
    else:
        def _range(field, unit=""):
            """Selectable products carry a set, not a value. Showing the first
            extracted candidate printed '30W' on a 30/35/40W fixture and
            '3500K' on a 3CCT one - wrong, not just thin."""
            vals = all_of(draft, field)
            if not vals:
                return "-"
            if len(vals) == 1:
                return vals[0]
            nums = []
            for v in vals:
                m = re.search(r"[\d.]+", v)
                if m:
                    nums.append((float(m.group()), v))
            if len(nums) == len(vals):
                nums.sort()
                return "/".join(re.sub(r"[^\d.]", "", v) for _, v in nums) + unit
            return " / ".join(vals[:4])

        chips = {
            "WATTAGE":  _range("wattage", "W"),
            "VOLTAGE":  pick(draft, "voltage") or "-",
            "L70":      pick(draft, "lifetime") or "-",
            "WARRANTY": pick(draft, "warranty") or "-",
            "CRI":      pick(draft, "cri") or "-",
            "CCT":      _range("cct", "K"),
        }
        headline = pick(draft, "efficacy") or "-"

    LABELS = {"ip_rating": "Ingress protection", "ik_rating": "Impact rating",
              "surge": "Surge protection", "voltage": "Input voltage",
              "cct": "Colour temperature", "cri": "Colour rendering",
              "pitch": "Pixel pitch", "nits": "Brightness", "transparency": "Transparency",
              "lifetime": "Rated life", "wattage": "Wattage options",
              "material": "Housing", "lens": "Lens", "mounting": "Mounting",
              "finish": "Finishes", "efficacy": "Efficacy", "wire_length": "Lead length",
              "weight": "Weight", "dimensions": "Overall dimensions",
              # display
              "refresh": "Refresh rate", "pixel_density": "Pixel density (dot/m2)",
              "module_size": "Module size (mm)", "module_res": "Module resolution",
              "cabinet_size": "Cabinet size (mm)", "cabinet_res": "Cabinet resolution",
              "power_max": "Max power (W/m2)", "power_avg": "Average power (W/m2)",
              "leds": "LED package", "scan": "Scan", "drive_ic": "Driver IC",
              "weight_m2": "Weight (kg/m2)", "viewing_angle": "Viewing angle",
              "operating_temp": "Operating temperature", "maintenance": "Service access"}
    # Every field that was read carries over. The first version used a fixed
    # list of ten and silently dropped material, lens, mounting, finish and
    # dimensions - half of what was on the source sheet.
    overview = []
    for f in ex:
        if f in ("dimensions", "weight", "wire_length"):
            continue  # these get their own DIMENSIONS block
        vals = all_of(draft, f)
        if vals:
            overview.append("%s: %s" % (LABELS.get(f, f.replace("_", " ").title()),
                                        " / ".join(vals[:5])))
    dims = {}
    for f, lab in (("dimensions", "Overall"), ("weight", "Weight"), ("wire_length", "Lead")):
        v = pick(draft, f)
        if v:
            dims[lab] = v
    if not overview:
        overview.append("No specification extracted - every field needs entering by hand.")

    # Certifications: only what a human marked verified survives the rebrand.
    # No DLC keys at all on a display sheet - DLC is a lighting-efficiency
    # programme and a null field is an invitation to fill it in.
    if is_display:
        certs = {"ul_etl": None, "ul_standard": None, "ul_file_number": None,
                 "fcc_id": None, "control_system": None}
    else:
        certs = {"dlc_product_id": None, "dlc_verified": False, "ul_etl": None,
                 "ul_standard": None, "ul_file_number": None, "fcc_id": None}
    for key, target in (("dlc", "dlc_product_id"), ("ul", "ul_file_number"), ("fcc", "fcc_id")):
        if target not in certs:
            continue
        blk = (draft.get("possible_certifications") or {}).get(key)
        if blk and blk.get("verified") and blk.get("candidates"):
            certs[target] = blk["candidates"][0]
            if key == "dlc":
                certs["dlc_verified"] = True
            if key == "ul":
                # The UL gate needs the NAMED STANDARD, not just a file number.
                # A file number alone does not say what the product was listed
                # to, and "UL certified" on a brochure says nothing at all.
                certs["ul_standard"] = blk.get("standard") or None
                certs["ul_etl"] = blk.get("mark") or "UL"

    return {
        "family": family,
        "product_type": ptype,
        "lc_sku_prefix": sku,
        "source_request": draft.get("_source_request", ""),
        "source_supplier_id": "REDACTED-IN-OUTPUT",
        "cover": {
            "headline_efficacy": headline,
            "tagline": "SPECIFICATION UNDER REVIEW",
            "chips": chips,
            "positioning": ("Draft specification compiled from supplier documentation. "
                            "Every figure requires confirmation before release."),
        },
        # Written by us from the facts we read - never the supplier's copy, which is
        # their positioning. A previous build leaked an INTERNAL placeholder note
        # ("The product description is written by us...") onto the customer-facing
        # page. Copy is generated; the caveat lives in the pre-release band.
        "description": describe(draft, family, ptype, is_display),
        "overview": overview,
        "badges": [b for b in [
            pick(draft, "ip_rating"), pick(draft, "ik_rating"), pick(draft, "warranty"),
            pick(draft, "mounting"),
            ("%d FINISHES" % len(all_of(draft, "finish"))) if len(all_of(draft, "finish")) > 1 else None,
            ("%d WATTAGES" % len(all_of(draft, "wattage"))) if len(all_of(draft, "wattage")) > 1 else None,
        ] if b][:4],
        "dimensions": dims,
        "hero_image": hero_uri,
        # No STATUS column. Verification state lives in the draft file
        # (verified:false per field) and in the cover's pre-release band; a
        # customer-facing table stamped UNVERIFIED on every row was noise, and
        # the reference sheets' electrical tables carry no such column.
        "electrical": {"title": "TECHNICAL DATA" if is_display else "ELECTRICAL DATA",
                       "columns": ["Specification", "Value"],
                       "rows": [[LABELS.get(k, k.replace("_", " ").title()).replace("Colour temperature", "CCT"),
                                 " / ".join(all_of(draft, k)[:6])]
                                for k in (draft.get("extracted") or {})
                                if k not in ("dimensions", "weight", "wire_length")],
                       "note": "Values taken from supplier documentation. Availability varies by configuration."},
        # A display has no lumen maintenance. overlay.py skips the panel entirely
        # when the body is empty, so this must be empty rather than a placeholder.
        "callout_title": "TECHNICAL NOTE" if is_display else "LUMEN MAINTENANCE",
        "callout_body": ("" if is_display else
                         "Lumen maintenance data pending. Must be backed by an LM-80 "
                         "report and projected per IES TM-21 before publication."),
        # Both reference sheets number their segments from 02, because 01 is
        # [BRAND] and [BRAND] is always LC. That is what "LC in front of all
        # the codes" means structurally: the prefix is not decoration, it is
        # segment one of the SKU. LC - TP65X2 - 20 - X.
        "order_logic": {"sample_code": "LC - %s - XX - X" % sku.replace("LC-", "", 1),
                        "segments": [
                            {"n": "01", "name": "BRAND",
                             "options": [["LC", "LED Connection - fixed, every SKU"]]},
                            {"n": "02", "name": "SERIES",
                             "options": [[sku.replace("LC-", "", 1), family]]},
                            {"n": "03", "name": "TO BE DEFINED",
                             "options": [["XX", "pending option set"]]}]},
        "certifications": certs,
        # A display has no light distribution, so no photometric block at all.
        **({} if is_display else {"photometrics": {"ies_files": []}}),
        "footer": {"phone": "702.847.7680", "web": "www.ledconnection.com",
                   "email": "bids@ledconnection.com",
                   "address": "915 E Dale Ave Ste 110 Henderson, NV 89044"},
        "verified": {},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("draft")
    ap.add_argument("--family", required=True)
    ap.add_argument("--type", required=True, dest="ptype")
    ap.add_argument("--sku", required=True)
    ap.add_argument("--hero", help="product photo PNG/JPG for the cover")
    a = ap.parse_args()

    hero_uri = None
    if a.hero and os.path.exists(a.hero):
        import base64
        ext = os.path.splitext(a.hero)[1].lower().lstrip(".") or "png"
        hero_uri = "data:image/%s;base64,%s" % (
            "jpeg" if ext in ("jpg", "jpeg") else ext,
            base64.b64encode(open(a.hero, "rb").read()).decode("ascii"))

    # "LC in front of all the codes" - normalise rather than assume. Both
    # reference SKUs are LC-TP and LC-LHB-OLH; a prefix typed inconsistently
    # would break the join into the Master Project Tool, where Type ID is the key.
    sku = a.sku.strip().upper()
    if not sku.startswith("LC-"):
        sku = "LC-" + sku.lstrip("-")
        print("  SKU normalised to %s" % sku)

    draft = json.load(io.open(a.draft, encoding="utf-8"))
    sheet = to_sheet(draft, a.family, a.ptype, sku, hero_uri)

    # Prove the vendor did not survive. The source filename often IS the
    # vendor's name, so it is checked explicitly rather than assumed away.
    blob = json.dumps(sheet, ensure_ascii=False).lower()
    src = (draft.get("_source_document") or "")
    leaks = [w for w in re.split(r"[^A-Za-z0-9]+", src)
             if len(w) > 3 and w.lower() in blob and w.lower() not in
             ("final", "spec", "sheet", "product", "catalog", "catalogue", "connection", "led")]
    if leaks:
        print("REFUSED: words from the source filename survived into the sheet: %s"
              % ", ".join(sorted(set(leaks))))
        print("The vendor is never named on an LC spec sheet, including via a filename.")
        sys.exit(2)

    blocking, warn = builder.check(sheet)
    for w in warn:
        print("  warn: %s" % w)
    if blocking:
        for b in blocking:
            print("  BLOCK: %s" % b)
        sys.exit(2)

    os.makedirs(builder.OUT, exist_ok=True)
    name = "%s_%s_SpecSheet_%s.html" % (a.family.replace(" ", ""),
                                        a.ptype.split()[0], sku)
    path = os.path.join(builder.OUT, name)
    io.open(path, "w", encoding="utf-8").write(builder.render(sheet, warn))
    pdf = builder.to_pdf(path)
    print("\n  REBRANDED: %s" % path)
    if pdf:
        print("  PDF      : %s" % pdf)
    print("  Vendor identity removed. Everything carried over is UNVERIFIED,")
    print("  so it renders with the PRE-RELEASE band until a human signs it off.")


if __name__ == "__main__":
    main()
