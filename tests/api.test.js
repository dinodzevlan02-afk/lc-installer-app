/* LC Installer App - API checks. Same approach as lc-customer-portal's smoke test.

     node tests/api.test.js        (or: npm test, which runs every test)

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

  console.log("jobs: read-only portal site, material check, claims, pins, submit");
  const JPEG = "data:image/jpeg;base64," + Buffer.concat([Buffer.from([0xff, 0xd8, 0xff, 0xe0]), Buffer.alloc(200, 7)]).toString("base64");
  check((await inst("GET", "jobs")).status === 401, "a switched-off-then-on installer must sign in again");
  await inst("POST", "login", { username: "mike.crew", password: PW });
  check((await inst("POST", "jobs", { projectId: "TEST-SITE-01", installers: ["mike.crew"] })).status === 403, "an installer cannot open a job");
  check((await lc("POST", "jobs", { projectId: "NO-SUCH-SITE", installers: [] })).status === 404, "a job needs a site in the customer portal");
  check((await lc("POST", "jobs", { projectId: "TEST-SITE-01", installers: ["nobody.here"] })).status === 400, "unknown installer refused");
  const jc = await lc("POST", "jobs", { projectId: "TEST-SITE-01", installers: [] });
  check(jc.status === 201 && jc.body.job.name === "Synthetic test site", "LC admin opens a job on a portal project");
  check(JSON.parse(fs.readFileSync(path.join(store, "jobs", "TEST-SITE-01.json"), "utf8")).v === 1, "the stored job carries its schema version");
  check((await lc("POST", "jobs", { projectId: "TEST-SITE-01" })).status === 409, "one job per project");
  check((await inst("GET", "jobs/TEST-SITE-01")).status === 404, "an installer not on the job cannot see it");
  check((await inst("GET", "jobs")).body.jobs.length === 0, "an installer's list leaves out jobs that are not theirs");
  check((await lc("PATCH", "jobs/TEST-SITE-01", { installers: ["mike.crew"] })).status === 200, "LC admin assigns the installer");

  console.log("all customer-portal projects: LED Connection only");
  check((await inst("GET", "projects")).status === 403, "an installer cannot list the portal's projects");
  check((await anon("GET", "projects")).status === 401, "the project list needs a session");
  const pl = await lc("GET", "projects");
  const p1 = pl.body.projects.find(p => p.id === "TEST-SITE-01"), p2 = pl.body.projects.find(p => p.id === "TEST-SITE-02");
  check(pl.status === 200 && p1 && p2, "LC admin sees every portal project, with or without a job");
  check(p1.job && p1.job.installers[0] === "mike.crew" && p2.job === null, "each project says whether it has a job and who is on it");
  check(p1.customer === "Test Customer" && p1.hasSite === true && p2.hasSite === false, "customer name shown; whether a project has a site comes from its site file");
  check(!/9999|8888|INTERNAL CUSTOMER NOTE|netsuite|uploadedBy/.test(JSON.stringify(pl.body)), "no NetSuite number or internal notes in the list");
  check((await lc("POST", "jobs", { projectId: "TEST-SITE-02", installers: [] })).status === 404, "no job on a project whose site was never uploaded");
  const jv = await inst("GET", "jobs/TEST-SITE-01");
  check(jv.status === 200, "the assigned installer opens the job");
  const text = JSON.stringify(jv.body);
  check(!/costPrice|sellPrice|margin|SECRET VENDOR|VN-SECRET|vn_sku|skbSnapshot|designNote|INTERNAL AUDIT NOTE|9999/.test(text), "no pricing, supplier, notes or NetSuite number reaches the installer");
  check(!("installers" in jv.body.job), "the installer is not shown who else is on the job");
  const bom = jv.body.site.bom;
  check(bom.length === 2 && bom[0].qty === 6 && bom[0].designName === "Optimus XL1 230W \u00b7 TY5SW" && bom[0].name === "Optimus 300W \u00b7 T5S" && bom[1].qty === 2, "material list: one line per product, one count per head, excluded head left out");
  check(jv.body.site.pins.length === 9 && jv.body.site.pins.filter(p => p.off).length === 1, "every head is a pin, the excluded one marked off");
  const moved = jv.body.site.pins.find(p => p.fid === "T-007");
  check(moved && Math.abs(moved.lng - (-115.0300 + 0.0008)) < 1e-9, "a position corrected in the portal wins over the audit's");
  check(JSON.stringify(jv.body.site.tags) === JSON.stringify([{ tag: "S07", count: 4 }, { tag: "S08", count: 2 }, { tag: "W1", count: 2 }]), "design tags (not the audit's) with their head counts");
  check(jv.body.contact.phone === "702.847.7680", "the company phone is on the job");

  console.log("UL-listed part numbers: LED Connection sets them, everyone sees them");
  const optLabel = "LC-SLOT-XL-XL1-HV-50-70-TY5SW";
  check(jv.body.parts === undefined, "an installer gets no part-number table");
  check(jv.body.site.bom.find(b => b.sku === optLabel).partNo.pn === "LC-SLOT-300W-HV-L5-XX-50-70-T5S-SS-BK" &&
        jv.body.site.pins.filter(p => p.partNo === "LC-SLOT-300W-HV-L5-XX-50-70-T5S-SS-BK").length === 6,
        "the decided part number applies with nothing saved: material line and every pin");
  check(jv.body.site.bom.find(b => b.sku === "LC-WP-40W-50K").partNo === null, "a design label with no decided number has none");
  const lj = await lc("GET", "jobs/TEST-SITE-01");
  const row = lj.body.parts.find(r => r.label === optLabel);
  check(row && row.saved === null && row.decided === "LC-SLOT-300W-HV-L5-XX-50-70-T5S-SS-BK", "LC admin sees it marked as decided, not saved");
  check((await inst("PUT", "jobs/TEST-SITE-01/parts", { byLabel: { [optLabel]: "LC-SLOT-300W-HV-L5-XX-50-70-T5S-SS-BK" } })).status === 403, "an installer cannot set part numbers");
  check((await lc("PUT", "jobs/TEST-SITE-01/parts", { byLabel: { [optLabel]: "LC-SLOT-300W-HV-L5-XX-50-70-T5SW-SS-BK" } })).status === 400, "a part number outside the order logic is refused");
  check((await lc("PUT", "jobs/TEST-SITE-01/parts", { byLabel: { "LC-NOT-ON-SITE": "LC-WP-40W-H-40K" } })).status === 400, "a design label that is not on the site is refused");
  check((await lc("PUT", "jobs/TEST-SITE-01/parts", { byLabel: { [optLabel]: "lc-slot-300w-hv-l5-xx-50-70-t5s-ss-bk", "LC-WP-40W-50K": "LC-WP-40W-H-50K" } })).status === 200, "LC admin saves part numbers");
  const ij = await inst("GET", "jobs/TEST-SITE-01");
  const ob = ij.body.site.bom.find(b => b.sku === optLabel);
  check(ob.partNo && ob.partNo.pn === "LC-SLOT-300W-HV-L5-XX-50-70-T5S-SS-BK" && ob.partNo.parts.bracket === "Straight square arm", "the installer sees the part number on the material line, explained");
  check(ij.body.site.pins.filter(p => p.partNo === "LC-SLOT-300W-HV-L5-XX-50-70-T5S-SS-BK").length === 6, "and on every pin of that product");
  check(ob.name === "Optimus 300W \u00b7 T5S" && ob.designName && ij.body.site.pins.find(p => p.partNo).productName === "Optimus 300W \u00b7 T5S", "the product name follows the saved part number, not the design label");
  check(ob.partNo.guide && ob.partNo.guide.bracket === "SS" && ob.partNo.guide.url === "/guides/optimus/LC-Optimus-Installation-Guide-SS.pdf",
    "the installation guide follows the bracket in the part number (SS)");
  check(ij.body.site.bom.find(b => b.sku === "LC-WP-40W-50K").partNo.guide === null, "a product with no guide family gets none");
  const wp = ij.body.site.bom.find(b => b.sku === "LC-WP-40W-50K");
  check(wp.partNo.checked === true && wp.name === "Prime Wallpack 40W" && wp.partNo.parts.means === "40W \u00b7 Standard output \u00b7 5000K \u00b7 No accessory",
    "a Prime Wallpack part number is checked against its order logic and explained");
  check((await lc("PUT", "jobs/TEST-SITE-01/parts", { byLabel: { "LC-WP-40W-50K": "LC-WP-45W-H-50K" } })).status === 400, "a wall pack wattage outside the order logic is refused");
  check(!/AOK|SECRET VENDOR/.test(JSON.stringify(ij.body)), "no supplier name or code reaches the installer");
  check((await lc("PUT", "jobs/TEST-SITE-01/parts", { byLabel: { "LC-WP-40W-50K": "" } })).status === 200 &&
        (await inst("GET", "jobs/TEST-SITE-01")).body.site.bom.find(b => b.sku === "LC-WP-40W-50K").partNo === null, "an empty value removes a part number");
  check(bom[0].catalog && /fixtures\/7\/spec-sheet\/Optimus-Spec\.pdf$/.test(bom[0].specSheetUrl) && bom[0].catalog.docs[0].label === "Installation instructions", "spec sheet and manuals come from the catalog by product id");
  check(bom[1].specSheetUrl === "https://example.com/wp.pdf", "the design's own spec sheet link wins");
  const pinA = jv.body.site.pins.find(p => p.tag === "S07"), pinOff = jv.body.site.pins.find(p => p.off);

  const ph = await inst("PUT", "jobs/TEST-SITE-01/photos", { dataUrl: JPEG });
  check(ph.status === 201 && /^[a-f0-9]{16}\.jpg$/.test(ph.body.name), "installer uploads a photo");
  check((await inst("PUT", "jobs/TEST-SITE-01/photos", { dataUrl: "data:image/jpeg;base64,AAAA" })).status === 400, "a non-JPEG is refused");
  check((await inst("PUT", "jobs/TEST-SITE-01/pins/" + pinA.id, { photos: [ph.body.name] })).status === 409, "no pin saved before the material is signed off");

  const k1 = bom[0].key, k2 = bom[1].key;
  check((await inst("PUT", "jobs/TEST-SITE-01/material", { lines: { "made-up": { received: 1 } } })).status === 400, "an unknown product line is refused");
  check((await inst("PUT", "jobs/TEST-SITE-01/material", { lines: { [k1]: { received: 2, damaged: 3 } } })).status === 400, "damaged cannot exceed received");
  check((await inst("PUT", "jobs/TEST-SITE-01/material", { lines: { [k1]: { received: 5, damaged: 1 } } })).status === 200, "counts saved as they go");
  check((await inst("POST", "jobs/TEST-SITE-01/approve", { confirm: true })).status === 400, "cannot sign off with a line not counted");
  check((await inst("POST", "jobs/TEST-SITE-01/approve", { lines: { [k2]: { received: 2 } } })).status === 400, "sign-off needs the confirm box");
  const ap = await inst("POST", "jobs/TEST-SITE-01/approve", { lines: { [k2]: { received: 2 } }, confirm: true });
  check(ap.status === 200 && ap.body.material.approved.short === 1 && ap.body.material.approved.damaged === 1, "installer signs off; one short and one damaged recorded against the site's own quantities");
  check((await inst("PUT", "jobs/TEST-SITE-01/material", { lines: { [k1]: { received: 6 } } })).status === 409, "signed-off counts are locked");

  check((await inst("POST", "jobs/TEST-SITE-01/claims", { kind: "damaged", lines: [{ key: k1, received: 5, damaged: 1 }] })).status === 400, "a damage claim needs a photo");
  const cl = await inst("POST", "jobs/TEST-SITE-01/claims", { kind: "damaged", lines: [{ key: k1, received: 5, damaged: 1 }], note: "Lens cracked", photos: [ph.body.name] });
  check(cl.status === 201 && /^MC-\d{6}-[0-9A-F]{4}$/.test(cl.body.claim.ref) && cl.body.claim.lines[0].expected === 6, "claim filed with a reference and the expected quantity from the site");
  check((await inst("POST", "jobs/TEST-SITE-01/claims", { kind: "shortage", photos: ["0000000000000000.jpg"], note: "x" })).status === 400, "a photo that was never uploaded is refused");

  check((await inst("PUT", "jobs/TEST-SITE-01/pins/" + pinA.id, { photos: [] })).status === 400, "a pin is not saved as installed without a photo");
  check((await inst("PUT", "jobs/TEST-SITE-01/pins/" + pinOff.id, { photos: [ph.body.name] })).status === 404, "an excluded head cannot be installed");
  check((await inst("PUT", "jobs/TEST-SITE-01/pins/" + pinA.id, { photos: [ph.body.name], note: "ok", serial: "SN1" })).status === 200, "installer saves a pin with its photo");
  check((await inst("POST", "jobs/TEST-SITE-01/submit")).status === 400, "cannot submit with heads left");
  for (const p of jv.body.site.pins) if (!p.off && p.id !== pinA.id) await inst("PUT", "jobs/TEST-SITE-01/pins/" + p.id, { photos: [ph.body.name] });
  const js = await inst("GET", "jobs/TEST-SITE-01");
  check(Object.values(js.body.pins).filter(p => p.installed).length === 8 && js.body.claims.length === 1, "the job shows every saved pin and the claim");
  check((await inst("GET", "jobs/TEST-SITE-01/photos/" + ph.body.name)).status === 200, "the installer can see the job's photos");
  check((await anon("GET", "jobs/TEST-SITE-01/photos/" + ph.body.name)).status === 401, "photos need a session");
  const sb = await inst("POST", "jobs/TEST-SITE-01/submit");
  check(sb.status === 200 && sb.body.job.submitted.heads === 8, "job submitted with every head installed");
  check((await inst("PUT", "jobs/TEST-SITE-01/pins/" + pinA.id, { photos: [ph.body.name] })).status === 409, "a submitted job is locked");
  const lst = await lc("GET", "jobs");
  check(lst.body.jobs[0].heads === 8 && lst.body.jobs[0].pinsSaved === 8 && lst.body.jobs[0].materialApproved, "LC admin's list shows progress");
  check((await lc("PATCH", "jobs/TEST-SITE-01", { reopenMaterial: true })).status === 200, "LC admin can reopen the material check");

  console.log("changing the installer on a job: LED Connection only");
  check((await lc("POST", "users", { username: "anna.crew", name: "Anna Crew", password: PW })).status === 201, "a second installer login");
  const anna = browser();
  await anna("POST", "login", { username: "anna.crew", password: PW });
  await anna("POST", "password", { current: PW, next: PW + "-a" });
  check((await anna("GET", "jobs/TEST-SITE-01")).status === 404, "before: the second installer cannot see the job");
  check((await inst("PATCH", "jobs/TEST-SITE-01", { installers: ["mike.crew", "anna.crew"] })).status === 403, "an installer cannot change who is on a job");
  check((await anna("PATCH", "jobs/TEST-SITE-01", { installers: ["anna.crew"] })).status === 403, "an installer not on the job cannot add themselves (refused before the job is even read)");
  check((await lc("PATCH", "jobs/TEST-SITE-01", { installers: ["dino"] })).status === 400, "an LC admin login cannot be named as the installer");
  const sw = await lc("PATCH", "jobs/TEST-SITE-01", { installers: ["anna.crew"] });
  check(sw.status === 200 && JSON.stringify(sw.body.job.installers) === '["anna.crew"]', "LC admin replaces the installer");
  check((await inst("GET", "jobs/TEST-SITE-01")).status === 404, "the replaced installer loses the job at once");
  check((await inst("GET", "jobs")).body.jobs.length === 0, "and it leaves their list");
  const aj = await anna("GET", "jobs/TEST-SITE-01");
  check(aj.status === 200 && Object.values(aj.body.pins).some(p => p.by === "mike.crew"), "the new installer sees the job, with the earlier installer's saved work");
  const auditTxt = (function walk(d, out) { for (const e of fs.readdirSync(d, { withFileTypes: true })) { const f = path.join(d, e.name); e.isDirectory() ? walk(f, out) : out.push(fs.readFileSync(f, "utf8")); } return out; })(path.join(store, "audit"), []).join("\n");
  check(/"removed": \[\s*"mike.crew"\s*\]/.test(auditTxt) && /"added": \[\s*"anna.crew"\s*\]/.test(auditTxt), "the audit records who was removed and who was added");
  check((await lc("PATCH", "users/anna.crew", { disabled: true })).status === 200 && (await lc("PATCH", "jobs/TEST-SITE-01", { installers: ["anna.crew"] })).status === 200, "a switched-off installer already on the job can stay listed");
  check((await lc("PATCH", "jobs/TEST-SITE-01", { installers: ["anna.crew", "temp.crew"] })).status === 200, "another installer can be added alongside");

  console.log("sites uploaded into the installer app (not the customer portal)");
  const own = { format: "lc-site", version: 1,
    project: { id: "TEST-OWN-01", name: "Synthetic own site", address: "Not a real site", customer: "Test", kind: "exterior" },
    site: { datasets: [{ id: "own-a", label: "Exterior", data: [
      { id: "A-1", schedule: "AL1", "pole id": "P1", "fixture type": "AreaLight", wattage: "400", latitude: "36.1", longitude: "-115.1", images: "https://example.com/p.jpg?sig=SECRET" },
      { id: "A-2", schedule: "AL1", "pole id": "P1", "fixture type": "AreaLight", wattage: "400", latitude: "36.1001", longitude: "-115.1" },
      { id: "C-1", schedule: "CP1", "fixture type": "Canopy", wattage: "150", latitude: "36.1002", longitude: "-115.1", deactivated: "Not in the design" }],
      solutions: { 0: { fam: "Optimus", lc_sku: "LC-SLOT-L-L1-480-40-70-TY5SW", watt: 180.75, tag: "S03", arrangement: "BACK-BACK", mh: 23, costPrice: 99, vendor: "SECRET VENDOR" },
                   1: { fam: "Optimus", lc_sku: "LC-SLOT-L-L1-480-40-70-TY5SW", watt: 180.75, tag: "S03", arrangement: "BACK-BACK", mh: 23 } },
      excluded: { 2: true } }] } };
  check((await inst("PUT", "sites/TEST-OWN-01", own)).status === 403, "an installer cannot upload a site");
  check((await anon("PUT", "sites/TEST-OWN-01", own)).status === 401, "no upload without a session");
  check((await lc("PUT", "sites/TEST-OWN-01", own, { "X-LCI": "" })).status === 403, "upload needs the CSRF header");
  check((await lc("PUT", "sites/TEST-OWN-01", { format: "something-else" })).status === 400, "a file that is not a site file is refused");
  check((await lc("PUT", "sites/OTHER-ID", own)).status === 400, "a file for another project id is refused");
  check((await lc("PUT", "sites/TEST-OWN-01", Object.assign({}, own, { site: { datasets: [{ id: "x", data: [{ id: "1" }], solutions: { 3: { tag: "S1" } } }] } }))).status === 400, "a solution on a row that does not exist is refused");
  const up = await lc("PUT", "sites/TEST-OWN-01", own);
  check(up.status === 201 && up.body.site.fixtures === 2 && up.body.replaced === false, "LC admin uploads a site: 2 heads to install, the excluded one not counted");
  const stored = fs.readFileSync(path.join(store, "sites", "TEST-OWN-01", "site.json"), "utf8");
  check(!/SECRET|costPrice|sig=/.test(stored), "pricing, supplier and signed photo links are not stored");
  check(!fs.existsSync(path.join(__dirname, "fixtures", "portal", "projects", "TEST-OWN-01.json")), "nothing is written to the customer portal");
  const pl2 = await lc("GET", "projects");
  const op = pl2.body.projects.find(p => p.id === "TEST-OWN-01");
  check(op && op.source === "installer" && op.hasSite && op.heads === 2 && op.customer === "Test" && op.job === null, "the uploaded site is in the project list, marked as an installer app site");
  check((await inst("GET", "sites")).status === 403 && (await lc("GET", "sites")).body.sites.length === 1, "only LED Connection lists uploaded sites");
  check((await lc("POST", "jobs", { projectId: "TEST-OWN-01", installers: ["mike.crew"] })).status === 201, "a job starts on an uploaded site");
  const tc = inst;
  const oj = await tc("GET", "jobs/TEST-OWN-01");
  check(oj.status === 200 && oj.body.site.project.source === "installer" && oj.body.site.pins.length === 3 && oj.body.site.pins.filter(p => p.off).length === 1,
    "the installer opens it: every audit row a pin, the excluded one off");
  check(oj.body.site.bom.length === 1 && oj.body.site.bom[0].qty === 2 && JSON.stringify(oj.body.site.tags) === '[{"tag":"S03","count":2}]', "material list and design tags from the uploaded site");
  check(!/SECRET|costPrice/.test(JSON.stringify(oj.body)), "no pricing or supplier reaches the installer");
  const ob1 = oj.body.site.bom[0];
  check(ob1.partNo && ob1.partNo.pn === "LC-SLOT-230W-HV-L5-XX-40-80-T5S-SS-BR" && /181W/.test(ob1.partNo.setup) && ob1.partNo.guide.bracket === "SS",
    "a decided part number applies on an uploaded site, with its set-up line and bracket guide");
  check(ob1.catalog && ob1.catalog.id === 7 && /fixtures\/7\/spec-sheet\/Optimus-Spec\.pdf$/.test(ob1.specSheetUrl),
    "a product with no catalog id finds its spec sheet by its family name in the catalog");
  const pinIds = oj.body.site.pins.map(p => p.id).join();
  const re = await lc("PUT", "sites/TEST-OWN-01", own);
  check(re.status === 200 && re.body.replaced === true, "the site can be replaced");
  check((await tc("GET", "jobs/TEST-OWN-01")).body.site.pins.map(p => p.id).join() === pinIds, "a replaced site keeps the same pin ids, so saved work stays on its heads");

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

const srv = spawn(process.execPath, [path.join(__dirname, "..", "dev", "server.js")], {
  env: Object.assign({}, process.env, { PORT: String(PORT), INSTALLER_LOCAL_STORE: store, INSTALLER_PORTAL_LOCAL_STORE: path.join(__dirname, "fixtures", "portal"), INSTALLER_CATALOG_FILE: path.join(__dirname, "fixtures", "catalog-data.json") }), stdio: ["ignore", "pipe", "inherit"]
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
