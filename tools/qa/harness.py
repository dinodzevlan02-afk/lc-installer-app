"""Browser harness: Chromium with fake camera/mic, Google tiles blocked (no network needed),
console errors, page errors and failed requests collected per page."""
import os
import io, os
from PIL import Image
from playwright.sync_api import sync_playwright

QA = os.environ.get("QA_OUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "out"))
os.makedirs(QA, exist_ok=True)
SHOTS = QA + "/shots"
os.makedirs(SHOTS, exist_ok=True)

def photo(path=QA + "/photo.jpg", color=(200, 120, 40)):
    Image.new("RGB", (1200, 900), color).save(path, "JPEG", quality=80)
    return path

def open_browser(p):
    return p.chromium.launch(executable_path="/opt/pw-browsers/chromium",
                             args=["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream"])

def context(br, kind="ipad", **kw):
    sizes = {"ipad": dict(viewport={"width": 1366, "height": 1024}, has_touch=True),
             "ipad-portrait": dict(viewport={"width": 1024, "height": 1366}, has_touch=True),
             "phone": dict(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True, device_scale_factor=3),
             "desktop": dict(viewport={"width": 1600, "height": 960}),
             "laptop": dict(viewport={"width": 1280, "height": 760})}
    opts = dict(sizes[kind]); opts.update(kw)
    ctx = br.new_context(permissions=["camera", "microphone"], **opts)
    ctx.route("https://mt*.google.com/**", lambda r: r.abort())
    ctx.route("https://*.google.com/**", lambda r: r.abort())
    return ctx

class Watch:
    """Collects what a tester watches in DevTools: console errors, uncaught errors, HTTP errors."""
    def __init__(self, page, ignore=()):
        self.errors, self.http = [], []
        page.on("console", lambda m: m.type == "error" and self.errors.append("console: " + m.text))
        page.on("pageerror", lambda e: self.errors.append("pageerror: " + str(e)))
        page.on("response", lambda r: r.status >= 400 and not any(i in r.url for i in ignore) and self.http.append("%d %s %s" % (r.status, r.request.method, r.url.split("4400")[-1])))

def login_ui(page, base, user, pw):
    page.goto(base + "/index.html"); page.wait_for_load_state("networkidle")
    page.fill("#siUser", user); page.fill("#siPass", pw)
    page.click("#fSignIn button[type=submit], #fSignIn button")
    page.wait_for_url("**/home.html", timeout=10000); page.wait_for_load_state("networkidle")
