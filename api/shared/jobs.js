/* LC Installer App - jobs: one installation of one site, a customer-portal
   project or a site uploaded into this app (sites/, api/sites).

   Storage (installer-app container, docs/storage.md):
     jobs/{id}.json                    the job: which portal project, who installs it, submitted?
     jobs/{id}/material.json           the material check: counts, then the installer's sign-off
     jobs/{id}/parts.json              design label -> UL-listed LC part number (LC admins)
     jobs/{id}/claims/{ref}.json       a material claim (short, damaged, wrong)
     jobs/{id}/pins/{pinId}.json       one installed head: who, when, note, photos
     jobs/{id}/photos/{16 hex}.jpg     photos for claims and pins
   A job's id is the portal project's id, so there is one job per site.

   Who: LED Connection admins see and manage every job. An installer sees
   only jobs that name them; anything else answers 404, as in the portal. */
const P = require("./app");
const SITE = require("./site");
const { A, ApiError } = P;

/* Every job record carries `v`, the shape it was written in (docs/storage.md).
   Bump it when a record's shape changes, and teach the readers the old
   shape, so stored jobs are migrated on purpose rather than misread. */
const SCHEMA = 1;

const RE_PROJECT = /^[A-Za-z0-9][A-Za-z0-9._-]{1,63}$/;
function normJob(id) {
  const s = String(id == null ? "" : id).trim();
  if (!RE_PROJECT.test(s)) throw new ApiError(400, "Job id must be the project id (2-64 characters: letters, digits, and . _ -).");
  return s;
}

const paths = {
  job: id => "jobs/" + id + ".json",
  material: id => "jobs/" + id + "/material.json",
  parts: id => "jobs/" + id + "/parts.json",
  claims: id => "jobs/" + id + "/claims/",
  claim: (id, ref) => "jobs/" + id + "/claims/" + ref + ".json",
  pins: id => "jobs/" + id + "/pins/",
  pin: (id, pin) => "jobs/" + id + "/pins/" + pin + ".json",
  flags: id => "jobs/" + id + "/flags/",
  flag: (id, ref) => "jobs/" + id + "/flags/" + ref + ".json",
  photos: id => "jobs/" + id + "/photos/",
  photo: (id, name) => "jobs/" + id + "/photos/" + name
};

const canSeeJob = (user, job) => A.isLc(user) || (Array.isArray(job.installers) && job.installers.includes(user.username));

/* -> { job, etag } or 404 for anyone who may not see it. */
async function requireJob(user, id) {
  const rec = await P.store().get(paths.job(id));
  if (!rec || !canSeeJob(user, rec.data)) throw new ApiError(404, "Job not found.");
  return { job: rec.data, etag: rec.etag };
}

async function requireSite(id) {
  const s = await SITE.site(id);
  if (!s) throw new ApiError(404, "No site for project \"" + id + "\" in this app or the customer portal.");
  return s;
}

/* Who an email went to is LED Connection's business: an installer sees only
   that it went out (and to how many), never the addresses. */
function forViewer(mail, user) {
  if (!mail || A.isLc(user)) return mail;
  const n = (mail.to || []).length + (mail.cc || []).length;
  return { sent: mail.sent, queued: !!mail.queued, local: !!mail.local, attached: mail.attached || 0, reason: mail.reason || null, at: mail.at, recipients: n, others: (mail.cc || []).length };
}
const withMail = (rec, user) => rec && rec.mail ? Object.assign({}, rec, { mail: forViewer(rec.mail, user) }) : rec;

/* A project's email settings as LC admins see them, every field filled
   (shapes in claimmail.js cleanJobNotify). */
function notifyOf(j) {
  const n = j.notify || {};
  return { lcOff: n.lcOff || [], lc: n.lc || [], installersOff: n.installersOff || [], installer: n.installer || [],
           client: n.client || [], installs: n.installs || "each" };
}
function publicJob(j, user) {
  const out = {
    id: j.id, name: j.name || j.id, address: j.address || "", installers: j.installers || [],
    created: j.created, submitted: withMail(j.submitted || null, user),
    accepted: withMail(j.accepted || null, user),
    sentBack: j.sentBack && j.sentBack.length ? withMail(Object.assign({}, j.sentBack[j.sentBack.length - 1], { submitted: undefined }), user) : null
  };
  if (A.isLc(user)) out.notify = notifyOf(j);
  else delete out.installers;
  return out;
}

/* Where an installer calls or writes when something is missing. App
   settings, so the office can change them without a deploy. */
function contact() {
  return {
    company: "LED Connection",
    phone: process.env.INSTALLER_CONTACT_PHONE || "702.847.7680",
    email: process.env.INSTALLER_CONTACT_EMAIL || "dinod@ledconnection.com"
  };
}

module.exports = { notifyOf, SCHEMA, normJob, paths, canSeeJob, requireJob, requireSite, publicJob, contact, forViewer, withMail };
