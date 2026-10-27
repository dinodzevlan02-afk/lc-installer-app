"""Charter 1: authorization, abuse and data validation through the HTTP API (OWASP WSTG 4.5 / 4.10)."""
import os
import base64, json, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bench import setup, Client, QA

lc, U = setup()
alice, bob, anon = U["alice"], U["bob"], Client()
K, T = "jobs/KR-00345-NV", "jobs/TEST-SITE-01"
res = []
def check(ok, what, detail=""):
    res.append((bool(ok), what, detail)); print(("PASS " if ok else "FAIL ") + what + ("  -- " + str(detail) if detail and not ok else ""))

# ---- setup data on alice's job
s, job = alice.call("GET", K); bom = job["site"]["bom"]; k0 = bom[0]["key"]
jpeg = base64.b64encode(bytes([0xff, 0xd8, 0xff, 0xe0]) + b"\0" * 200).decode()
s, ph = alice.call("PUT", K + "/photos", {"dataUrl": "data:image/jpeg;base64," + jpeg}); check(s == 201, "alice uploads a photo")
webm = bytes([0x1a, 0x45, 0xdf, 0xa3]) + b"A" * 4000
s, md = alice.call("PUT", K + "/media", {"data": base64.b64encode(webm).decode(), "kind": "webm"}); check(s == 201, "alice uploads a recording")
s, ms = alice.call("POST", K + "/messages", {"kind": "voice", "media": md["name"], "note": "evidence", "seconds": 4}); check(s == 201, "alice sends a message")

# ---- horizontal access: bob (other crew) on alice's job
for m, p, b in [("GET", K, None), ("PUT", K + "/material", {"lines": {k0: {"received": 1}}}),
                ("POST", K + "/claims", {"kind": "other", "note": "x"}), ("POST", K + "/messages", {"kind": "voice", "media": md["name"]}),
                ("PUT", K + "/media", {"data": base64.b64encode(webm).decode(), "kind": "webm"}),
                ("GET", K + "/media/" + md["name"], None), ("GET", K + "/photos/" + ph["name"], None),
                ("POST", K + "/approve", {"lines": {}, "confirm": True}), ("POST", K + "/flags", {"kind": "pole", "pinId": "x", "note": "x"}),
                ("POST", K + "/submit", {})]:
    s, b2 = bob.call(m, p, b)
    check(s == 404, "other crew cannot %s %s (404)" % (m, p.replace(K, "<alice job>")), s)

# ---- vertical: installer on LC-only actions
for m, p, b in [("PUT", K + "/parts", {"byLabel": {}}), ("POST", K + "/accept", {}), ("POST", K + "/sendback", {"reason": "x"}),
                ("PATCH", K, {"installers": ["alice", "bob"]}), ("PATCH", K, {"reopenMaterial": True}),
                ("POST", "deleted", {"projectId": "KR-00345-NV", "confirm": "KR-00345-NV", "mode": "reset"}),
                ("PUT", "sites/KR-00345-NV", {}), ("GET", "users", None), ("GET", "companies", None), ("GET", "projects", None),
                ("POST", "relay/pair", {}), ("POST", "relay/test", {}), ("GET", "deleted", None)]:
    s, b2 = alice.call(m, p, b)
    check(s in (401, 403, 404, 405), "installer refused on %s %s" % (m, p), (s, b2))

# ---- no session
for m, p in [("GET", K), ("GET", K + "/media/" + md["name"]), ("GET", K + "/photos/" + ph["name"]), ("POST", K + "/messages"), ("PUT", K + "/media")]:
    s, _ = anon.call(m, p, {} if m != "GET" else None)
    check(s == 401, "no session: %s %s -> 401" % (m, p.replace(K, "<job>")), s)

# ---- CSRF header on the new endpoints
for m, p, b in [("PUT", K + "/media", {"data": base64.b64encode(webm).decode(), "kind": "webm"}),
                ("POST", K + "/messages", {"kind": "voice", "media": md["name"]}), ("POST", K + "/claims", {"kind": "other", "note": "x"})]:
    s, _ = alice.call(m, p, b, csrf=False)
    check(s == 403, "no X-LCI header refused: %s %s" % (m, p.replace(K, "<job>")), s)

# ---- data validation
for val, why in [(-1, "negative"), (1.5, "decimal"), (100001, "huge"), ("abc", "text")]:
    s, _ = alice.call("PUT", K + "/material", {"lines": {k0: {"received": val}}})
    check(s == 400, "received %s refused" % why, s)
s, _ = alice.call("PUT", K + "/material", {"lines": {k0: {"received": 2, "damaged": 3}}}); check(s == 400, "damaged > received refused", s)
s, _ = alice.call("PUT", K + "/material", {"lines": {"no-such-line": {"received": 2}}}); check(s == 400, "unknown product line refused", s)
s, _ = alice.call("POST", K + "/claims", {"kind": "other", "note": "x" * 2001}); check(s == 400, "claim note over 2000 chars refused", s)
s, b2 = alice.call("POST", K + "/messages", {"kind": "voice", "media": md["name"], "seconds": -5})
check(s == 201 and b2["message"]["seconds"] is None, "negative seconds stored as unknown", (s, b2.get("message", {}).get("seconds") if isinstance(b2, dict) else b2))
s, _ = alice.call("POST", K + "/messages", {"kind": "voice", "media": "../../system/setup.json"}); check(s == 400, "message media path traversal refused", s)
s, _, _ = alice.call("GET", K + "/media/..%2f..%2fsystem%2fsetup.json", raw=True); check(s == 404, "media GET path traversal refused", s)
s, _, _ = alice.call("GET", K + "/photos/..%2fpins", raw=True); check(s == 404, "photo GET path traversal refused", s)

# ---- upload abuse
s, _ = alice.call("PUT", K + "/media", {"data": base64.b64encode(b"<html><script>alert(1)</script>" * 10).decode(), "kind": "webm"}); check(s == 400, "HTML disguised as webm refused", s)
s, _ = alice.call("PUT", K + "/media", {"data": base64.b64encode(b"x" * (3 * 1024 * 1024 + 10)).decode(), "kind": "webm"}); check(s == 413, "part over 3 MB refused", s)
s, b2 = alice.call("PUT", K + "/media", {"data": base64.b64encode(b"B" * 100).decode(), "kind": "webm", "part": 1, "parts": 2, "upload": "abcdef0123456789"})
s2, b3 = alice.call("PUT", K + "/media", {"data": base64.b64encode(b"B" * 100).decode(), "kind": "webm", "part": 1, "parts": 2, "upload": "abcdef0123456789"})
check(s2 in (202, 400, 409), "last part sent with part 0 missing does not commit a broken file", (s, s2, b3))
# overwrite: reuse an existing recording's name as the upload id
victim = md["name"].split(".")[0]
evil = bytes([0x1a, 0x45, 0xdf, 0xa3]) + b"EVIL" * 50
s, b2 = alice.call("PUT", K + "/media", {"data": base64.b64encode(evil).decode(), "kind": "webm", "part": 0, "parts": 1, "upload": victim})
st, buf, _ = alice.call("GET", K + "/media/" + md["name"], raw=True)
check(buf == webm, "an upload id equal to an existing recording cannot overwrite that recording", "status %s, now %d bytes, EVIL in it: %s" % (s, len(buf), b"EVIL" in buf))

# ---- logout revokes the session
old = alice.ck
s, _ = alice.call("POST", "logout", {})
ghost = Client(); ghost.ck = old
s, _ = ghost.call("GET", K)
check(s == 401, "an old session cookie is useless after logout", s)

json.dump(res, open(QA + "/c1.json", "w"))
print("\n%d checks, %d failed" % (len(res), sum(1 for r in res if not r[0])))
