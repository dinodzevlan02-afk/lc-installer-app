# Shared chrome: CSS, page furniture, leak guard, Chrome PDF render, PNG preview.
# LC-XCPA layout (log/lc-xcpa-specsheet-20261008). The supplier is named ZERO times.
# Copied 2026-10-12 from log/pf-1574/build-20261009 for the Kroger track head + T8 sheets;
# copied again 2026-10-16 from kroger-t8-20261006/specsheets-20261012 for LC HOIST (HST).
# OUT, PREVIEW, the leak-guard word list (case-insensitive now), the source folders and the
# safe-token list are the changes.
# Copied again 2026-10-19 from youlumi-specsheets-20261016\hoist for LC OPTIMUS SERIES (LC-SLOT),
# the DLC private-label (Standard) sheet. New OUT/PREVIEW, new vendor word list, word-boundary
# patterns (VENDOR_RE) for short tokens, and the source-filename tokens of the factory files.
import io, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = r"C:\Users\DinoDzevlan\Downloads\AOK Optimus DLC listing 2026-10-19"
PREVIEW = os.path.join(OUT, "_previews", "optimus")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

FOOT = ('<div class="foot"><span><b>PHONE:</b>702.847.7680</span>'
        '<span><b>WEB:</b>www.ledconnection.com</span>'
        '<span><b>EMAIL:</b>bids@ledconnection.com</span>'
        '<span class="addr">915 E Dale Ave Ste 110 Henderson, NV 89044</span></div>')

CUSTOM = '<div class="custom">For custom solutions please contact our sales representative.</div>'


def hdr(t, s):
    return ('<div class="hdr"><span class="t">%s</span><span class="s">%s</span>'
            '<img src="assets/logo_head.png" alt="LED Connection"></div>' % (t, s))


CSS = """
@page { size: 8.5in 11in; margin: 0; }
@font-face { font-family:Poppins; src:url("assets/fonts/Poppins-Light.ttf"); font-weight:300; }
@font-face { font-family:Poppins; src:url("assets/fonts/Poppins-Regular.ttf"); font-weight:400; }
@font-face { font-family:Poppins; src:url("assets/fonts/Poppins-Medium.ttf"); font-weight:500; }
@font-face { font-family:Poppins; src:url("assets/fonts/Poppins-SemiBold.ttf"); font-weight:600; }
@font-face { font-family:Poppins; src:url("assets/fonts/Poppins-Bold.ttf"); font-weight:700; }
@font-face { font-family:Poppins; src:url("assets/fonts/Poppins-ExtraBold.ttf"); font-weight:800; }
@font-face { font-family:Poppins; src:url("assets/fonts/Poppins-Black.ttf"); font-weight:900; }
:root { --navy:#1A1A2E; --orange:#f37021; --ink:#1A1A2E; --grey:#5d6170; --line:#d9dbe1; --soft:#f4f4f6; }
* { box-sizing:border-box; }
html, body { margin:0; padding:0; font-family:Poppins, Arial, sans-serif; color:var(--ink);
  -webkit-print-color-adjust:exact; print-color-adjust:exact; }
.page { width:8.5in; height:11in; position:relative; overflow:hidden; page-break-after:always; background:#fff; }
.page:last-child { page-break-after:auto; }
.foot { position:absolute; left:0; right:0; bottom:0; height:.32in; background:var(--navy);
  border-top:3px solid var(--orange); color:#fff; display:flex; align-items:center; gap:.28in;
  padding:0 .45in; font-size:7.6pt; font-weight:500; }
.foot b { color:var(--orange); font-weight:600; font-size:6.4pt; letter-spacing:.04em; margin-right:4px; }
.foot .addr { margin-left:auto; }
/* cover */
.side { position:absolute; left:0; top:0; bottom:.32in; width:.93in; background:var(--navy); }
.side .vt { position:absolute; left:50%; bottom:.98in; writing-mode:vertical-rl; transform:translateX(-50%) rotate(180deg); transform-origin:center center;
  white-space:nowrap; color:var(--orange); font-weight:700; font-size:7.4pt; letter-spacing:.12em; }
.side img { position:absolute; left:50%; transform:translateX(-50%); bottom:.12in; width:.74in; }
.art { position:absolute; left:1.15in; top:.52in; right:1.30in; height:4.72in; object-fit:contain; }
.art.tall { left:3.9in; right:1.3in; top:.42in; height:4.85in; }
.badges { position:absolute; right:.42in; top:5.40in; display:flex; flex-direction:column; align-items:center; gap:.1in; }
.badges img { width:.5in; }
.badges img.cul { width:.72in; }
.tbadge { width:.78in; border:1.4px solid var(--navy); border-radius:3px; text-align:center; padding:.03in .02in;
  font-size:5.1pt; font-weight:800; letter-spacing:.03em; line-height:1.25; color:var(--navy); }
.tbadge i { display:block; font-style:normal; color:var(--orange); font-size:5.6pt; }
.cv { position:absolute; left:1.25in; top:5.52in; right:.45in; }
.kick { font-size:12pt; font-weight:500; letter-spacing:.02em; }
.big { font-family:Poppins; font-weight:900; font-size:44pt; line-height:1; letter-spacing:.01em; margin:.04in 0 .1in; }
.big.sm { font-size:34pt; }
.rule { width:2.1in; height:4px; background:var(--orange); margin:.06in 0 .14in; }
.lpw { color:var(--orange); font-weight:900; font-size:20pt; letter-spacing:.03em; }
.tag { font-size:7.4pt; color:#454857; letter-spacing:.035em; margin-top:.05in; }
.strip { display:grid; grid-template-columns:repeat(6,1fr); margin-top:.24in; border-top:1px solid var(--line); }
.strip div { padding:.11in .07in .04in 0; border-right:1px solid var(--line); margin-right:.09in; }
.strip div:last-child { border-right:0; }
.strip small { display:block; color:var(--orange); font-size:5.6pt; font-weight:600; letter-spacing:.07em; }
.strip span { font-weight:800; font-size:9.8pt; line-height:1.15; }
.pn { margin-top:.18in; font-size:8pt; color:#454857; }
.pn b { color:var(--ink); font-weight:700; letter-spacing:.02em; }
.callout { margin-top:.14in; background:var(--soft); border-left:4px solid var(--orange); padding:.12in .18in; }
.callout h4 { margin:0 0 .04in; font-size:8.2pt; font-weight:800; letter-spacing:.05em; }
.callout p { margin:0; font-size:8.2pt; line-height:1.45; }
.custom { position:absolute; right:.6in; bottom:.45in; font-size:8pt; font-style:italic; font-weight:300; color:#454857; }
.proj { position:absolute; left:1.25in; right:.45in; top:.30in; font-size:7pt; font-weight:600; letter-spacing:.06em;
  color:#7a7e8c; }
/* inner pages */
.hdr { position:absolute; left:.45in; right:.45in; top:.32in; height:.42in; border-bottom:1px solid var(--line);
  display:flex; align-items:center; gap:.2in; }
.hdr .t { color:var(--orange); font-weight:800; font-size:7.6pt; letter-spacing:.06em; }
.hdr .s { color:#7a7e8c; font-size:7pt; letter-spacing:.04em; }
.hdr img { margin-left:auto; height:.42in; margin-top:-.08in; }
.body { position:absolute; left:.45in; right:.45in; top:.95in; bottom:.52in; }
.h1 { font-size:10pt; font-weight:500; margin-top:.18in; }
.h1 + .big { font-size:30pt; margin:.02in 0 .02in; }
.code { color:var(--orange); font-weight:900; font-size:11.5pt; letter-spacing:.03em; }
.code small { display:block; color:#7a7e8c; font-weight:500; font-size:7.2pt; letter-spacing:.03em; margin-top:1px; }
.hero2 { position:absolute; right:0; top:.05in; width:2.45in; }
.hero2.nar { width:1.9in; }
.wrapn { padding-right:2.65in; }
.icons { display:flex; gap:.1in; margin-top:.20in; align-items:center; }
.icons img { height:.62in; }
.dim0 { width:.58in; height:.58in; border-radius:50%; border:3px solid var(--orange); border-right-color:#f6b08a;
  display:flex; flex-direction:column; align-items:center; justify-content:center; font-weight:800; font-size:6.2pt;
  line-height:1.05; text-align:center; color:var(--ink); }
.hl { margin-top:.26in; background:#fdeee5; border-left:4px solid var(--orange); padding:.1in .16in; }
.hl h4 { margin:0 0 .03in; font-size:7.8pt; font-weight:800; letter-spacing:.05em; }
.hl p { margin:0; font-size:8.4pt; line-height:1.4; }
.sec { display:flex; align-items:center; margin:.18in 0 .09in; }
.sec h3 { margin:0; background:var(--navy); color:#fff; font-size:9.5pt; font-weight:800; letter-spacing:.08em;
  padding:.05in .14in; min-width:3.1in; border-left:5px solid var(--orange); }
.sec::after { content:""; flex:1; height:1px; background:var(--line); align-self:flex-end; }
p.txt { margin:0; font-size:8.4pt; line-height:1.5; }
ul.ov { margin:0; padding-left:.18in; font-size:8.2pt; line-height:1.45; }
ul.ov.two { column-count:2; column-gap:.3in; }
ul.ov li::marker { color:var(--orange); }
.dims { display:flex; align-items:flex-start; gap:.25in; }
.dims img { width:3.1in; }
.dims .w { font-size:7.6pt; line-height:1.6; color:#454857; }
.dims .w b { color:var(--ink); }
/* order logic */
.olx { font-size:8.4pt; margin-bottom:.09in; }
.sample { background:var(--navy); color:#fff; padding:.1in .22in .08in; border-left:5px solid var(--orange); }
.sample small { font-size:6.6pt; letter-spacing:.1em; color:#b9bccb; }
.segs { display:flex; align-items:flex-end; gap:.05in; margin-top:.02in; font-weight:900; font-size:15pt; letter-spacing:.02em; }
.segs .sg { display:flex; flex-direction:column; align-items:center; }
.segs .sg i { font-style:normal; color:var(--orange); font-size:6.2pt; font-weight:600; margin-top:.02in; letter-spacing:.05em; }
.segs .o { color:var(--orange); }
.segs .dash { color:#6c7083; font-weight:600; padding-bottom:.12in; }
.cards { display:grid; gap:.05in; margin-top:.1in; }
.card { background:var(--soft); font-size:6.8pt; line-height:1.32; }
.card h5 { margin:0; background:var(--orange); color:#fff; font-size:6.2pt; font-weight:700; letter-spacing:.04em; padding:.04in .05in; }
.card div { padding:.06in .06in .08in; }
.card b { display:block; font-weight:800; font-size:7.4pt; }
.card .op { margin-top:.05in; }
table { width:100%; border-collapse:collapse; font-size:7.4pt; }
th { background:var(--navy); color:#fff; font-weight:700; font-size:6.6pt; letter-spacing:.04em; text-align:left; padding:.055in .08in; }
td { padding:.04in .08in; border-bottom:1px solid #e6e7ec; }
tr:nth-child(even) td { background:#f6f6f8; }
td.k { font-weight:800; }
td.c, th.c { text-align:center; }
.pass { color:#1b7f4a; font-weight:800; }
.note { font-size:6.9pt; color:#454857; margin-top:.06in; line-height:1.4; }
.note b { color:var(--ink); }
.cfm { color:#b4531a; font-weight:800; }
.tbar { background:var(--orange); color:#fff; text-align:center; font-weight:800; font-size:7.2pt; letter-spacing:.08em; padding:.06in; margin-top:.14in; }
.small-h { font-size:7.2pt; font-weight:800; letter-spacing:.05em; margin:.02in 0 .05in; }
.photo-grid { display:grid; grid-template-columns:1fr 1fr; gap:.22in; margin-top:.05in; }
.pcard { border:1px solid var(--line); padding:.08in .08in .04in; }
.pcard h6 { margin:0 0 .04in; font-size:7.2pt; font-weight:800; letter-spacing:.04em; color:var(--navy); }
.pcard .sub { font-size:6.6pt; color:#7a7e8c; margin-bottom:.04in; }
.pcard .pw { height:2.45in; }
.pcard .pw svg { height:100%; width:auto; display:block; margin:0 auto; }
.twocol { display:grid; grid-template-columns:1fr 1fr; gap:.22in; }
.band { background:#fdeee5; border-left:4px solid var(--orange); padding:.08in .14in; font-size:7.2pt; line-height:1.45; margin-top:.1in; }
.band b { font-weight:800; }
"""


def doc(title, pages):
    return ("<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">\n"
            "<title>%s</title>\n<style>%s</style>\n</head>\n<body>\n%s\n</body></html>\n"
            % (title, CSS, "\n".join(pages)))


# ---------------------------------------------------------------- leak guard
# Everything that could name or fingerprint the factory. The LC part numbers
# carry the factory's stock code by Dino's rule (2026-10-08, "LC- + the XSY
# factory code, kept intact"), so the code itself is allowed; the NAME, the
# brand, the domains, the contacts and the source filenames are not.
VENDOR_WORDS = [
    # LC OPTIMUS (2026-10-19). Factory name and domain, its people, its address (street, park,
    # district, cities, other plants), its phones, its model prefix and model-code fragments,
    # its optic codes, its DLC family code, the LED and driver brands printed in its catalogue,
    # and the LED / driver brands on our own 2023 sheet (no longer the parts used).
    "AOK", "aokledlight", "aok-", "Shirly", "Wally", "Wendy", "rd9@", "Shajing", "St George",
    "St. George", "Minsheng", "Huizhou", "Fuzhou", "Yinghui", "Zhongkai", "Chenjiang", "Dongsheng",
    "Baihuazhou", "Cangshan", "Binan", "Laguna", "Shenzhen",
    "WoT", "NVS", "HVS", "S5-DV", "-DV-", "T302", "T402", "T502", "T422", "T542", "BBBFPK",
    "626-986", "626 986", "986-4050", "755 2357", "2357 9148", "518124", "516006", "350007",
    "Seoul", "Sosen", "Lumileds", "Meanwell", "Mean Well", "HVG", "Mitsubishi", "EN AC-46100",
    "AOK2026", "SL130",
]
# Short tokens that need word boundaries (a bare substring would hit ordinary words, e.g.
# "LC-SLOT series" contains "ot series").
VENDOR_RE = [r"\bot series\b", r"\bot-series\b", r"\b\d{2,3}wot\b", r"\bs5\b", r"\b[345]0[78]0\b",
             r"\bjl-\d", r"\bsk618\b", r"\bbri816\b", r"\bfsp-2\d\d"]
# Commercial terms that must never appear on an LC sheet.
MONEY = [r"\$\s*\d", r"\bmoq\b", r"\bfob\b", r"\bexw\b", r"\bincoterm", r"\bunit price",
         r"\bprice\b", r"\bpricing\b", r"\bquotation\b", r"\bdeposit\b", r"\breseller licen"]


def leak_check(label, html, extra_ok=()):
    blob = html.lower()
    hits = []
    for w in VENDOR_WORDS:
        if w in extra_ok:
            continue
        if w.lower() in blob:
            hits.append("vendor word %r" % w)
    for pat in VENDOR_RE:
        m = re.search(pat, blob)
        if m:
            hits.append("vendor pattern %r" % m.group(0))
    for pat in MONEY:
        m = re.search(pat, blob)
        if m:
            hits.append("commercial term %r" % m.group(0))
    if "\u2014" in html:
        hits.append("em dash")
    # filename-leak guard: no source filename token may survive. The LC OPTIMUS factory
    # sources (2026-10-19): the DLC export, the catalogue and the factory mail folder.
    srcfiles = [r"C:\Users\DinoDzevlan\Downloads\lc-sourcing\log\walmart-v811\mail\1008-0011_DLC_Data_Export_2026-08-31.xlsx"]
    catdir = r"C:\Users\DinoDzevlan\Downloads\lc-sourcing\log\walmart-v811\aok-1019"
    srcfiles += [os.path.join(catdir, f) for f in os.listdir(catdir)]
    toks = set()
    for fn in srcfiles:
        for t in re.split(r"[^A-Za-z0-9]+", os.path.splitext(os.path.basename(fn))[0]):
            if len(t) > 3 and not t.isdigit():
                toks.add(t.lower())
    # Ordinary English and lighting vocabulary that happens to sit in a source filename.
    safe = {"data", "export", "catalog", "light", "certificate", "using", "listing", "image",
            "outlook", "form", "edits", "excel", "private", "label", "luna", "jpeg"}
    for t in sorted(toks):
        if t in safe or t in extra_ok:
            continue
        if re.search(r"\b%s\b" % re.escape(t), blob):
            hits.append("source-filename token %r" % t)
    print("  LEAK CHECK %-26s %s" % (label, "PASS" if not hits else "FAIL: " + "; ".join(sorted(set(hits)))))
    return hits


def to_pdf(html_path, pdf_name):
    os.makedirs(OUT, exist_ok=True)
    tmpprof = tempfile.mkdtemp(prefix="lcchrome-")
    tmppdf = os.path.join(tempfile.gettempdir(), "lc-" + re.sub(r"\W+", "-", pdf_name) + ".pdf")
    if os.path.exists(tmppdf):
        os.remove(tmppdf)
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--user-data-dir=" + tmpprof, "--no-pdf-header-footer",
           "--run-all-compositor-stages-before-draw", "--virtual-time-budget=20000",
           "--print-to-pdf=" + tmppdf, "file:///" + html_path.replace("\\", "/")]
    subprocess.run(cmd, check=False, capture_output=True, timeout=240)
    if not os.path.exists(tmppdf) or os.path.getsize(tmppdf) < 20000:
        raise SystemExit("Chrome produced no PDF for " + pdf_name)
    dest = os.path.join(OUT, pdf_name)
    for _ in range(6):
        try:
            shutil.copyfile(tmppdf, dest)
            break
        except OSError:
            import time
            time.sleep(1.5)
    shutil.rmtree(tmpprof, ignore_errors=True)
    return dest


def strip_metadata(pdf_path, title, subject):
    import pymupdf
    d = pymupdf.open(pdf_path)
    d.set_metadata({"title": title, "author": "LED Connection, LLC",
                    "subject": subject, "keywords": "", "creator": "LED Connection",
                    "producer": "LED Connection"})
    d.saveIncr()
    d.close()


def preview(pdf_path):
    import pymupdf
    os.makedirs(PREVIEW, exist_ok=True)
    d = pymupdf.open(pdf_path)
    base = os.path.splitext(os.path.basename(pdf_path))[0]
    outs = []
    for i, p in enumerate(d):
        f = os.path.join(PREVIEW, "%s - p%d.png" % (base, i + 1))
        p.get_pixmap(dpi=110).save(f)
        outs.append(f)
    return outs


def pdf_text_check(pdf_path):
    """Second leak pass on the RENDERED text layer - catches anything that
    reached the page through an image-free vector path."""
    import pymupdf
    d = pymupdf.open(pdf_path)
    blob = "".join(p.get_text() for p in d).lower()
    hits = [w for w in VENDOR_WORDS if w.lower() in blob]
    hits += ["pattern:" + m.group(0) for m in (re.search(p, blob) for p in VENDOR_RE) if m]
    meta = " ".join(str(v) for v in d.metadata.values() if v).lower()
    hits += ["metadata:" + w for w in VENDOR_WORDS if w.lower() in meta]
    fname = os.path.basename(pdf_path).lower()
    hits += ["filename:" + w for w in VENDOR_WORDS if w.lower() in fname]
    if "—" in "".join(p.get_text() for p in d):
        hits.append("em dash in text layer")
    return hits
