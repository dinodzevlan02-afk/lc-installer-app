/* LC Installer App - one-time links: invites for new logins, and
   password-reset links an admin sends. Copied from lc-customer-portal.

   The link carries a random 256-bit token. Storage only ever holds its
   SHA-256, in two places that must agree:
     invites/{hash}.json   { username, expires, kind }   lookup by token
     users/{u}.json        .invite = { hash, expires, kind, sentAt }
   Issuing a new link deletes the old lookup and overwrites .invite, so only
   the newest link works. Using it clears both. A token read out of the
   storage container is therefore useless; only the link itself works. */
const crypto = require("crypto");
const { store } = require("./store");

const INVITE_DAYS = 7;
const sha = s => crypto.createHash("sha256").update(String(s)).digest("hex");

/* Where links point. INSTALLER_PUBLIC_URL wins (set it when a custom domain is
   added); otherwise the host this request came in on. */
function baseUrl(req) {
  const env = (process.env.INSTALLER_PUBLIC_URL || "").replace(/\/+$/, "");
  if (env) return env;
  const h = (req && req.headers) || {};
  /* Static Web Apps hands its managed functions the browser's original URL
     here; the Host header can be the internal function host instead, which
     would put an unreachable address into the emailed link. */
  const orig = h["x-ms-original-url"];
  if (orig) { try { return new URL(orig).origin; } catch (e) { /* fall through */ } }
  const host = String(h["x-forwarded-host"] || h.host || "").split(",")[0].trim();
  const local = /^(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$/.test(host);
  const proto = String(h["x-forwarded-proto"] || (local ? "http" : "https")).split(",")[0].trim();
  return proto + "://" + host;
}

/* Mutates `user` (caller saves it) and writes the lookup. -> { link, expires } */
async function issue(req, user, kind) {
  const token = crypto.randomBytes(32).toString("base64url");
  const hash = sha(token);
  const expires = new Date(Date.now() + INVITE_DAYS * 86400000).toISOString();
  if (user.invite && user.invite.hash) await store().del("invites/" + user.invite.hash + ".json").catch(() => {});
  await store().put("invites/" + hash + ".json", { username: user.username, expires, kind }, { ifNoneMatch: "*" });
  user.invite = { hash, expires, kind, sentAt: new Date().toISOString() };
  return { link: baseUrl(req) + "/index.html?invite=" + token, expires };
}

/* -> { user, etag, hash } for a live token, or null. */
async function lookup(token) {
  if (typeof token !== "string" || token.length < 20 || token.length > 100) return null;
  const hash = sha(token);
  const inv = await store().get("invites/" + hash + ".json");
  if (!inv) return null;
  if (Date.parse(inv.data.expires) < Date.now()) return null;
  const rec = await store().get("users/" + inv.data.username + ".json");
  if (!rec || !rec.data.invite || rec.data.invite.hash !== hash) return null;
  return { user: rec.data, etag: rec.etag, hash };
}

async function retire(hash) { await store().del("invites/" + hash + ".json").catch(() => {}); }

module.exports = { issue, lookup, retire, baseUrl, INVITE_DAYS };
