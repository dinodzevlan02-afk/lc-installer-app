"""
Drop a vendor datasheet in, get a spec sheet DRAFT out.

    python specsheet/intake.py                 process anything in the drop folder
    python specsheet/intake.py <file.pdf>      process one file

What it does NOT do is decide anything. It reads a supplier PDF, pulls out the
numbers it can find, and writes a draft data file with every one of them marked
unverified. A human confirms them before the sheet loses its PRE-RELEASE band.

That is the whole design. Extraction is cheap and often wrong; the expensive
part is knowing which numbers you are willing to put LED Connection's name on.
"""

import io, json, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import tablespec  # noqa: E402

_od = os.environ.get("OneDriveCommercial") or os.environ.get("OneDrive")
ENG = os.path.join(_od, "LED Documents - Engineering", "Sourcing Dino") if _od else None
DROP = os.path.join(ENG, "_DROP VENDOR FILES HERE") if ENG else os.path.join(HERE, "drop")
DRAFTS = os.path.join(ENG, "Spec Sheet Drafts") if ENG else os.path.join(HERE, "output")
SRC = os.path.join(ENG, "Vendor Source Files") if ENG else os.path.join(HERE, "source")

# What we try to find. Each is a (field, regex, hint) - the hint is what a human
# is being asked to confirm, phrased as the question rather than the answer.
# Regex over a whole brochure is the FALLBACK, not the primary path - see
# tablespec.py for why. Two patterns here were actively poisonous and are fixed:
#
#   lifetime  matched "3840H" out of "3840HZ" and published a refresh rate as
#             rated life. `h` now refuses to match when a Z follows it.
#   wattage   matched "60W" out of "averaging 60W/m2 per hour" - a power-density
#             marketing claim read as fixture wattage. A W followed by /m2 or a
#             square-metre sign is now rejected.
#
# Both survived because a regex cannot tell a headline from a specification.
_NOT_PER_AREA = r"(?!\s*/\s*(?:m|㎡|sq))"

PATTERNS = [
    ("wattage",      r"(\d{1,4}\s*[-–]\s*\d{1,4}\s*W\b|\b\d{1,4}\s*W\b)" + _NOT_PER_AREA, "wattage range"),
    ("voltage",      r"(\d{2,3}\s*[-–]\s*\d{2,3}\s*V(?:AC)?)",                    "input voltage"),
    ("efficacy",     r"(\d{2,3}\s*(?:lm/W|LM/W))",                                "efficacy"),
    ("cct",          r"(\d{4}\s*K(?:\s*/\s*\d{4}\s*K)*)",                         "CCT options"),
    ("cri",          r"(?:CRI|\bRa\b)[^\d]{0,12}(\d{2}\+?)",          "CRI (written as CRI or Ra)"),
    ("ip_rating",    r"\b(IP\s?\d{2}(?:\s*/\s*IP\s?\d{2})?)\b",                   "IP rating"),
    ("ik_rating",    r"\b(IK\s?\d{2})\b",                                         "impact rating"),
    ("warranty",     r"(\d\s*[-\s]?year)",                                        "warranty term"),
    ("lifetime",     r"([\d,]{4,9}\s*(?:h(?!z)|hrs|hours)\b)",                    "rated life"),
    ("pitch",        r"\b(P\d{1,2}(?:\.\d+)?)\b|(\d{1,2}\.\d{1,3}\s*[x*×]\s*\d{1,2}\.\d{1,3})", "pixel pitch (display)"),
    ("nits",         r"([\d,]{3,6})\s*(?:nits|cd/m)",                             "brightness (display)"),
    ("transparency", r"(\d{2})\s*%\s*(?:transparen|permeab)|transparen\w*[^\d]{0,14}(\d{2})\s*%", "transparency (display)"),
    ("refresh",      r"([\d,]{3,6})\s*Hz\b",                                      "refresh rate (display)"),
    ("surge",        r"(\d{1,2}\s?kV)",                                           "surge protection"),
]

# Fields that belong to exactly one category. A display sheet must never carry
# wattage/CCT/CRI/efficacy and a luminaire must never carry pitch/nits - see
# AGENT.md 5a. Asking a screen factory for a CRI is the giveaway that we have
# never bought one; printing it on our own sheet is worse.
LIGHTING_ONLY = {"wattage", "efficacy", "cct", "cri", "lifetime", "surge", "lens"}
DISPLAY_ONLY = {"pitch", "nits", "transparency", "refresh", "pixel_density",
                "module_size", "module_res", "cabinet_size", "cabinet_res",
                "power_max", "power_avg", "leds", "scan", "drive_ic", "weight_m2"}

# NOTE on the DLC pattern: the first version was \bP[A-Z0-9]{7,}\b, which
# matched PROTECTION, PROCESSING, PERFORMANCE and PROCESSOR out of a real
# document. A DLC Product ID is P followed by DIGITS - allowing letters turns
# every capitalised P-word into a candidate certification number, which is the
# worst possible false positive to put in front of someone who is about to
# publish it under LC's name.
CERT = [
    ("dlc",   r"\b(P\d{6,8})\b",                   "possible DLC Product ID - MUST be checked on the QPL by a human"),
    ("ul",    r"\b([Ee]\d{5,7})\b",                "possible UL file number - confirm the standard too"),
    ("fcc",   r"\b(2[A-Z0-9]{4}-[A-Z0-9\-]{2,})\b","possible FCC ID - verifiable in the public FCC database"),
]


class NoTextLayer(Exception):
    def __init__(self, pages):
        self.pages = pages


def render_pages(path, out_dir, dpi=170, limit=4):
    """Rasterise pages so a PDF with no text layer can still be read by eye."""
    import pymupdf
    os.makedirs(out_dir, exist_ok=True)
    doc = pymupdf.open(path)
    made = []
    for i in range(min(doc.page_count, limit)):
        png = os.path.join(out_dir, "%s_p%d.png" %
                           (os.path.splitext(os.path.basename(path))[0], i + 1))
        doc[i].get_pixmap(dpi=dpi).save(png)
        made.append(png)
    return made


def extract(path):
    import pymupdf
    doc = pymupdf.open(path)
    text = "\n".join(doc[i].get_text() for i in range(min(doc.page_count, 25)))

    # A design-tool PDF with outlined type has NO text layer. Reporting
    # "0 fields found" for that reads as "this document is empty" when it
    # actually means "I cannot read this document" - two very different
    # things, and the second silently stalls the pipeline. Hit on the first
    # real vendor sheet: an InDesign export, 0 characters, 5 images, 230
    # vector paths.
    if len(text.strip()) < 40:
        raise NoTextLayer(doc.page_count)

    found, certs = {}, {}
    for field, rx, hint in PATTERNS:
        hits = []
        for m in re.finditer(rx, text, re.I):
            v = next((g for g in m.groups() if g), None) if m.groups() else m.group(0)
            v = (v or "").strip()
            if v and v not in hits:
                hits.append(v)
            if len(hits) >= 6:
                break
        if hits:
            found[field] = {"candidates": hits, "confirm": hint, "verified": False,
                            "source": "regex over full document - LOW TRUST, may be a "
                                      "marketing headline rather than a specification"}
    for key, rx, hint in CERT:
        hits = list(dict.fromkeys(m.group(1) for m in re.finditer(rx, text)))[:4]
        if hits:
            certs[key] = {"candidates": hits, "confirm": hint, "verified": False}

    # The spec matrix, when there is one, OVERRIDES the regex sweep. It is the
    # difference between "this number appears in the document" and "this is the
    # Brightness of the model we are buying".
    matrix = tablespec.scan(doc)
    return doc.page_count, found, certs, matrix


def apply_matrix(found, matrix, model):
    """Replace regex guesses with the chosen model's column."""
    replaced = []
    for field, bymodel in matrix["rows"].items():
        val = bymodel.get(model)
        if not val or val == "-":
            continue
        if field in found:
            replaced.append("%s: %s -> %s" % (field, found[field]["candidates"][0], val))
        found[field] = {"candidates": [val], "verified": False,
                        "confirm": "from the vendor's own spec table, model %s (page %d)"
                                   % (model, matrix["page"]),
                        "source": "spec matrix - column %s" % model}
    return replaced


def process(path):
    name = os.path.basename(path)
    print("\n  reading: %s" % name)
    try:
        pages, found, certs, matrix = extract(path)
    except NoTextLayer as e:
        shots = render_pages(path, os.path.join(DRAFTS, "_page-images"))
        print("  !! NO TEXT LAYER - %d page(s), nothing machine-readable." % e.pages)
        print("     Almost certainly an Illustrator or InDesign export with the type")
        print("     converted to outlines, which is normal for a vendor spec sheet.")
        print("     THIS IS NOT AN EMPTY DOCUMENT - it cannot be parsed, which is different.")
        print("     Pages rendered so they can be read by eye:")
        for s in shots:
            print("       %s" % s)
        return
    print("  pages: %d   fields found: %d   possible cert numbers: %d"
          % (pages, len(found), len(certs)))

    # --- the spec matrix, if the document has one ---------------------------
    selected, replaced = None, []
    if matrix:
        print("  spec matrix on page %d: %d models x %d rows  [%s]"
              % (matrix["page"], len(matrix["models"]), len(matrix["rows"]),
                 ", ".join(matrix["models"])))
        if len(matrix["models"]) == 1:
            selected = matrix["models"][0]
        else:
            env = os.environ.get("LC_SPEC_MODEL")
            if env and env in matrix["models"]:
                selected = env
        if selected:
            replaced = apply_matrix(found, matrix, selected)
            print("  model %s selected - %d field(s) taken from the table" % (selected, len(matrix["rows"])))
            for r in replaced:
                print("    CORRECTED  %s" % r)
        else:
            print("  !! MODEL NOT CHOSEN. The table holds %d models and the quote decides"
                  % len(matrix["models"]))
            print("     which one. Set _selected_model in the draft, or LC_SPEC_MODEL=<model>.")
            print("     Until then every field below is a LOW-TRUST regex guess.")

    # Category. A document with a pixel pitch and a brightness in nits is a
    # display, whatever else the brochure says about it.
    display_hits = len((DISPLAY_ONLY & set(found)) | (DISPLAY_ONLY & set(matrix["rows"] if matrix else {})))
    category = "display" if display_hits >= 2 else "lighting"
    print("  category: %s" % category.upper())

    # Cross-category fields are DROPPED, not carried. This is the rule that
    # would have stopped a transparent display shipping as a 60 W LED troffer.
    drop = (LIGHTING_ONLY if category == "display" else DISPLAY_ONLY) & set(found)
    for f in sorted(drop):
        print("    dropped %-12s (%s field, this is a %s sheet): %s"
              % (f, "lighting" if category == "display" else "display",
                 category, ", ".join(found[f]["candidates"][:3])))
        found.pop(f)

    stem = re.sub(r"[^A-Za-z0-9]+", "-", os.path.splitext(name)[0]).strip("-")[:60]
    draft = {
        "_status": "DRAFT - nothing here is verified. Confirm each field, then set verified:true.",
        "_source_document": name,
        "_source_note": ("This file carries the VENDOR'S identity. It is provenance, not "
                         "content - the spec sheet cites it and never reproduces it."),
        "family": "",
        "product_type": "",
        "lc_sku_prefix": "",
        "_naming_note": ("Family name and LC SKU prefix are catalogue decisions Dino makes. "
                         "The builder refuses to generate them - Type ID is the join key into "
                         "the Master Project Tool."),
        "_category": category,
        "_category_note": ("Drives which fields may appear. A display sheet carries no "
                           "wattage, CCT, CRI, efficacy, rated life, DLC line, IES file or "
                           "photometric page - see AGENT.md 5a."),
        "_matrix": ({"page": matrix["page"], "models": matrix["models"],
                     "rows": matrix["rows"]} if matrix else None),
        "_selected_model": selected,
        "_selected_model_note": ("Which COLUMN of the vendor's spec table this sheet is built "
                                 "from. The quotation decides it. Null means no model was "
                                 "chosen and the extracted values are low-trust regex guesses "
                                 "rather than that model's real specification."),
        "extracted": found,
        "possible_certifications": certs,
        "_cert_warning": ("NOTHING above reaches a spec sheet until verified. A DLC ID or UL "
                          "file number on a published sheet is a claim LC makes to a utility "
                          "and an inspector."),
    }

    for d in (DRAFTS, SRC):
        os.makedirs(d, exist_ok=True)
    out = os.path.join(DRAFTS, "%s.draft.json" % stem)
    io.open(out, "w", encoding="utf-8").write(json.dumps(draft, indent=2, ensure_ascii=False))
    shutil.copy2(path, os.path.join(SRC, name))

    print("  draft:  %s" % out)
    print("  filed:  %s" % os.path.join(SRC, name))
    if found:
        print("\n  found, all UNVERIFIED:")
        for k, v in found.items():
            print("    %-13s %s" % (k, ", ".join(v["candidates"][:4])))
    if certs:
        print("\n  possible certification numbers - none usable until checked:")
        for k, v in certs.items():
            print("    %-5s %s" % (k, ", ".join(v["candidates"])))
    print("\n  Next: fill family / product_type / lc_sku_prefix, verify the numbers,")
    print("        then run:  python specsheet/build.py <that file>")


def main():
    if len(sys.argv) > 1:
        process(sys.argv[1]); return
    os.makedirs(DROP, exist_ok=True)
    files = [f for f in os.listdir(DROP) if f.lower().endswith(".pdf")]
    if not files:
        print("Nothing to read.")
        print("Drop a vendor datasheet (PDF) into:")
        print("  %s" % DROP)
        return
    for f in files:
        process(os.path.join(DROP, f))


if __name__ == "__main__":
    main()
