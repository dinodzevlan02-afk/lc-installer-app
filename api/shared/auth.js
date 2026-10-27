/* LC Installer App - passwords, sessions, and who may do what.

   Same model as lc-customer-portal's api/shared/auth.js (2026-10-20, Dino:
   "all same security"), with its own cookie, header and secrets so a
   session for one app is never a session for the other:
   - Passwords are scrypt (slow, salted).
   - The session is an HttpOnly cookie, so page script can never read it and
     nothing has to be kept in sessionStorage. Every state-changing request
     must also carry the X-LCI header, which a cross-site form cannot send.
   - Every request re-reads the user. Disabling a login or changing a
     password ends their sessions at once, through `sv` (session version),
     instead of 12 hours later.

   Roles: lc-admin   LED Connection office. Manages logins, sees everything.
          installer  Field crew. Signs in, sees their own work. Manages nobody. */
const crypto = require("crypto");

const ROLES = ["lc-admin", "installer"];
const SESSION_HOURS = 12;
const COOKIE = "lci_s";
const MIN_PASSWORD = 10;

class ApiError extends Error {
  constructor(status, message) { super(message); this.status = status; }
}

/* ── Passwords ──────────────────────────────────────────────────────────── */
const SCRYPT = { N: 16384, r: 8, p: 1, keylen: 32 };

function scrypt(password, salt, prm) {
  return new Promise((resolve, reject) =>
    crypto.scrypt(password, salt, prm.keylen, { N: prm.N, r: prm.r, p: prm.p, maxmem: 64 * 1024 * 1024 },
      (err, key) => err ? reject(err) : resolve(key)));
}

async function hashPassword(password) {
  const salt = crypto.randomBytes(16);
  const key = await scrypt(password, salt, SCRYPT);
  return { alg: "scrypt", N: SCRYPT.N, r: SCRYPT.r, p: SCRYPT.p, salt: salt.toString("base64"), hash: key.toString("base64") };
}

async function verifyPassword(password, rec) {
  if (!rec || rec.alg !== "scrypt") return false;
  const want = Buffer.from(rec.hash, "base64");
  const got = await scrypt(password, Buffer.from(rec.salt, "base64"), { N: rec.N, r: rec.r, p: rec.p, keylen: want.length });
  return got.length === want.length && crypto.timingSafeEqual(got, want);
}

/* Run once for an unknown username so a wrong name takes as long as a wrong
   password; otherwise timing tells an attacker which usernames exist. */
const DUMMY = { alg: "scrypt", N: SCRYPT.N, r: SCRYPT.r, p: SCRYPT.p, salt: "AAAAAAAAAAAAAAAAAAAAAA==", hash: "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=" };
async function burnPasswordCheck(password) { await verifyPassword(password, DUMMY).catch(() => false); }

function checkPasswordPolicy(pw) {
  if (typeof pw !== "string" || pw.length < MIN_PASSWORD) throw new ApiError(400, "Password must be at least " + MIN_PASSWORD + " characters.");
  if (pw.length > 200) throw new ApiError(400, "Password is too long.");
}

/* ── Session token (HS256 JWT) ──────────────────────────────────────────── */
function secret() {
  const s = process.env.INSTALLER_JWT_SECRET;
  if (!s || s.length < 16) throw new ApiError(500, "INSTALLER_JWT_SECRET app setting is not configured (min 16 chars).");
  return s;
}
const b64url = buf => Buffer.from(buf).toString("base64").replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");

function signSession(user) {
  const now = Math.floor(Date.now() / 1000);
  const h = b64url(JSON.stringify({ alg: "HS256", typ: "JWT" }));
  /* sid names this one sign-in, so SIGN OUT can end it on the server
     (user.endedSessions) without signing the same login out elsewhere. */
  const p = b64url(JSON.stringify({ sub: user.username, sv: user.sessionVersion || 0, sid: crypto.randomBytes(9).toString("hex"),
                                    iat: now, exp: now + SESSION_HOURS * 3600 }));
  const sig = b64url(crypto.createHmac("sha256", secret()).update(h + "." + p).digest());
  return h + "." + p + "." + sig;
}

function verifySession(token) {
  try {
    const parts = String(token).split(".");
    if (parts.length !== 3) return null;
    const sig = b64url(crypto.createHmac("sha256", secret()).update(parts[0] + "." + parts[1]).digest());
    const a = Buffer.from(sig), b = Buffer.from(parts[2]);
    if (a.length !== b.length || !crypto.timingSafeEqual(a, b)) return null;
    const payload = JSON.parse(Buffer.from(parts[1].replace(/-/g, "+").replace(/_/g, "/"), "base64").toString("utf8"));
    if (!payload.exp || Date.now() / 1000 > payload.exp) return null;
    return payload;
  } catch (e) { return null; }
}

/* ── Cookies ────────────────────────────────────────────────────────────── */
function readCookie(req, name) {
  const raw = (req.headers && (req.headers.cookie || req.headers.Cookie)) || "";
  for (const part of raw.split(";")) {
    const i = part.indexOf("=");
    if (i > 0 && part.slice(0, i).trim() === name) return decodeURIComponent(part.slice(i + 1).trim());
  }
  return null;
}
const sessionCookie = token => COOKIE + "=" + token + "; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=" + SESSION_HOURS * 3600;
const clearCookie = () => COOKIE + "=; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=0";

/* ── Permissions ────────────────────────────────────────────────────────── */
const isLc = u => u.role === "lc-admin";

/* Logins are managed by LED Connection only, as in the customer portal. */
function canManageUser(actor, target) {
  return isLc(actor);
}

/* Which roles may `actor` hand out? */
function grantableRoles(actor) {
  if (isLc(actor)) return ROLES.slice();
  return [];
}

module.exports = {
  ROLES, COOKIE, MIN_PASSWORD, ApiError,
  hashPassword, verifyPassword, burnPasswordCheck, checkPasswordPolicy,
  signSession, verifySession, readCookie, sessionCookie, clearCookie,
  isLc, canManageUser, grantableRoles
};
