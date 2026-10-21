/* Installer companies: the crews LED Connection hires (Dino, 2026-10-21:
   "first a customer, then people inside that customer that will be
   installers, and we allocate them to a site as we go"). The customer
   portal's Customers, for installers. LED Connection admins only.

   GET   /api/companies        every company, with how many people and jobs.
   POST  /api/companies        { name, phone?, email?, notes? }
   PATCH /api/companies/{id}   { name?, phone?, email?, notes?, status? }
                               status "suspended" signs every login of the
                               company out on its next request (app.js
                               requireSession); "active" lets them back in.
   A person belongs to one company (users.companyId). What an installer sees
   is still decided per job: only jobs that name them (api/jobs). */
const P = require("../shared/app");
const { ApiError } = P;

const STATUSES = ["active", "suspended"];
const RE_EMAIL = /^[^\s@<>"]+@[^\s@<>"]+\.[^\s@<>"]+$/;
const RE_PHONE = /^[0-9+().\- ]{7,25}$/;
function contact(body, c) {
  if (body.phone !== undefined) {
    const v = P.text(body.phone, 25, "Phone");
    if (v && !RE_PHONE.test(v)) throw new ApiError(400, "That phone number does not look right.");
    c.phone = v;
  }
  if (body.email !== undefined) {
    const v = P.text(body.email, 200, "Email").toLowerCase();
    if (v && !RE_EMAIL.test(v)) throw new ApiError(400, "That email address does not look right.");
    c.email = v;
  }
  if (body.notes !== undefined) c.notes = P.text(body.notes, 1000, "Notes");
}

module.exports = P.handler(async ({ req, method, body, params, send }) => {
  const { user } = await P.requireLc(req);
  const id = params.id ? P.normCompany(params.id) : null;

  if (method === "GET") {
    const [companies, users, jobs] = await Promise.all([P.loadAll("companies/"), P.loadAll("users/"), P.loadAll("jobs/")]);
    const out = companies.map(c => {
      const people = users.filter(u => u.companyId === c.id).map(u => u.username);
      return Object.assign({}, c, { people: people.length,
        jobs: jobs.filter(j => (j.installers || []).some(u => people.includes(u))).length });
    }).sort((a, b) => a.name.localeCompare(b.name));
    if (id) { const one = out.find(c => c.id === id); if (!one) throw new ApiError(404, "Company not found."); return send(200, one); }
    return send(200, { companies: out });
  }

  if (method === "POST") {
    const name = P.text(body.name, 100, "Name");
    if (!name) throw new ApiError(400, "Company name is required.");
    const cid = P.normCompany(body.id || P.slugify(name));
    const rec = { id: cid, name, status: "active", phone: "", email: "", notes: "", created: new Date().toISOString(), createdBy: user.username };
    contact(body, rec);
    try { await P.store().put(P.paths.company(cid), rec, { ifNoneMatch: "*" }); }
    catch (e) { if (e.code === "CONFLICT") throw new ApiError(409, "There is already a company \"" + name + "\"."); throw e; }
    await P.audit(req, user.username, "company.create", "company:" + cid, { name });
    return send(201, Object.assign({}, rec, { people: 0, jobs: 0 }));
  }

  if (method === "PATCH") {
    if (!id) throw new ApiError(400, "Which company?");
    const cur = await P.store().get(P.paths.company(id));
    if (!cur) throw new ApiError(404, "Company not found.");
    const c = cur.data, before = Object.assign({}, c);
    if (body.name !== undefined) { const n = P.text(body.name, 100, "Name"); if (!n) throw new ApiError(400, "Name cannot be empty."); c.name = n; }
    contact(body, c);
    if (body.status !== undefined) {
      if (!STATUSES.includes(body.status)) throw new ApiError(400, "Status must be active or suspended.");
      c.status = body.status;
    }
    Object.assign(c, { updated: new Date().toISOString(), updatedBy: user.username });
    await P.store().put(P.paths.company(id), c, { ifMatch: cur.etag });
    /* People carry the company name too (emails, pin records): keep it in step. */
    if (c.name !== before.name) {
      for (const u of (await P.loadAll("users/")).filter(u => u.companyId === id)) {
        const r = await P.store().get(P.paths.user(u.username));
        if (r) { r.data.company = c.name; await P.store().put(P.paths.user(u.username), r.data, { ifMatch: r.etag }).catch(() => {}); }
      }
    }
    const changed = Object.keys(c).filter(k => !["updated", "updatedBy"].includes(k) && c[k] !== before[k]);
    await P.audit(req, user.username, "company.update", "company:" + id, { changed, status: c.status });
    return send(200, c);
  }

  throw new ApiError(405, "Method not allowed.");
});
