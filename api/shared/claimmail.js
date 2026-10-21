/* The email about a material claim (Dino, 2026-10-21): to Cassie and Dino,
   "with the photo inside", the note, and the quantities that are missing.

   Who hears is set on the server, so no page can redirect it (Dino, later
   the same day: "who do we want to report this? ... add new email ... all
   of them from LED Connection ... and who I have assigned as installer and
   who is going to be client"):
   - To: LED Connection's list, the same for every project. Edited on the
     home page EMAIL panel (system/notify.json), @ledconnection.com only;
     until then INSTALLER_NOTIFY_TO, else cassieh@, dinod@, davidw@ and
     sergeiv@ (Dino, 2026-10-21: Cassie, him, David X. Williams and Sergei
     "for the testing purposes").
   - CC, per project (job.notify, set in the project's EMAILS dialog): the
     job's installers whose login has an email (unless unticked there), and
     the client contacts typed for that project.
   Photos are read back from storage and attached; mail.sendMail keeps what
   fits the sender. Never throws: the claim is saved whatever happens. */
const P = require("./app");
const J = require("./jobs");
const MAIL = require("./mail");
const INV = require("./invite");

const NOTIFY_DEFAULT = ["cassieh@ledconnection.com", "dinod@ledconnection.com", "davidw@ledconnection.com", "sergeiv@ledconnection.com"];
const NOTIFY_PATH = "system/notify.json";
const RE_EMAIL = /^[^\s@<>",;()]+@[^\s@<>",;()]+\.[a-z]{2,}$/i;
const RE_LC = /@ledconnection\.com$/i;
function defaultList() {
  const env = (process.env.INSTALLER_NOTIFY_TO || "").split(",").map(x => x.trim()).filter(Boolean);
  return env.length ? env : NOTIFY_DEFAULT;
}
/* LED Connection's list: -> { to, at?, by?, saved } */
async function lcList() {
  const r = await P.store().get(NOTIFY_PATH).catch(() => null);
  if (r && Array.isArray(r.data.to) && r.data.to.length) return { to: r.data.to, at: r.data.at, by: r.data.by, saved: true };
  return { to: defaultList(), saved: false };
}
/* Check a new LED Connection list: 1-20 addresses, all @ledconnection.com. */
function cleanLcList(list) {
  if (!Array.isArray(list)) throw new P.ApiError(400, "to must be a list of email addresses.");
  const out = [...new Set(list.map(x => String(x || "").trim().toLowerCase()).filter(Boolean))];
  if (!out.length) throw new P.ApiError(400, "Keep at least one LED Connection address.");
  if (out.length > 20) throw new P.ApiError(400, "At most 20 addresses.");
  const bad = out.find(a => !RE_EMAIL.test(a) || !RE_LC.test(a));
  if (bad) throw new P.ApiError(400, "\"" + bad + "\" is not an @ledconnection.com address. Installers and the client are set per project.");
  return out;
}
/* A project's own recipients, as saved on the job:
   { installersOff: [username], client: [{ name, email }] }. Installers are
   on unless unticked, so one added to the job later hears too. */
function cleanJobNotify(n, job) {
  if (!n || typeof n !== "object") throw new P.ApiError(400, "notify must be an object.");
  const off = Array.isArray(n.installersOff) ? [...new Set(n.installersOff.map(P.normUser))] : [];
  const stray = off.find(u => !(job.installers || []).includes(u));
  if (stray) throw new P.ApiError(400, "\"" + stray + "\" is not an installer on this job.");
  const client = Array.isArray(n.client) ? n.client : [];
  if (client.length > 10) throw new P.ApiError(400, "At most 10 client contacts.");
  const out = { installersOff: off, client: client.map(c => ({ name: String((c && c.name) || "").trim().slice(0, 80), email: String((c && c.email) || "").trim().toLowerCase() })) };
  const bad = out.client.find(c => !RE_EMAIL.test(c.email));
  if (bad) throw new P.ApiError(400, "\"" + (bad.email || bad.name || "(blank)") + "\" is not an email address.");
  return out;
}
/* Who gets this job's claim email. -> { to, cc, installers: [{ username, name, email }], client, skipped: [username] } */
async function recipients(job) {
  const to = (await lcList()).to;
  const n = job.notify || {};
  const on = (job.installers || []).filter(u => !(n.installersOff || []).includes(u));
  const installers = [], skipped = [];
  for (const u of on) {
    const rec = await P.store().get(P.paths.user(u)).catch(() => null);
    if (rec && !rec.data.disabled && RE_EMAIL.test(rec.data.email || "")) installers.push({ username: u, name: rec.data.name || u, email: rec.data.email.toLowerCase() });
    else skipped.push(u);
  }
  const client = (n.client || []).filter(c => RE_EMAIL.test(c.email));
  const seen = new Set(to.map(a => a.toLowerCase()));
  const cc = installers.map(i => i.email).concat(client.map(c => c.email)).filter(a => !seen.has(a) && seen.add(a));
  return { to, cc, installers, client, skipped };
}
const esc = MAIL.esc;

/* Per product: expected from the site, what the installer counted, and what
   is missing: short = expected - received (when received was counted). */
function lineFacts(l) {
  const short = l.received == null ? null : Math.max(0, l.expected - l.received);
  return Object.assign({}, l, { short });
}

function claimEmail(c) {
  const subject = "[" + c.ref + "] Material claim: " + c.kindLabel + " - " + c.jobName;
  const lines = c.lines.map(lineFacts);
  const cell = 'style="padding:5px 8px;border:1px solid #d9dde5"';
  const head = 'style="padding:5px 8px;border:1px solid #d9dde5;background:#f3f4f7;text-align:left"';
  const num = v => (v == null ? "-" : String(v));
  const table = !lines.length ? "" :
    '<tr><td style="padding:12px 0 0"><table cellpadding="0" cellspacing="0" style="border-collapse:collapse;font-size:13px">' +
    '<tr><th ' + head + '>Product</th><th ' + head + '>Part no.</th><th ' + head + '>Tags</th><th ' + head + '>Expected</th><th ' + head + '>Received</th>' +
    '<th ' + head + '>Missing</th><th ' + head + '>Damaged</th></tr>' +
    lines.map(l => '<tr><td ' + cell + '>' + esc(l.name) + '</td><td ' + cell + '>' + esc(l.pn || l.sku || "-") + '</td><td ' + cell + '>' + esc((l.tags || []).join(", ") || "-") + '</td>' +
      '<td ' + cell + '>' + num(l.expected) + '</td><td ' + cell + '>' + num(l.received) + '</td>' +
      '<td ' + cell + (l.short ? ' bgcolor="#fde8e8"' : "") + '><b>' + num(l.short) + '</b></td>' +
      '<td ' + cell + (l.damaged ? ' bgcolor="#fde8e8"' : "") + '><b>' + num(l.damaged) + '</b></td></tr>').join("") +
    '</table></td></tr>';
  const missing = lines.reduce((s, l) => s + (l.short || 0), 0), damaged = lines.reduce((s, l) => s + (l.damaged || 0), 0);
  const rows = [
    ["Job", c.jobName + (c.address ? ", " + c.address : "")],
    ["Problem", c.kindLabel],
    ["Missing", missing ? missing + " (see the table)" : "none counted"],
    ["Damaged", damaged ? damaged + " (see the table)" : "none"],
    ["Photos", !c.photoCount ? "none" : c.attached === c.photoCount ? c.photoCount + " (attached)" :
      c.photoCount + " (" + (c.attached ? c.attached + " attached, the rest are" : "too large to attach, they are") + " on the job page)"],
    ["Reported by", c.by + (c.company ? " (" + c.company + ")" : "") + (c.phone ? ", " + c.phone : "") + ", " + c.when]
  ];
  const html =
    '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="font-family:Segoe UI,Arial,sans-serif;font-size:14px;color:#1f2430">' +
    '<tr><td style="padding:0 0 10px;font-size:18px;font-weight:700;color:#b45309">Material claim ' + esc(c.ref) + '</td></tr>' +
    rows.map(r => '<tr><td style="padding:3px 0"><b>' + esc(r[0]) + ':</b> ' + esc(r[1]) + '</td></tr>').join("") +
    table +
    (c.note ? '<tr><td style="padding:12px 0 0"><b>What happened:</b><br>' + esc(c.note).replace(/\n/g, "<br>") + '</td></tr>' : "") +
    '<tr><td style="padding:16px 0 0"><a href="' + esc(c.link) + '" style="color:#f37021;font-weight:700">Open the job in the Installer App</a></td></tr></table>';
  return { subject, html };
}

/* -> { sent, queued?, local?, to, attached, reason? } */
async function notifyClaim(req, id, job, site, claim, user, partOf) {
  let to = defaultList(), cc = [];
  try {
    ({ to, cc } = await recipients(job));
    const attachments = [];
    let room = MAIL.ATTACH_BUDGET;
    for (const [i, name] of (claim.photos || []).entries()) {
      const got = await P.store().getBytes(J.paths.photo(id, name)).catch(() => null);
      if (!got || got.buf.length > room) continue;
      room -= got.buf.length;
      attachments.push({ name: claim.ref + "-photo-" + (i + 1) + ".jpg", contentType: "image/jpeg", bytes: got.buf });
    }
    const tagsOf = Object.fromEntries(site.bom.map(b => [b.key, b.tags]));
    const mail = claimEmail({
      ref: claim.ref, kindLabel: claim.kindLabel, note: claim.note,
      jobName: job.name || id, address: job.address || site.project.address || "",
      lines: claim.lines.map(l => Object.assign({ tags: tagsOf[l.key] || [], pn: partOf(l.sku) }, l)),
      photoCount: (claim.photos || []).length, attached: attachments.length,
      by: user.name || user.username, company: user.company || "", phone: user.phone || "",
      when: new Date(claim.at).toUTCString(),
      link: INV.baseUrl(req) + "/job.html?id=" + encodeURIComponent(id)
    });
    const r = await MAIL.sendMail({ to, cc, subject: mail.subject, html: mail.html, attachments });
    const out = r.sent ? { sent: true, queued: !!r.queued, local: !!r.local, to, cc, attached: attachments.length }
                       : { sent: false, reason: r.reason, to, cc, attached: 0 };
    await P.audit(req, user.username, "claim.notify", "job:" + id, { ref: claim.ref, to, cc, sent: out.sent, queued: out.queued, attached: out.attached });
    return out;
  } catch (e) {
    console.error("[claimmail] " + e.message);
    return { sent: false, reason: "The email could not be sent.", to, cc, attached: 0 };
  }
}

module.exports = { notifyClaim, claimEmail, lcList, cleanLcList, cleanJobNotify, recipients, NOTIFY_PATH };
