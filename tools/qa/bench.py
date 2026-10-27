"""QA bench for the LC Installer App: a fresh local server + store, an LC admin,
two crews with one installer each, two jobs. Import Client / setup from here."""
import os
import json, os, subprocess, time, urllib.request, urllib.error, http.cookiejar, shutil

APP = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
QA = os.environ.get("QA_OUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "out"))
os.makedirs(QA, exist_ok=True)
PORT = 4400
BASE = "http://127.0.0.1:%d" % PORT
STORE = QA + "/store"
PW = "Correct-Horse-9"


class Client:
    def __init__(self):
        self.ck = ""

    def call(self, method, path, body=None, headers=None, raw=False, csrf=True):
        h = {"Content-Type": "application/json"}
        if method != "GET" and csrf:
            h["X-LCI"] = "1"
        if self.ck:
            h["Cookie"] = self.ck
        h.update(headers or {})
        data = None if body is None else (body if isinstance(body, bytes) else json.dumps(body).encode())
        req = urllib.request.Request(BASE + "/api/" + path, data=data, method=method, headers=h)
        try:
            r = urllib.request.urlopen(req, timeout=60)
            status, buf, hdr = r.status, r.read(), dict(r.headers)
        except urllib.error.HTTPError as e:
            status, buf, hdr = e.code, e.read(), dict(e.headers)
        sc = hdr.get("Set-Cookie") or hdr.get("set-cookie")
        if sc:
            v = sc.split(";")[0]
            self.ck = "" if v.endswith("=") else v
        if raw:
            return status, buf, hdr
        try:
            j = json.loads(buf.decode() or "null")
        except Exception:
            j = buf.decode(errors="replace")
        return status, j

    def cookie(self):
        return self.ck


def start_server():
    shutil.rmtree(STORE, ignore_errors=True)
    env = dict(os.environ, INSTALLER_LOCAL_STORE=STORE, PORT=str(PORT))
    log = open(QA + "/server.log", "w")
    subprocess.Popen(["node", "dev/server.js"], cwd=APP, env=env, stdout=log, stderr=log, start_new_session=True)
    for _ in range(50):
        try:
            urllib.request.urlopen(BASE + "/index.html", timeout=2)
            return
        except Exception:
            time.sleep(0.2)
    raise SystemExit("server did not start")


def setup():
    start_server()
    lc = Client()
    assert lc.call("POST", "setup", {"key": "local-dev-setup-key", "username": "dino", "name": "Dino Dzevlan", "password": PW,
                                    "email": "dinod@ledconnection.com"})[0] in (200, 201)
    assert lc.call("POST", "login", {"username": "dino", "password": PW})[0] == 200
    for name in ("Crew A", "Crew B"):
        lc.call("POST", "companies", {"name": name})
    users = {}
    for u, co, nm in (("alice", "crew-a", "Alice Field"), ("bob", "crew-b", "Bob Other")):
        s, b = lc.call("POST", "users", {"username": u, "name": nm, "companyId": co, "email": u + "@crew.example"})
        assert s == 201, (s, b)
        token = urllib.parse.parse_qs(urllib.parse.urlparse(b["invite"]["link"]).query)["invite"][0] if b.get("invite", {}).get("link") else None
        c = Client()
        if token is None:
            # invite went by email (dev outbox): read the newest message to this address
            ob = QA + "/store/outbox"
            msgs = sorted((os.path.join(ob, f) for f in os.listdir(ob) if f.endswith(".json")), key=os.path.getmtime)
            for f in reversed(msgs):
                m = json.load(open(f))
                if u + "@crew.example" in json.dumps(m.get("to")):
                    import re
                    token = re.search(r"invite=([A-Za-z0-9_-]+)", m["html"]).group(1)
                    break
        s, b = c.call("POST", "invite", {"token": token, "password": PW})
        assert s in (200, 201), (s, b)
        users[u] = c
    site = json.load(open(APP + "/tools/sites/out/KR-00345-NV.site.json"))
    assert lc.call("PUT", "sites/KR-00345-NV", site)[0] in (200, 201)
    assert lc.call("POST", "jobs", {"projectId": "KR-00345-NV", "installers": ["alice"]})[0] == 201
    assert lc.call("POST", "jobs", {"projectId": "TEST-SITE-01", "installers": ["bob"]})[0] == 201
    return lc, users


import urllib.parse  # noqa: E402

if __name__ == "__main__":
    lc, users = setup()
    print("bench ready on", BASE, "users:", list(users))
