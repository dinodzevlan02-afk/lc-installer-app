"""
For every project folder that has a vendor sheet and no LC sheet yet: build one.

    python specsheet/project-sheet.py            all projects
    python specsheet/project-sheet.py --force    rebuild even if one exists

Runs after project-collect.ps1 in the watcher. Deterministic where it can be:
if the vendor PDF has a text layer, intake -> rebrand -> overlay happen here.
If it has NO text layer (Illustrator/InDesign exports usually don't), the
pages are rendered to PNG and a _NEEDS-EYES.md is left in the folder; the
watcher's model stage reads the images and writes the draft, then this script
picks it up on the next tick.

Family name and SKU are PLACEHOLDERS derived from the project name and are
flagged as such - both are catalogue decisions Dino makes.
"""

# NOTE: project folders are named '<subject> [<vendor>]'. glob treats [..] as a
# character class, so EVERY glob over a project dir must use glob.escape(d), or it
# silently matches nothing - which is why no LC spec sheet was built for any
# bracketed vendor folder until 2026-09-15.
import glob, io, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

_od = os.environ.get("OneDriveCommercial") or os.environ.get("OneDrive")
BASE = os.path.join(_od, "LED Documents - Engineering", "Sourcing Dino") if _od else None
PY = sys.executable


def run(args):
    r = subprocess.run([PY] + args, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=ROOT, env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def naming_rules():
    """Dino's catalogue naming rules (specsheet/naming.json). Product class decides the
    SKU prefix; the series name is always his to choose."""
    p = os.path.join(HERE, "naming.json")
    if not os.path.exists(p):
        return []
    try:
        return (json.load(io.open(p, encoding="utf-8-sig")) or {}).get("classes", [])
    except Exception:
        return []


def class_for(*texts):
    """Which naming class this product falls into, from the vendor sheet's product type,
    the request spec and the project name. Returns the rule dict or None."""
    blob = " ".join(t for t in texts if t).lower()
    for rule in naming_rules():
        if any(m.lower() in blob for m in rule.get("match", [])):
            return rule
    return None


def placeholder_family(project_name, vendor_words=()):
    """A placeholder family name and SKU, labelled as one everywhere it appears.

    THIS USED TO NAME THE VENDOR. Project names are written as
    'Unilight - outdoor transparent LED film', so deriving the family from the
    project name put 'Unilight Outdoor Transparent Led Film Series' on the cover
    rail, page 2 and page 3 of an LC spec sheet. Hard rule 1 in AGENT.md is that
    the factory is never named, and a PRE-RELEASE banner does not excuse it.

    Vendor words are stripped. If nothing survives, we do NOT invent something -
    the caller blocks and asks Dino, because the family name is his decision."""
    drop = {w.lower() for w in vendor_words if len(w) > 2}
    # The request id is ours and means nothing on a catalogue sheet. Since project names
    # became "REQ-0005 - <company>" it was producing "Req 0005 Lighting Co Ltd Series"
    # and the SKU "LC-R0LC". Strip it, and drop the corporate suffixes with it.
    project_name = re.sub(r"^\s*REQ(?:-D)?-\d+\s*[-–]\s*", "", project_name or "")
    words = [w for w in re.split(r"[^A-Za-z0-9]+", project_name) if w
             and w.lower() not in ("co", "ltd", "llc", "inc", "corp", "limited", "company")]
    kept = [w for w in words if w.lower() not in drop]
    if not kept:
        return None, None
    fam = " ".join(w.capitalize() for w in kept) + " Series"
    code = "".join(w[0] for w in kept).upper()[:4] or "TMP"
    return fam, "LC-" + code


def vendor_words_for(project, draft_src):
    """Everything that could name the factory: the recipient's domain, the
    project name's leading token, and the source filename."""
    # Lower-cased throughout: the same token arrives as "Transparent" from a
    # filename and "transparent" from a domain, and a case-sensitive discard
    # let the generic word through and refused a perfectly good sheet.
    out = set()
    to = (project.get("to") or "")
    if "@" in to:
        dom = to.split("@", 1)[1]
        out.update(w.lower() for w in re.split(r"[^A-Za-z0-9]+", dom) if len(w) > 2
                   and w.lower() not in ("com", "net", "org", "cn", "co"))
    name = project.get("name") or ""
    # Strip a leading request id FIRST. Project names became "REQ-0005 - <company>" on
    # 2026-09-14, and splitting on the hyphen made "REQ" the lead token: the guard then
    # hunted for "req" - a substring of "required" and "frequency", so it refused every
    # sheet - while never looking for "bbier" at all. False alarm and no protection.
    name = re.sub(r"^\s*REQ(?:-D)?-\d+\s*[-–]\s*", "", name)
    lead = re.split(r"\s*[-–]\s*", name)[0]
    out.update(w.lower() for w in re.split(r"[^A-Za-z0-9]+", lead) if len(w) > 2)
    out.update(w.lower() for w in re.split(r"[^A-Za-z0-9]+", draft_src or "") if len(w) > 3)
    # Words that describe the PRODUCT rather than the company. These are safe on
    # an LC sheet; the vendor's trading name is not.
    out -= {"vendor", "sheet", "spec", "outdoor", "indoor", "transparent", "screen",
            "film", "mesh", "led", "display", "connection", "rfq", "facade", "direct",
            "sun", "glazed", "fixed", "series", "pitch", "module", "panel", "light",
            "lighting", "poster", "window", "rental", "curtain",
            "troffer", "basket", "center", "centre", "recessed", "highbay", "wallpack",
            "gen", "6gen", "spec", "quotation", "quote", "series",
            # OUR OWN domain is never a vendor word. An internal colleague running
            # a drill writes from @ledconnection.com, and "ledconnection" is in the
            # footer of every sheet by design - treating it as vendor identity made
            # the guard refuse our own document.
            "ledconnection", "ledconnectionlv",
            # English stopwords. "tommy the great" contributed "the", which appears
            # in any sentence on any sheet. A real supplier called "The X Company"
            # would have hit this too.
            "the", "and", "for", "with", "from", "inc", "ltd", "llc", "corp", "company",
            # Request ids are ours, not a factory's. Belt and braces with the strip above.
            "req", "reqd"}
    return out


def leak_check(sheet, vendor_words):
    """Refuse rather than publish. rebrand.py's CLI has this guard; this path
    called to_sheet() directly and skipped it, which is how the vendor's name
    reached a rendered PDF."""
    blob = json.dumps(sheet, ensure_ascii=False).lower()
    return sorted({w for w in vendor_words if w.lower() in blob})


def main():
    force = "--force" in sys.argv
    # --test-no-ul MUST be scoped with --only <substring>. An unscoped waiver
    # would silently rebuild every blocked project, including ones deliberately
    # withdrawn for exactly this reason.
    test_no_ul = "--test-no-ul" in sys.argv
    only = None
    if "--only" in sys.argv:
        i = sys.argv.index("--only")
        if i + 1 < len(sys.argv):
            only = sys.argv[i + 1].lower()
    if test_no_ul and not only:
        print("--test-no-ul requires --only <project substring>. Refusing to waive the UL "
              "gate across every project at once.")
        return 2
    if not BASE or not os.path.isdir(BASE):
        print("Sourcing Dino not synced"); return 1
    reg = json.load(io.open(os.path.join(ROOT, "projects.json"), encoding="utf-8"))
    built = 0
    for p in reg.get("projects", []):
        if only and only not in p["name"].lower():
            continue
        d = os.path.join(BASE, p["folder"])
        if not os.path.isdir(d):
            continue
        vendor_pdfs = sorted(glob.glob(os.path.join(glob.escape(d), "03 Vendor Sheet - *.pdf")))
        have_lc = glob.glob(os.path.join(glob.escape(d), "04 LC Spec Sheet*.pdf"))
        if not vendor_pdfs or (have_lc and not force):
            continue

        # ------------------------------------------------------ THE TRIGGER
        # Dino's rule, 2026-09-11: build the LC sheet as soon as we have all
        # three of (1) a confirmed UL/ETL listing, (2) a vendor spec sheet and
        # (3) pricing. Not at request-closed, which was the old trigger and
        # meant the sheet showed up long after it was useful.
        #
        # All three are required. The UL half is also a hard gate enforced
        # again in build.check() - both domains, no exceptions.
        pricing = (glob.glob(os.path.join(glob.escape(d), "02 Pricing*")) +
                   glob.glob(os.path.join(glob.escape(d), "05 Pricing Summary*")))
        if not pricing:
            print("[%s] waiting: vendor sheet present, no pricing yet." % p["name"])
            continue

        src = vendor_pdfs[-1]
        print("[%s] vendor sheet: %s" % (p["name"], os.path.basename(src)))

        # 1. intake
        rc, out = run([os.path.join(HERE, "intake.py"), src])
        # A hand-written draft in the project folder always wins, and that has to
        # be checked BEFORE the no-text-layer bail. Fixed 2026-09-28: the bail sat
        # above it, so an outlined-type PDF re-wrote _NEEDS-EYES.md on every run and
        # the draft the model stage had already written was never read. Alite
        # REQ-0008 sat in that state from 2026-09-22.
        local = glob.glob(os.path.join(glob.escape(d), "*.draft.json"))
        if "NO TEXT LAYER" in out and not local:
            io.open(os.path.join(d, "_NEEDS-EYES.md"), "w", encoding="utf-8").write(
                "# Vendor sheet has no text layer\n\n`%s` is an outlined-type PDF. Pages were "
                "rendered to `Spec Sheet Drafts/_page-images/`. The model stage of the watcher "
                "reads them and writes `%s.draft.json` into this folder; project-sheet.py then "
                "builds the LC sheet on its next run.\n" % (os.path.basename(src),
                                                             re.sub(r"[^A-Za-z0-9]+", "-", os.path.splitext(os.path.basename(src))[0]).strip("-")[:60]))
            print("   no text layer - left _NEEDS-EYES.md, pages rendered for the model stage")
            continue
        m = re.search(r"draft:\s+(.+\.draft\.json)", out)
        draft = m.group(1).strip() if m else None
        if local:
            draft = local[-1]
        if not draft or not os.path.exists(draft):
            print("   intake produced no draft:\n" + out[-600:]); continue

        # 2. rebrand -> sheet dict (via rebrand.to_sheet, not its CLI, so we can
        #    choose the hero and the output folder)
        import rebrand, overlay, build as builder
        dj = json.load(io.open(draft, encoding="utf-8"))

        vw = vendor_words_for(p, dj.get("_source_document"))
        # An ASSIGNED family in projects.json always wins. The family name is a
        # catalogue decision (AGENT.md 4); once Dino has made it, it must survive
        # every rebuild rather than being re-derived from the project name.
        assigned = bool(p.get("family") and p.get("lc_sku_prefix"))
        if assigned:
            fam, sku = p["family"], p["lc_sku_prefix"].strip().upper()
            if not sku.startswith("LC-"):
                sku = "LC-" + sku.lstrip("-")
        else:
            fam, sku = placeholder_family(p["name"], vw)
            # A naming rule fixes the PREFIX by product class (Dino, 2026-09-15: every
            # troffer is LC-CBT-<series>). It does not invent the series name - that is
            # still his, so the sheet keeps its placeholder banner until he names it.
            rule = class_for(dj.get("product_type"), dj.get("_category"),
                             " ".join(str(v) for v in (dj.get("_matrix") or {}).get("models", [])[:3]),
                             p.get("name"), p.get("subject"))
            if rule:
                sku = "%s-%s" % (rule["prefix"], re.sub(r"[^A-Z0-9]+", "",
                                                        (sku or "").split("-")[-1].upper()) or "TBD")
                print("   naming rule: %s -> prefix %s (series name still pending)"
                      % (rule["class"], rule["prefix"]))
        if not fam:
            print("   blocked: every word of the project name names the vendor, so there is "
                  "no placeholder family left. Dino assigns the family name.")
            continue

        # Product type follows the CATEGORY the extractor determined. It was
        # hardcoded to "LED Troffer" for every project, which is how a
        # transparent display shipped as a troffer.
        cat = dj.get("_category") or "lighting"
        ptype = (p.get("product_type")
                 or {"display": "Transparent LED Display"}.get(cat, "Luminaire"))
        if cat == "display" and dj.get("_matrix") and not dj.get("_selected_model"):
            print("   blocked: the vendor sheet holds %d models and none is selected. "
                  "The quote decides which column is ours - set _selected_model in the draft."
                  % len(dj["_matrix"]["models"]))
            continue

        ul = (dj.get("possible_certifications") or {}).get("ul") or {}
        if test_no_ul:
            print("   UL GATE WAIVED - internal test build, authorised by Dino 2026-09-11.")
            print("   No certification is claimed on the sheet; the cert block stays empty.")
        elif not (ul.get("verified") and ul.get("candidates") and ul.get("standard")):
            print("[%s] BLOCKED - no confirmed UL/ETL listing, so no LC sheet." % p["name"])
            print("      Need a file number AND the named standard, both confirmed by a human.")
            print("      Set possible_certifications.ul = {verified:true, candidates:[\"E123456\"],")
            print("      standard:\"UL 1598\"} in %s once you have them." % os.path.basename(draft))
            continue

        sheet = rebrand.to_sheet(dj, fam, ptype, sku)
        if not assigned:
            sheet["cover"]["subtitle"] = "PLACEHOLDER FAMILY AND SKU - CATALOGUE NAMES PENDING"

        leaks = leak_check(sheet, vw)
        if leaks:
            print("   REFUSED: vendor identity survived into the sheet: %s" % ", ".join(leaks))
            continue
        # Hero photo. A PNG already in the project folder wins - that is the
        # human-chosen one. Otherwise lift it off the vendor sheet: AGENT.md 6
        # allows a vendor product photo when it carries no badge or watermark,
        # and until now nothing actually fetched one, so every sheet rendered
        # the "PRODUCT PHOTOGRAPH" placeholder unless someone did it by hand.
        hero_warn = []
        shots = sorted(glob.glob(os.path.join(glob.escape(d), "*.png")))
        if shots:
            sheet["hero_png"] = shots[0]
        else:
            try:
                import hero
                cand = hero.find(src, os.path.join(d, "hero - from vendor sheet.png"))
            except Exception as e:
                cand = None
                print("   hero extraction failed (%s) - placeholder kept" % e)
            if cand:
                sheet["hero_png"] = cand
                hero_warn = ["Hero photo was lifted from the vendor datasheet. Check it "
                             "carries no vendor badge or watermark before release."]
                print("   hero photo lifted from the vendor sheet: %s" % os.path.basename(cand))
        blocking, warn = builder.check(sheet, allow_no_ul=test_no_ul)
        warn = hero_warn + warn
        if blocking:
            print("   blocked: " + "; ".join(blocking)); continue
        if not assigned:
            warn = ["Family name %r and SKU %r are placeholders from the project name" % (fam, sku)] + warn
        # A test build gets a name that does NOT match the "04 LC Spec Sheet*"
        # glob, so it can never be mistaken for the real sheet and never blocks
        # a proper build once a listing exists.
        out_pdf = os.path.join(d, ("04 TEST BUILD (no UL) - %s.pdf" if test_no_ul
                                   else "04 LC Spec Sheet - %s.pdf") % sku)
        path, poppins = overlay.build(sheet, warn, out_pdf)
        print("   built: %s  (%s)" % (os.path.basename(path), "Poppins" if poppins else "Helvetica fallback"))
        built += 1
    print("%d LC sheet(s) built" % built)
    return 0


if __name__ == "__main__":
    sys.exit(main())
