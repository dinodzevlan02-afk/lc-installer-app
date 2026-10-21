/* Deleting a project, and bringing it back. LED Connection only.

   GET  /api/deleted                 every deleted project, newest first: { deleted: [manifest] }
   GET  /api/deleted?preview={id}    what deleting {id} would remove: { id, name, source, counts, files }
   POST /api/deleted                 { projectId, confirm: projectId } -> deletes it, { deleted: manifest }
   POST /api/deleted                 { projectId, confirm: projectId, mode: "reset" } -> resets the
                                     job's work (a clean start), { deleted: manifest with kind "reset" }
   POST /api/deleted/{key}           { action: "restore" } -> puts it back, { restored: manifest }

   Dino, 2026-10-21: "delete ... only by LED Connection ... asked, are you
   sure ... activity log of that if someone has deleted, and save everything
   in backend in a case I need to return back what was happening".
   So nothing is thrown away. Every file of the project is COPIED to
   deleted/{key}/files/{its own path} first; only then are the originals
   removed. deleted/{key}.json is the manifest: who, when, what, and later
   who restored it. The archive is kept after a restore too.

   What a project is here: its job (jobs/{id}.json and everything under
   jobs/{id}/: material check, part numbers, claims, installed pins, photos)
   and, for a site uploaded to this app (Kroger 345), that site
   (sites/{id}.json and sites/{id}/). A customer portal project's own data
   is never touched (read only); it goes back to the ADD picker. */
const P = require("../shared/app");
const J = require("../shared/jobs");
const SITE = require("../shared/site");
const { ApiError } = P;

const RE_KEY = /^\d{8}T\d{6}(\d{3})?Z-[A-Za-z0-9._-]{2,64}$/;
/* 20261021T140512345Z: milliseconds, so two actions on one project in the
   same second (a delete and a reset) never share an archive. */
const stampNow = () => new Date().toISOString().replace(/[-:.]/g, "");
const manifestPath = key => "deleted/" + key + ".json";
const archivePath = (key, p) => "deleted/" + key + "/files/" + p;
const typeOf = (p, t) => /\.json$/i.test(p) ? "application/json; charset=utf-8" : /\.jpe?g$/i.test(p) ? "image/jpeg" : (t || "application/octet-stream");

/* RESET (Dino, 2026-10-21: "deleting all the work on the pins ... make a
   clean project ... only LED Connection"): the job stays (installers, site,
   part numbers, claim emails), its WORK goes: the material counts and
   sign-off, claims, installed heads, photos, and the submitted state. Same
   rules as a delete: archived first (with a copy of the job record, for the
   submitted state), logged, restorable while no new work has been saved. */
const workPrefixes = id => [J.paths.claims(id), J.paths.pins(id), J.paths.photos(id)];
async function workOf(id) {
  const s = P.store();
  const [mat, ...lists] = await Promise.all([s.get(J.paths.material(id))].concat(workPrefixes(id).map(p => s.list(p))));
  return (mat ? [J.paths.material(id)] : []).concat(...lists);
}

/* Every stored file of the project, job record first. */
async function filesOf(id) {
  const s = P.store();
  const [job, jobFiles, site, siteFiles] = await Promise.all([
    s.get(J.paths.job(id)), s.list("jobs/" + id + "/"), s.get("sites/" + id + ".json"), s.list("sites/" + id + "/")
  ]);
  const files = [];
  if (job) files.push(J.paths.job(id));
  files.push(...jobFiles);
  if (site) files.push("sites/" + id + ".json");
  files.push(...siteFiles);
  return { job: job && job.data, site: site && site.data, files };
}

function countsOf(files, id) {
  const under = pre => files.filter(f => f.startsWith(pre)).length;
  return {
    claims: under(J.paths.claims(id)), pins: under(J.paths.pins(id)), photos: under(J.paths.photos(id)),
    material: files.includes(J.paths.material(id)), parts: files.includes(J.paths.parts(id)),
    site: files.includes("sites/" + id + ".json")
  };
}

/* Copy each path from from(p) to to(p) in small parallel batches; a file that is already there (a retry)
   is left as it is. */
async function copyAll(list, from, to) {
  const s = P.store();
  for (let i = 0; i < list.length; i += 8) {
    await Promise.all(list.slice(i, i + 8).map(async p => {
      const b = await s.getBytes(from(p));
      if (!b) return;
      await s.putBytes(to(p), b.buf, typeOf(p, b.contentType)).catch(e => { if (e.code !== "CONFLICT") throw e; });
    }));
  }
}

/* Nothing is removed until every file is in the archive. */
async function verify(k, files) {
  const have = new Set(await P.store().list("deleted/" + k + "/files/"));
  const missing = files.filter(p => !have.has(archivePath(k, p)));
  if (missing.length) throw new ApiError(500, "The archive is missing " + missing.length + " file(s); nothing more was deleted. Try again.");
}

module.exports = P.handler(async ({ req, method, body, params, query, send }) => {
  const { user } = await P.requireLc(req);
  const s = P.store();
  const key = params.key ? String(params.key) : null;
  if (key && !RE_KEY.test(key)) throw new ApiError(404, "Not found.");

  if (method === "GET" && query.preview) {
    const id = J.normJob(query.preview);
    const f = await filesOf(id);
    if (!f.job && !f.site) throw new ApiError(404, "Nothing stored for project \"" + id + "\".");
    return send(200, { id, name: (f.job && f.job.name) || (f.site && f.site.name) || id,
      source: f.site ? "installer" : "portal", counts: countsOf(f.files, id), files: f.files.length });
  }

  if (method === "GET" && !key) {
    const deleted = (await P.loadAll("deleted/")).sort((a, b) => String(b.at).localeCompare(String(a.at)));
    return send(200, { deleted });
  }

  if (method === "POST" && !key && body.mode === "reset") {
    const id = J.normJob(body.projectId);
    if (body.confirm !== id) throw new ApiError(400, "Confirm the reset: send confirm with the project id.");
    const jrec = await s.get(J.paths.job(id));
    if (!jrec) throw new ApiError(404, "No job on project \"" + id + "\".");
    const first = await workOf(id);
    const k = stampNow() + "-" + id;
    /* 1. Copy the work and the job record. 2. Remove the work. 3. Anything
       saved meanwhile is archived and removed too. 4. Clear "submitted". */
    await copyAll(first.concat([J.paths.job(id)]), p => p, p => archivePath(k, p));
    await verify(k, first.concat([J.paths.job(id)]));
    const manifest = {
      v: 1, kind: "reset", key: k, id, name: jrec.data.name || id, address: jrec.data.address || "", customer: jrec.data.customer || "",
      source: (await s.get("sites/" + id + ".json")) ? "installer" : "portal", installers: jrec.data.installers || [],
      at: new Date().toISOString(), by: user.username, byName: user.name || user.username,
      reason: String(body.reason || "").trim().slice(0, 500), files: [], counts: null, restored: []
    };
    await s.put(manifestPath(k), Object.assign({}, manifest, { state: "archiving", files: first }), { ifNoneMatch: "*" });
    for (let i = 0; i < first.length; i += 8) await Promise.all(first.slice(i, i + 8).map(p => s.del(p)));
    const late = await workOf(id);
    await copyAll(late, p => p, p => archivePath(k, p));
    await verify(k, late);
    for (let i = 0; i < late.length; i += 8) await Promise.all(late.slice(i, i + 8).map(p => s.del(p)));
    const all = first.concat(late.filter(p => !first.includes(p)));
    const cur = await s.get(J.paths.job(id));
    if (cur) {
      const j = cur.data;
      j.submitted = null;
      j.reset = { at: manifest.at, by: user.username, archive: k };
      j.updated = manifest.at; j.updatedBy = user.username;
      await s.put(J.paths.job(id), j, { ifMatch: cur.etag });
    }
    manifest.files = all;
    manifest.counts = countsOf(all, id);
    const mrec = await s.get(manifestPath(k));
    await s.put(manifestPath(k), manifest, { ifMatch: mrec.etag });
    await P.audit(req, user.username, "job.reset", "job:" + id, { archive: k, files: all.length, counts: manifest.counts, reason: manifest.reason || undefined });
    return send(200, { deleted: manifest });
  }

  if (method === "POST" && !key) {
    const id = J.normJob(body.projectId);
    if (body.confirm !== id) throw new ApiError(400, "Confirm the delete: send confirm with the project id.");
    const first = await filesOf(id);
    if (!first.job && !first.site) throw new ApiError(404, "Nothing stored for project \"" + id + "\".");
    const stamp = stampNow();
    const k = stamp + "-" + id;
    /* 1. Copy everything. 2. Remove the job record, so nobody can save to
       the job any more. 3. Copy anything saved in between. 4. Remove the
       rest. A failure before step 2 leaves the project as it was. */
    await copyAll(first.files, p => p, p => archivePath(k, p));
    await verify(k, first.files);
    const manifest = {
      v: 1, key: k, id, name: (first.job && first.job.name) || (first.site && first.site.name) || id,
      address: (first.job && first.job.address) || (first.site && first.site.address) || "",
      customer: (first.site && first.site.customer) || (first.job && first.job.customer) || "",
      source: first.site ? "installer" : "portal",
      installers: (first.job && first.job.installers) || [],
      at: new Date().toISOString(), by: user.username, byName: user.name || user.username,
      reason: String(body.reason || "").trim().slice(0, 500),
      files: [], counts: null, restored: []
    };
    await s.put(manifestPath(k), Object.assign({}, manifest, { state: "archiving", files: first.files }), { ifNoneMatch: "*" });
    if (first.job) await s.del(J.paths.job(id));
    const now = await filesOf(id);
    const late = now.files.filter(p => !first.files.includes(p));
    await copyAll(late, p => p, p => archivePath(k, p));
    const all = first.files.concat(late);
    await verify(k, all);
    for (let i = 0; i < now.files.length; i += 8) await Promise.all(now.files.slice(i, i + 8).map(p => s.del(p)));
    SITE.forget(id);
    manifest.files = all;
    manifest.counts = countsOf(all, id);
    const rec = await s.get(manifestPath(k));
    await s.put(manifestPath(k), manifest, { ifMatch: rec.etag });
    await P.audit(req, user.username, "job.delete", "job:" + id, { archive: k, files: all.length, counts: manifest.counts, source: manifest.source, reason: manifest.reason || undefined });
    return send(200, { deleted: manifest });
  }

  if (method === "POST" && key) {
    if (body.action !== "restore") throw new ApiError(400, "Unknown action.");
    const rec = await s.get(manifestPath(key));
    if (!rec) throw new ApiError(404, "Not found.");
    const m = rec.data;
    /* A reset goes back onto the job that is still there, only while
       nobody has saved new work on it; "submitted" comes back as it was. */
    if (m.kind === "reset") {
      const cur = await s.get(J.paths.job(m.id));
      if (!cur) throw new ApiError(409, "Project \"" + m.id + "\" has no job any more; restore its delete first.");
      const now = await workOf(m.id);
      if (now.length && m.state !== "archiving") throw new ApiError(409, "New work was saved on " + (m.name || m.id) + " after the reset (" + now.length + " file(s)). Reset it again first, or keep what is there.");
      await copyAll(m.files, p => archivePath(key, p), p => p);
      const was = await s.getBytes(archivePath(key, J.paths.job(m.id)));
      const j = cur.data;
      j.submitted = was ? (JSON.parse(was.buf.toString("utf8")).submitted || null) : j.submitted;
      j.reset = Object.assign({}, j.reset, { restoredAt: new Date().toISOString(), restoredBy: user.username });
      await s.put(J.paths.job(m.id), j, { ifMatch: cur.etag });
      delete m.state;
      m.restored = (m.restored || []).concat([{ at: new Date().toISOString(), by: user.username, byName: user.name || user.username }]);
      await s.put(manifestPath(key), m, { ifMatch: rec.etag });
      await P.audit(req, user.username, "job.restore", "job:" + m.id, { archive: key, files: m.files.length, kind: "reset" });
      return send(200, { restored: m });
    }
    /* A delete that stopped half way ("archiving") can always be put back:
       files still in place are left as they are. */
    const there = await filesOf(m.id);
    if (m.state !== "archiving" && (there.job || there.site)) throw new ApiError(409, "Project \"" + m.id + "\" exists again here. Delete it first, or keep the one that is there.");
    /* The job record goes back last, so the job reappears only when all
       of its work is back. */
    const job = J.paths.job(m.id);
    const back = p => archivePath(key, p);
    await copyAll(m.files.filter(p => p !== job), back, p => p);
    if (m.files.includes(job)) await copyAll([job], back, p => p);
    SITE.forget(m.id);
    delete m.state;
    m.restored = (m.restored || []).concat([{ at: new Date().toISOString(), by: user.username, byName: user.name || user.username }]);
    await s.put(manifestPath(key), m, { ifMatch: rec.etag });
    await P.audit(req, user.username, "job.restore", "job:" + m.id, { archive: key, files: m.files.length });
    return send(200, { restored: m });
  }

  throw new ApiError(405, "Method not allowed.");
});
