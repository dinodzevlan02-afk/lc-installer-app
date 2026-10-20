/* GET /api/projects - LED Connection admins only: every project in the
   customer portal, with its job here if there is one.

   { projects: [{ id, name, address, customer, kind, installDate, heads,
                  job: null | { installers, materialApproved, pinsSaved, submitted } }] }

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
  const [metas, customers, jobs] = await Promise.all([
    directChildren(ps, "projects/", names), directChildren(ps, "customers/"), P.loadAll("jobs/")
  ]);
  const custName = Object.fromEntries(customers.map(c => [c.id, c.name || c.id]));
  const jobOf = Object.fromEntries(jobs.map(j => [j.id, j]));

  const projects = await Promise.all(metas.map(async m => {
    const j = jobOf[m.id];
    let job = null;
    if (j) {
      const [mat, pins] = await Promise.all([P.store().get(J.paths.material(j.id)), P.store().list(J.paths.pins(j.id))]);
      job = { installers: j.installers || [], materialApproved: !!(mat && mat.data.approved), pinsSaved: pins.length, submitted: j.submitted || null };
    }
    const site = m.site || {};
    return {
      id: m.id, name: m.name || m.id, address: m.address || "",
      customer: m.customerId ? (custName[m.customerId] || m.customerId) : "",
      kind: site.kind || "", installDate: m.installDate || "",
      heads: typeof site.fixtures === "number" ? site.fixtures : null,
      hasSite: withSite.has(m.id),
      job
    };
  }));
  projects.sort((a, b) => a.customer.localeCompare(b.customer) || a.name.localeCompare(b.name));
  send(200, { projects });
});
