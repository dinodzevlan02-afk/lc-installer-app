/* The Outlook relay's side of this app's mail queue. Ported from
   lc-customer-portal api/relay (Dino, 2026-10-14 there; 2026-10-21 here for
   material claims). See mail.js. The portal's own relay (already running on
   Dino's PC) is accepted too, so no second pairing is needed; pairing here
   never touches the portal.

   GET  /api/relay/outbox                -> { messages: [...] }  oldest first,
                                           up to 5, attachments base64
   POST /api/relay/outbox  { id, ok: true }                    sent: moves it
                                           to mailqueue/sent/ (without the
                                           attachment bytes) as the record
   POST /api/relay/outbox  { id, ok: false, error }            failed: tried
                                           again next round; after 5 tries it
                                           moves to mailqueue/failed/

   POST /api/relay/pair  { keyHash? }    LC admin, signed in. With keyHash
                                           (SHA-256 hex of a key the relay
                                           made itself) it registers that.
                                           Without, it makes a new
                                           relay key and returns it ONCE; the
                                           app keeps only its SHA-256 in
                                           system/relay.json. Pairing again
                                           replaces it (the old relay stops).

   The outbox is not for a signed-in user: tools/outlook-relay.ps1 on
   Dino's PC proves itself with the X-Relay-Key header, checked against
   INSTALLER_RELAY_KEY or the paired key's hash. With neither, the outbox does
   not exist (404). The queue holds customer emails, so the key is long and
   compared in constant time. */
const crypto = require("crypto");
const P = require("../shared/app");
const MAIL = require("../shared/mail");
const { A, ApiError } = P;

const PENDING = "mailqueue/pending/", SENT = "mailqueue/sent/", FAILED = "mailqueue/failed/";
const RE_ID = /^[0-9TZ-]{20,40}-[a-f0-9]{8}$/;
const MAX_TRIES = 5;
const SEEN = "system/relay-seen.json";

const sha = v => crypto.createHash("sha256").update(String(v)).digest();

/* Any accepted relay key (mail.js relayHashes: this app's own, or the
   customer portal's relay, which polls this app too). */
async function checkKey(req) {
  const want = await MAIL.relayHashes();
  if (!want.length) throw new ApiError(404, "Not found.");
  const h = req.headers || {};
  const got = String(h["x-relay-key"] || h["X-Relay-Key"] || "");
  const gh = sha(got);
  const hit = got && want.find(w => crypto.timingSafeEqual(gh, w.hash));
  if (!hit) throw new ApiError(401, "Bad relay key.");
  /* When a relay last came for mail, for the home page (written at most
     every 5 minutes, the relay asks every 15 seconds). */
  const seen = await P.store().get(SEEN).catch(() => null);
  if (!seen || Date.now() - (seen.data.at || 0) > 5 * 60000)
    await P.store().put(SEEN, { at: Date.now(), via: hit.via }).catch(() => null);
}

module.exports = P.handler(async ({ req, method, body, params, send }) => {
  const st = P.store();
  const action = String(params.action || "");

  if (action === "pair") {
    if (method !== "POST") throw new ApiError(405, "Method not allowed.");
    const { user } = await P.requireSession(req);
    if (!A.isLc(user)) throw new ApiError(403, "Only LED Connection can pair a mail relay.");
    /* Preferred: the relay made its own key and only its SHA-256 comes
       here (keyHash), so the key never travels (2026-10-14: a browser
       extension rightly refused to hand a returned key on). Otherwise a
       new key is made and returned once. */
    const given = /^[a-f0-9]{64}$/.test(String(body.keyHash || "")) ? String(body.keyHash) : null;
    if (body.keyHash !== undefined && !given) throw new ApiError(400, "keyHash must be 64 hex characters.");
    const key = given ? null : crypto.randomBytes(20).toString("hex");   // 40 characters, 160 bits
    await st.put("system/relay.json", { keyHash: given || sha(key).toString("hex"), pairedAt: Date.now(), pairedBy: user.username,
                                         from: String(body.from || "").slice(0, 200) });
    MAIL.relayForget();
    await P.audit(req, user.username, "relay.pair", "system:relay", { from: body.from || null, byHash: !!given });
    return send(200, given ? { paired: true } : { key });
  }
  /* GET /api/relay/status  LC admin: how mail goes out and to whom, for the
     home page EMAIL panel. relay: which relay may fetch the queue (this
     app's own pairing, or the customer portal's relay); seenAt: when one
     last came for mail. */
  if (action === "status") {
    if (method !== "GET") throw new ApiError(405, "Method not allowed.");
    await P.requireLc(req);
    const CM = require("../shared/claimmail");
    const [hashes, seen, list] = await Promise.all([MAIL.relayHashes(), st.get(SEEN).catch(() => null), CM.lcList()]);
    const [pending, sent, failed] = await Promise.all([PENDING, SENT, FAILED].map(p => st.list(p).then(n => n.filter(x => x.endsWith(".json"))).catch(() => [])));
    const last = sent.sort().slice(-1)[0];
    const own = hashes.find(h => h.via !== "portal"), portal = hashes.find(h => h.via === "portal");
    return send(200, {
      graph: MAIL.mailConfigured(),
      relay: hashes.length > 0, via: hashes.map(h => h.via),
      pairedAt: own ? own.pairedAt || null : null, pairedBy: own ? own.pairedBy || null : null,
      portalRelay: !!portal, seenAt: seen ? seen.data.at : null, seenVia: seen ? seen.data.via : null,
      pending: pending.length, failed: failed.length, sent: sent.length,
      lastSent: last ? ((await st.get(last).catch(() => null)) || { data: {} }).data.sentAt || null : null,
      notifyTo: list.to, notifySaved: list.saved, notifyAt: list.at || null, notifyBy: list.by || null
    });
  }
  /* POST /api/relay/test  LC admin: a short test email to LED Connection's
     list, the same way a claim goes, so the route can be checked without
     filing a claim. */
  if (action === "test") {
    if (method !== "POST") throw new ApiError(405, "Method not allowed.");
    const { user } = await P.requireLc(req);
    const CM = require("../shared/claimmail");
    const to = (await CM.lcList()).to;
    const when = new Date().toUTCString();
    const r = await MAIL.sendMail({ to, subject: "[Installer App] Test email",
      html: '<p style="font-family:Segoe UI,Arial,sans-serif;font-size:14px">This is a test from the LC Installer App, sent by ' + MAIL.esc(user.name || user.username) +
            ' at ' + MAIL.esc(when) + '. Material claims reach this list the same way.</p>' });
    await P.audit(req, user.username, "mail.test", "system:notify", { to, sent: r.sent, queued: !!r.queued });
    return send(200, { sent: r.sent, queued: !!r.queued, local: !!r.local, reason: r.reason || null, to });
  }
  /* POST /api/relay/notify { to: [address] }  LC admin: LED Connection's
     list for every claim email. @ledconnection.com only; installers and
     the client are set per project. */
  if (action === "notify") {
    if (method !== "POST") throw new ApiError(405, "Method not allowed.");
    const { user } = await P.requireLc(req);
    const CM = require("../shared/claimmail");
    const to = CM.cleanLcList(body.to);
    const before = (await CM.lcList()).to;
    await st.put(CM.NOTIFY_PATH, { to, at: new Date().toISOString(), by: user.username });
    await P.audit(req, user.username, "notify.update", "system:notify", { added: to.filter(a => !before.includes(a)), removed: before.filter(a => !to.includes(a)) });
    return send(200, { notifyTo: to });
  }
  if (action !== "outbox") throw new ApiError(404, "Not found.");
  await checkKey(req);

  if (method === "GET") {
    const names = (await st.list(PENDING)).filter(n => n.endsWith(".json")).sort().slice(0, 5);
    const msgs = (await Promise.all(names.map(n => st.get(n)))).filter(Boolean).map(r => r.data);
    return send(200, { messages: msgs });
  }

  if (method === "POST") {
    const id = String(body.id || "");
    if (!RE_ID.test(id)) throw new ApiError(400, "Bad message id.");
    const cur = await st.get(PENDING + id + ".json");
    if (!cur) throw new ApiError(404, "Not in the queue.");
    const m = cur.data;
    if (body.ok === true) {
      const rec = Object.assign({}, m, { sentAt: Date.now(), attachments: (m.attachments || []).map(a => ({ name: a.name, contentType: a.contentType })) });
      await st.put(SENT + id + ".json", rec, { compact: true });
      await st.del(PENDING + id + ".json");
      return send(200, { done: "sent" });
    }
    m.attempts = (m.attempts || 0) + 1;
    m.lastError = String(body.error || "unknown").slice(0, 500);
    if (m.attempts >= MAX_TRIES) {
      await st.put(FAILED + id + ".json", m, { compact: true });
      await st.del(PENDING + id + ".json");
      return send(200, { done: "failed" });
    }
    await st.put(PENDING + id + ".json", m, { ifMatch: cur.etag, compact: true });
    return send(200, { done: "retry", attempts: m.attempts });
  }

  throw new ApiError(405, "Method not allowed.");
});
