/* The installer's work on a job. Everyone here must be able to see the job
   (LC admin, or an installer it names); anything else answers 404.

   PUT  /api/jobs/{id}/material          { lines: { [productKey]: { received, damaged, note } } }
                                         Saves the counts so far (until signed off).
   POST /api/jobs/{id}/approve           { lines, confirm: true }
                                         The installer signs off the counted quantities.
                                         Expected quantities come from the site, never the page.
                                         Unlocks the install, shortages or not (a claim covers those).
   POST /api/jobs/{id}/claims            { kind, lines: [{ key, received, damaged }], note, photos: [name] }
                                         A material claim; "damaged" needs a photo.
   PUT  /api/jobs/{id}/pins/{pinId}      { installed, note, serial, photos: [name] }
                                         Marks one head installed. Needs the material signed off
                                         and at least one photo.
   POST /api/jobs/{id}/submit            Hands the job back once every head is installed.
   PUT  /api/jobs/{id}/parts             LC admins: { byLabel: { "<design label>": "<LC part number>" | "" } }
                                         The UL-listed part number for each design label;
                                         an Optimus one must follow the order logic (shared/parts.js).
   PUT  /api/jobs/{id}/photos            { dataUrl: "data:image/jpeg;base64,..." } -> { name, url }
   GET  /api/jobs/{id}/photos/{name}     the JPEG */
const crypto = require("crypto");
const P = require("../shared/app");
const J = require("../shared/jobs");
const PARTS = require("../shared/parts");
const CLAIMMAIL = require("../shared/claimmail");
const { ApiError } = P;

const MAX_PHOTO = 3 * 1024 * 1024, MAX_PHOTOS = 6, MAX_QTY = 100000;
const RE_PHOTO = /^[a-f0-9]{16}\.jpg$/;
const RE_PIN = /^[a-f0-9]{20}$/;
const CLAIM_KINDS = { shortage: "Short shipped", damaged: "Damaged", wrong: "Wrong product", other: "Other" };

function count(v, field) {
  if (v === "" || v == null) return null;
  const n = Number(v);
  if (!Number.isInteger(n) || n < 0 || n > MAX_QTY) throw new ApiError(400, field + " must be a whole number.");
  return n;
}

/* Only lines the site really has; quantities whole numbers. */
function cleanLines(lines, site) {
  if (lines == null) return {};
  if (typeof lines !== "object" || Array.isArray(lines)) throw new ApiError(400, "lines must be an object.");
  const keys = new Set(site.bom.map(b => b.key)), out = {};
  for (const [k, v] of Object.entries(lines)) {
    if (!keys.has(k)) throw new ApiError(400, "Unknown product line \"" + k + "\".");
    const received = count(v && v.received, "Received");
    const damaged = count(v && v.damaged, "Damaged") || 0;
    if (received != null && damaged > received) throw new ApiError(400, "Damaged cannot be more than received.");
    out[k] = { received, damaged, note: P.text(v && v.note, 500, "Note") };
  }
  return out;
}

async function cleanPhotos(id, list) {
  if (list == null) return [];
  if (!Array.isArray(list) || list.length > MAX_PHOTOS) throw new ApiError(400, "Up to " + MAX_PHOTOS + " photos.");
  const names = [...new Set(list.map(String))];
  for (const n of names) {
    if (!RE_PHOTO.test(n)) throw new ApiError(400, "Bad photo name.");
    if (!(await P.store().getBytes(J.paths.photo(id, n)))) throw new ApiError(400, "Photo " + n + " was not uploaded.");
  }
  return names;
}

const who = u => ({ by: u.username, byName: u.name || u.username });

/* The part number the job shows for a design label: saved, else decided. */
async function partOfJob(id) {
  const rec = await P.store().get(J.paths.parts(id));
  const saved = (rec && rec.data.byLabel) || {};
  return sku => (saved[sku] && saved[sku].pn) || PARTS.DECIDED[sku] || null;
}

module.exports = P.handler(async ({ req, method, body, params, send, context }) => {
  const { user } = await P.requireSession(req);
  const id = J.normJob(params.id);
  const action = String(params.action || "");
  const key = params.key ? String(params.key) : "";
  const { job, etag: jobEtag } = await J.requireJob(user, id);

  /* ── Photos ─────────────────────────────────────────────────────────── */
  if (action === "photos") {
    if (method === "GET") {
      if (!RE_PHOTO.test(key)) throw new ApiError(404, "Not found.");
      const got = await P.store().getBytes(J.paths.photo(id, key));
      if (!got) throw new ApiError(404, "Not found.");
      context.res = { status: 200, isRaw: true, body: got.buf,
        headers: { "Content-Type": "image/jpeg", "Cache-Control": "private, max-age=86400", "X-Content-Type-Options": "nosniff" } };
      return;
    }
    if (method !== "PUT" || key) throw new ApiError(405, "Method not allowed.");
    const m = /^data:image\/jpeg;base64,([A-Za-z0-9+/=]+)$/.exec(String(body.dataUrl || ""));
    if (!m) throw new ApiError(400, "Send the photo as a JPEG.");
    const buf = Buffer.from(m[1], "base64");
    if (buf.length < 100 || buf[0] !== 0xff || buf[1] !== 0xd8 || buf[2] !== 0xff) throw new ApiError(400, "That is not a JPEG photo.");
    if (buf.length > MAX_PHOTO) throw new ApiError(413, "Photo is too large (max 3 MB).");
    const name = crypto.randomBytes(8).toString("hex") + ".jpg";
    await P.store().putBytes(J.paths.photo(id, name), buf, "image/jpeg");
    await P.audit(req, user.username, "photo.upload", "job:" + id, { name, bytes: buf.length });
    return send(201, { name, url: "/api/jobs/" + encodeURIComponent(id) + "/photos/" + name });
  }

  /* ── Part numbers (LED Connection only; allowed after submit too) ─── */
  if (action === "parts") {
    if (method !== "PUT") throw new ApiError(405, "Method not allowed.");
    if (!P.A.isLc(user)) throw new ApiError(403, "Only LED Connection sets part numbers.");
    const site = await J.requireSite(id);
    const labels = new Set(site.bom.map(b => b.sku));
    const by = body.byLabel;
    if (!by || typeof by !== "object" || Array.isArray(by)) throw new ApiError(400, "byLabel must be an object of design label: part number.");
    const cur = await P.store().get(J.paths.parts(id));
    const rec = cur ? cur.data : { v: J.SCHEMA, byLabel: {} };
    const changed = {};
    for (const [label, raw] of Object.entries(by)) {
      if (!labels.has(label)) throw new ApiError(400, "\"" + label + "\" is not a product on this site.");
      if (raw === "" || raw == null) { if (rec.byLabel[label]) { delete rec.byLabel[label]; changed[label] = null; } continue; }
      const c = PARTS.check(raw);
      if (!c.ok) throw new ApiError(400, label + ": " + c.error);
      rec.byLabel[label] = Object.assign({ pn: c.pn, at: new Date().toISOString() }, who(user));
      changed[label] = c.pn;
    }
    await P.store().put(J.paths.parts(id), rec, cur ? { ifMatch: cur.etag } : { ifNoneMatch: "*" });
    await P.audit(req, user.username, "parts.update", "job:" + id, changed);
    return send(200, { byLabel: rec.byLabel });
  }

  if (job.submitted && action !== "claims" && action !== "flags") throw new ApiError(409, "This job was submitted on " + job.submitted.at.slice(0, 10) + ". Ask LED Connection to reopen it.");
  const site = await J.requireSite(id);

  /* ── Material check ─────────────────────────────────────────────────── */
  if (action === "material" || action === "approve") {
    if (method !== (action === "material" ? "PUT" : "POST")) throw new ApiError(405, "Method not allowed.");
    const cur = await P.store().get(J.paths.material(id));
    const mat = cur ? cur.data : { v: J.SCHEMA, lines: {}, approved: null };
    if (mat.approved) throw new ApiError(409, "The material was already signed off. Ask LED Connection to reopen it.");
    mat.lines = Object.assign({}, mat.lines, cleanLines(body.lines, site));
    mat.updated = new Date().toISOString(); mat.updatedBy = user.username;

    if (action === "approve") {
      if (body.confirm !== true) throw new ApiError(400, "Confirm that you counted the material.");
      const summary = site.bom.map(b => {
        const l = mat.lines[b.key] || {};
        if (l.received == null) throw new ApiError(400, "Enter the received quantity for " + b.name + ".");
        return { key: b.key, name: b.name, sku: b.sku, expected: b.qty, received: l.received, damaged: l.damaged || 0,
                 short: Math.max(0, b.qty - l.received), over: Math.max(0, l.received - b.qty) };
      });
      mat.approved = Object.assign({ at: new Date().toISOString(),
        short: summary.reduce((s, x) => s + x.short, 0), damaged: summary.reduce((s, x) => s + x.damaged, 0),
        over: summary.reduce((s, x) => s + x.over, 0), summary }, who(user));
    }
    const etag = await P.store().put(J.paths.material(id), mat, cur ? { ifMatch: cur.etag } : { ifNoneMatch: "*" });
    if (action !== "approve") return send(200, { material: mat, materialEtag: etag });
    await P.audit(req, user.username, "material.approve", "job:" + id,
      { short: mat.approved.short, damaged: mat.approved.damaged, over: mat.approved.over });
    /* Emailed to the same list as a claim; the sign-off is saved first. */
    const notify = await CLAIMMAIL.notifySignoff(req, id, job, site, mat.approved, user, await partOfJob(id));
    mat.approved.mail = CLAIMMAIL.mailRecord(notify);
    const etag2 = await P.store().put(J.paths.material(id), mat, { ifMatch: etag }).catch(() => etag);
    return send(200, { material: Object.assign({}, mat, { approved: J.withMail(mat.approved, user) }), materialEtag: etag2, notify: J.forViewer(notify, user) });
  }

  /* ── Claims ─────────────────────────────────────────────────────────── */
  if (action === "claims") {
    if (method !== "POST") throw new ApiError(405, "Method not allowed.");
    const kind = String(body.kind || "");
    if (!CLAIM_KINDS[kind]) throw new ApiError(400, "Pick what is wrong: short shipped, damaged, wrong product or other.");
    const byKey = Object.fromEntries(site.bom.map(b => [b.key, b]));
    const lines = (Array.isArray(body.lines) ? body.lines : []).map(l => {
      const b = byKey[l && l.key];
      if (!b) throw new ApiError(400, "Unknown product line.");
      return { key: b.key, name: b.name, sku: b.sku, expected: b.qty, received: count(l.received, "Received"), damaged: count(l.damaged, "Damaged") || 0 };
    });
    const note = P.text(body.note, 2000, "Note");
    if (!lines.length && !note) throw new ApiError(400, "Say which products, or describe the problem.");
    const photos = await cleanPhotos(id, body.photos);
    if (kind === "damaged" && !photos.length) throw new ApiError(400, "A damage claim needs at least one photo.");
    const now = new Date();
    const ref = "MC-" + now.toISOString().slice(2, 10).replace(/-/g, "") + "-" + crypto.randomBytes(2).toString("hex").toUpperCase();
    const claim = Object.assign({ v: J.SCHEMA, ref, kind, kindLabel: CLAIM_KINDS[kind], lines, note, photos, status: "open", at: now.toISOString() }, who(user));
    await P.store().put(J.paths.claim(id, ref), claim, { ifNoneMatch: "*" });
    await P.audit(req, user.username, "claim.create", "job:" + id, { ref, kind, lines: lines.length, photos: photos.length });
    /* Emailed to LED Connection (Cassie + Dino) with the photos; the claim
       is saved first, so a failed email never loses it. The part number on
       each line is the one the job shows (saved, else decided). */
    const notify = await CLAIMMAIL.notifyClaim(req, id, job, site, claim, user, await partOfJob(id));
    claim.mail = { sent: notify.sent, queued: !!notify.queued, to: notify.to, cc: notify.cc || [], attached: notify.attached, at: new Date().toISOString(), reason: notify.reason || null };
    await P.store().put(J.paths.claim(id, ref), claim).catch(() => null);
    return send(201, { claim: J.withMail(claim, user), notify: J.forViewer(notify, user) });
  }

  /* ── A problem flagged on one fixture (Dino, 2026-10-21) ─────────────
     Any head on the site, at any point of the install (also after submit,
     like a claim). Saved first, then emailed to the claim list. */
  if (action === "flags") {
    if (method !== "POST") throw new ApiError(405, "Method not allowed.");
    const kind = String(body.kind || "");
    if (!CLAIMMAIL.FLAG_KINDS[kind]) throw new ApiError(400, "Pick what the problem is.");
    const pin = site.pins.find(p => p.id === String(body.pinId || ""));
    if (!pin) throw new ApiError(400, "Pick the fixture the problem is on.");
    const note = P.text(body.note, 2000, "Note");
    const photos = await cleanPhotos(id, body.photos);
    if (!note && !photos.length) throw new ApiError(400, "Describe the problem or add a photo.");
    const now = new Date();
    const ref = "FL-" + now.toISOString().slice(2, 10).replace(/-/g, "") + "-" + crypto.randomBytes(2).toString("hex").toUpperCase();
    const partNo = pin.product ? (await partOfJob(id))(pin.product.sku) : null;
    const flag = Object.assign({ v: J.SCHEMA, ref, kind, kindLabel: CLAIMMAIL.FLAG_KINDS[kind], pinId: pin.id, fid: pin.fid, tag: pin.tag, poleId: pin.poleId || null,
      product: pin.productName || null, partNo, note, photos, status: "open", at: now.toISOString() }, who(user));
    await P.store().put(J.paths.flag(id, ref), flag, { ifNoneMatch: "*" });
    await P.audit(req, user.username, "flag.create", "job:" + id, { ref, kind, pin: pin.id, tag: pin.tag, photos: photos.length });
    const notify = await CLAIMMAIL.notifyFlag(req, id, job, site, flag, user);
    flag.mail = CLAIMMAIL.mailRecord(notify);
    await P.store().put(J.paths.flag(id, ref), flag).catch(() => null);
    return send(201, { flag: J.withMail(flag, user), notify: J.forViewer(notify, user) });
  }

  /* ── Installed heads ────────────────────────────────────────────────── */
  if (action === "pins") {
    if (method !== "PUT") throw new ApiError(405, "Method not allowed.");
    if (!RE_PIN.test(key)) throw new ApiError(404, "Pin not found.");
    const pin = site.pins.find(p => p.id === key);
    if (!pin || pin.off || !pin.product) throw new ApiError(404, "Pin not found.");
    const mat = await P.store().get(J.paths.material(id));
    if (!mat || !mat.data.approved) throw new ApiError(409, "Sign off the material check first.");
    const installed = body.installed !== false;
    const photos = await cleanPhotos(id, body.photos);
    if (installed && !photos.length) throw new ApiError(400, "Take a photo of the installed fixture first.");
    const rec = Object.assign({
      v: J.SCHEMA, pinId: key, fid: pin.fid, tag: pin.tag, poleId: pin.poleId, product: pin.productName, sku: pin.product.sku,
      installed, note: P.text(body.note, 1000, "Note"), serial: P.text(body.serial, 100, "Serial"), photos,
      at: new Date().toISOString()
    }, who(user));
    await P.store().put(J.paths.pin(id, key), rec, { compact: true });
    await P.audit(req, user.username, installed ? "pin.install" : "pin.undo", "job:" + id, { pin: key, tag: pin.tag, photos: photos.length });
    return send(200, { pin: rec });
  }

  /* ── Submit ─────────────────────────────────────────────────────────── */
  if (action === "submit") {
    if (method !== "POST") throw new ApiError(405, "Method not allowed.");
    const todo = site.pins.filter(p => !p.off && p.product);
    const saved = (await Promise.all((await P.store().list(J.paths.pins(id))).map(n => P.store().get(n)))).filter(Boolean).map(r => r.data);
    const done = new Set(saved.filter(r => r.installed).map(r => r.pinId));
    const left = todo.filter(p => !done.has(p.id)).length;
    if (left) throw new ApiError(400, left + " fixture" + (left === 1 ? " is" : "s are") + " not saved as installed yet.");
    job.submitted = Object.assign({ at: new Date().toISOString(), heads: todo.length }, who(user));
    const je = await P.store().put(J.paths.job(id), job, { ifMatch: jobEtag });
    await P.audit(req, user.username, "job.submit", "job:" + id, { heads: todo.length });
    const openOf = async pre => (await Promise.all((await P.store().list(pre)).map(n => P.store().get(n)))).filter(r => r && r.data.status === "open").length;
    const notify = await CLAIMMAIL.notifySubmit(req, id, job, site, job.submitted, user, { claims: await openOf(J.paths.claims(id)), flags: await openOf(J.paths.flags(id)) });
    job.submitted.mail = CLAIMMAIL.mailRecord(notify);
    await P.store().put(J.paths.job(id), job, { ifMatch: je }).catch(() => null);
    return send(200, { job: J.publicJob(job, user), notify: J.forViewer(notify, user) });
  }

  throw new ApiError(404, "No such action.");
});
