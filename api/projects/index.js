/* GET /api/projects - LED Connection admins only: every project in the
   customer portal, and every site uploaded into this app (sites/, source
   "installer"), with its job here if there is one. An uploaded site wins
   over a portal project with the same id, as in site.js.

   { projects: [{ id, name, address, customer, kind, installDate, heads, source,
                  job: null | { installers, materialApproved, pinsSaved, submitted, notify } }] }

   Read from the portal's container through the read-only portalStore,
   WHITELISTED like site.js: never the NetSuite number, notes or who
   uploaded what. Installers get 403: they see only the jobs that name them
   (GET /api/jobs), never the list of LED Connection's customers. */
const P = require("../shared/app");
const J = require("../shared/jobs");
const { portalStore } = require("../shared/store");

async function directChildren(store, prefix, all) {
  const names = (all || await store.list(prefix)).filter(n => n.endsWith(".json") && !n.slice(prefix.length).includes("/"));
  return (await Promise.all(names.map(n => store.get(n)))).filter(Boolean).map(r => r.data);
}

module.exports = P.handler(async ({ req, send }) => {
  await P.requireLc(req);
  const ps = portalStore();
  /* One listing gives both the project records and which of them really
     have a site file (projects/{id}/site.json), without reading the sites. */
  const names = await ps.list("projects/");
  const withSite = new Set(names.filter(n => /^projects\/[^/]+\/site\.json$/.test(n)).map(n => n.split("/")[1]));
  const [metas, customers, jobs, own] = await Promise.all([
    directChildren(ps, "projects/", names), directChildren(ps, "customers/"), P.loadAll("jobs/"), P.loadAll("sites/")
  ]);
  const ownIds = new Set(own.map(o => o.id));
  const custName = Object.fromEntries(customers.map(c => [c.id, c.name || c.id]));
  const jobOf = Object.fromEntries(jobs.map(j => [j.id, j]));

  async function jobFor(id) {
    const j = jobOf[id];
    if (!j) return null;
    const [mat, pins] = await Promise.all([P.store().get(J.paths.material(j.id)), P.store().list(J.paths.pins(j.id))]);
    return { installers: j.installers || [], materialApproved: !!(mat && mat.data.approved), pinsSaved: pins.length, submitted: j.submitted || null,
             notify: { installersOff: (j.notify && j.notify.installersOff) || [], client: (j.notify && j.notify.client) || [] } };
  }
  const fromPortal = metas.filter(m => !ownIds.has(m.id)).map(async m => {
    const site = m.site || {};
    return {
      id: m.id, name: m.name || m.id, address: m.address || "",
      customer: m.customerId ? (custName[m.customerId] || m.customerId) : "",
      kind: site.kind || "", installDate: m.installDate || "",
      heads: typeof site.fixtures === "number" ? site.fixtures : null,
      hasSite: withSite.has(m.id), source: "portal",
      job: await jobFor(m.id)
    };
  });
  const fromHere = own.map(async o => ({
    id: o.id, name: o.name || o.id, address: o.address || "", customer: o.customer || "",
    kind: o.kind || "", installDate: o.installDate || "",
    heads: typeof o.fixtures === "number" ? o.fixtures : null,
    hasSite: true, source: "installer", uploaded: o.uploaded || null,
    job: await jobFor(o.id)
  }));
  const projects = await Promise.all(fromPortal.concat(fromHere));
  projects.sort((a, b) => a.customer.localeCompare(b.customer) || a.name.localeCompare(b.name));
  send(200, { projects });
});
