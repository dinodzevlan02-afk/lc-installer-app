/* Sites kept in the installer app itself (not in the customer portal).

   GET  /api/sites          LC admin: every uploaded site, { sites: [meta] }
   PUT  /api/sites/{id}     LC admin: upload or replace a site file
                            (format "lc-site", built by tools/sites/build-site.js)

   Kroger 345 first (Dino, 2026-10-20: "written only in the installer app").
   A replaced site keeps its saved work: pin ids come from the dataset id and
   the audit row id (site.js pinKey), so the same rows land on the same pins.
   Installers never upload or list sites; they reach a site only through a
   job that names them. */
const P = require("../shared/app");
const SITE = require("../shared/site");
const FILE = require("../shared/sitefile");
const { ApiError } = P;

module.exports = P.handler(async ({ req, method, body, params, send }) => {
  const { user } = await P.requireLc(req);

  if (method === "GET" && !params.id) {
    const sites = await P.loadAll("sites/");
    sites.sort((a, b) => String(a.name).localeCompare(String(b.name)));
    return send(200, { sites });
  }

  if (method === "PUT" && params.id) {
    const id = String(params.id);
    const { meta, site } = FILE.check(id, body, user.username);
    const before = await P.store().get("sites/" + id + ".json");
    /* The site first, then its record: a site without a record is never
       read, so a half-finished upload cannot show up as a project. */
    await P.store().put("sites/" + id + "/site.json", site, { compact: true });
    await P.store().put("sites/" + id + ".json", meta, before ? { ifMatch: before.etag } : { ifNoneMatch: "*" });
    SITE.forget(id);
    await P.audit(req, user.username, before ? "site.replace" : "site.upload", "site:" + id,
      { fixtures: meta.fixtures, rows: meta.rows, source: meta.source });
    return send(before ? 200 : 201, { site: meta, replaced: !!before });
  }

  throw new ApiError(405, "Method not allowed.");
});
