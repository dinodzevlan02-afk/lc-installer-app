"""
Build an LED Connection spec sheet from a verified data file.

    python specsheet/build.py specsheet/data/omnitron.json
    python specsheet/build.py --demo

It renders the structure of the two reference sheets (Omnitron, Triproof):
cover with six chips, description + overview + badges, electrical data +
order logic, and a photometric page only if a real IES file exists.

The final artwork stays in Illustrator. What this produces is the complete,
verified, correctly-worded content in the right structure, so the design step
is layout rather than transcription and fact-checking.

IT REFUSES TO BUILD rather than publish something wrong. See AGENT.md.
"""

import io, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))

# Output goes to the company OneDrive so the team can reach it and it survives
# this machine. Falls back to a local folder if OneDrive is not mounted - a
# missing cloud drive should not stop a build.
# Preference order, most shared first: the Engineering sandbox the team can
# see, then the personal OneDrive, then local. A missing cloud drive should
# never stop a build.
_od = os.environ.get("OneDriveCommercial") or os.environ.get("OneDrive")
OUT = os.path.join(HERE, "output")
if _od and os.path.isdir(_od):
    _eng = os.path.join(_od, "LED Documents - Engineering", "Sourcing Dino")
    if os.path.isdir(_eng):
        OUT = os.path.join(_eng, "Spec Sheet Drafts")
    else:
        OUT = os.path.join(_od, "Sourcing", "Spec Sheets")

# Commercial terms that must never reach a published spec sheet.
#
# NOTE: a bare \bcost\b was the first version and it was wrong - it blocked
# the Omnitron sheet's own real copy, "built for clean installs and lower
# shipping cost". That sentence is a product claim, not a price. What must
# never appear is OUR cost or a trade term, so the pattern targets those.
BANNED = re.compile(
    r"\b(FOB|DDP|EXW|CIF|MOQ|incoterm|margin|landed cost|unit cost|unit price|"
    r"our cost|cost per unit|price per m2|target price)\b"
    r"|\$\s?[\d,]+"
    r"|\bUSD\s?[\d,]+", re.I)


def fail(msg):
    print("REFUSED: %s" % msg)
    sys.exit(2)


def check(d, allow_no_ul=False):
    """Every reason not to publish. Returns (blocking, warnings).

    allow_no_ul exists for INTERNAL DRILLS ONLY and is never the default. It
    downgrades the UL gate from a block to a loud warning. It does NOT invent a
    certification - the cert block stays empty and no UL claim is printed. The
    thing being waived is our willingness to build the document, not the fact
    that the product is unlisted."""
    blocking, warn = [], []

    for f in ("family", "product_type", "lc_sku_prefix"):
        if not d.get(f):
            blocking.append("%s is not set. Family name and LC SKU prefix are catalogue "
                            "decisions Dino makes - never generated." % f)

    # Supplier identity must not survive into the document.
    blob = json.dumps({k: v for k, v in d.items() if k != "verified"}, ensure_ascii=False)
    if d.get("source_supplier_id") and d["source_supplier_id"] != "REDACTED-IN-OUTPUT":
        blocking.append("source_supplier_id is present in the payload. The factory is never "
                        "named on a spec sheet, in any field.")
    m = BANNED.search(blob)
    if m:
        blocking.append("commercial term %r found in the content. A spec sheet describes a "
                        "product; price lives in the quote." % m.group(0))

    # Certifications: verified or absent.
    c = d.get("certifications") or {}
    if c.get("dlc_product_id") and not c.get("dlc_verified"):
        blocking.append("DLC Product ID %s is present but dlc_verified is false. The QPL is "
                        "behind a sign-in wall, so this needs a human check. Publishing it is "
                        "a claim LC makes to a utility." % c["dlc_product_id"])
    # ---------------------------------------------------------------- UL GATE
    # Dino's rule, 2026-09-11: a confirmed UL/ETL listing is a PRECONDITION for
    # an LC spec sheet, in both domains. Not a warning - a block.
    #
    # The reasoning is already in company-profile.md hard requirement 2: a
    # supplier without a verifiable UL/ETL file number "cannot be used on our
    # work". Publishing an LC-branded sheet for a fixture we cannot legally
    # install is the same class of error as publishing an unverified cert - a
    # document that looks finished and is wrong.
    #
    # "Confirmed" means we hold the FILE NUMBER and the NAMED STANDARD. The word
    # "certified", a mark on a brochure, or a listing on a component inside the
    # assembly (a UL power supply in a non-UL screen) is not confirmation.
    if not (c.get("ul_file_number") and c.get("ul_standard")):
        have = []
        if c.get("ul_etl"):
            have.append("mark claimed as %r" % c["ul_etl"])
        if c.get("ul_file_number"):
            have.append("file number %s" % c["ul_file_number"])
        if c.get("ul_standard"):
            have.append("standard %s" % c["ul_standard"])
        msg = ("NO CONFIRMED UL/ETL LISTING - no LC spec sheet is built. Need BOTH a file "
               "number and the named standard (UL 1598 for a luminaire, UL 48 for a sign or "
               "display). Have: %s." % (", ".join(have) if have else "nothing"))
        if allow_no_ul:
            warn.append("UL GATE WAIVED FOR AN INTERNAL TEST - this product has NO confirmed "
                        "UL/ETL listing. NOT RELEASABLE. No certification is claimed anywhere "
                        "on this sheet.")
        else:
            blocking.append(msg)
    # A display sheet has no DLC line and no photometric page, so warning about
    # their absence is wrong - and worse, the warnings print in the PRE-RELEASE
    # band, which put the word "DLC" on a transparent-screen sheet.
    is_display = "photometrics" not in d or "dlc_product_id" not in c

    if not is_display:
        if not c.get("dlc_product_id"):
            warn.append("No DLC Product ID. Lighting jobs run on rebates; the sheet will omit it.")
    if is_display:
        if not c.get("fcc_id"):
            warn.append("No FCC ID. It is the one certification here verifiable in a public "
                        "database, so it is the one to insist on.")
        if not c.get("control_system"):
            warn.append("Control system not named. Novastar / Colorlight / proprietary is a "
                        "lock-in decision the customer inherits.")

    # Photometrics - lighting only. A display emits content, not a distribution.
    if not is_display:
        ies = (d.get("photometrics") or {}).get("ies_files") or []
        if not ies:
            warn.append("No IES file - photometric page omitted. This is the lighting hard gate "
                        "showing up as a missing page. Never trace a curve from a supplier PDF.")

    # Provenance.
    ver = d.get("verified") or {}
    if not ver:
        warn.append("No provenance recorded. Every published number should name the document "
                    "it came from.")
    return blocking, warn


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def render(d, warn=None):
    """Lay the sheet out the way the reference sheets are laid out.

    The first version of this function rebuilt the CONTENT of the references
    and ignored their DESIGN, and the result looked like a different company's
    document. A spec sheet that does not match the catalogue reads as one.
    """
    import theme

    f = d["footer"]
    foot = ("<div class='foot'><em>PHONE:</em> %s <em>WEB:</em> %s <em>EMAIL:</em> %s"
            "<span class='addr'>%s</span></div>") % (
        esc(f["phone"]), esc(f["web"]), esc(f["email"]), esc(f["address"]))

    fam = esc(d["family"]).upper()
    ptype = esc(d["product_type"]).upper()
    sku = esc(d["lc_sku_prefix"])
    cv = d["cover"]

    banner = ""
    if warn:
        banner = ("<div class='prerel'><b>PRE-RELEASE &mdash; NOT FOR DISTRIBUTION</b>"
                  "<ul>%s</ul></div>" % "".join("<li>%s</li>" % esc(w) for w in warn))

    # ---- cover -----------------------------------------------------------
    chips = "".join("<div><span>%s</span><b>%s</b></div>" % (esc(k), esc(v))
                    for k, v in cv["chips"].items())
    shot = d.get("hero_image")
    hero_inner = ("<div class='shot'><img src='%s'></div>" % esc(shot) if shot
                  else "<div class='noshot'>PRODUCT PHOTOGRAPH</div>")

    pages = ["""<section class='page cover'>
  <div class='rail'><div class='rail-txt'>LED CONNECTION &mdash; %s</div>
    <div class='rail-logo'>%s</div></div>
  <div class='hero'>%s%s<div class='logo-tr'>%s</div></div>
  <div class='cbody'>%s
    <div class='ptype'>%s</div>
    <div class='fam'>%s</div>
    <div class='rule'></div>%s%s
    <div class='specs'>%s</div>
    <div class='callout'><b>%s</b><p>%s</p></div>
    <div class='custom'>For custom solutions please contact our sales representative.</div>
  </div>%s
</section>""" % (fam, theme.logo(False), theme.trace_svg(), hero_inner, theme.logo(),
                 banner, ptype, fam,
                 ("<div class='eff'>%s</div>" % esc(cv["headline_efficacy"])
                  if cv.get("headline_efficacy") not in (None, "", "-") else ""),
                 ("<div class='sub'>%s</div>" % esc(cv["subtitle"])
                  if cv.get("subtitle") else ""), chips,
                 esc(cv["tagline"]), esc(cv["positioning"]), foot)]

    def head():
        return ("<div class='phead'><div class='t'>%s &mdash; %s</div>"
                "<div class='s'>%s</div><div class='lg'>%s</div></div>"
                % (ptype, fam, sku, theme.logo()))

    def bar(t):
        return "<div class='secbar'><b>%s</b><i></i></div>" % esc(t).upper()

    # ---- page 2: description, overview, dimensions -----------------------
    badges = "".join("<div class='badge'>%s</div>" % esc(b).upper()
                     for b in d.get("badges", [])[:5])
    bullets = "".join("<li>%s</li>" % esc(x) for x in d.get("overview", []))
    q = d.get("quality_line") or "Built for the application, specified without guesswork."
    dims = d.get("dimensions") or {}
    dims_html = ""
    if dims:
        dims_html = bar("Dimensions") + "<div class='dims'>" + "".join(
            "<div><span>%s</span><b>%s</b></div>" % (esc(k).upper(), esc(v))
            for k, v in dims.items()) + "</div>"
    pages.append("""<section class='page'>%s<div class='body'>
  <div class='ptype'>%s</div><div class='fam' style='font-size:30pt'>%s</div>
  <div style='color:%s;font-weight:800;font-size:12pt;margin-top:.04in'>%s</div>
  <div class='badges'>%s</div>
  <div class='cream'><b>QUALITY DEFENDER</b><p>%s</p></div>
  %s<p class='txt'>%s</p>
  %s<ul class='ov'>%s</ul>%s
</div>%s</section>""" % (head(), ptype, fam, theme.ORANGE, sku, badges, esc(q),
                        bar("Product Description"), esc(d["description"]),
                        bar("Overview"), bullets, dims_html, foot))

    # ---- page 3: order logic + electrical --------------------------------
    ol = d.get("order_logic") or {}
    code = esc(ol.get("sample_code", ""))
    if " - " in code:
        first, rest = code.split(" - ", 1)
        code_html = "<em>%s -</em> %s" % (first, rest)
    else:
        code_html = code
    marks = " ".join("[%s]" % esc(s["n"]) for s in ol.get("segments", []))
    segs = "".join(
        "<div class='seg'><div class='h'>%s %s</div><div class='o'>%s</div></div>" % (
            esc(s["n"]), esc(s["name"]).upper(),
            "".join("<b>%s</b><span>%s</span>" % (esc(o[0]), esc(o[1]))
                    for o in s["options"]))
        for s in ol.get("segments", []))

    e = d.get("electrical") or {}
    thead = "".join("<th>%s</th>" % esc(c) for c in e.get("columns", []))
    rows = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % esc(c) for c in r)
                   for r in e.get("rows", []))
    pages.append("""<section class='page'>%s<div class='body'>
  %s<p class='txt'>Build a %s SKU by selecting one option from each segment.</p>
  <div class='sample'><div class='lbl'>SAMPLE CODE</div>
    <div class='code'>%s</div><div class='mark'>[BRAND] %s</div></div>
  <div class='segs'>%s</div>
  <div class='notes'>For custom solutions please contact our sales representative.</div>
  %s<table><tr>%s</tr>%s</table>
  <div class='cream'><b>%s</b><p>%s</p></div>
</div>%s</section>""" % (head(), bar("Order Logic"), esc(d["family"]), code_html, marks,
                        segs, bar("Electrical Data"), thead, rows,
                        esc(e.get("note", "NOTE")), esc(d.get("lumen_maintenance", "")), foot))

    # ---- photometrics ----------------------------------------------------
    ies = (d.get("photometrics") or {}).get("ies_files") or []
    if ies:
        pages.append("<section class='page'>%s<div class='body'>%s"
                     "<p class='txt'>Polar candela plot per lumen package: %s</p>"
                     "</div>%s</section>"
                     % (head(), bar("Photometric Distribution"), esc(", ".join(ies)), foot))

    return ("<!doctype html><meta charset='utf-8'><title>%s %s &mdash; LED Connection</title>"
            "<style>%s</style>%s" % (esc(d["family"]), esc(d["product_type"]),
                                     theme.CSS, "".join(pages)))


def to_pdf(html_path):
    """Render the sheet to PDF.

    Chrome/Edge headless rather than a Python PDF library: the layout uses
    flexbox and print CSS, and a library that reimplements a subset of CSS
    would silently drop exactly the parts that make the sheet look like the
    reference. Better to use the engine that already renders it correctly.
    """
    import shutil, subprocess
    cands = [
        os.path.join(os.environ.get("ProgramFiles", ""), "Google", "Chrome", "Application", "chrome.exe"),
        os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Google", "Chrome", "Application", "chrome.exe"),
        os.path.join(os.environ.get("ProgramFiles", ""), "Microsoft", "Edge", "Application", "msedge.exe"),
        os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Microsoft", "Edge", "Application", "msedge.exe"),
    ]
    exe = next((c for c in cands if c and os.path.exists(c)), None)
    if not exe:
        print("  note: no Chrome or Edge found - HTML written, PDF skipped.")
        return None

    import tempfile, time
    pdf_path = os.path.splitext(html_path)[0] + ".pdf"
    url = "file:///" + html_path.replace("\\", "/").replace(" ", "%20")

    # A dedicated profile directory is not optional. With the user's normal
    # Chrome running, headless shares the default profile, finds it locked,
    # and EXITS ZERO without writing anything - so the old PDF silently
    # survives next to a freshly written HTML. Caught by comparing mtimes,
    # which is also why the check below exists rather than trusting exit code.
    profile = tempfile.mkdtemp(prefix="lc-pdf-")

    # Render to a plain temp path and copy in afterwards. Writing straight
    # into OneDrive works the first time and then silently stops working:
    # the sync client holds the existing file, Chrome cannot replace it, and
    # still exits ZERO - leaving a stale PDF beside a freshly written HTML.
    tmp_pdf = os.path.join(tempfile.mkdtemp(prefix="lc-out-"), "sheet.pdf")
    cmd = [exe, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--no-first-run", "--no-default-browser-check",
           "--user-data-dir=" + profile,
           "--no-pdf-header-footer", "--print-to-pdf-no-header",
           "--print-to-pdf=" + tmp_pdf, url]
    try:
        subprocess.run(cmd, check=True, timeout=180,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print("  note: PDF render failed (%s). HTML is still valid." % e)
        return None

    if not os.path.exists(tmp_pdf) or os.path.getsize(tmp_pdf) < 2000:
        print("  note: Chrome produced no usable PDF. HTML is still valid.")
        return None
    # OneDrive holds a file it is syncing, so an overwrite can fail with
    # WinError 32 seconds after the previous build. Retry briefly, then write
    # a versioned name rather than losing the render - a spec sheet that
    # silently failed to update is the failure mode this whole file guards
    # against.
    for attempt in range(6):
        try:
            shutil.copy2(tmp_pdf, pdf_path)
            return pdf_path
        except Exception:
            time.sleep(1.5)

    alt = "%s_%s.pdf" % (os.path.splitext(pdf_path)[0], time.strftime("%H%M%S"))
    try:
        shutil.copy2(tmp_pdf, alt)
        print("  note: the existing PDF was locked by OneDrive, so this build was")
        print("        written alongside it rather than over it.")
        return alt
    except Exception as e:
        print("  note: could not write the PDF into place (%s)." % e)
        print("        It is here instead: %s" % tmp_pdf)
        return tmp_pdf


def demo():
    p = os.path.join(HERE, "schema.json")
    return json.load(io.open(p, encoding="utf-8"))["example"]


def main():
    if "--demo" in sys.argv:
        d = demo()
    elif len(sys.argv) > 1:
        d = json.load(io.open(sys.argv[1], encoding="utf-8"))
    else:
        fail("usage: build.py <data.json> | --demo")

    blocking, warn = check(d)
    for w in warn:
        print("  warn: %s" % w)
    if blocking:
        print()
        for b in blocking:
            print("  BLOCK: %s" % b)
        fail("%d blocking issue(s). An incomplete spec sheet is normal; a confident wrong "
             "one is a liability." % len(blocking))

    os.makedirs(OUT, exist_ok=True)
    name = "%s_%s_SpecSheet_%s.html" % (
        d["family"].replace(" ", ""), d["product_type"].split()[0], d["lc_sku_prefix"])
    path = os.path.join(OUT, name)
    io.open(path, "w", encoding="utf-8").write(render(d, warn))
    pdf = to_pdf(path)
    print()
    print("  built: %s" % path)
    if pdf:
        print("  PDF  : %s" % pdf)
    print("  pages: %d  (photometric page %s)" % (
        3 + (1 if (d.get("photometrics") or {}).get("ies_files") else 0),
        "included" if (d.get("photometrics") or {}).get("ies_files") else "OMITTED - no IES"))
    print("  open it and print to PDF at Letter, or hand it to the Illustrator step.")


if __name__ == "__main__":
    main()
