/* LC Installer App - request handling and the records themselves.
   Same shape as lc-customer-portal's api/shared/portal.js.

   Storage paths (see docs/storage.md):
     users/{username}.json          one login
     invites/{sha256}.json          one live invite / reset link
     audit/{yyyy-mm}/{stamp}.json   who did what, append-only
     system/setup.json              written once, when the first admin is made */
const { store, StoreError } = require("./store");
const A = require("./auth");
const { ApiError } = A;

/* ── Ids ────────────────────────────────────────────────────────────────── */
const RE_USER = /^[a-z0-9][a-z0-9._@-]{2,63}$/;

function normUser(u) {
  const s = String(u == null ? "" : u).trim().toLowerCase();
  if (!RE_USER.test(s)) throw new ApiError(400, "Username must be 3-64 characters: letters, digits, and . _ @ -");
  return s;
}
function text(v, max, field) {
  if (v == null) return "";
  if (typeof v !== "string") throw new ApiError(400, field + " must be text.");
  const s = v.trim();
  if (s.length > max) throw new ApiError(400, field + " is too long (max " + max + ").");
  return s;
}

const paths = {
  user: u => "users/" + u + ".json",
  company: c => "companies/" + c + ".json"
};
/* Installer company ids: a slug of the name ("crew-a", "led-connection"). */
function normCompany(c) {
  const s = String(c || "").trim().toLowerCase();
  if (!/^[a-z0-9][a-z0-9-]{1,48}$/.test(s)) throw new ApiError(400, "Company id must be 2-49 letters, digits or dashes.");
  return s;
}
function slugify(name) {
  return String(name || "").toLowerCase().normalize("NFKD").replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 48) || "company";
}

/* ── Loaders ────────────────────────────────────────────────────────────── */
/* Direct children only: anything under a record's own folder is its data. */
async function loadAll(prefix) {
  const names = (await store().list(prefix)).filter(n => n.endsWith(".json") && !n.slice(prefix.length).includes("/"));
  const recs = await Promise.all(names.map(n => store().get(n)));
  return recs.filter(Boolean).map(r => r.data);
}

/* What a user record looks like to anyone outside the store: never the
   password hash, never the lockout counters. */
function publicUser(u) {
  return {
    username: u.username, name: u.name || "", email: u.email || "", phone: u.phone || "", company: u.company || "", companyId: u.companyId || null,
    role: u.role, disabled: !!u.disabled, mustChangePassword: !!u.mustChangePassword,
    hasPassword: !!u.password,
    invite: u.invite ? { kind: u.invite.kind, sentAt: u.invite.sentAt, expires: u.invite.expires, expired: Date.parse(u.invite.expires) < Date.now() } : null,
    created: u.created, createdBy: u.createdBy, lastLogin: u.lastLogin || null
  };
}

/* What the pages are told about the signed-in user: who they are and which
   screens to show. The screens are only a convenience - every endpoint
   re-checks the same rules on its own. */
function describeMe(user) {
  const lc = A.isLc(user);
  return {
    user: publicUser(user),
    can: {
      manageUsers: lc,
      grantRoles: A.grantableRoles(user)
    }
  };
}

/* ── Audit ──────────────────────────────────────────────────────────────── */
async function audit(req, actor, action, target, detail) {
  const now = new Date();
  const stamp = now.toISOString().replace(/[:.]/g, "-") + "-" + Math.random().toString(36).slice(2, 8);
  const ym = now.toISOString().slice(0, 7);
  try {
    await store().put("audit/" + ym + "/" + stamp + ".json", {
      at: now.toISOString(), actor: actor || null, action, target: target || null, detail: detail || null,
      ip: (req && req.headers && (req.headers["x-forwarded-for"] || "").split(",")[0].trim()) || null
    }, { ifNoneMatch: "*" });
  } catch (e) { /* an audit write must never block the action it records */ }
}

/* ── Session ────────────────────────────────────────────────────────────── */
/* Returns { user, etag } for the signed-in user, or throws 401.
   Re-reads the record every time; see auth.js for why. */
async function requireSession(req) {
  const tok = A.readCookie(req, A.COOKIE);
  const claims = tok && A.verifySession(tok);
  if (!claims) throw new ApiError(401, "Not signed in.");
  const rec = await store().get(paths.user(claims.sub));
  if (!rec) throw new ApiError(401, "Not signed in.");
  const user = rec.data;
  if (user.disabled || (user.sessionVersion || 0) !== claims.sv) throw new ApiError(401, "Session ended. Sign in again.");
  if (claims.sid && (user.endedSessions || []).some(e => e.sid === claims.sid)) throw new ApiError(401, "Signed out. Sign in again.");
  /* An installer company switched off by LED Connection signs all its
     people out on their next request. */
  if (user.companyId) {
    const co = await store().get(paths.company(user.companyId)).catch(() => null);
    if (co && co.data.status === "suspended") throw new ApiError(401, "Your company's access is switched off. Contact LED Connection.");
  }
  return { user, etag: rec.etag };
}

async function requireLc(req) {
  const s = await requireSession(req);
  if (!A.isLc(s.user)) throw new ApiError(403, "LED Connection only.");
  return s;
}

/* ── Handler wrapper ────────────────────────────────────────────────────── */
/* Wraps a function so every response is JSON, never cached, and every error
   comes back as { error } with the right status instead of a stack trace. */
function handler(fn) {
  return async function (context, req) {
    const send = (status, body, extraHeaders) => {
      context.res = {
        status,
        headers: Object.assign({ "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" }, extraHeaders || {}),
        body: JSON.stringify(body == null ? {} : body)
      };
    };
    try {
      const method = String(req.method || "GET").toUpperCase();
      /* CSRF: a page on another site can make the browser POST here with
         our cookie attached (SameSite=Strict already stops most of that);
         it cannot add a custom header without a CORS preflight we never
         answer. */
      if (method !== "GET" && method !== "HEAD") {
        const h = req.headers || {};
        if ((h["x-lci"] || h["X-LCI"] || h["X-Lci"]) !== "1") throw new ApiError(403, "Missing request header.");
      }
      let body = req.body;
      if (typeof body === "string") { try { body = body ? JSON.parse(body) : {}; } catch (e) { throw new ApiError(400, "Body must be JSON."); } }
      if (body && Buffer.isBuffer(body)) { try { body = JSON.parse(body.toString("utf8")); } catch (e) { throw new ApiError(400, "Body must be JSON."); } }
      await fn({ req, method, body: body || {}, params: req.params || {}, query: req.query || {}, send, context });
      if (!context.res) send(204, null);
    } catch (e) {
      if (e instanceof ApiError) return send(e.status, { error: e.message });
      if (e instanceof StoreError && e.code === "CONFLICT") return send(409, { error: "Someone else changed this at the same time. Reload and try again." });
      if (e instanceof StoreError && e.code === "NOT_CONFIGURED") return send(500, { error: e.message });
      context.log && context.log.error && context.log.error(e);
      send(500, { error: "Server error." });
    }
  };
}

module.exports = {
  store, ApiError, A, paths, loadAll, publicUser, describeMe, audit, requireSession, requireLc, handler,
  normUser, normCompany, slugify, text
};
