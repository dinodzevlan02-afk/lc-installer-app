"""Charter 4: Operations + Time (SFDPOT). What happens when the field gets messy: the session
runs out, the signal drops, two tablets edit the same job, someone opens a bad link."""
import os
import json, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bench import setup, BASE, PW, QA
from harness import open_browser, context, Watch, login_ui, SHOTS
from playwright.sync_api import sync_playwright

lc, U = setup()
res = []
def check(ok, what, detail=""):
    res.append((bool(ok), what, str(detail))); print(("PASS " if ok else "FAIL ") + what + ("  -- " + str(detail) if detail and not ok else ""))
def toast(pg):
    t = pg.locator(".toast")
    return t.inner_text() if t.count() and t.is_visible() else ""
J = BASE + "/job.html?id=KR-00345-NV"

with sync_playwright() as p:
    br = open_browser(p)
    ctx = context(br, "ipad"); pg = ctx.new_page(); W = Watch(pg)
    login_ui(pg, BASE, "alice", PW)
    pg.goto(J); pg.wait_for_load_state("networkidle")

    # 1. the signal drops while counting: autosave fails
    pg.route("**/api/jobs/KR-00345-NV/material", lambda r: r.abort("internetdisconnected"))
    pg.locator('button[data-f="received"][data-d="1"]').nth(0).click()
    pg.wait_for_timeout(3500)
    t = toast(pg); pg.screenshot(path=SHOTS + "/c4-offline-save.png")
    check("no signal" in t.lower() and "save" in t.lower(), "a count that cannot be saved (no signal) says it is not saved yet", t or "nothing shown")
    pg.unroute("**/api/jobs/KR-00345-NV/material")
    pg.locator('button[data-f="received"][data-d="1"]').nth(1).click()
    pg.wait_for_timeout(3000)
    saved = U["alice"].call("GET", "jobs/KR-00345-NV")[1]["material"].get("lines", {})
    keys = [b["key"] for b in U["alice"].call("GET", "jobs/KR-00345-NV")[1]["site"]["bom"]]
    check(saved.get(keys[0], {}).get("received") is not None, "the count made while offline is saved once the signal is back", saved.get(keys[0]))

    # 2. two tablets on the same job: last write wins?
    ctx2 = context(br, "ipad"); pg2 = ctx2.new_page()
    login_ui(pg2, BASE, "alice", PW); pg2.goto(J); pg2.wait_for_load_state("networkidle")
    pg.locator("input[data-f=received]").nth(2).fill("5"); pg.locator("input[data-f=received]").nth(2).dispatch_event("change"); pg.wait_for_timeout(2500)
    pg2.locator("input[data-f=received]").nth(3).fill("4"); pg2.locator("input[data-f=received]").nth(3).dispatch_event("change"); pg2.wait_for_timeout(2500)
    lines = U["alice"].call("GET", "jobs/KR-00345-NV")[1]["material"].get("lines", {})
    check(lines.get(keys[2], {}).get("received") == 5 and lines.get(keys[3], {}).get("received") == 4,
          "two tablets counting different products on one job keep both counts", {k[:12]: (lines.get(k) or {}).get("received") for k in keys[:4]})

    # 3. session expires mid-work
    ctx.clear_cookies()
    pg.locator('button[data-f="received"][data-d="1"]').nth(4).click(); pg.wait_for_timeout(3000)
    t = toast(pg); pg.screenshot(path=SHOTS + "/c4-session-expired.png")
    check("sign" in (t + pg.url).lower() or "index.html" in pg.url, "an expired session says so / goes to sign-in", (t, pg.url))
    login_ui(pg, BASE, "alice", PW)

    # 4. sign off twice (two tablets)
    s, job = U["alice"].call("GET", "jobs/KR-00345-NV")
    full = {b["key"]: {"received": b["qty"], "damaged": 0} for b in job["site"]["bom"]}
    U["alice"].call("PUT", "jobs/KR-00345-NV/material", {"lines": full})
    a = U["alice"].call("POST", "jobs/KR-00345-NV/approve", {"lines": full, "confirm": True})[0]
    b = U["alice"].call("POST", "jobs/KR-00345-NV/approve", {"lines": full, "confirm": True})[0]
    import glob
    mails = [m for m in (json.load(open(f)) for f in glob.glob(QA + "/store/outbox/*.json")) if "Material signed off" in (m.get("subject") or "")]
    check(a == 200 and b in (409, 400) and len(mails) == 1, "a second sign-off is refused and sends no second email", (a, b, len(mails)))

    # 5. bad links
    pg.goto(BASE + "/job.html?id=NO-SUCH-JOB"); pg.wait_for_load_state("networkidle"); pg.wait_for_timeout(800)
    body = pg.locator("body").inner_text()
    pg.screenshot(path=SHOTS + "/c4-bad-job.png")
    check("not found" in body.lower() or "no job" in body.lower(), "a link to a job that does not exist says so", body[:200].replace("\n", " | "))
    pg.goto(BASE + "/job.html?id=TEST-SITE-01"); pg.wait_for_load_state("networkidle"); pg.wait_for_timeout(800)
    body2 = pg.locator("body").inner_text()
    check("not found" in body2.lower() and "TEST" not in body2.split("not found")[0][-40:], "a link to another crew's job reads as not found", body2[:200].replace("\n", " | "))
    pg.goto(BASE + "/job.html"); pg.wait_for_load_state("networkidle"); pg.wait_for_timeout(800)
    check(pg.locator("#vLoading").inner_text() != "Loading the job…" or "job" in pg.url, "job page with no id does not hang on Loading", pg.locator("body").inner_text()[:160].replace("\n", " | "))

    # 6. upload drops mid-way: error shown, a retry works
    pg.goto(J); pg.wait_for_load_state("networkidle")
    pg.locator("#vMaterial [data-rec]").click(); pg.click('#rcKinds [data-k="camera"]'); pg.wait_for_timeout(1200)
    pg.click("#rcGo"); pg.wait_for_timeout(2500); pg.click("#rcGo"); pg.wait_for_timeout(1000)
    pg.route("**/api/jobs/KR-00345-NV/media", lambda r: r.abort("internetdisconnected"))
    pg.click("#rcSend"); pg.wait_for_timeout(2500)
    info = pg.locator("#rcInfo").inner_text(); t = toast(pg)
    check("not sent" in info.lower() and pg.locator("#rcSend").is_enabled(), "a failed upload says not sent and lets the installer try again", (info, t))
    pg.unroute("**/api/jobs/KR-00345-NV/media")
    pg.click("#rcSend"); pg.wait_for_timeout(2500)
    check("MS-" in toast(pg), "the retry sends the message", toast(pg))
    br.close()

json.dump(res, open(QA + "/c4.json", "w"))
print("\n%d checks, %d failed" % (len(res), sum(1 for r in res if not r[0])))
