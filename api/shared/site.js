/* LC Installer App - a project's site, as an installer needs it.

   Two sources, one shape ({ format:"lc-site", site:{ datasets } }):
   1. The installer app's OWN sites (Dino, 2026-10-20: Kroger 345 "written
      only in the installer app"), in this app's container:
        sites/{id}.json              name, address, customer, kind, source
        sites/{id}/site.json         { format:"lc-site", site: { datasets } }
      uploaded by an LC admin (PUT /api/sites/{id}) from a file built by
      tools/sites/build-site.js. An own site wins over a portal project with
      the same id. It has no portal.json, so no hand-moved pins.
   2. The customer portal's container (portalStore, read-only):
     projects/{id}.json           name, address, customer
     projects/{id}/site.json      { format:"lc-site", site: { datasets:[...] } }
     projects/{id}/portal.json    { projects: { [dsId]: { assets: { [fid]: { pos } } } } }
   Field meanings follow lc-customer-portal/portal.html (cpFixtureId,
   cpExistingWatts, cpShortProduct, cpProductKey, cpGroups): one audit row
   is one head, ds.solutions / ds.excluded are keyed by row INDEX, a pin's
   label is row.schedule, poles group by row['pole id'], and a position
   corrected by hand (asset.pos) wins over the audit's.

   WHITELIST, not a blacklist: only the fields named below leave this file,
   so pricing, supplier, margin, configurator snapshots and audit notes (the
   portal's sitefilter SOLUTION_INTERNAL / ROW_INTERNAL) can never reach an
   installer, even when the suite adds a new internal field. */
const crypto = require("crypto");
const { portalStore, store } = require("./store");
const CATALOG = require("./catalog");

const num = v => { const n = parseFloat(v); return isFinite(n) ? n : null; };
const str = v => (v == null ? "" : String(v).trim());

function fixtureId(row, idx) {
  const id = row.id != null ? row.id : row.ID != null ? row.ID : row.Id;
  return id != null && String(id).trim() ? String(id).trim() : "row-" + idx;
}

/* A head's key in the installer app's own storage: stable across a site
   re-upload as long as the audit row keeps its id. */
const pinKey = (dsId, fid) => crypto.createHash("sha1").update(String(dsId) + "\u0000" + String(fid)).digest("hex").slice(0, 20);

function existingWatts(row) {
  const sys = num(row["system wattage"]);
  if (sys != null) return sys;
  const w = num(row.wattage);
  if (w == null) return null;
  const lamps = num(row["number of lamps"]);
  return w * (lamps == null ? 1 : lamps);
}

/* Same grouping as the portal's product list: family + LC SKU. */
function productKey(sol, row) {
  if (sol && (sol.fam || sol.lc_sku)) return str(sol.fam) + " · " + str(sol.lc_sku);
  return (str(row.schedule) ? str(row.schedule) + " · " : "") + (str(row["fixture type"]) || "Unclassified");
}

/* "Optimus XL1 230W · TY5SW", as cpShortProduct. */
function shortProduct(sol, fallback) {
  const fam = sol && sol.fam, sku = sol && sol.lc_sku;
  if (!fam || !sku) return fallback;
  let w = null, beam = null, head = null;
  String(sku).toUpperCase().split("-").forEach(x => {
    if (!w && /^\d{1,4}W$/.test(x)) w = x;
    if (!head && /^(S|L|XL)\d$/.test(x)) head = x;
    if (!beam && /^(T[1-5][SMW]{0,2}|TY\d{1,2}[SMW]{0,2}|TYPE[1-5])$/.test(x)) beam = x.replace(/^TYPE/, "T");
  });
  if (!w && sol.watt && parseFloat(sol.watt) > 0) w = Math.round(parseFloat(sol.watt)) + "W";
  return fam + (head ? " " + head : "") + (w ? " " + w : "") + (beam ? " · " + beam : "");
}

/* Look-alikes get the first SKU segments that differ, then the full key. */
function nameProducts(bom) {
  const seen = {};
  bom.forEach(b => (seen[b.name] = seen[b.name] || []).push(b));
  Object.values(seen).forEach(same => {
    if (same.length < 2) return;
    const segs = same.map(b => String(b.sku || b.key).split("-"));
    same.forEach((b, i) => {
      const own = segs[i].filter((x, j) => segs.some((o, k) => k !== i && o[j] !== x));
      b.name = own.length ? b.name + " · " + own.slice(0, 2).join("-") : b.key;
    });
  });
  const dupes = {};
  bom.forEach(b => { dupes[b.name] = (dupes[b.name] || 0) + 1; });
  bom.forEach(b => { if (dupes[b.name] > 1) b.name = b.key; });
}

/* The solution fields an installer sees. */
function publicProduct(sol) {
  if (!sol) return null;
  return {
    fam: str(sol.fam), sku: str(sol.lc_sku), cat: str(sol.cat), desc: str(sol.desc),
    watt: num(sol.watt), cct: str(sol.cct), volt: str(sol.volt), specific: str(sol.specific),
    designTag: str(sol.tag), arrangement: str(sol.arrangement), mh: num(sol.mh), tilt: num(sol.tilt),
    armLength: num(sol.armLength), includePole: !!sol.includePole, rotation: num(sol.rotation),
    prodId: sol.prodId != null ? sol.prodId : null, specSheetUrl: str(sol.specSheetUrl) || null
  };
}

/* -> { project, datasets, pins, bom, tags } or null when neither this app
   nor the portal has such a site. */
async function loadSite(projectId) {
  const own = store();
  const [ownMeta, ownSite] = await Promise.all([own.get("sites/" + projectId + ".json"), own.get("sites/" + projectId + "/site.json")]);
  if (ownMeta && ownSite) return buildSite(ownMeta.data, ownSite.data, {}, "installer");
  const ps = portalStore();
  const [meta, siteRec, portalRec] = await Promise.all([
    ps.get("projects/" + projectId + ".json"),
    ps.get("projects/" + projectId + "/site.json"),
    ps.get("projects/" + projectId + "/portal.json")
  ]);
  if (!meta || !siteRec) return null;
  return buildSite(meta.data, siteRec.data, (portalRec && portalRec.data && portalRec.data.projects) || {}, "portal");
}

async function buildSite(m, siteRec, pprojects, source) {
  const site = (siteRec && siteRec.site) || {};

  const pins = [], bomMap = {}, datasets = [];
  (site.datasets || []).forEach(ds => {
    const assets = (pprojects[ds.id] && pprojects[ds.id].assets) || {};
    datasets.push({ id: ds.id, label: str(ds.label) || str(ds.projectName) || str(ds.name) });
    (ds.data || []).forEach((row, idx) => {
      if (!row) return;
      const sol = ds.solutions && ds.solutions[idx];
      const off = !!(ds.excluded && ds.excluded[idx]);
      const fid = fixtureId(row, idx);
      const a = assets[fid];
      const lat = a && a.pos ? num(a.pos.lat) : num(row.latitude);
      const lng = a && a.pos ? num(a.pos.lng) : num(row.longitude);
      const key = productKey(sol, row);
      const product = publicProduct(sol);
      pins.push({
        id: pinKey(ds.id, fid), ds: ds.id, fid, idx,
        /* The DESIGN's tag (sol.tag: S13, FCW2, FL3, as on the photometric
           sheet's luminaire schedule) is the one the installer works by
           (Dino, 2026-10-20: "use this tag names"); the audit's own tag
           (row.schedule: CK1, WP, A2) stays as auditTag for reference, and
           is the fallback for a head with no design tag. */
        tag: str(sol && sol.tag) || str(row.schedule) || fid, auditTag: str(row.schedule),
        poleId: str(row["pole id"]),
        lat, lng,
        existing: {
          type: str(row["fixture type"]), tech: str(row["tech type"]), watts: existingWatts(row),
          mh: num(row["mounting height"]), mounting: str(row["mounting type"]), area: str(row.area),
          voltage: str(row.voltage)
        },
        productKey: product ? key : null, product,
        off, offReason: off ? str(row.deactivated) : ""
      });
      if (product && !off) {
        const b = bomMap[key] || (bomMap[key] = { key, name: shortProduct(sol, key), sku: product.sku, fam: product.fam,
          watt: product.watt, cct: product.cct, volt: product.volt, specific: product.specific, cat: product.cat,
          prodId: product.prodId, specSheetUrl: product.specSheetUrl, qty: 0, tags: [], tagCounts: {} });
        b.qty++;
        /* Heads per design tag inside this product: one box type can serve
           several tags (A-05: S13 + S14 + S15 are all the XL1 TY5SW head). */
        const t = str(sol && sol.tag) || str(row.schedule);
        if (t) { if (!b.tags.includes(t)) b.tags.push(t); b.tagCounts[t] = (b.tagCounts[t] || 0) + 1; }
      }
    });
  });

  const bom = Object.values(bomMap).sort((a, b) => b.qty - a.qty || a.name.localeCompare(b.name));
  const byNum = (a, b) => a.localeCompare(b, undefined, { numeric: true });
  bom.forEach(b => b.tags.sort(byNum));
  nameProducts(bom);
  /* Spec sheet, photo and manuals from the LC catalog by product id; the
     design's own spec sheet link wins when it has one. */
  await Promise.all(bom.map(async b => {
    b.catalog = await CATALOG.product(b.prodId);
    if (!b.specSheetUrl && b.catalog) b.specSheetUrl = b.catalog.specSheetUrl;
  }));
  const names = Object.fromEntries(bom.map(b => [b.key, b.name]));
  pins.forEach(p => { if (p.productKey) p.productName = names[p.productKey] || shortProduct(null, p.productKey); });

  const tags = {};
  pins.forEach(p => { if (!p.off) tags[p.tag] = (tags[p.tag] || 0) + 1; });

  return {
    project: { id: m.id, name: str(m.name), address: str(m.address), installDate: str(m.installDate), kind: (m.site && m.site.kind) || str(m.kind), source },
    datasets, pins, bom,
    tags: Object.keys(tags).sort((a, b) => a.localeCompare(b, undefined, { numeric: true })).map(t => ({ tag: t, count: tags[t] }))
  };
}

/* The site changes rarely and is read on every job open: keep it a minute
   (an upload here clears it, see forget). */
const cache = new Map();
const forget = projectId => cache.delete(projectId);
async function site(projectId) {
  const hit = cache.get(projectId);
  if (hit && Date.now() - hit.at < 60000) return hit.value;
  const value = await loadSite(projectId);
  cache.set(projectId, { at: Date.now(), value });
  return value;
}

module.exports = { site, loadSite, forget, shortProduct, productKey, fixtureId, pinKey, existingWatts };
