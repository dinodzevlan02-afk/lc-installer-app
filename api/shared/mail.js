/* LC Installer App - outgoing email. Ported from lc-customer-portal
   api/shared/mail.js (2026-10-21); keep the two in step.

   Dino, 2026-10-21: a material claim goes to Cassie and him "with the photo
   inside", the way the customer portal sends tickets. Three ways out, in
   this order:
     1. Microsoft Graph, when INSTALLER_MAIL_TENANT_ID / _CLIENT_ID /
        _CLIENT_SECRET / _FROM are set (an M365 admin has to approve it).
     2. THE OUTLOOK RELAY, as in the portal: the message is queued in this
        app's own storage (mailqueue/pending/) and tools/outlook-relay.ps1 on
        Dino's PC sends it through his Outlook from dinod@ within seconds
        and reports back (api/relay). On once a relay is paired from the
        home page (system/relay.json keeps only the key's SHA-256) or
        INSTALLER_RELAY_KEY is set. This app's relay key is its own, not the
        portal's.
     3. Locally (dev/server.js) with neither: written to <store>/outbox/.
   Not set up at all -> { sent: false, reason }: the claim is saved anyway
   and the office still sees it on the job page. Never throws. Dino is BCC'd
   on everything he is not already addressed on. */
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

let tokenCache = { token: null, exp: 0 };

function configured() {
  const e = process.env;
  return !!(e.INSTALLER_MAIL_TENANT_ID && e.INSTALLER_MAIL_CLIENT_ID && e.INSTALLER_MAIL_CLIENT_SECRET && e.INSTALLER_MAIL_FROM);
}

async function graphToken() {
  if (tokenCache.token && Date.now() < tokenCache.exp - 60000) return tokenCache.token;
  const e = process.env;
  const r = await fetch("https://login.microsoftonline.com/" + encodeURIComponent(e.INSTALLER_MAIL_TENANT_ID) + "/oauth2/v2.0/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      client_id: e.INSTALLER_MAIL_CLIENT_ID, client_secret: e.INSTALLER_MAIL_CLIENT_SECRET,
      scope: "https://graph.microsoft.com/.default", grant_type: "client_credentials"
    })
  });
  const j = await r.json().catch(() => ({}));
  if (!r.ok || !j.access_token) throw new Error("token: " + (j.error_description || j.error || r.status));
  tokenCache = { token: j.access_token, exp: Date.now() + (j.expires_in || 3600) * 1000 };
  return j.access_token;
}

/* Dino is BCC'd on everything he is not already addressed on, as in the
   portal (Dino, 2026-10-14). */
const SENDER = () => (process.env.INSTALLER_MAIL_FROM || "dinod@ledconnection.com").toLowerCase();
function bccFor(to, cc) {
  const me = SENDER();
  return [].concat(to, cc || []).some(a => String(a).toLowerCase() === me) ? [] : [me];
}
/* Who may fetch the queue: a relay key whose SHA-256 is one of these.
   - INSTALLER_RELAY_KEY (app setting), or a relay paired from this app's home
     page (system/relay.json holds the key's SHA-256, never the key);
   - THE CUSTOMER PORTAL'S RELAY (Dino, 2026-10-21: "don't ask, just do it").
     It already runs on Dino's PC with its own key; its SHA-256 is in the
     portal's system/relay.json, which this app can read (read-only SAS). So
     the same relay sends both apps' emails, with no second pairing: its
     script (lc-customer-portal tools/outlook-relay.ps1) polls this app too.
   -> [{ hash: Buffer, via: "setting" | "installer" | "portal", pairedAt, pairedBy }] */
async function relayHashes() {
  const out = [];
  const env = String(process.env.INSTALLER_RELAY_KEY || "");
  if (env.length >= 24) out.push({ hash: crypto.createHash("sha256").update(env).digest(), via: "setting" });
  const { store, portalStore } = require("./store");
  const own = await store().get("system/relay.json").catch(() => null);
  if (own && /^[a-f0-9]{64}$/.test(own.data.keyHash || "")) out.push({ hash: Buffer.from(own.data.keyHash, "hex"), via: "installer", pairedAt: own.data.pairedAt, pairedBy: own.data.pairedBy });
  const portal = await portalStore().get("system/relay.json").catch(() => null);
  if (portal && /^[a-f0-9]{64}$/.test(portal.data.keyHash || "")) out.push({ hash: Buffer.from(portal.data.keyHash, "hex"), via: "portal", pairedAt: portal.data.pairedAt, pairedBy: portal.data.pairedBy });
  return out;
}
/* The relay is on when any of those exists. Read at most once a minute. */
let relayCache = { at: 0, on: false };
async function relayConfigured() {
  if (Date.now() - relayCache.at < 60000) return relayCache.on;
  relayCache = { at: Date.now(), on: (await relayHashes()).length > 0 };
  return relayCache.on;
}
function relayForget() { relayCache.at = 0; }

async function queueForRelay(msg, bcc) {
  const { store } = require("./store");
  const id = new Date().toISOString().replace(/[:.]/g, "-") + "-" + crypto.randomBytes(4).toString("hex");
  await store().put("mailqueue/pending/" + id + ".json", {
    id, queuedAt: Date.now(), attempts: 0,
    to: [].concat(msg.to), cc: [].concat(msg.cc || []), bcc, subject: msg.subject, html: msg.html,
    attachments: (msg.attachments || []).map(a => ({ name: a.name, contentType: a.contentType, b64: a.bytes.toString("base64") }))
  }, { ifNoneMatch: "*", compact: true });
  return id;
}

/* msg: { to, cc?, toName?, subject, html, attachments?: [{ name, contentType, bytes: Buffer }] }
   Graph's sendMail takes the whole message in one request of at most 4 MB,
   attachments base64-encoded inside it, so sendMail keeps fewer there.
   -> { sent: true } | { sent: false, reason } */
const ATTACH_BUDGET = 20 * 1024 * 1024;         // photos read for one email; sendMail trims to the sender
const RELAY_ATTACH_MAX = 22 * 1024 * 1024;      // Outlook's practical attachment ceiling
const GRAPH_ATTACH_MAX = 3.4 * 1024 * 1024;     // Graph sendMail takes the whole message in one <= 4 MB request
/* Keep attachments within the sender's limit, in order; the body always
   links to the job, so a dropped photo is one click away. -> { kept, dropped } */
function fitAttachments(atts, max) {
  const kept = []; let total = 0, dropped = 0;
  for (const a of atts || []) { if (total + a.bytes.length <= max) { kept.push(a); total += a.bytes.length; } else dropped++; }
  return { kept, dropped };
}
async function sendMail(msg) {
  const bcc = bccFor(msg.to, msg.cc);
  if (!configured()) {
    if (await relayConfigured()) {
      try { const kept = fitAttachments(msg.attachments, RELAY_ATTACH_MAX).kept; return { sent: true, queued: true, id: await queueForRelay(Object.assign({}, msg, { attachments: kept }), bcc) }; }
      catch (e) { console.error("[mail] queue: " + e.message); return { sent: false, reason: "The email could not be queued." }; }
    }
    if (process.env.INSTALLER_LOCAL_STORE) {
      const dir = path.join(process.env.INSTALLER_LOCAL_STORE, "outbox");
      fs.mkdirSync(dir, { recursive: true });
      const f = path.join(dir, new Date().toISOString().replace(/[:.]/g, "-") + "-" + [].concat(msg.to).join("+").replace(/[^a-z0-9@._+-]/gi, "_") + ".json");
      /* Attachments are written beside it as files; the JSON lists them. */
      const out = Object.assign({}, msg, { bcc, attachments: (msg.attachments || []).map(a => ({ name: a.name, contentType: a.contentType, bytes: a.bytes.length })) });
      fs.writeFileSync(f, JSON.stringify(out, null, 2));
      (msg.attachments || []).forEach(a => fs.writeFileSync(f.replace(/\.json$/, "-" + a.name), a.bytes));
      return { sent: true, local: true };
    }
    return { sent: false, reason: "Email is not set up yet." };
  }
  try {
    const token = await graphToken();
    const r = await fetch("https://graph.microsoft.com/v1.0/users/" + encodeURIComponent(process.env.INSTALLER_MAIL_FROM) + "/sendMail", {
      method: "POST",
      headers: { Authorization: "Bearer " + token, "Content-Type": "application/json" },
      body: JSON.stringify({
        message: {
          subject: msg.subject,
          body: { contentType: "HTML", content: msg.html },
          toRecipients: [].concat(msg.to).map(a => ({ emailAddress: { address: a, name: (!Array.isArray(msg.to) && msg.toName) || undefined } })),
          ccRecipients: [].concat(msg.cc || []).map(a => ({ emailAddress: { address: a } })),
          bccRecipients: bcc.map(a => ({ emailAddress: { address: a } })),
          attachments: fitAttachments(msg.attachments, GRAPH_ATTACH_MAX).kept.map(a => ({
            "@odata.type": "#microsoft.graph.fileAttachment", name: a.name, contentType: a.contentType, contentBytes: a.bytes.toString("base64")
          }))
        },
        saveToSentItems: true
      })
    });
    if (r.status === 202 || r.ok) return { sent: true };
    const t = await r.text().catch(() => "");
    console.error("[mail] Graph sendMail " + r.status + ": " + t.slice(0, 300));
    return { sent: false, reason: "The email could not be sent (" + r.status + ")." };
  } catch (e) {
    console.error("[mail] " + e.message);
    return { sent: false, reason: "The email could not be sent." };
  }
}

const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

/* ── A new login: the one-time set-password link, worded for the role ──
   The customer portal's invite email, in this app's words (Dino,
   2026-10-21: "when I'm creating new logins ... immediately send them an
   email ... same like the customer portal"). No passwords in email, only
   the link; no em dashes (house rule for outbound mail). */
const ROLE_WORDS = {
  installer: { label: "installer", what: "It holds your install jobs: the material check, the install map with every fixture, photos, and the job sheets." },
  "lc-admin": { label: "LED Connection admin", what: "You manage projects, installers, logins and project emails, and approve finished installs." }
};
function inviteEmail({ to, name, username, link, kind, role, company, invitedBy, expiresDays }) {
  const reset = kind === "reset";
  const rw = ROLE_WORDS[role] || ROLE_WORDS.installer;
  const subject = reset ? "Reset your LED Connection Installer App password" : "Your LED Connection Installer App access";
  const hello = name ? "Hello " + esc(name.split(" ")[0]) + "," : "Hello,";
  const lead = reset
    ? "A password reset was requested for your LED Connection Installer App login."
    : (invitedBy ? esc(invitedBy) + " has" : "LED Connection has") + " given you access to the LED Connection Installer App as <b>" +
      esc(rw.label) + "</b>" + (company ? " (" + esc(company) + ")" : "") + ". " + rw.what;
  const button = reset ? "Reset your password" : "Set your password";
  const html =
    '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#0a0e1a;padding:32px 12px;font-family:Segoe UI,Arial,sans-serif">' +
    '<tr><td align="center"><table role="presentation" width="100%" style="max-width:520px;background:#0f1626;border:1px solid #3a2a1f;border-radius:12px" cellpadding="0" cellspacing="0">' +
    '<tr><td style="padding:28px 32px 8px;font-size:12px;letter-spacing:3px;font-weight:700;color:#f37021">LED CONNECTION</td></tr>' +
    '<tr><td style="padding:0 32px;font-size:22px;font-weight:600;color:#ffffff">Installer App</td></tr>' +
    '<tr><td style="padding:20px 32px 0;font-size:15px;line-height:1.6;color:#d6dae4">' + hello + '<br><br>' + lead + '</td></tr>' +
    '<tr><td style="padding:16px 32px 0;font-size:14px;color:#9aa3b8">Your username: <b style="color:#ffffff;font-family:Consolas,monospace">' + esc(username) + '</b></td></tr>' +
    '<tr><td style="padding:24px 32px"><a href="' + esc(link) + '" style="display:inline-block;background:#f37021;color:#0a0e1a;text-decoration:none;font-weight:700;font-size:14px;letter-spacing:1px;padding:13px 26px;border-radius:8px">' + button + '</a></td></tr>' +
    '<tr><td style="padding:0 32px;font-size:12px;line-height:1.6;color:#8a93a8">This link works once and expires in ' + expiresDays + ' days. If the button does not work, paste this address into your browser:<br>' +
    '<a href="' + esc(link) + '" style="color:#22d3ee;word-break:break-all">' + esc(link) + '</a></td></tr>' +
    '<tr><td style="padding:22px 32px 28px;font-size:12px;line-height:1.6;color:#6b7488">' +
    (reset ? "If you did not ask for this, you can ignore this email; your password stays the same." : "If you were not expecting this, you can ignore this email.") +
    ' Questions? LED Connection, 702.847.7680.</td></tr>' +
    '</table></td></tr></table>';
  return { to: [to], toName: name, subject, html };
}

module.exports = { relayConfigured, relayHashes, relayForget, sendMail, mailConfigured: configured, esc, inviteEmail, ATTACH_BUDGET };
