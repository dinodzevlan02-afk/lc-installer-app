"""
Read a vendor spec MATRIX - one column per model - instead of grepping the page.

Why this exists. The first display sheet this pipeline built said the product was
a 60 W LED troffer with a rated life of 3840 hours and a brightness of 10,000.
Every one of those numbers is real text on the vendor PDF:

    "Low power consumption, averaging 60W/m2 per hour."   -> wattage 60W
    "3840HZ"                                              -> lifetime 3840H
    "Brightness up to 10,000 cd/m2"                       -> nits 10,000

They are marketing-page claims, and two of them are contradicted by the vendor's
own spec table four pages later. A regex over a 15-page brochure cannot tell the
difference between a headline and a specification - it takes whichever appears
first. That is not a tuning problem, it is the wrong instrument.

A real spec table is a matrix: a Model row across the top, labelled rows down the
side, and the value we want sits at one intersection. So find the Model row,
learn the column centres from it, and read every other row by x-position. Then a
number is not "somewhere in the document", it is "Brightness, column C0715".

Pure geometry - no page-layout dependency beyond PyMuPDF's word boxes.
"""

import re

# Row labels we understand, mapped to our field names. Matching is loose on the
# left (the vendor writes "Brightness (nits)", "IP Rating(Front/Rear)") and the
# key is the first thing on the row.
ROW_MAP = [
    ("pitch",         r"^pitch\b"),
    ("leds",          r"^leds?\b"),
    ("pixel_density", r"^pixel\s*density"),
    ("module_size",   r"^module\s*size"),
    ("module_res",    r"^module\s*resolution"),
    ("cabinet_size",  r"^cabinet\s*size"),
    ("cabinet_res",   r"^cabinet\s*resolution"),
    ("transparency",  r"^transparency"),
    ("refresh",       r"^refresh"),
    ("nits",          r"^brightness"),
    ("power_max",     r"^max\s*power"),
    ("power_avg",     r"^avg\s*power"),
    ("ip_rating",     r"^ip\s*rating"),
    ("maintenance",   r"^maintenance|^installation"),
    ("weight_m2",     r"^weight"),
    ("scan",          r"^scan"),
    ("drive_ic",      r"^driv\w*\s*ic"),
    ("voltage",       r"^(?:input\s*)?voltage"),
    ("operating_temp", r"^(?:operating|working)\s*temp"),
    ("viewing_angle", r"^viewing\s*angle"),
]


def _lines(page, tol=4):
    """Group words into visual rows by y, keeping each word's x."""
    rows = {}
    for x0, y0, x1, y1, word, *_ in page.get_text("words"):
        rows.setdefault(round(y0 / tol) * tol, []).append((x0, x1, word))
    return [(y, sorted(rows[y])) for y in sorted(rows)]


def _row_text(cells):
    return " ".join(w for _, _, w in cells)


def find_matrix(page):
    """Return (models, {field: {model: value}}) for a model-per-column table,
    or (None, {}) when this page does not hold one."""
    rows = _lines(page)

    header = None
    for i, (y, cells) in enumerate(rows):
        txt = _row_text(cells)
        if re.match(r"^model\b", txt, re.I) and len(cells) >= 3:
            header = (i, cells)
            break
    if not header:
        return None, {}

    hi, hcells = header
    # column centres from every word after the label "Model"
    cols = [((x0 + x1) / 2.0, w) for x0, x1, w in hcells
            if not re.match(r"^model$", w, re.I)]
    if len(cols) < 2:
        return None, {}
    models = [w for _, w in cols]
    centres = [c for c, _ in cols]

    def assign(cells, label_end):
        """Bucket a row's value-words into the nearest column."""
        out = {}
        for x0, x1, w in cells:
            if x1 <= label_end:
                continue
            mid = (x0 + x1) / 2.0
            j = min(range(len(centres)), key=lambda k: abs(centres[k] - mid))
            out.setdefault(j, []).append(w)
        return {models[j]: " ".join(v) for j, v in out.items()}

    found = {}
    pending = None      # a label whose values wrapped onto the next line
    for y, cells in rows[hi + 1:]:
        txt = _row_text(cells)
        field = None
        for name, rx in ROW_MAP:
            if re.match(rx, txt, re.I):
                field = name
                break

        label_end = centres[0] - 20

        # "Max Power / 690 690 690 / Consumption" - the label is split over three
        # lines and the numbers sit alone in the middle one. Carry the label
        # forward rather than losing the row: peak load is our electrical scope.
        if field is None and pending and re.fullmatch(r"[\d\s.,/x*-]+", txt.strip()):
            vals = assign(cells, label_end)
            if vals:
                found[pending] = vals
                pending = None
                continue
        if not field or field in found:
            continue
        vals = assign(cells, label_end)
        if not vals:
            pending = field
            continue
        # A single value spanning the table (Refresh rate 3840HZ, Cabinet Size,
        # IP Rating) applies to every model rather than to the one column it
        # happened to land nearest.
        if len(vals) == 1 and len(models) > 1:
            only = list(vals.values())[0]
            vals = {m: only for m in models}
        found[field] = vals

    return (models, found) if found else (None, {})


def scan(doc, max_pages=25):
    """First model matrix in the document. Vendor brochures put marketing first
    and the real table late, which is exactly why page order must not decide
    which number wins."""
    for i in range(min(doc.page_count, max_pages)):
        models, found = find_matrix(doc[i])
        if models and len(found) >= 4:
            return {"page": i + 1, "models": models, "rows": found}
    return None
