/* LC Installer App - API smoke test. Same approach as lc-customer-portal's.

     node dev/smoke.js

   Starts dev/server.js on a spare port with a THROWAWAY store folder, walks
   the whole sign-in and login model through the real HTTP API, and exits
   non-zero if any rule does not hold. Run it after any change to api/. */
const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");
const os = require("os");

const PORT = 4398;
const BASE = "http://127.0.0.1:" + PORT + "/api/";
const store = fs.mkdtempSync(path.join(os.tmpdir(), "lci-smoke-"));
const PW = "correct-horse-battery";

let failed = 0, passed = 0;
function check(cond, what) {
  if (cond) { passed++; console.log("  ok   " + what); }
  else { failed++; console.log("  FAIL " + what); }
}

/* A tiny cookie jar per "browser". */
function browser() {
  let cookie = "";
  return async function call(method, url, body, headers) {
    const h = Object.assign({ "Content-Type": "application/json" }, method === "GET" ? {} : { "X-LCI": "1" }, headers || {});
    if (cookie) h.Cookie = cookie;
    const r = await fetch(BASE + url, { method, headers: h, body: body === undefined ? undefined : JSON.stringify(body) });
    const sc = r.headers.get("set-cookie");
    if (sc) { const v = sc.split(";")[0]; cookie = /=$/.test(v) ? "" : v; }
    const t = await r.text();
    let j = null; try { j = t ? JSON.parse(t) : null; } catch (e) { j = t; }
    return { status: r.status, body: j, setCookie: sc, cookie: () => cookie };
  };
}

async function main() {
  const lc = browser(), inst = browser(), inst2 = browser(), anon = browser();

  console.log("setup");
  check((await anon("GET", "setup")).body.needed === true, "setup is needed on an empty store");
  check((await anon("POST", "setup", { key: "wrong-key-123", username: "dino", password: PW })).status === 403, "wrong setup key refused");
  check((await anon("POST", "setup", { key: "local-dev-setup-key", username: "dino", password: PW }, { "X-LCI": "" })).status === 403, "missing X-LCI header refused (CSRF guard)");
  check((await anon("POST", "setup", { key: "local-dev-setup-key", username: "dino", password: PW }, { "X-LCI": "", "X-LCP": "1" })).status === 403, "the customer portal's X-LCP header is not accepted");
  check((await anon("POST", "setup", { key: "local-dev-setup-key", username: "dino", password: "short" })).status === 400, "short password refused");
  const s = await lc("POST", "setup", { key: "local-dev-setup-key", username: "Dino", name: "Dino Dzevlan", password: PW });
  check(s.status === 200 && s.body.user.role === "lc-admin" && s.body.user.username === "dino", "first admin created, username lower-cased");
  check(/^lci_s=/.test(s.setCookie || ""), "session cookie is lci_s, not the portal's lcp_s");
  check(/HttpOnly/.test(s.setCookie) && /SameSite=Strict/.test(s.setCookie) && /Secure/.test(s.setCookie), "session cookie is HttpOnly, Secure, SameSite=Strict");
  check(!JSON.stringify(s.body).includes("hash"), "no password hash in the response");
  check((await anon("POST", "setup", { key: "local-dev-setup-key", username: "evil", password: PW })).status === 409, "setup refuses a second time");
  check((await anon("GET", "setup")).body.needed === false, "setup no longer needed");

  console.log("logins (LC admin)");
  const add = await lc("POST", "users", { username: "mike.crew", name: "Mike Crew", phone: "+1 555 010 2030", company: "Crew A" });
  check(add.status === 201 && add.body.user.role === "installer", "LC admin adds an installer (role defaults to installer)");
  check(add.body.invite && /index\.html\?invite=/.test(add.body.invite.link), "a one-time set-password link comes back once");
  check(!JSON.stringify(add.body.user).includes("hash"), "the new login carries no invite or password hash");
  check((await lc("POST", "users", { username: "mike.crew" })).status === 409, "duplicate username refused");
  check((await lc("POST", "users", { username: "bad", role: "customer-user" })).status === 403, "unknown role refused");
  check((await lc("POST", "users", { username: "x y" })).status === 400, "bad username refused");
  check((await lc("POST", "users", { username: "bad.mail", email: "not-an-email" })).status === 400, "bad email refused");
  check((await lc("POST", "users", { username: "temp.crew", password: PW })).status === 201, "LC admin adds a login with a temporary password");

  console.log("invite link");
  const token = new URL(add.body.invite.link).searchParams.get("invite");
  check((await anon("GET", "invite?token=" + "x".repeat(40))).status === 404, "a made-up token is refused");
  const iv = await anon("GET", "invite?token=" + encodeURIComponent(token));
  check(iv.status === 200 && iv.body.username === "mike.crew" && iv.body.kind === "invite", "the link names its login");
  check((await anon("POST", "invite", { token, password: "short" })).status === 400, "short password refused on the link");
  const acc = await inst("POST", "invite", { token, password: PW });
  check(acc.status === 200 && acc.body.user.username === "mike.crew", "installer sets a password and is signed in");
  check((await anon("POST", "invite", { token, password: PW + "x" })).status === 404, "the link works only once");

  console.log("sign-in");
  check((await anon("POST", "login", { username: "mike.crew", password: "not-the-password" })).status === 401, "wrong password refused");
  check((await anon("POST", "login", { username: "nobody-here", password: PW })).body.error === (await anon("POST", "login", { username: "mike.crew", password: "nope-nope-nope" })).body.error, "unknown user and wrong password give the same message");
  const tl = await inst2("POST", "login", { username: "TEMP.CREW", password: PW });
  check(tl.status === 200 && tl.body.user.mustChangePassword === true, "temporary password signs in and must be changed");
  check((await inst2("POST", "password", { current: PW, next: PW + "-2" })).status === 200, "temporary password changed");
  check((await inst2("GET", "me")).body.user.mustChangePassword === false, "flag cleared, session kept");

  console.log("installer: no admin powers");
  check((await inst("GET", "me")).body.can.manageUsers === false, "/me says installers do not manage logins");
  check((await inst("GET", "users")).status === 403, "installer cannot list logins");
  check((await inst("GET", "users/dino")).status === 404, "installer cannot read another login");
  check((await inst("GET", "users/mike.crew")).status === 200, "installer can read their own login");
  check((await inst("POST", "users", { username: "sneaky", role: "lc-admin" })).status === 403, "installer cannot create logins");
  check((await inst("PATCH", "users/mike.crew", { role: "lc-admin" })).status === 403, "installer cannot promote themselves");
  check((await inst("PATCH", "users/temp.crew", { disabled: true })).status === 403, "installer cannot switch others off");

  console.log("session rules");
  check((await anon("GET", "me")).status === 401, "no cookie, no session");
  check((await anon("GET", "me", undefined, { Cookie: "lci_s=" + "a.b.c" })).status === 401, "forged token refused");
  check((await lc("PATCH", "users/dino", { disabled: true })).status === 400, "admin cannot switch themselves off");
  check((await lc("PATCH", "users/dino", { role: "installer" })).status === 400, "admin cannot change their own role");
  const off = await lc("PATCH", "users/mike.crew", { disabled: true });
  check(off.status === 200 && off.body.user.disabled === true, "LC admin switches the installer off");
  check((await inst("GET", "me")).status === 401, "switching off ends the installer's session at once");
  check((await anon("POST", "login", { username: "mike.crew", password: PW })).status === 403, "a switched-off login cannot sign in");
  check((await lc("PATCH", "users/mike.crew", { sendInvite: true })).status === 400, "no link for a switched-off login");
  await lc("PATCH", "users/mike.crew", { disabled: false });
  const rs = await lc("PATCH", "users/mike.crew", { sendInvite: true });
  check(rs.status === 200 && rs.body.invite.kind === "reset", "a login with a password gets a reset link");

  console.log("password change ends other sessions");
  const a = browser(), b = browser();
  await a("POST", "login", { username: "temp.crew", password: PW + "-2" });
  await b("POST", "login", { username: "temp.crew", password: PW + "-2" });
  check((await a("POST", "password", { current: PW + "-2", next: PW + "-3" })).status === 200, "password changed on device A");
  check((await a("GET", "me")).status === 200, "device A stays signed in");
  check((await b("GET", "me")).status === 401, "device B is signed out");

  console.log("lockout");
  for (let i = 0; i < 5; i++) await anon("POST", "login", { username: "temp.crew", password: "wrong-wrong-" + i });
  check((await anon("POST", "login", { username: "temp.crew", password: PW + "-3" })).status === 429, "five wrong passwords lock the login, even with the right one");

  console.log("last admin");
  const add2 = await lc("POST", "users", { username: "office2", role: "lc-admin", password: PW });
  check(add2.status === 201, "second LC admin created");
  const o2 = browser();
  await o2("POST", "login", { username: "office2", password: PW });
  await o2("POST", "password", { current: PW, next: PW + "-o" });
  check((await o2("PATCH", "users/dino", { disabled: true })).status === 200, "one admin can switch another off");
  check((await o2("PATCH", "users/office2", { disabled: true })).status === 400, "the last active admin cannot be switched off");

  console.log("audit and storage");
  const auditFiles = [];
  (function walk(d) { for (const e of fs.readdirSync(d, { withFileTypes: true })) { const f = path.join(d, e.name); e.isDirectory() ? walk(f) : auditFiles.push(f); } })(path.join(store, "audit"));
  check(auditFiles.length >= 10, "actions are written to the audit log (" + auditFiles.length + ")");
  const raw = fs.readFileSync(path.join(store, "users", "mike.crew.json"), "utf8");
  check(!raw.includes(token), "the invite token itself is never stored");

  console.log("logout");
  const lo = await o2("POST", "logout");
  check(/Max-Age=0/.test(lo.setCookie || ""), "logout clears the cookie");
  check((await o2("GET", "me")).status === 401, "signed out");
}

const srv = spawn(process.execPath, [path.join(__dirname, "server.js")], {
  env: Object.assign({}, process.env, { PORT: String(PORT), INSTALLER_LOCAL_STORE: store }), stdio: ["ignore", "pipe", "inherit"]
});
let started = false;
srv.stdout.on("data", d => {
  if (started || !/dev server/.test(String(d))) return;
  started = true;
  main().catch(e => { failed++; console.error(e); }).finally(() => {
    srv.kill();
    fs.rmSync(store, { recursive: true, force: true });
    console.log("\n" + passed + " passed, " + failed + " failed");
    process.exit(failed ? 1 : 0);
  });
});
setTimeout(() => { if (!started) { console.error("dev server did not start"); srv.kill(); process.exit(1); } }, 10000);
