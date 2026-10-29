"""Charter 6: Sergei's iPad notes (2026-10-29), each checked in the browser."""
import os
import base64, json, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bench import setup, BASE, PW, QA
from harness import open_browser, context, login_ui, photo, SHOTS
from playwright.sync_api import sync_playwright

lc, U = setup()
res = []
def check(ok, what, detail=""):
    res.append((bool(ok), what, str(detail))); print(("PASS " if ok else "FAIL ") + what + ("  -- " + str(detail) if detail and not ok else ""))
JPG = photo()
J = BASE + "/job.html?id=KR-00345-NV"
# the office relay is paired, so app emails queue for it (as on the live site)
lc.call("POST", "relay/pair", {})

with sync_playwright() as p:
    br = open_browser(p); ctx = context(br, "ipad"); pg = ctx.new_page()
    login_ui(pg, BASE, "alice", PW)
    # The live catalog lists every bracket's manual on the Optimus (what Sergei
    # saw); this bench cannot reach it, so the job reply gets six of them.
    def with_manuals(route):
        r = route.fetch(); j = r.json()
        for b in j.get("site", {}).get("bom", []):
            if "Optimus" in (b.get("name") or ""):
                b["catalog"] = dict(b.get("catalog") or {}, docs=[{"label": "Installation manual " + c, "url": "https://example.invalid/" + c + ".pdf"} for c in ("F", "R", "SR", "SS", "T", "U")])
        route.fulfill(response=r, json=j)
    pg.route("**/api/jobs/KR-00345-NV", lambda r: with_manuals(r) if r.request.method == "GET" else r.continue_())
    pg.goto(J); pg.wait_for_load_state("networkidle")

    # Material 2b: Photo Library as well as the camera
    caps = pg.evaluate("Array.from(document.querySelectorAll('input[type=file]')).filter(i => i.hasAttribute('capture')).map(i => i.id)")
    check(caps == [], "no photo button forces the camera (iPad offers Photo Library too)", caps)

    # Material 2a: REPORT with a damaged count updates the row
    pg.locator("[data-report]").nth(2).click(); pg.wait_for_timeout(300)
    pg.click('#clKinds [data-k="damaged"]')
    pg.fill("#clLines [data-r]", "12"); pg.fill("#clLines [data-dm]", "2")
    with pg.expect_file_chooser() as fc:
        pg.click("#clPhotoBtn")
    fc.value.set_files(JPG); pg.wait_for_timeout(1200)
    pg.click("#clSend"); pg.wait_for_timeout(2500)
    row = pg.locator("[data-line]").nth(2)
    rec = row.locator("input[data-f=received]").input_value(); dmg = row.locator("input[data-f=damaged]").input_value()
    check(rec == "12" and dmg == "2" and "DAMAGED 2" in row.inner_text().upper(), "a damaged count typed in REPORT shows on the row", (rec, dmg))
    t = pg.locator(".toast").inner_text()
    check("queued" in t and "relay" in t, "with the office relay waiting, the toast says the email is queued, not sent", t)
    pg.reload(); pg.wait_for_load_state("networkidle")
    check(pg.locator("[data-line]").nth(2).locator("input[data-f=damaged]").input_value() == "2", "the row's new counts are saved")

    # sign off so the install opens
    s, job = U["alice"].call("GET", "jobs/KR-00345-NV")
    lines = {b["key"]: {"received": b["qty"], "damaged": 0} for b in job["site"]["bom"]}
    U["alice"].call("PUT", "jobs/KR-00345-NV/material", {"lines": lines})
    U["alice"].call("POST", "jobs/KR-00345-NV/approve", {"lines": lines, "confirm": True})
    pg.reload(); pg.wait_for_load_state("networkidle"); pg.click("#stInstall"); pg.wait_for_timeout(1500)

    # Install 2: find by ID, ID in the card heading
    s01 = [x for x in job["site"]["pins"] if x["tag"] == "S01"][0]
    pg.fill("#findFid", str(s01["fid"])); pg.press("#findFid", "Enter"); pg.wait_for_timeout(1200)
    head = pg.locator("#card h2").inner_text()
    check("ID " + str(s01["fid"]) in head and head.startswith("S01"), "FIND FIXTURE opens that pin; the card heading shows its ID", head)
    labels = pg.evaluate("Array.from(document.querySelectorAll('.lbl')).filter(l => getComputedStyle(l.parentElement).visibility !== 'hidden').map(l => l.textContent)")
    check(any((" · " + str(s01["fid"])) in l for l in labels), "close in, map tags carry the fixture ID", labels[:6])

    # Install 1: only this fixture's documents, the rest behind MORE DOCUMENTS
    shown = pg.locator("#card .docs a:visible").all_inner_texts()
    more = pg.locator("#card [data-moredocs]")
    check(more.count() == 1 and pg.locator("#card .moredocs").is_hidden() and not any("manual" in s.lower() for s in shown),
          "only this fixture's guide, spec sheet and job sheet show; the other manuals wait behind MORE DOCUMENTS", (shown, more.count()))
    pg.screenshot(path=SHOTS + "/c6-s01-card.png")
    more.click(); pg.wait_for_timeout(200)
    check(pg.locator("#card .moredocs").is_visible(), "MORE DOCUMENTS opens them")

    # Install 3: flag -> red pin, Problems chip; the list stays on its own pin
    pg.click("#card [data-flag]"); pg.wait_for_timeout(300)
    pg.locator("#flKinds button").first.click(); pg.fill("#flNote", "Arm bent"); pg.click("#flSend"); pg.wait_for_timeout(2000)
    fill = pg.evaluate("(() => { const s = Array.from(document.querySelectorAll('path.leaflet-interactive')).map(e => e.getAttribute('fill')); return s.filter(f => f === '#ef4444').length; })()")
    check(fill == 1, "the flagged fixture turns red on the map", fill)
    chip = pg.locator(".flt.prob")
    check(chip.count() == 1 and "1" in chip.inner_text(), "a PROBLEMS chip appears with the count", chip.inner_text() if chip.count() else "none")
    pg.click("#card [data-next]"); pg.wait_for_timeout(800)
    check(pg.locator("#flags").inner_text().strip() == "" and "Arm bent" not in pg.locator("#card").inner_text(), "another pin's card does not carry the flag")
    chip.click(); pg.wait_for_timeout(600)
    check("Arm bent" in pg.locator("#flags").inner_text(), "PROBLEMS lists the job's flags")
    pg.screenshot(path=SHOTS + "/c6-problems.png")
    br.close()

json.dump(res, open(QA + "/c6.json", "w"))
print("\n%d checks, %d failed" % (len(res), sum(1 for r in res if not r[0])))
