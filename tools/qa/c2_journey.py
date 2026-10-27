"""Charter 2: the installer's whole job on an iPad, then LED Connection approves it.
Function + Operations (SFDPOT): every step a real installer takes, with what the screen says."""
import os
import json, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bench import setup, BASE, PW, QA
from harness import open_browser, context, Watch, login_ui, photo, SHOTS
from playwright.sync_api import sync_playwright

lc, U = setup()
res = []
def check(ok, what, detail=""):
    res.append((bool(ok), what, str(detail))); print(("PASS " if ok else "FAIL ") + what + ("  -- " + str(detail) if detail and not ok else ""))
def shot(pg, name): pg.screenshot(path=SHOTS + "/c2-" + name + ".png")
JPG = photo()

with sync_playwright() as p:
    br = open_browser(p)
    ctx = context(br, "ipad")
    pg = ctx.new_page(); W = Watch(pg)
    login_ui(pg, BASE, "alice", PW)
    shot(pg, "01-home")
    check(pg.locator("text=Kroger 345").count() > 0, "installer's home lists the Kroger 345 job")
    check(pg.locator("text=TEST-SITE-01").count() == 0 and pg.locator("text=Test Site").count() == 0, "installer does not see the other crew's job")
    pg.goto(BASE + "/job.html?id=KR-00345-NV"); pg.wait_for_load_state("networkidle")
    shot(pg, "02-material")
    check(pg.locator("#btnApprove").inner_text().strip().upper().startswith("CHECKLIST 0 / 7"), "main button starts at CHECKLIST 0 / 7", pg.locator("#btnApprove").inner_text())
    check(pg.locator("#stInstall").is_disabled(), "INSTALL step is locked before sign-off")
    check(pg.locator("text=Downlight 16W").count() > 0 and pg.locator("text=Set to 16W").count() > 0, "rows show product and short set-up line")

    # count everything: the first + sets the expected quantity
    n = pg.locator("[data-line]").count()
    for i in range(n):
        pg.locator('button[data-f="received"][data-d="1"]').nth(i).click()
    pg.wait_for_timeout(300)
    # one short, one damaged
    pg.locator('button[data-f="received"][data-d="-1"]').nth(1).click()
    pg.locator('button[data-f="damaged"][data-d="1"]').nth(2).click()
    pg.wait_for_timeout(1500)
    txt = pg.locator("#btnApprove").inner_text().upper()
    check("7 / 7" in txt and "PROCEED" in txt, "button reads 7 / 7 · PROCEED TO INSTALLATION when all counted", txt)
    check("1 short" in pg.locator("#matSum").inner_text() and "1 damaged" in pg.locator("#matSum").inner_text(), "summary shows 1 short, 1 damaged", pg.locator("#matSum").inner_text())

    # autosave survives a reload
    pg.reload(); pg.wait_for_load_state("networkidle")
    vals = pg.evaluate("Array.from(document.querySelectorAll('input[data-f=received]')).map(i => i.value)")
    check(all(v != "" for v in vals), "counts survive a reload (autosave)", vals)

    # REPORT on the short row: one product, kind preset
    pg.locator("[data-report]").nth(1).click(); pg.wait_for_timeout(300)
    check(pg.locator("#clLines .cl-line:not(.head)").count() == 1, "REPORT on a row shows only that product")
    check(pg.locator("#clKinds .on").inner_text().upper() == "SHORT SHIPPED", "kind preset to SHORT SHIPPED from the count")
    pg.fill("#clNote", '<img src=x onerror="window.__xss=1"> one box missing')
    pg.click("#clSend"); pg.wait_for_timeout(1500)
    check("saved" in pg.locator(".toast").inner_text(), "short claim sends", pg.locator(".toast").inner_text())
    check(pg.evaluate("window.__xss") is None and pg.locator("#claims").inner_text().find("<img") >= 0, "a note with HTML shows as text, nothing runs")
    # damaged claim without photo is refused, with photo works
    pg.locator("[data-report]").nth(2).click(); pg.wait_for_timeout(300)
    check(pg.locator("#clKinds .on").inner_text().upper() == "DAMAGED", "kind preset to DAMAGED from the count")
    pg.click("#clSend"); pg.wait_for_timeout(1000)
    check("photo" in pg.locator(".toast").inner_text().lower(), "damaged claim without a photo is refused with a reason", pg.locator(".toast").inner_text())
    with pg.expect_file_chooser() as fc:
        pg.click("#clPhotoBtn")
    fc.value.set_files(JPG); pg.wait_for_timeout(1500)
    check(pg.locator("#clShots img").count() == 1, "photo shows in the claim")
    shot(pg, "03-claim-damaged")
    # double tap SEND: must file one claim, not two
    before = len(lc.call("GET", "jobs/KR-00345-NV")[1]["claims"])
    pg.locator("#clSend").dblclick(); pg.wait_for_timeout(2000)
    after = len(lc.call("GET", "jobs/KR-00345-NV")[1]["claims"])
    check(after - before == 1, "double-tapping SEND CLAIM files one claim", "%d new" % (after - before))

    # checklist and sign-off
    pg.click("#btnApprove"); pg.wait_for_timeout(300)
    shot(pg, "04-checklist")
    check(pg.locator(".ck li").count() == 7, "checklist lists 7 products")
    check(pg.locator("#apSend").is_enabled(), "PROCEED enabled when all counted")
    pg.click("#apSend"); pg.wait_for_timeout(800)
    check("tick" in pg.locator(".toast").inner_text().lower(), "PROCEED without the confirm box asks for it", pg.locator(".toast").inner_text())
    pg.check("#apConfirm"); pg.click("#apSend"); pg.wait_for_timeout(2000)
    check(pg.locator("#btnApprove").is_hidden(), "main button gone after sign-off")
    check(pg.locator("input[data-f=received]").first.is_disabled(), "counts locked after sign-off")
    check(not pg.locator("#stInstall").is_disabled(), "INSTALL unlocked")
    shot(pg, "05-signed")

    # install view
    pg.click("#stInstall"); pg.wait_for_timeout(2500)
    shot(pg, "06-install")
    pins = pg.locator("path.leaflet-interactive")
    check(pins.count() >= 88, "install map shows the heads", pins.count())
    pins.first.click(force=True); pg.wait_for_timeout(500)
    shot(pg, "07-pincard")
    check(pg.locator("#card [data-save]").is_disabled(), "SAVE AS INSTALLED is disabled until a photo is taken")
    with pg.expect_file_chooser() as fc:
        pg.click("#card [data-shot]")
    fc.value.set_files(JPG); pg.wait_for_timeout(1500)
    pg.fill("#pinSerial", "SN-0001")
    pg.click("#card [data-save]"); pg.wait_for_timeout(1500)
    check("1 / 88" in pg.locator("#progBig").inner_text(), "progress counts the saved head", pg.locator("#progBig").inner_text())
    pg.click("#card [data-next]"); pg.wait_for_timeout(600)
    check(pg.locator("#card [data-save]").count() == 1, "NEXT opens another head")
    # flag a problem
    pg.click("#card [data-flag]"); pg.wait_for_timeout(300)
    pg.locator("#flKinds button").first.click(); pg.fill("#flNote", "Arm cracked")
    pg.click("#flSend"); pg.wait_for_timeout(1500)
    check("FL-" in pg.locator(".toast").inner_text() or "flag" in pg.locator(".toast").inner_text().lower(), "flag a problem sends", pg.locator(".toast").inner_text())
    # submit is refused while heads are left
    check(pg.locator("#btnSubmit").is_disabled(), "SUBMIT JOB disabled while heads are left")
    # record a message from the install side
    pg.locator("#vInstall [data-rec]").click(); pg.wait_for_timeout(300)
    pg.click('#rcKinds [data-k="voice"]'); pg.wait_for_timeout(1200)
    pg.click("#rcGo"); pg.wait_for_timeout(2000); pg.click("#rcGo"); pg.wait_for_timeout(1000)
    pg.click("#rcSend"); pg.wait_for_timeout(2500)
    check("MS-" in pg.locator(".toast").inner_text(), "voice message sends from the install side", pg.locator(".toast").inner_text())

    # finish the rest through the API (88 heads) and submit in the UI
    s, job = U["alice"].call("GET", "jobs/KR-00345-NV")
    import base64
    s, ph = U["alice"].call("PUT", "jobs/KR-00345-NV/photos", {"dataUrl": "data:image/jpeg;base64," + base64.b64encode(open(JPG, "rb").read()).decode()})
    for pin in job["site"]["pins"]:
        if not pin.get("off") and not (job["pins"].get(pin["id"]) or {}).get("installed"):
            U["alice"].call("PUT", "jobs/KR-00345-NV/pins/" + pin["id"], {"photos": [ph["name"]]})
    pg.reload(); pg.wait_for_load_state("networkidle"); pg.click("#stInstall"); pg.wait_for_timeout(1500)
    check("88 / 88" in pg.locator("#progBig").inner_text(), "all 88 heads saved", pg.locator("#progBig").inner_text())
    check(pg.locator("#btnSubmit").is_enabled(), "SUBMIT JOB enabled when every head is saved")
    pg.once("dialog", lambda d: d.accept())
    pg.click("#btnSubmit"); pg.wait_for_timeout(2500)
    shot(pg, "08-submitted")
    check(U["alice"].call("GET", "jobs/KR-00345-NV")[1]["job"].get("submitted"), "job is submitted")
    # after submit the installer cannot change a pin
    s, _ = U["alice"].call("PUT", "jobs/KR-00345-NV/pins/" + job["site"]["pins"][0]["id"], {"photos": [ph["name"]], "note": "late"})
    check(s in (403, 409), "a submitted job refuses pin changes", s)
    inst_errors = list(W.errors); inst_http = list(W.http)

    # LED Connection approves
    ctx2 = context(br, "desktop"); p2 = ctx2.new_page(); W2 = Watch(p2)
    login_ui(p2, BASE, "dino", PW)
    p2.goto(BASE + "/job.html?id=KR-00345-NV&review=1"); p2.wait_for_load_state("networkidle"); p2.wait_for_timeout(1500)
    shot(p2, "09-review")
    check(p2.locator("#approval").is_visible(), "LC admin sees the approval bar")
    btns = p2.locator("#approval button")
    names = [b.inner_text().upper() for b in btns.all()]
    check(any("APPROVE" in n for n in names) and any("SEND BACK" in n for n in names), "APPROVE and SEND BACK offered", names)
    br.close()

print("installer console/page errors:", inst_errors)
print("installer HTTP errors:", inst_http)
print("admin errors:", W2.errors, W2.http)
json.dump({"res": res, "errors": inst_errors, "http": inst_http, "admin": [W2.errors, W2.http]}, open(QA + "/c2.json", "w"))
print("\n%d checks, %d failed" % (len(res), sum(1 for r in res if not r[0])))
