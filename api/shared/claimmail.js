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
/* A project's own recipients, as saved on the job (Dino, 2026-10-21: three
   sets, each with an x and an add):
   { lcOff: [email], lc: [{ name, email }],          LED Connection
     installersOff: [username], installer: [{ name, email }],   installers
     client: [{ name, email }], installs: "each" | "off" }
   lcOff takes people off the home page's list for THIS project only; lc adds
   @ledconnection.com people for it. Installer logins are on unless taken
   off, so one added to the job later hears too; installer adds any email
   (a crew office, a foreman without a login). A project always keeps at
   least one LED Connection address: it hears about everything. */
function cleanContacts(list, what, lcOnly) {
  const arr = Array.isArray(list) ? list : [];
  if (arr.length > 10) throw new P.ApiError(400, "At most 10 " + what + " contacts.");
  const seen = new Set(), out = [];
  for (const c of arr) {
    const one = { name: String((c && c.name) || "").trim().slice(0, 80), email: String((c && c.email) || "").trim().toLowerCase() };
    if (!RE_EMAIL.test(one.email)) throw new P.ApiError(400, "\"" + (one.email || one.name || "(blank)") + "\" is not an email address.");
    if (lcOnly && !RE_LC.test(one.email)) throw new P.ApiError(400, "\"" + one.email + "\" is not an @ledconnection.com address. Put it under Installers or Client.");
    if (!seen.has(one.email)) { seen.add(one.email); out.push(one); }
  }
  return out;
}
function cleanJobNotify(n, job, lcDefault) {
  if (!n || typeof n !== "object") throw new P.ApiError(400, "notify must be an object.");
  const off = Array.isArray(n.installersOff) ? [...new Set(n.installersOff.map(P.normUser))] : [];
  const stray = off.find(u => !(job.installers || []).includes(u));
  if (stray) throw new P.ApiError(400, "\"" + stray + "\" is not an installer on this job.");
  if (n.installs !== undefined && n.installs !== "each" && n.installs !== "off") throw new P.ApiError(400, "installs must be \"each\" or \"off\".");
  const lcOff = Array.isArray(n.lcOff) ? [...new Set(n.lcOff.map(a => String(a || "").trim().toLowerCase()).filter(Boolean))] : [];
  const out = { lcOff, lc: cleanContacts(n.lc, "LED Connection", true), installersOff: off,
                installer: cleanContacts(n.installer, "installer"), client: cleanContacts(n.client, "client"),
                installs: n.installs === "off" ? "off" : "each" };
  if (lcDefault && !lcTo(lcDefault, out).length) throw new P.ApiError(400, "Keep at least one LED Connection address on the project.");
  return out;
}
/* The LED Connection addresses of a project: the home page's list less the
   ones taken off it, plus its own. */
function lcTo(list, n) {
  const off = new Set(((n && n.lcOff) || []).map(a => a.toLowerCase()));
  const to = list.map(a => a.toLowerCase()).filter(a => !off.has(a));
  for (const c of (n && n.lc) || []) if (!to.includes(c.email)) to.push(c.email);
  return to;
}
/* Who gets this job's emails. -> { to, cc, installers: [{ username, name, email }], client, skipped: [username] } */
async function recipients(job) {
  const list = (await lcList()).to;
  const n = job.notify || {};
  let to = lcTo(list, n);
  if (!to.length) to = list;   /* the home list changed under a project: LED Connection still hears */
  const on = (job.installers || []).filter(u => !(n.installersOff || []).includes(u));
  const installers = [], skipped = [];
  for (const u of on) {
    const rec = await P.store().get(P.paths.user(u)).catch(() => null);
    if (rec && !rec.data.disabled && RE_EMAIL.test(rec.data.email || "")) installers.push({ username: u, name: rec.data.name || u, email: rec.data.email.toLowerCase() });
    else skipped.push(u);
  }
  const extra = (n.installer || []).filter(c => RE_EMAIL.test(c.email));
  const client = (n.client || []).filter(c => RE_EMAIL.test(c.email));
  const seen = new Set(to);
  const cc = installers.map(i => i.email).concat(extra.map(c => c.email), client.map(c => c.email)).filter(a => !seen.has(a) && seen.add(a));
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

/* ── The other emails (Dino, 2026-10-21): "when I do the sign off ... and
   everything that I do install, if someone is reporting a problem or
   flagging something, I want that to be reaching out to all of these
   emails". Same recipients as a claim (LED Connection's list, CC the
   job's installers and client), same way out, same rule: the record is
   saved first and a failed email never fails it. ─────────────────────── */
async function photoAttachments(id, prefix, names) {
  const out = [];
  let room = MAIL.ATTACH_BUDGET;
  for (const [i, name] of (names || []).entries()) {
    const got = await P.store().getBytes(J.paths.photo(id, name)).catch(() => null);
    if (!got || got.buf.length > room) continue;
    room -= got.buf.length;
    out.push({ name: prefix + "-photo-" + (i + 1) + ".jpg", contentType: "image/jpeg", bytes: got.buf });
  }
  return out;
}
const CELL = 'style="padding:5px 8px;border:1px solid #d9dde5"';
const HEAD = 'style="padding:5px 8px;border:1px solid #d9dde5;background:#f3f4f7;text-align:left"';
function page(title, color, rows, table, note, link, linkText, button) {
  return '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="font-family:Segoe UI,Arial,sans-serif;font-size:14px;color:#1f2430">' +
    '<tr><td style="padding:0 0 10px;font-size:18px;font-weight:700;color:' + color + '">' + esc(title) + '</td></tr>' +
    rows.filter(Boolean).map(r => '<tr><td style="padding:3px 0"><b>' + esc(r[0]) + ':</b> ' + esc(r[1]) + '</td></tr>').join("") +
    (table ? '<tr><td style="padding:12px 0 0">' + table + '</td></tr>' : "") +
    (note ? '<tr><td style="padding:12px 0 0"><b>' + esc(button && button.noteLabel || "What happened") + ':</b><br>' + esc(note).replace(/\n/g, "<br>") + '</td></tr>' : "") +
    (button && button.href ? '<tr><td style="padding:20px 0 4px"><a href="' + esc(button.href) + '" style="display:inline-block;padding:14px 26px;background:#f37021;color:#0a0e1a;' +
      'font-weight:800;letter-spacing:.06em;text-decoration:none;border-radius:8px">' + esc(button.text) + '</a></td></tr>' +
      (button.hint ? '<tr><td style="padding:4px 0 0;font-size:12px;color:#6b7280">' + esc(button.hint) + '</td></tr>' : "") : "") +
    '<tr><td style="padding:16px 0 0"><a href="' + esc(link) + '" style="color:#f37021;font-weight:700">' + esc(linkText) + '</a></td></tr></table>';
}
const byLine = u => (u.name || u.username) + (u.company ? " (" + u.company + ")" : "") + (u.phone ? ", " + u.phone : "");
async function deliver(req, id, job, user, msg, action, detail) {
  let to = defaultList(), cc = [];
  try {
    ({ to, cc } = await recipients(job));
    const r = await MAIL.sendMail(Object.assign({ to, cc }, msg));
    const out = r.sent ? { sent: true, queued: !!r.queued, local: !!r.local, to, cc, attached: (msg.attachments || []).length }
                       : { sent: false, reason: r.reason, to, cc, attached: 0 };
    await P.audit(req, user.username, action, "job:" + id, Object.assign({ to, cc, sent: out.sent, queued: out.queued }, detail));
    return out;
  } catch (e) {
    console.error("[claimmail] " + action + ": " + e.message);
    return { sent: false, reason: "The email could not be sent.", to, cc, attached: 0 };
  }
}
const mailRecord = n => ({ sent: n.sent, queued: !!n.queued, to: n.to, cc: n.cc || [], attached: n.attached || 0, at: new Date().toISOString(), reason: n.reason || null });

/* Material signed off: what arrived against the design, line by line. */
async function notifySignoff(req, id, job, site, approved, user, partOf) {
  const jobName = job.name || id, tagsOf = Object.fromEntries(site.bom.map(b => [b.key, b.tags]));
  const bad = v => v ? ' bgcolor="#fde8e8"' : "";
  const table = '<table cellpadding="0" cellspacing="0" style="border-collapse:collapse;font-size:13px"><tr><th ' + HEAD + '>Product</th><th ' + HEAD + '>Part no.</th><th ' + HEAD + '>Tags</th><th ' + HEAD +
    '>Expected</th><th ' + HEAD + '>Received</th><th ' + HEAD + '>Short</th><th ' + HEAD + '>Over</th><th ' + HEAD + '>Damaged</th></tr>' +
    approved.summary.map(l => '<tr><td ' + CELL + '>' + esc(l.name) + '</td><td ' + CELL + '>' + esc(partOf(l.sku) || l.sku || "-") + '</td><td ' + CELL + '>' + esc((tagsOf[l.key] || []).join(", ") || "-") +
      '</td><td ' + CELL + '>' + l.expected + '</td><td ' + CELL + '>' + l.received + '</td><td ' + CELL + bad(l.short) + '><b>' + l.short + '</b></td><td ' + CELL + '>' + l.over +
      '</td><td ' + CELL + bad(l.damaged) + '><b>' + l.damaged + '</b></td></tr>').join("") + '</table>';
  const clean = !approved.short && !approved.damaged;
  const subject = "[" + jobName + "] Material signed off: " + (clean ? "everything received" : [approved.short ? approved.short + " short" : "", approved.damaged ? approved.damaged + " damaged" : ""].filter(Boolean).join(", "));
  const html = page("Material signed off", clean ? "#15803d" : "#b45309", [
    ["Job", jobName + (job.address ? ", " + job.address : "")],
    ["Result", clean ? "Every product received as designed" : (approved.short ? approved.short + " short" : "") + (approved.short && approved.damaged ? ", " : "") + (approved.damaged ? approved.damaged + " damaged" : "")],
    approved.over ? ["Over", approved.over + " more than the design"] : null,
    ["Signed off by", byLine(user) + ", " + new Date(approved.at).toUTCString()],
    ["Next", clean ? "The install is unlocked." : "The install is unlocked; the shortage or damage needs a claim (REPORT A PROBLEM) if one was not filed."]
  ], table, "", INV.baseUrl(req) + "/job.html?id=" + encodeURIComponent(id), "Open the job in the Installer App");
  return deliver(req, id, job, user, { subject, html }, "material.notify", { short: approved.short, damaged: approved.damaged });
}

/* A problem flagged on one fixture during the install. */
const FLAG_KINDS = { pole: "Pole or arm damaged", power: "No power / wiring problem", access: "Cannot reach it (access, lift)",
                     fit: "Fixture does not fit the bracket or arm", other: "Other" };
async function notifyFlag(req, id, job, site, flag, user) {
  const jobName = job.name || id;
  const attachments = await photoAttachments(id, flag.ref, flag.photos);
  const subject = "[" + flag.ref + "] Install problem: " + flag.kindLabel + " - " + jobName;
  const html = page("Install problem " + flag.ref, "#b91c1c", [
    ["Job", jobName + (job.address ? ", " + job.address : "")],
    ["Problem", flag.kindLabel],
    ["Fixture", [flag.tag, flag.poleId ? "pole " + flag.poleId : "", "fixture " + flag.fid].filter(Boolean).join(" · ")],
    ["Product", (flag.product || "-") + (flag.partNo ? " (" + flag.partNo + ")" : "")],
    ["Photos", !flag.photos.length ? "none" : attachments.length === flag.photos.length ? flag.photos.length + " (attached)" : flag.photos.length + " (" + attachments.length + " attached, the rest are on the job page)"],
    ["Reported by", byLine(user) + ", " + new Date(flag.at).toUTCString()]
  ], "", flag.note, INV.baseUrl(req) + "/job.html?id=" + encodeURIComponent(id) + "#install", "Open the job in the Installer App");
  return deliver(req, id, job, user, { subject, html, attachments }, "flag.notify", { ref: flag.ref, attached: attachments.length });
}

/* One fixture saved as installed, its photo as the proof (Dino, 2026-10-21:
   "a notification for every fixture that is installed ... and the proof
   being uploaded a photo"). Off per project with job.notify.installs. */
async function notifyInstalled(req, id, job, rec, user, progress) {
  const jobName = job.name || id;
  const attachments = await photoAttachments(id, (rec.tag || "fixture") + "-" + rec.fid, rec.photos);
  const subject = "[" + jobName + "] Installed: " + [rec.tag, rec.poleId ? "pole " + rec.poleId : ""].filter(Boolean).join(" · ") + " (" + progress.done + " of " + progress.total + ")";
  const html = page("Fixture installed", "#15803d", [
    ["Job", jobName + (job.address ? ", " + job.address : "")],
    ["Fixture", [rec.tag, rec.poleId ? "pole " + rec.poleId : "", "fixture " + rec.fid].filter(Boolean).join(" · ")],
    ["Product", (rec.product || "-") + (rec.partNo ? " (" + rec.partNo + ")" : "")],
    rec.serial ? ["Serial / date code", rec.serial] : null,
    ["Proof", attachments.length ? attachments.length + " photo" + (attachments.length > 1 ? "s" : "") + " attached" : "photo on the job page"],
    ["Progress", progress.done + " of " + progress.total + " fixtures installed"],
    ["Installed by", byLine(user) + ", " + new Date(rec.at).toUTCString()]
  ], "", rec.note, INV.baseUrl(req) + "/job.html?id=" + encodeURIComponent(id) + "#install", "Open the job in the Installer App",
  rec.note ? { noteLabel: "Installer's note" } : null);
  return deliver(req, id, job, user, { subject, html, attachments }, "pin.notify", { pin: rec.pinId, tag: rec.tag, attached: attachments.length });
}

/* The installer submitted the job: every head saved as installed. This is
   the big one: it asks LED Connection to approve, with a button into the
   app (sign-in required, so a forwarded email cannot approve anything). */
async function notifySubmit(req, id, job, site, submitted, user, open) {
  const jobName = job.name || id;
  const review = INV.baseUrl(req) + "/job.html?id=" + encodeURIComponent(id) + "&review=1";
  const subject = "[" + jobName + "] Install complete: " + submitted.heads + " fixtures - approval needed";
  const html = page("Install complete: approval needed", "#b45309", [
    ["Job", jobName + (job.address ? ", " + job.address : "")],
    ["Installed", submitted.heads + " of " + submitted.heads + " fixtures, each with a photo"],
    ["Submitted by", byLine(user) + ", " + new Date(submitted.at).toUTCString()],
    open.claims || open.flags ? ["Still open", [open.claims ? open.claims + " material claim" + (open.claims > 1 ? "s" : "") : "", open.flags ? open.flags + " install problem" + (open.flags > 1 ? "s" : "") : ""].filter(Boolean).join(", ")] : ["Still open", "nothing"],
    ["Next", "LED Connection reviews the photos and approves the install, or sends it back with a reason."]
  ], "", "", review, "Or open the job in the Installer App",
  { href: review, text: "REVIEW AND APPROVE", hint: "Opens the job in the Installer App. Sign in with your LED Connection login, check the installed fixtures, then press APPROVE." });
  return deliver(req, id, job, user, { subject, html }, "submit.notify", { heads: submitted.heads });
}

/* LED Connection approved the install: the job is done. */
async function notifyAccepted(req, id, job, accepted, user) {
  const jobName = job.name || id;
  const subject = "[" + jobName + "] Install approved: " + (job.submitted ? job.submitted.heads + " fixtures" : "done");
  const html = page("Install approved", "#15803d", [
    ["Job", jobName + (job.address ? ", " + job.address : "")],
    job.submitted ? ["Installed", job.submitted.heads + " fixtures, submitted by " + (job.submitted.byName || job.submitted.by) + " on " + new Date(job.submitted.at).toUTCString()] : null,
    ["Approved by", byLine(user) + ", " + new Date(accepted.at).toUTCString()]
  ], "", accepted.note, INV.baseUrl(req) + "/job.html?id=" + encodeURIComponent(id) + "#install", "Open the job in the Installer App",
  accepted.note ? { noteLabel: "Note" } : null);
  return deliver(req, id, job, user, { subject, html }, "accept.notify", {});
}

/* LED Connection sent the install back: the job opens again for the installer. */
async function notifySentBack(req, id, job, back, user) {
  const jobName = job.name || id;
  const subject = "[" + jobName + "] Install sent back: " + back.reason.slice(0, 80);
  const html = page("Install sent back", "#b91c1c", [
    ["Job", jobName + (job.address ? ", " + job.address : "")],
    ["Sent back by", byLine(user) + ", " + new Date(back.at).toUTCString()],
    ["Next", "The job is open again: fix what is described below, then submit it again."]
  ], "", back.reason, INV.baseUrl(req) + "/job.html?id=" + encodeURIComponent(id) + "#install", "Open the job in the Installer App",
  { noteLabel: "What to fix" });
  return deliver(req, id, job, user, { subject, html }, "sendback.notify", {});
}

module.exports = { notifyClaim, claimEmail, lcList, cleanLcList, cleanJobNotify, lcTo, recipients, NOTIFY_PATH,
                   notifySignoff, notifyFlag, notifySubmit, notifyInstalled, notifyAccepted, notifySentBack, FLAG_KINDS, mailRecord };
