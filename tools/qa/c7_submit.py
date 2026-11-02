"""Charter 7: SUBMIT MATERIAL CHECK (2026-11-02): report each problem from the list, then submit."""
import os, sys, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bench import setup, BASE, PW, QA
from harness import open_browser, login_ui, context, photo, SHOTS
from playwright.sync_api import sync_playwright
lc, U = setup()
JPG = photo()
res = []
def check(ok, what, d=""):
    res.append(ok); print(("PASS " if ok else "FAIL ") + what + ("  -- " + str(d) if not ok else ""))
with sync_playwright() as p:
    br = open_browser(p); ctx = context(br, "desktop"); pg = ctx.new_page()
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    login_ui(pg, BASE, "alice", PW); pg.goto(BASE + "/job.html?id=KR-00345-NV"); pg.wait_for_load_state("networkidle")
    n = pg.locator("[data-line]").count()
    check("SUBMIT" in pg.locator("#btnApprove").inner_text().upper(), "main button says SUBMIT", pg.locator("#btnApprove").inner_text())
    # count everything: tap + once on each (starts from expected), then make row 2 short by 1
    for i in range(n):
        pg.locator('button[data-f="received"][data-d="1"]').nth(i).click(); pg.wait_for_timeout(80)
    pg.locator('button[data-f="received"][data-d="-1"]').nth(2).click(); pg.wait_for_timeout(80)
    pg.locator('button[data-f="received"][data-d="-1"]').nth(2).click(); pg.wait_for_timeout(1200)
    btn = pg.locator("#btnApprove").inner_text()
    check("SUBMIT MATERIAL CHECK" in btn.upper() and f"{n} / {n}" in btn, "all counted: SUBMIT MATERIAL CHECK · n / n", btn)
    pg.locator(".bar").screenshot(path=SHOTS + "/submit-footer.png")
    pg.click("#btnApprove"); pg.wait_for_timeout(400)
    pg.locator("#ovApprove .dlg").screenshot(path=SHOTS + "/submit-1-short.png")
    check(pg.locator("#apSend").is_disabled() and pg.locator("[data-ckreport]").count() == 1, "a short product: REPORT in the list, SUBMIT locked")
    pg.click("[data-ckreport]"); pg.wait_for_timeout(400)
    check(not pg.locator("#ovClaim").is_hidden() and pg.locator("#ovApprove").is_hidden(), "REPORT opens that product's claim")
    pg.fill("#clNote", "one box missing"); pg.click("#clSend"); pg.wait_for_timeout(2000)
    check(not pg.locator("#ovApprove").is_hidden() and pg.locator(".ckdone").count() == 1 and pg.locator("#apSend").is_enabled(),
          "after the claim, back on the list: REPORTED MC-..., SUBMIT unlocked", pg.locator(".ckdone").all_inner_texts())
    pg.locator("#ovApprove .dlg").screenshot(path=SHOTS + "/submit-2-reported.png")
    pg.click("#apSend"); pg.wait_for_timeout(400)
    check("tick the box" in pg.locator(".toast").inner_text().lower(), "submit needs the confirm box")
    pg.check("#apConfirm"); pg.click("#apSend"); pg.wait_for_timeout(2500)
    t = pg.locator(".toast").inner_text()
    check("submitted" in t.lower() and not pg.locator("#vInstall").is_hidden(), "submitted: toast says so, install opens", t)
    print("errors", errs)
    br.close()
json.dump(res, open(QA + "/c7.json", "w"))
print("\n%d checks, %d failed" % (len(res), sum(1 for r in res if not r)))
