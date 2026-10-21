#!/usr/bin/env python3
"""
An LC spec sheet DRAFT from a vendor datasheet Dino sends back on a HABER? thread.

    python haber-specsheet.py <vendor.pdf> ["what he asked"]     build one, print the result

Dino, 2026-09-21: "are you able to build LC spec sheet out of the attachment that I
provide to you? I ask a question, and you provide me all products available, I leave
what I want, and reply to you with attachment that I want a spec sheet, and also
mention a note that Dino needs to approve this spec sheet."

WHAT THIS IS. The same pipeline the watcher runs for a project folder - intake reads
the vendor PDF, rebrand turns the draft into an LC sheet with placeholder family and
SKU, overlay renders it on the template - driven from an email reply instead of a
project folder, and built as a DRAFT: the UL gate that blocks a project sheet is
waived here the way an internal test build waives it, and the band across the hero
says so. Nothing on the sheet is verified. The family name and the SKU are his to
assign; the sheet says so on its cover. The factory is never named on the sheet -
that is hard rule 1 in specsheet/AGENT.md and it holds for a draft too: a vendor
word that survives into the sheet is a refusal, not a warning.

HOW THE VALUES ARE READ. intake.py runs first for the draft's shape and its regex
candidates; then a model reads the rendered pages and writes the draft proper - the
regex over a brochure is a hint, not a reading (on the first build it offered a CRI
of 10 and an efficacy of 30 lm/W, both artefacts). The model's draft is checked to
exist and to parse; if it left nothing usable, intake's draft is used and the band
says the values are low trust. The model is never trusted to have done anything it
did not leave on disk.

THE FAMILY NAME comes from Dino's own words in the request - "4 inch downlight" gives
"4 Inch Downlight Series" - never from the file name, which on the first build leaked
a date and lost the product words. It is a placeholder either way and the sheet says so.
"""
import datetime
import glob
import importlib.util
import io
import json
import os
import re
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.abspath(__file__))
SPEC = os.path.join(ROOT, "specsheet")
sys.path.insert(0, SPEC)
sys.path.insert(0, os.path.join(ROOT, "slack"))
import links  # noqa: E402


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


H = _load("haber", os.path.join(ROOT, "haber.py"))                    # claude(), log(), CFG
PS = _load("projectsheet", os.path.join(SPEC, "project-sheet.py"))    # run(), placeholder_family(), class_for(), vendor_words_for(), leak_check()
import rebrand, overlay, build as builder  # noqa: E402
try:
    import hero  # noqa: E402
except Exception:
    hero = None

ENG = PS.BASE
DRAFTS = os.path.join(ENG, "Spec Sheet Drafts") if ENG else os.path.join(SPEC, "output")
FROM = os.path.join(DRAFTS, "_from-email")
SCHEMA = os.path.join(SPEC, "schema.json")

APPROVAL = "DRAFT - REQUIRES DINO'S APPROVAL. Nothing on this sheet is verified; every value is as read from the vendor document."
INTENT = re.compile(r"spec\s*-?\s*sheet|specsheet|\blc\s+sheet|cut\s*-?\s*sheet|data\s*sheet\s+for\s+us", re.I)
REQUEST_NOISE = re.compile(r"(?i)\b(i|we|want|need|please|can|could|you|make|build|give|me|us|a|an|the|this|that|for|of|spec|sheet|specsheet|lc|cut|data|from|it|and|also|haber|thanks|thank|dino|attached|attachment|file|pdf|one|these|those|hi|hello|regards|best)\b")


def wants_sheet(text):
    return bool(INTENT.search(text or ""))


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# --------------------------------------------------------------- model stage --

def render_pages(src, stem, limit=5, dpi=150):
    """Page images for the model to read, whether or not the PDF has a text layer."""
    import pymupdf
    imgdir = os.path.join(DRAFTS, "_page-images")
    os.makedirs(imgdir, exist_ok=True)
    out = []
    doc = pymupdf.open(src)
    for i in range(min(doc.page_count, limit)):
        p = os.path.join(imgdir, "%s-email-p%02d.png" % (stem, i + 1))
        doc.load_page(i).get_pixmap(matrix=pymupdf.Matrix(dpi / 72.0, dpi / 72.0)).save(p)
        out.append(p)
    doc.close()
    return out


def model_stage(src, stem, seed_draft=None):
    """A model reads the rendered pages and writes the draft. Seeded with intake's own
    draft when there is one - the shape to mirror, and its regex candidates as hints to
    confirm or discard. Returns (draft path or None, reason)."""
    try:
        shots = render_pages(src, stem)
    except Exception as e:
        return None, "could not render pages: %s" % str(e)[:120]
    if not shots:
        return None, "no pages rendered - nothing for the model to read"
    example = ""
    if seed_draft and os.path.exists(seed_draft):
        example = io.open(seed_draft, encoding="utf-8").read()[:7000]
    if not example:
        for cand in sorted(glob.glob(os.path.join(glob.escape(DRAFTS), "*.draft.json")), key=os.path.getmtime, reverse=True):
            try:
                example = io.open(cand, encoding="utf-8").read()[:6000]
                break
            except OSError:
                continue
    if not example:
        try:
            example = json.dumps(json.load(io.open(SCHEMA, encoding="utf-8-sig")).get("example_lighting", {}), indent=1)[:6000]
        except Exception:
            example = "{}"
    draft = os.path.join(DRAFTS, "%s.model.draft.json" % stem)
    if os.path.exists(draft):
        os.remove(draft)
    prompt = (
        "You are reading a lighting vendor's datasheet. Use the Read tool on each of these page images, in order:\n"
        + "\n".join(shots[:6]) +
        "\n\nThen use the Write tool ONCE to write a spec sheet DRAFT as JSON to exactly this path:\n" + draft +
        "\n\nMirror the SHAPE of this existing draft exactly (same top-level keys, same nesting; the values are yours "
        "to fill from the pages):\n<<<\n" + example + "\n>>>\n\n"
        "Rules: every extracted value is a candidate with verified:false and a one-line source saying which page it "
        "was read from. The example's candidates came from a regex and may be wrong - keep only what the pages "
        "actually print, correct what they contradict, drop what they do not support. The vendor's company name and "
        "its model numbers go ONLY under _source_document, as an object {\"file\": ..., \"vendor\": \"<company as "
        "printed>\", \"models\": [...]}, nowhere else. Set product_type to what the sheet is (for example 'LED "
        "Downlight', 'Linear High Bay', 'Wall Pack'). _category is lighting or display. Never invent a value that is "
        "not printed on the pages; leave a field out rather than guess. Any UL, ETL or DLC number printed goes under "
        "possible_certifications with verified:false. Do not use any other tool. When the file is written, reply "
        "with only the word WRITTEN.")
    try:
        r = H.claude(prompt, tools="Read,Write", max_turns=14, timeout=600, job="probe")
    except Exception as e:
        return None, "model stage failed: %s" % str(e)[:200]
    if not os.path.exists(draft):
        return None, "model reported %r but left no draft on disk" % (r or "")[:60]
    try:
        dj = json.load(io.open(draft, encoding="utf-8"))
    except Exception as e:
        return None, "model wrote a draft that does not parse: %s" % str(e)[:120]
    if not isinstance(dj, dict) or not (dj.get("extracted") or {}):
        return None, "model wrote a draft with no extracted values"
    return draft, ""


# ---------------------------------------------------------------------- build --

def family_from_request(question, vendor_words):
    """Dino's own words, minus the request noise and the vendor, as a placeholder."""
    ask = REQUEST_NOISE.sub(" ", question or "")
    ask = re.sub(r"[^A-Za-z0-9 ]+", " ", ask)
    ask = re.sub(r"\s+", " ", ask).strip()
    if not ask:
        return None, None
    return PS.placeholder_family(ask, vendor_words)


def build_one(path, question, who):
    name = os.path.basename(path)
    res = {"file": name, "status": "failed", "why": "", "warn": []}
    if not name.lower().endswith(".pdf"):
        res.update(status="skipped", why="only a PDF datasheet can become a spec sheet")
        return res
    os.makedirs(FROM, exist_ok=True)
    src = os.path.join(FROM, "%s_%s" % (datetime.date.today().isoformat(), re.sub(r'[\\/:*?"<>|]', "_", name)))
    if not os.path.exists(src):
        shutil.copy2(path, src)
    # the stem names the draft and nothing else; it comes from the ORIGINAL file name
    stem = re.sub(r"[^A-Za-z0-9]+", "-", os.path.splitext(name)[0]).strip("-")[:60] or "sheet"

    # 1. intake for the shape and the hints, then a model read of the pages for the values
    rc, out = PS.run([os.path.join(SPEC, "intake.py"), src])
    seed = None
    m = re.search(r"draft:\s+(.+\.draft\.json)", out)
    if m and os.path.exists(m.group(1).strip()):
        seed = m.group(1).strip()
    draft, why = model_stage(src, stem, seed)
    if not draft:
        if seed:
            draft = seed
            res["warn"].append("The model read of the pages failed (%s); the values are intake's regex candidates and are LOW TRUST." % why)
        else:
            res["why"] = ("no text layer and " if "NO TEXT LAYER" in out else "") + why
            return res
    dj = json.load(io.open(draft, encoding="utf-8"))
    res["draft"] = draft
    res["fields"] = len(dj.get("extracted") or {})

    # 2. the vendor, as the reading recorded it, and a placeholder family from the request
    sd = dj.get("_source_document")
    vendor_name = (sd.get("vendor") if isinstance(sd, dict) else "") or ""
    vw = {w.lower() for w in re.split(r"[^A-Za-z0-9]+", vendor_name) if len(w) > 2}
    vw |= PS.vendor_words_for({"name": "", "to": who or ""}, "")
    fam, sku = family_from_request(question, vw)
    warn_pre = [APPROVAL]
    if not fam:
        base = (dj.get("product_type") or "").strip()
        fam = ("%s Series" % base) if base else "Unnamed Series"
        sku = ("LC-" + "".join(w[0] for w in base.split()).upper()[:4]) if base else "LC-TBD"
        warn_pre.append("Family name %r and SKU %r are placeholders from the product type on the sheet. Dino assigns both." % (fam, sku))
    else:
        warn_pre.append("Family name %r and SKU %r are placeholders from the words of the request. Dino assigns both." % (fam, sku))
    rule = PS.class_for(dj.get("product_type"), dj.get("_category"),
                        " ".join(str(v) for v in (dj.get("_matrix") or {}).get("models", [])[:3]), stem, question)
    if rule:
        sku = "%s-%s" % (rule["prefix"], re.sub(r"[^A-Z0-9]+", "", (sku or "").split("-")[-1].upper()) or "TBD")
    cat = dj.get("_category") or "lighting"
    ptype = (dj.get("product_type") or "").strip() or {"display": "Transparent LED Display"}.get(cat, "Luminaire")
    ul = (dj.get("possible_certifications") or {}).get("ul") or {}
    if not (ul.get("verified") and ul.get("candidates") and ul.get("standard")):
        warn_pre.append("UL/ETL listing NOT confirmed. The certification block stays empty until a file number and the standard are confirmed by a person.")

    # 3. the sheet, with the factory checked out of it
    sheet = rebrand.to_sheet(dj, fam, ptype, sku)
    sheet.setdefault("cover", {})["subtitle"] = "DRAFT - PLACEHOLDER FAMILY AND SKU - REQUIRES DINO'S APPROVAL"
    leaks = PS.leak_check(sheet, vw)
    if leaks:
        res.update(status="refused", why="the vendor's identity survived into the sheet (%s) - assign a family name that does not carry it" % ", ".join(leaks))
        return res
    hero_warn = []
    if hero:
        try:
            cand = hero.find(src, os.path.join(FROM, stem + " - hero.png"))
            if cand:
                sheet["hero_png"] = cand
                hero_warn = ["Hero photo was lifted from the vendor datasheet. Check it carries no vendor badge or watermark."]
        except Exception:
            pass
    blocking, warn = builder.check(sheet, allow_no_ul=True)
    if blocking:
        res.update(status="blocked", why="; ".join(blocking))
        return res
    out_pdf = os.path.join(DRAFTS, "DRAFT LC Spec Sheet - %s - %s - requires Dino approval.pdf" % (sku, stem[:48]))
    warn_all = warn_pre + res["warn"] + hero_warn + warn
    path_out, poppins = overlay.build(sheet, warn_all, out_pdf)
    res.update(status="built", pdf=path_out, family=fam, sku=sku, ptype=ptype, vendor=vendor_name, warn=warn_all, why="")
    return res


def build_from_files(paths, question, who):
    out = []
    for p in paths:
        try:
            out.append(build_one(p, question, who))
        except Exception as e:
            out.append({"file": os.path.basename(p), "status": "failed", "why": "%s: %s" % (type(e).__name__, str(e)[:200]), "warn": []})
    return out


# ---------------------------------------------------------------- rendering --

def render_email(results, question):
    h = ["<p style='font-size:15px'><b>%s</b></p>" % esc(APPROVAL)]
    built = [r for r in results if r["status"] == "built"]
    if built:
        h.append("<p>%d draft sheet%s attached. The family name and SKU on each are placeholders - yours to assign - and the cover says so. "
                 "Nothing on them is verified; the band across the hero lists what is pending.</p>" % (len(built), "" if len(built) == 1 else "s"))
        h.append("<table border='1' cellpadding='6' style='border-collapse:collapse;font-size:13px'>"
                 "<tr><th align='left'>From</th><th align='left'>Draft</th><th align='left'>Type</th><th align='left'>Placeholder family / SKU</th><th align='left'>Fields read</th><th align='left'>Pending</th></tr>")
        for r in built:
            h.append("<tr><td style='vertical-align:top'>%s</td><td style='vertical-align:top'>%s</td><td style='vertical-align:top'>%s</td>"
                     "<td style='vertical-align:top'>%s<br><span style='color:#888'>%s</span></td><td style='vertical-align:top'>%s</td>"
                     "<td style='vertical-align:top;font-size:12px'>%s</td></tr>" % (
                         esc(r["file"]), esc(os.path.basename(r["pdf"])), esc(r.get("ptype", "")), esc(r.get("family", "")), esc(r.get("sku", "")),
                         r.get("fields", 0), "<br>".join(esc(w) for w in r["warn"][1:6])))
        h.append("</table>")
    others = [r for r in results if r["status"] != "built"]
    if others:
        h.append("<p><b>Not built:</b></p><ul>%s</ul>" % "".join("<li>%s - <b>%s</b>: %s</li>" % (esc(r["file"]), esc(r["status"]), esc(r.get("why", ""))) for r in others))
    h.append("<p style='color:#666;font-size:12px'>To release a sheet: assign the family name and SKU, confirm each value against the vendor document, confirm the UL/ETL file number and standard, then the pre-release band comes off. Until then this is a draft for your approval and nothing else.</p>")
    return "".join(h)


def slack_summary(results, question):
    L = ["*HABER? spec sheet draft* — _%s_" % re.sub(r"\s+", " ", (question or "")).strip()[:160], "", "*%s*" % APPROVAL, ""]
    for r in results:
        if r["status"] == "built":
            u = None
            try:
                u = links.web_url(r["pdf"])
            except Exception:
                pass
            nm = os.path.basename(r["pdf"])
            L.append(":page_facing_up: %s — %s, placeholder %s / %s, %s field(s) read" % (
                ("<%s|%s>" % (u, nm)) if u else nm, r.get("ptype", ""), r.get("family", ""), r.get("sku", ""), r.get("fields", 0)))
        else:
            L.append(":no_entry_sign: %s — %s: %s" % (r["file"], r["status"], (r.get("why") or "")[:160]))
    L.append("")
    L.append("_The drafts went to Dino by email as attachments._")
    return "\n".join(L)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__); return 2
    q = args[1] if len(args) > 1 else "spec sheet"
    res = build_from_files([args[0]], q, "dinod@ledconnection.com")
    for r in res:
        print("%-9s %s" % (r["status"].upper(), r["file"]))
        for k in ("pdf", "family", "sku", "ptype", "vendor", "fields", "why", "draft"):
            if r.get(k) not in (None, "", 0):
                print("   %-7s %s" % (k, r[k]))
        for w in r.get("warn", []):
            print("   band    - " + w)
    return 0


if __name__ == "__main__":
    sys.exit(main())
