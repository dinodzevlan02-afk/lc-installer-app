/* LC Installer App - the LC catalog's public product files: spec sheet,
   photo and instruction manuals per product id (sol.prodId).

   Read server-side from internal-catalog/catalog-data.json (the file the
   catalog and the customer portal read), kept for an hour. URL rules as
   lc-customer-portal cpSpecFromCatalog and lc-catalog fileUrlFor:
     v2 files    fixtures/{id}/{spec-sheet|image|instruction-manuals}/{file}
     legacy      files/{id}/{spec|pdfs}/{file}
   WHITELIST: only names, categories, options and file links leave this
   file; the catalog's vendor and vendor SKU never reach an installer.
   If the catalog cannot be read, products simply have no catalog links. */
const BASE = (process.env.INSTALLER_CATALOG_BASE || "https://stled03.blob.core.windows.net/internal-catalog/").replace(/\/?$/, "/");
const enc = encodeURIComponent;

function fileUrl(id, folder, legacy, f) {
  if (!f) return null;
  if (typeof f === "string") return BASE + enc(f);
  if (f.url) return f.url;
  if (!f.filename) return null;
  if (f.v === 2) return BASE + "fixtures/" + enc(id) + "/" + folder + "/" + enc(f.filename);
  return BASE + "files/" + enc(id) + "/" + legacy + "/" + enc(f.filename);
}

function publicCatalogProduct(p) {
  const img = (p.imgs || [])[0];
  return {
    id: p.id, fam: p.fam || "", model: p.model || "", cat: p.cat || "", app: p.app || "",
    mounts: Array.isArray(p.mounts) ? p.mounts : [], volts: Array.isArray(p.volts) ? p.volts : [],
    ul: !!p.ulMultiListed, dlc: !!p.dlcQualified,
    specSheetUrl: fileUrl(p.id, "spec-sheet", "spec", p.pubFile),
    imageUrl: img ? fileUrl(p.id, "image", "images", img) : null,
    docs: (p.pdfDocs || []).map(f => ({ label: f.label || f.filename || "Document", kind: f.kind || "", url: fileUrl(p.id, "instruction-manuals", "pdfs", f) }))
      .filter(d => d.url)
  };
}

let cached = null;
async function products() {
  if (cached && Date.now() - cached.at < 3600000) return cached.map;
  try {
    let d;
    if (process.env.INSTALLER_CATALOG_FILE) {
      /* Dev and tests: a local copy of catalog-data.json. */
      d = JSON.parse(require("fs").readFileSync(process.env.INSTALLER_CATALOG_FILE, "utf8"));
    } else {
      const r = await fetch(BASE + "catalog-data.json", { cache: "no-store" });
      if (!r.ok) throw new Error("catalog " + r.status);
      d = await r.json();
    }
    const map = new Map();
    (d.products || []).forEach(p => { if (p && p.id != null && !p.archived) map.set(String(p.id), publicCatalogProduct(p)); });
    cached = { at: Date.now(), map };
    return map;
  } catch (e) {
    /* Try again in five minutes, not on every request. */
    cached = { at: Date.now() - 3600000 + 300000, map: (cached && cached.map) || new Map() };
    return cached.map;
  }
}

async function product(prodId) {
  if (prodId == null) return null;
  return (await products()).get(String(prodId)) || null;
}

module.exports = { product, products, publicCatalogProduct };
