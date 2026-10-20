/* Jobs.

   GET   /api/jobs            LC admin: every job. Installer: the jobs that name them.
                              Each with progress: material signed off?, heads installed / total.
   GET   /api/jobs/{id}       One job, everything the job page needs:
                              { job, site, material, pins, claims, contact }
   POST  /api/jobs            LC admin: { projectId, installers: [username] }
                              Opens a job on a customer-portal project (Walmart 2741 first).
   PATCH /api/jobs/{id}       LC admin: { installers?, reopenMaterial? }
                              reopenMaterial lets the installer count again. */
const P = require("../shared/app");
const J = require("../shared/jobs");
const PARTS = require("../shared/parts");
const GUIDES = require("../shared/guides");
const { A, ApiError } = P;

/* Installer logins only: an LC admin already sees every job, so naming one
   here would mean nothing. A switched-off login may stay on a job (it is
   already locked out), but cannot be newly added. */
async function cleanInstallers(list, current) {
  if (!Array.isArray(list)) throw new ApiError(400, "installers must be a list of usernames.");
  const out = [];
  for (const u of [...new Set(list.map(P.normUser))]) {
    const rec = await P.store().get(P.paths.user(u));
    if (!rec) throw new ApiError(400, "No login \"" + u + "\".");
    if (rec.data.role !== "installer") throw new ApiError(400, "\"" + u + "\" is not an installer login.");
    if (rec.data.disabled && !(current || []).includes(u)) throw new ApiError(400, "\"" + u + "\" is switched off.");
    out.push(u);
  }
  return out;
}

async function progress(id) {
  const [mat, pins] = await Promise.all([P.store().get(J.paths.material(id)), P.store().list(J.paths.pins(id))]);
  return { materialApproved: !!(mat && mat.data.approved), pinsSaved: pins.length };
}

module.exports = P.handler(async ({ req, method, body, params, send }) => {
  const { user } = await P.requireSession(req);
  const id = params.id ? J.normJob(params.id) : null;

  if (method === "GET" && !id) {
    const all = (await P.loadAll("jobs/")).filter(j => J.canSeeJob(user, j));
    all.sort((a, b) => String(a.name).localeCompare(String(b.name)));
    const jobs = await Promise.all(all.map(async j => {
      const out = J.publicJob(j, user);
      const s = await J.requireSite(j.id).catch(() => null);
      out.heads = s ? s.pins.filter(p => !p.off && p.product).length : null;
      return Object.assign(out, await progress(j.id));
    }));
    return send(200, { jobs });
  }

  if (method === "GET") {
    const { job } = await J.requireJob(user, id);
    let site = await J.requireSite(id);
    const [mat, pinNames, claimNames] = await Promise.all([
      P.store().get(J.paths.material(id)),
      P.store().list(J.paths.pins(id)),
      P.store().list(J.paths.claims(id))
    ]);
    const pins = {};
    (await Promise.all(pinNames.map(n => P.store().get(n)))).forEach(r => { if (r) pins[r.data.pinId] = r.data; });
    const claims = (await Promise.all(claimNames.map(n => P.store().get(n)))).filter(Boolean).map(r => r.data)
      .sort((a, b) => String(b.at).localeCompare(String(a.at)));
    /* UL-listed part numbers saved for this job, on each material line and
       pin. The cached site is shared, so it is copied, never written to. */
    const partsRec = await P.store().get(J.paths.parts(id));
    const saved = (partsRec && partsRec.data.byLabel) || {};
    const pnOf = sku => (saved[sku] && saved[sku].pn) || PARTS.DECIDED[sku] || null;
    /* The installation guide follows the bracket in the part number. */
    const describe = pn => { const c = PARTS.check(pn); return c.ok ? { pn: c.pn, checked: c.checked, parts: c.parts || null, short: c.short || null, guide: GUIDES.forPart(c) } : null; };
    /* Once a checked part number is saved, the product's name follows it
       ("Optimus 300W · T5S"), so name, box and part number agree; the
       design label's own name ("Optimus XL1 · TY5SW") stays on the label. */
    const bom = site.bom.map(b => {
      const pn = pnOf(b.sku) ? describe(pnOf(b.sku)) : null;
      return Object.assign({}, b, { partNo: pn }, pn && pn.short ? { name: pn.short, designName: b.name } : {});
    });
    const nameOf = Object.fromEntries(bom.map(b => [b.key, b.name]));
    site = Object.assign({}, site, {
      bom,
      pins: site.pins.map(p => p.product && pnOf(p.product.sku)
        ? Object.assign({}, p, { partNo: pnOf(p.product.sku), productName: nameOf[p.productKey] || p.productName }) : p)
    });
    /* LED Connection also gets the table to edit: the saved number, or the
       decided one that applies until a different number is saved. */
    const parts = !A.isLc(user) ? undefined : site.bom.map(b => ({
      label: b.sku, name: b.name, tags: b.tags, qty: b.qty,
      saved: saved[b.sku] || null,
      decided: !saved[b.sku] && PARTS.DECIDED[b.sku] ? PARTS.DECIDED[b.sku] : null
    }));
    return send(200, {
      job: J.publicJob(job, user), site, parts,
      material: mat ? mat.data : { lines: {}, approved: null },
      materialEtag: mat ? mat.etag : null,
      pins, claims, contact: J.contact()
    });
  }

  if (!A.isLc(user)) throw new ApiError(403, "Only LED Connection opens and assigns jobs.");

  if (method === "POST") {
    const pid = J.normJob(body.projectId);
    const site = await J.requireSite(pid);
    const job = {
      v: J.SCHEMA, id: pid, name: site.project.name || pid, address: site.project.address || "",
      installers: await cleanInstallers(body.installers || []),
      created: new Date().toISOString(), createdBy: user.username, submitted: null
    };
    try { await P.store().put(J.paths.job(pid), job, { ifNoneMatch: "*" }); }
    catch (e) { if (e.code === "CONFLICT") throw new ApiError(409, "There is already a job for " + pid + "."); throw e; }
    await P.audit(req, user.username, "job.create", "job:" + pid, { installers: job.installers });
    return send(201, { job: J.publicJob(job, user) });
  }

  if (method === "PATCH") {
    if (!id) throw new ApiError(400, "Which job?");
    const { job, etag } = await J.requireJob(user, id);
    const logged = {};
    /* Changing who installs: whoever is taken off loses the job on their
       next request (404); their saved counts, claims and pins stay, with
       their name on them. The audit keeps who was added and removed. */
    if (body.installers !== undefined) {
      const before = job.installers || [];
      job.installers = await cleanInstallers(body.installers, before);
      logged.added = job.installers.filter(u => !before.includes(u));
      logged.removed = before.filter(u => !job.installers.includes(u));
    }
    if (body.reopenMaterial) {
      const mat = await P.store().get(J.paths.material(id));
      if (mat && mat.data.approved) {
        mat.data.history = (mat.data.history || []).concat([{ approved: mat.data.approved, reopenedAt: new Date().toISOString(), reopenedBy: user.username }]);
        mat.data.approved = null;
        await P.store().put(J.paths.material(id), mat.data, { ifMatch: mat.etag });
        logged.reopenMaterial = true;
      }
    }
    job.updated = new Date().toISOString(); job.updatedBy = user.username;
    await P.store().put(J.paths.job(id), job, { ifMatch: etag });
    await P.audit(req, user.username, "job.update", "job:" + id, logged);
    return send(200, { job: J.publicJob(job, user) });
  }

  throw new ApiError(405, "Method not allowed.");
});
