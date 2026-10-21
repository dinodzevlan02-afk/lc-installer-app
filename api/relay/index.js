/* The Outlook relay's side of this app's mail queue. Ported from
   lc-customer-portal api/relay (Dino, 2026-10-14 there; 2026-10-21 here for
   material claims). See mail.js. This app has its own key: pairing here
   never touches the portal's relay.

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

const sha = v => crypto.createHash("sha256").update(String(v)).digest();

async function checkKey(req) {
  const env = String(process.env.INSTALLER_RELAY_KEY || "");
  const paired = await P.store().get("system/relay.json").catch(() => null);
  const wantHash = env.length >= 24 ? sha(env) : (paired && paired.data.keyHash ? Buffer.from(paired.data.keyHash, "hex") : null);
  if (!wantHash) throw new ApiError(404, "Not found.");
  const h = req.headers || {};
  const got = String(h["x-relay-key"] || h["X-Relay-Key"] || "");
  if (!got || !crypto.timingSafeEqual(sha(got), wantHash)) throw new ApiError(401, "Bad relay key.");
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
  /* GET /api/relay/status  LC admin: how mail goes out, for the home page. */
  if (action === "status") {
    if (method !== "GET") throw new ApiError(405, "Method not allowed.");
    await P.requireLc(req);
    const paired = await st.get("system/relay.json").catch(() => null);
    const [pending, sent, failed] = await Promise.all([PENDING, SENT, FAILED].map(p => st.list(p).then(n => n.filter(x => x.endsWith(".json"))).catch(() => [])));
    const last = sent.sort().slice(-1)[0];
    return send(200, {
      graph: MAIL.mailConfigured(),
      relay: !!(paired && paired.data.keyHash) || String(process.env.INSTALLER_RELAY_KEY || "").length >= 24,
      pairedAt: paired ? paired.data.pairedAt : null, pairedBy: paired ? paired.data.pairedBy : null,
      pending: pending.length, failed: failed.length, sent: sent.length,
      lastSent: last ? ((await st.get(last).catch(() => null)) || { data: {} }).data.sentAt || null : null,
      notifyTo: require("../shared/claimmail").notifyList()
    });
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
