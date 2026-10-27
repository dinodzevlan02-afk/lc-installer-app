"""Charter 3: Platform (SFDPOT) + accessibility. Each page and dialog on phone, iPad (both ways),
laptop and desktop: sideways scroll, touch targets under 44 px on touch screens, axe-core."""
import os
import json, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bench import setup, BASE, PW, QA
from harness import open_browser, context, Watch, login_ui, SHOTS
from playwright.sync_api import sync_playwright

lc, U = setup()
# alice signs off so the install view opens
s, job = U["alice"].call("GET", "jobs/KR-00345-NV")
lines = {b["key"]: {"received": b["qty"], "damaged": 0} for b in job["site"]["bom"]}
U["alice"].call("PUT", "jobs/KR-00345-NV/material", {"lines": lines})
assert U["alice"].call("POST", "jobs/KR-00345-NV/approve", {"lines": lines, "confirm": True})[0] == 200
if not os.path.exists(QA + "/axe.min.js"):   # axe-core from npm (cdns may be blocked)
    import subprocess, tarfile
    subprocess.run(["npm", "pack", "axe-core@4.10.2", "--silent"], cwd=QA, check=True)
    with tarfile.open(QA + "/axe-core-4.10.2.tgz") as t:
        open(QA + "/axe.min.js", "wb").write(t.extractfile("package/axe.min.js").read())
AXE = open(QA + "/axe.min.js").read()

PROBE = """() => {
  const vw = document.documentElement.clientWidth, out = {overflow: document.documentElement.scrollWidth - vw, small: [], wide: []};
  const coarse = matchMedia('(pointer: coarse)').matches;
  document.querySelectorAll('button, a.btn, input:not([type=hidden]), select, textarea, [role=button]').forEach(el => {
    const r = el.getBoundingClientRect(), cs = getComputedStyle(el);
    if (!r.width || !r.height || cs.visibility === 'hidden' || el.closest('[hidden]')) return;
    if (el.closest('.leaflet-control-attribution')) return;
    const label = (el.innerText || el.value || el.getAttribute('aria-label') || el.id || el.tagName).trim().slice(0, 30);
    if (coarse && (r.height < 44 || (r.width < 44 && el.type !== 'checkbox'))) out.small.push(label + ' ' + Math.round(r.width) + 'x' + Math.round(r.height));
    if (r.right > vw + 1) out.wide.push(label + ' right=' + Math.round(r.right));
  });
  return out;
}"""

results = {}
def probe(pg, name, kind):
    pg.wait_for_timeout(400)
    d = pg.evaluate(PROBE)
    pg.add_script_tag(content=AXE)
    ax = pg.evaluate("async () => (await axe.run(document, {resultTypes: ['violations']})).violations.map(v => ({id: v.id, impact: v.impact, n: v.nodes.length, help: v.help, eg: v.nodes.slice(0,2).map(n => n.target.join(' '))}))")
    pg.screenshot(path=SHOTS + "/c3-%s-%s.png" % (kind, name))
    results.setdefault(kind, {})[name] = {"overflow": d["overflow"], "small": d["small"][:12], "nsmall": len(d["small"]), "wide": d["wide"][:6],
                                           "axe": [a for a in ax if a["impact"] in ("serious", "critical")]}
    r = results[kind][name]
    print("%-14s %-16s overflow=%-4s small=%-3d offscreen=%-2d axe(serious+)=%s" % (kind, name, d["overflow"], len(d["small"]), len(d["wide"]),
          ", ".join("%s(%d)" % (a["id"], a["n"]) for a in r["axe"]) or "-"))

with sync_playwright() as p:
    br = open_browser(p)
    for kind in ("phone", "ipad-portrait", "ipad", "laptop", "desktop"):
        ctx = context(br, kind); pg = ctx.new_page()
        pg.goto(BASE + "/index.html"); pg.wait_for_load_state("networkidle"); probe(pg, "signin", kind)
        login_ui(pg, BASE, "alice", PW); probe(pg, "home-installer", kind)
        pg.goto(BASE + "/job.html?id=KR-00345-NV"); pg.wait_for_load_state("networkidle"); probe(pg, "material", kind)
        pg.locator("[data-report]").first.click(); probe(pg, "dlg-report", kind); pg.click("#clCancel")
        pg.locator("[data-docs]").first.click(); probe(pg, "dlg-docs", kind); pg.click("#dcClose")
        pg.locator("#vMaterial [data-rec]").click(); probe(pg, "dlg-record", kind); pg.click("#rcCancel")
        pg.click("#stInstall"); pg.wait_for_timeout(1500); probe(pg, "install", kind)
        pg.locator("path.leaflet-interactive").nth(5).click(force=True); probe(pg, "pincard", kind)
        pg.goto(BASE + "/manual.html?job=KR-00345-NV&p=" + job["site"]["bom"][0]["key"]); pg.wait_for_load_state("networkidle"); probe(pg, "jobsheet", kind)
        ctx.close()
        # LC admin home only on the two big sizes
        if kind in ("ipad", "desktop"):
            ctx = context(br, kind); pg = ctx.new_page()
            login_ui(pg, BASE, "dino", PW); probe(pg, "home-lc", kind); ctx.close()
    br.close()
json.dump(results, open(QA + "/c3.json", "w"), indent=1)
