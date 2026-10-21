"""Build an LC spec sheet from one product file, on the LC template.

    python3 .claude/skills/lc-spec-sheet/scripts/make_sheet.py <product.json> [--out file.pdf]

The engine is the sourcing desk's pipeline (scripts/specsheet/, copied unchanged
from Dino's PC on 2026-10-21 except the hero size when there is no banner):
rebrand.to_sheet -> leak check -> build.check -> overlay.build on
assets/template_LC-TP.pdf. This driver is the desk's worked example
(build_lc_fl_ws.py) made general, so a product is a data file, not a script.

Paths in the product file are relative to the product file. The product file
keys are described in SKILL.md; examples/LC-FL-WS-3CCT.json is the reference.
"""
import io, json, os, sys

import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "specsheet"))
import rebrand, overlay, build as builder  # noqa: E402

IN_MM = 25.4


def leak_check(sheet, vendor_words):
    """Supplier words anywhere in the sheet = refuse (the desk's project-sheet.leak_check)."""
    blob = json.dumps(sheet, ensure_ascii=False).lower()
    return sorted({w for w in vendor_words if w.lower() in blob})


def draft_from(p):
    """The draft shape rebrand.to_sheet reads: extracted fields, never verified here."""
    src = p.get("source_note", "supplier documents")
    ex = {k: {"candidates": v["values"], "confirm": v.get("src", ""), "verified": False, "source": src}
          for k, v in p["extracted"].items()}
    return {"product_type": p["product_type"], "_category": p.get("category", "lighting"),
            "extracted": ex, "possible_certifications": p.get("certifications", {})}


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    pf = os.path.abspath(argv[1])
    base = os.path.dirname(pf)
    p = json.load(io.open(pf, encoding="utf-8"))
    rel = lambda x: os.path.normpath(os.path.join(base, x))
    out = rel(argv[argv.index("--out") + 1]) if "--out" in argv else rel(p["out"])

    sheet = rebrand.to_sheet(draft_from(p), p["family"], p["product_type_label"], p["sku"])
    cv = sheet["cover"]
    for k, v in p.get("cover", {}).items():
        cv[k] = v
    for k in ("badges", "quality_line", "description", "order_logic"):
        if k in p:
            sheet[k] = p[k]
    if "overview" in p:
        sheet["overview"] = p["overview"]
    else:
        drop = tuple(p.get("overview_drop", []))
        sheet["overview"] = [r for r in sheet["overview"] if not (drop and r.startswith(drop))][:p.get("overview_max", 12)]
        sheet["overview"] += p.get("overview_add", [])
    if p.get("dims_panel"):
        sheet["dimensions"] = {}          # drawn beside the drawing below, not in the grey boxes
    if p.get("electrical_note"):
        sheet["electrical"]["note"] = p["electrical_note"]

    leaks = leak_check(sheet, p.get("vendor_words", []))
    if leaks:
        sys.exit("refused: supplier identity on the sheet: %s" % leaks)

    tmpdir = os.path.join(os.path.dirname(out), "_work")
    os.makedirs(tmpdir, exist_ok=True)
    src = p.get("vendor_pdf") and pymupdf.open(rel(p["vendor_pdf"]))
    z = pymupdf.Matrix(3, 3)
    if p.get("hero"):
        h = p["hero"]
        hero_png = os.path.join(tmpdir, "hero.png")
        src[h["page"]].get_pixmap(matrix=z, clip=pymupdf.Rect(*h["clip"])).save(hero_png)
        sheet["hero_png"] = hero_png

    blocking, warn = builder.check(sheet, allow_no_ul=p.get("draft", True))
    if blocking:
        sys.exit("blocked: %s" % blocking)
    if warn:
        print("check warnings (shown in the conflicts box / your summary, not on a banner):", warn)

    # No red PRE-RELEASE banner (Dino, 2026-10-21). Draft status is the cover subtitle
    # and the DRAFT CONFLICTS box on page 3. "banner": [...] in the product file brings it back.
    band = p.get("banner") or []
    tmp = os.path.join(tmpdir, "sheet.pdf")
    path, poppins = overlay.build(sheet, band, tmp)
    if not poppins:
        print("WARNING: full Poppins family missing, sheet set in Helvetica")

    pdf = pymupdf.open(path)
    R = overlay.R
    dp = p.get("dims_panel")
    if dp:                                   # page 2: drawing left, dimensions right
        p2 = pdf[1]
        F = overlay.Fonts(p2)
        if dp.get("drawing"):
            d = dp["drawing"]
            draw_png = os.path.join(tmpdir, "drawing.png")
            src[d["page"]].get_pixmap(matrix=z, clip=pymupdf.Rect(*d["clip"])).save(draw_png)
            p2.insert_image(R(60, 995, 560, 1140), filename=draw_png, keep_proportion=True)
        p2.draw_rect(R(585, 1000, 900, 1140), color=None, fill=overlay.GREY)
        overlay.text(p2, F, R(600, 1006, 890, 1136), dp["text"], "semi", 7.6, overlay.INK, lh=1.2)
    if p.get("conflicts"):                   # page 3: between LUMEN MAINTENANCE and the footer
        p3 = pdf[2]
        F3 = overlay.Fonts(p3)
        PX = overlay.PX
        p3.draw_rect(pymupdf.Rect(36, 704, 576, 764), color=None, fill=overlay.CREAM)
        p3.draw_rect(pymupdf.Rect(36, 704, 38.5, 764), color=None, fill=overlay.ORANGE)
        overlay.text(p3, F3, R(77, 704 / PX + 6, 880, 704 / PX + 20), p.get("conflicts_title", "DRAFT CONFLICTS"), "bold", 6.6, overlay.INK)
        overlay.text(p3, F3, R(77, 704 / PX + 22, 880, 764 / PX - 2), "\n".join(p["conflicts"]), "light", 6.0, overlay.INK, lh=1.2)
    pdf.set_metadata({"title": "%s %s - Spec Sheet" % (p["sku"], p["family"]), "author": "LED Connection",
                      "creator": "LED Connection", "producer": "LED Connection", "subject": "", "keywords": ""})
    os.makedirs(os.path.dirname(out), exist_ok=True)
    pdf.save(out, garbage=3, deflate=True)
    pdf.close()

    text = "".join(pg.get_text() for pg in pymupdf.open(out)).lower()
    found = [w for w in p.get("vendor_words", []) if w.lower() in text]
    if found:
        os.remove(out)
        sys.exit("refused after render: supplier words in the PDF text: %s" % found)
    print("built:", out)


if __name__ == "__main__":
    main(sys.argv)
