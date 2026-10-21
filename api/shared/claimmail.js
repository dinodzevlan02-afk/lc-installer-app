/* The email about a material claim (Dino, 2026-10-21): to Cassie and Dino,
   "with the photo inside", the note, and the quantities that are missing.

   Who hears is set here, on the server, so no page can redirect it:
   INSTALLER_NOTIFY_TO (comma-separated), else the pair the customer portal
   uses for tickets (cassieh@ + dinod@). Photos are read back from storage
   and attached; mail.sendMail keeps what fits the sender. Never throws: the
   claim is saved whatever happens to the email. */
const P = require("./app");
const J = require("./jobs");
const MAIL = require("./mail");
const INV = require("./invite");

const NOTIFY_DEFAULT = ["cassieh@ledconnection.com", "dinod@ledconnection.com"];
function notifyList() {
  const env = (process.env.INSTALLER_NOTIFY_TO || "").split(",").map(x => x.trim()).filter(Boolean);
  return env.length ? env : NOTIFY_DEFAULT;
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
  const to = notifyList();
  try {
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
    const r = await MAIL.sendMail({ to, subject: mail.subject, html: mail.html, attachments });
    const out = r.sent ? { sent: true, queued: !!r.queued, local: !!r.local, to, attached: attachments.length }
                       : { sent: false, reason: r.reason, to, attached: 0 };
    await P.audit(req, user.username, "claim.notify", "job:" + id, { ref: claim.ref, to, sent: out.sent, queued: out.queued, attached: out.attached });
    return out;
  } catch (e) {
    console.error("[claimmail] " + e.message);
    return { sent: false, reason: "The email could not be sent.", to, attached: 0 };
  }
}

module.exports = { notifyClaim, claimEmail, notifyList };
