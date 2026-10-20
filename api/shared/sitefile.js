/* LC Installer App - a site file uploaded into this app (format "lc-site").

   The same shape the customer portal stores (site.datasets[].data rows,
   solutions and excluded keyed by row INDEX), built outside the app by
   tools/sites/build-site.js from the LED Audit app's export and the
   approved design. check() is the only way one gets in: it refuses
   anything malformed and KEEPS ONLY the solution fields site.js reads, so
   pricing, supplier or configurator snapshots cannot be stored here even if
   a file carries them. Audit photo links are dropped too: they are signed
   (SAS) URLs and expire. */
const { ApiError } = require("./auth");

const RE_ID = /^[A-Za-z0-9][A-Za-z0-9._-]{1,63}$/;
const RE_DS = /^[A-Za-z0-9._-]{1,64}$/;
const MAX_BYTES = 4 * 1024 * 1024, MAX_ROWS = 5000, MAX_DATASETS = 20;
const SOL_TEXT = ["fam", "lc_sku", "cat", "desc", "cct", "volt", "specific", "tag", "arrangement"];
const SOL_NUM = ["watt", "mh", "tilt", "armLength", "rotation"];
const ROW_DROP = ["images"];

const bad = msg => { throw new ApiError(400, msg); };

function text(v, max, what) {
  if (v == null || v === "") return "";
  if (typeof v !== "string" && typeof v !== "number") bad(what + " must be text.");
  const s = String(v).trim();
  if (s.length > max) bad(what + " is too long (max " + max + ").");
  return s;
}

function row(r, where) {
  if (!r || typeof r !== "object" || Array.isArray(r)) bad(where + " is not a record.");
  const keys = Object.keys(r);
  if (keys.length > 100) bad(where + " has too many fields.");
  const out = {};
  keys.forEach(k => {
    if (ROW_DROP.includes(k)) return;
    if (k.length > 64) bad(where + ": field name too long.");
    const v = r[k];
    if (v == null || typeof v === "number" || typeof v === "boolean") out[k] = v;
    else if (typeof v === "string") { if (v.length > 500) bad(where + ": \"" + k + "\" is too long."); out[k] = v; }
    else bad(where + ": \"" + k + "\" must be a plain value.");
  });
  return out;
}

function solution(s, where) {
  if (!s || typeof s !== "object" || Array.isArray(s)) bad(where + " is not a solution.");
  const out = {};
  SOL_TEXT.forEach(k => { if (s[k] != null && s[k] !== "") out[k] = text(s[k], 200, where + " " + k); });
  SOL_NUM.forEach(k => {
    if (s[k] == null || s[k] === "") return;
    const n = Number(s[k]);
    if (!isFinite(n)) bad(where + " " + k + " must be a number.");
    out[k] = n;
  });
  if (s.includePole != null) out.includePole = !!s.includePole;
  if (s.prodId != null && s.prodId !== "") {
    if (!/^\d{1,9}$/.test(String(s.prodId))) bad(where + " prodId must be a catalog product number.");
    out.prodId = Number(s.prodId);
  }
  if (s.specSheetUrl) {
    const u = text(s.specSheetUrl, 500, where + " specSheetUrl");
    if (!/^https:\/\//.test(u)) bad(where + " specSheetUrl must be an https link.");
    out.specSheetUrl = u;
  }
  return out;
}

function byIndex(obj, n, where, each) {
  if (obj == null) return {};
  if (typeof obj !== "object" || Array.isArray(obj)) bad(where + " must be keyed by row number.");
  const out = {};
  Object.keys(obj).forEach(k => {
    if (!/^\d+$/.test(k) || +k >= n) bad(where + ": row " + k + " does not exist.");
    const v = each(obj[k], where + " row " + k);
    if (v !== undefined) out[k] = v;
  });
  return out;
}

/* -> { meta, site } ready to store, or throws 400. */
function check(id, body, by) {
  if (!RE_ID.test(String(id || ""))) bad("Site id must be 2-64 characters: letters, digits, and . _ -");
  if (!body || body.format !== "lc-site" || body.version !== 1) bad("Not a site file (format \"lc-site\", version 1).");
  if (Buffer.byteLength(JSON.stringify(body)) > MAX_BYTES) bad("The site file is too big (max 4 MB).");
  const p = body.project || {};
  if (p.id != null && String(p.id) !== id) bad("The file is for \"" + p.id + "\", not \"" + id + "\".");
  const name = text(p.name, 120, "Project name");
  if (!name) bad("The site file has no project name.");
  const kind = p.kind || "exterior";
  if (kind !== "exterior" && kind !== "interior") bad("kind must be exterior or interior.");
  const installDate = text(p.installDate, 10, "installDate");
  if (installDate && !/^\d{4}-\d{2}-\d{2}$/.test(installDate)) bad("installDate must be YYYY-MM-DD.");

  const dsIn = body.site && body.site.datasets;
  if (!Array.isArray(dsIn) || !dsIn.length || dsIn.length > MAX_DATASETS) bad("The site needs 1-" + MAX_DATASETS + " datasets.");
  const seen = new Set();
  let heads = 0, rows = 0;
  const datasets = dsIn.map((ds, i) => {
    const where = "Dataset " + (i + 1);
    if (!ds || !RE_DS.test(String(ds.id || ""))) bad(where + " needs an id (letters, digits, . _ -).");
    if (seen.has(ds.id)) bad("Two datasets are called \"" + ds.id + "\".");
    seen.add(ds.id);
    if (!Array.isArray(ds.data) || !ds.data.length) bad(where + " has no audit rows.");
    rows += ds.data.length;
    if (rows > MAX_ROWS) bad("Too many audit rows (max " + MAX_ROWS + ").");
    const data = ds.data.map((r, j) => row(r, where + " row " + j));
    const solutions = byIndex(ds.solutions, data.length, where + " solutions", solution);
    const excluded = byIndex(ds.excluded, data.length, where + " excluded", v => (v ? true : undefined));
    heads += Object.keys(solutions).filter(k => !excluded[k]).length;
    return { id: ds.id, label: text(ds.label, 120, where + " label"), data, solutions, excluded };
  });

  const src = body.source || {};
  const source = {};
  ["audit", "design", "mapping", "built", "builder"].forEach(k => { if (src[k]) source[k] = text(src[k], 300, "source " + k); });
  const meta = {
    v: 1, id, name, address: text(p.address, 200, "Address"), customer: text(p.customer, 80, "Customer"),
    kind, installDate, fixtures: heads, rows, source,
    uploaded: new Date().toISOString(), uploadedBy: by
  };
  return { meta, site: { format: "lc-site", version: 1, site: { datasets } } };
}

module.exports = { check, MAX_BYTES };
