import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bench import setup, BASE, PW
from harness import open_browser, context, login_ui, SHOTS
from playwright.sync_api import sync_playwright
lc, U = setup()
s, job = U["alice"].call("GET", "jobs/KR-00345-NV")
lines = {b["key"]: {"received": b["qty"], "damaged": 0} for b in job["site"]["bom"]}
U["alice"].call("PUT", "jobs/KR-00345-NV/material", {"lines": lines}); U["alice"].call("POST", "jobs/KR-00345-NV/approve", {"lines": lines, "confirm": True})
with sync_playwright() as p:
    br = open_browser(p); ctx = context(br, "phone"); pg = ctx.new_page()
    login_ui(pg, BASE, "alice", PW); pg.goto(BASE + "/job.html?id=KR-00345-NV"); pg.wait_for_load_state("networkidle")
    pg.click("#stInstall"); pg.wait_for_timeout(1500)
    pg.locator("path.leaflet-interactive").nth(5).tap(force=True); pg.wait_for_timeout(1500)
    r = pg.evaluate("(() => { const c = document.getElementById('card').getBoundingClientRect(); return [Math.round(c.top), Math.round(c.height)]; })()")
    print("card top, height:", r, "of", pg.viewport_size["height"], "| back button visible:", pg.locator("#card [data-tomap]").is_visible(), "| save visible:", pg.locator("#card [data-shot]").is_visible())
    pg.screenshot(path=SHOTS + "/c5-phone-card.png")
    pg.locator("#card [data-tomap]").tap(); pg.wait_for_timeout(800)
    print("after back: progress visible:", pg.locator(".prog").is_visible(), "| filters visible:", pg.locator("#filters").is_visible())
    br.close()
