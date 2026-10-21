/* Logins. Same rules as lc-customer-portal's api/users, without customers.

   Roles:  lc-admin   LED Connection office. Sees and manages everything.
           installer  Field crew (LED Connection's own or a subcontractor,
                      named in `company`). Manages nobody.
   Only LED Connection admins manage logins; everyone else is refused below,
   whatever the page shows.

   GET   /api/users                LC admin: everyone.
   GET   /api/users/{username}     LC admin: anyone. Others: themselves only.
   POST  /api/users                { username, name, email?, phone?, companyId, role }
                                   An installer belongs to an installer
                                   company (api/companies): companyId is
                                   required for one, and its name is kept on
                                   the login as `company`. An LED Connection
                                   admin has none.
                                   Issues a one-time set-password link
                                   (shared/invite.js) and returns it ONCE for
                                   the admin to pass on (text or email) only
                                   when it cannot be emailed: no email on the
                                   login, mail not set up, or the Outlook
                                   relay has not checked in (see deliverLink).
   PATCH /api/users/{username}     { name?, email?, phone?, companyId?, role?, disabled?, sendInvite? }
                                   companyId moves an installer to another
                                   company (their jobs stay as assigned).
                                   sendInvite: a new invite, or for someone who
                                   already has a password, a reset link.
                                   Disabling or a role change signs that person
                                   out everywhere.

   Guard rails: nobody can switch themselves off or change their own role,
   and the last active LED Connection admin cannot be removed, so the app
   can never be left with no one able to manage it. */
const P = require("../shared/app");
const INV = require("../shared/invite");
const MAIL = require("../shared/mail");
const { A, ApiError } = P;

const RE_EMAIL = /^[^\s@<>"]+@[^\s@<>"]+\.[^\s@<>"]+$/;
const RE_PHONE = /^[0-9+().\- ]{7,25}$/;

async function otherActiveLcAdmins(exceptUsername) {
  const all = await P.loadAll("users/");
  return all.filter(u => u.role === "lc-admin" && !u.disabled && u.username !== exceptUsername).length;
}

/* Installers may have only a phone, so email is optional here. */
function cleanEmail(v) {
  const e = P.text(v, 200, "Email").toLowerCase();
  if (e && !RE_EMAIL.test(e)) throw new ApiError(400, "That email address does not look right.");
  return e;
}
function cleanPhone(v) {
  const p = P.text(v, 25, "Phone");
  if (p && !RE_PHONE.test(p)) throw new ApiError(400, "That phone number does not look right.");
  return p;
}

/* The link goes back to the admin, once, in this response only. It is a key
   to someone else's login: pass it on by one channel and do not keep it. */
/* Issues the link and emails it (Dino, 2026-10-21, "immediately send them
   an email ... same like the customer portal"). The link comes back to the
   admin only when the email will not reach them: no email on the login
   (installers may have only a phone), mail not set up or failed, or queued
   for the Outlook relay while the relay has not checked in for 15 minutes
   (it would sit in the queue). One channel otherwise. */
const RELAY_STALE = 15 * 60000;
async function issueLink(req, user) {
  const kind = user.password ? "reset" : "invite";
  const { link, expires } = await INV.issue(req, user, kind);
  return { kind, link, expires };
}
/* After the login is saved: email the link. -> what the page is told */
async function deliverLink(user, issued, actor) {
  const { kind, link, expires } = issued;
  const base = { kind, expires, to: user.email || user.phone || "", name: user.name || "", username: user.username };
  if (!user.email) return Object.assign(base, { emailSent: false, reason: "No email on this login", link });
  let mail;
  try {
    mail = await MAIL.sendMail(MAIL.inviteEmail({ to: user.email, name: user.name, username: user.username, link, kind,
      role: user.role, company: user.company, invitedBy: actor && actor.name, expiresDays: INV.INVITE_DAYS }));
  } catch (e) { console.error("[users] invite mail: " + e.message); mail = { sent: false, reason: "The email could not be sent." }; }
  if (!mail.sent) return Object.assign(base, { emailSent: false, reason: mail.reason, link });
  const out = Object.assign(base, { emailSent: true, queued: !!mail.queued, local: !!mail.local });
  if (mail.queued) {
    const seen = await P.store().get("system/relay-seen.json").catch(() => null);
    if (!seen || Date.now() - (seen.data.at || 0) > RELAY_STALE) Object.assign(out, { relayIdle: true, link });
  }
  return out;
}

/* The installer company a login joins: it must exist and be active. */
async function companyFor(id) {
  const cid = P.normCompany(id);
  const co = await P.store().get(P.paths.company(cid));
  if (!co) throw new ApiError(400, "No installer company \"" + cid + "\". Add it under Installer companies first.");
  if (co.data.status === "suspended") throw new ApiError(400, co.data.name + " is switched off: switch it on before adding people.");
  return co.data;
}

module.exports = P.handler(async ({ req, method, body, params, send }) => {
  const { user: actor } = await P.requireSession(req);
  const uname = params.username ? P.normUser(params.username) : null;

  if (method === "GET") {
    if (uname) {
      const t = await P.store().get(P.paths.user(uname));
      if (!t || (uname !== actor.username && !A.canManageUser(actor, t.data))) throw new ApiError(404, "User not found.");
      return send(200, P.publicUser(t.data));
    }
    if (!A.isLc(actor)) throw new ApiError(403, "Only LED Connection manages logins.");
    const all = (await P.loadAll("users/")).filter(u => A.canManageUser(actor, u));
    all.sort((a, b) => a.username.localeCompare(b.username));
    return send(200, { users: all.map(P.publicUser) });
  }

  const grantable = A.grantableRoles(actor);
  if (!grantable.length) throw new ApiError(403, "Only LED Connection manages logins.");

  if (method === "POST") {
    const username = P.normUser(body.username);
    const role = body.role || "installer";
    if (!grantable.includes(role)) throw new ApiError(403, "You cannot create a login with role " + role + ".");
    const rec = {
      username, role,
      name: P.text(body.name, 100, "Name"), email: cleanEmail(body.email), phone: cleanPhone(body.phone),
      company: "", companyId: null,
      password: null, sessionVersion: 1, disabled: false, mustChangePassword: false,
      created: new Date().toISOString(), createdBy: actor.username
    };
    if (role === "installer") {
      if (!body.companyId) throw new ApiError(400, "Pick the installer's company.");
      const co = await companyFor(body.companyId);
      rec.companyId = co.id; rec.company = co.name;
    }
    /* A password set directly (API only, not offered in the pages) is a
       temporary one: they must change it on first sign-in. */
    let invite = null, issued = null;
    if (body.password !== undefined) {
      A.checkPasswordPolicy(body.password);
      rec.password = await A.hashPassword(body.password);
      rec.mustChangePassword = true;
    } else {
      issued = await issueLink(req, rec);
    }
    try { await P.store().put(P.paths.user(username), rec, { ifNoneMatch: "*" }); }
    catch (e) {
      if (rec.invite) await INV.retire(rec.invite.hash);
      if (e.code === "CONFLICT") throw new ApiError(409, "Username \"" + username + "\" is already taken.");
      throw e;
    }
    if (issued) invite = await deliverLink(rec, issued, actor);
    await P.audit(req, actor.username, "user.create", "user:" + username, { role, invite: invite && { emailSent: invite.emailSent, queued: !!invite.queued } });
    return send(201, { user: P.publicUser(rec), invite });
  }

  if (method === "PATCH") {
    if (!uname) throw new ApiError(400, "Which user?");
    const cur = await P.store().get(P.paths.user(uname));
    if (!cur || !A.canManageUser(actor, cur.data)) throw new ApiError(404, "User not found.");
    const t = cur.data, self = uname === actor.username, changes = {};
    let endSessions = false;

    if (body.name !== undefined) changes.name = P.text(body.name, 100, "Name");
    if (body.email !== undefined) changes.email = cleanEmail(body.email);
    if (body.phone !== undefined) changes.phone = cleanPhone(body.phone);
    if (body.companyId !== undefined && body.companyId !== t.companyId) {
      if ((body.role || t.role) !== "installer") throw new ApiError(400, "Only installers belong to an installer company.");
      const co = await companyFor(body.companyId);
      changes.companyId = co.id; changes.company = co.name;
    }

    if (body.role !== undefined && body.role !== t.role) {
      if (self) throw new ApiError(400, "You cannot change your own role.");
      if (!grantable.includes(body.role)) throw new ApiError(403, "You cannot give the role " + body.role + ".");
      if (t.role === "lc-admin" && !(await otherActiveLcAdmins(uname))) throw new ApiError(400, "This is the last LED Connection admin.");
      changes.role = body.role;
      endSessions = true;
      if (body.role === "installer" && !changes.companyId && !t.companyId) throw new ApiError(400, "Pick the installer's company.");
      if (body.role !== "installer") { changes.companyId = null; changes.company = ""; }
    }

    if (body.disabled !== undefined) {
      const d = !!body.disabled;
      if (d && self) throw new ApiError(400, "You cannot switch off your own login.");
      if (d && t.role === "lc-admin" && !(await otherActiveLcAdmins(uname))) throw new ApiError(400, "This is the last LED Connection admin.");
      if (d !== !!t.disabled) { changes.disabled = d; if (d) endSessions = true; }
    }

    if (body.password !== undefined) {
      if (self) throw new ApiError(400, "Use Change password for your own login.");
      A.checkPasswordPolicy(body.password);
      t.password = await A.hashPassword(body.password);
      changes.mustChangePassword = true;
      delete t.lockedUntil; t.failedLogins = 0;
      endSessions = true;
    }

    Object.assign(t, changes, { updated: new Date().toISOString(), updatedBy: actor.username });
    let invite = null, issued = null;
    if (body.sendInvite) {
      if (self) throw new ApiError(400, "Use Change password for your own login.");
      if (t.disabled) throw new ApiError(400, "Switch this login on before sending it a link.");
      issued = await issueLink(req, t);
    }
    if (endSessions) t.sessionVersion = (t.sessionVersion || 0) + 1;
    await P.store().put(P.paths.user(uname), t, { ifMatch: cur.etag });
    if (issued) invite = await deliverLink(t, issued, actor);
    const logged = Object.assign({}, changes);
    if (body.password !== undefined) logged.passwordReset = true;
    if (invite) logged.invite = { kind: invite.kind, emailSent: invite.emailSent, queued: !!invite.queued };
    await P.audit(req, actor.username, "user.update", "user:" + uname, logged);
    return send(200, { user: P.publicUser(t), invite });
  }

  throw new ApiError(405, "Method not allowed.");
});
