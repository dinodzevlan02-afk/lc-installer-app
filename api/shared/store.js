/* LC Installer App - storage. Copied from lc-customer-portal (2026-10-20).

   Everything the app knows lives as plain JSON in ONE private container
   (default stled03 / installer-app), its own, never the portal's, so a bug
   here cannot reach customer records. Other apps may read it later
   without going through this API. The layout is documented in
   docs/storage.md; keep the two in step.

   Two backends behind one interface:
     - blob:  Azure Blob REST with a container SAS (INSTALLER_STORAGE_SAS).
              No npm packages, same approach as lc-catalog's api/.
     - local: a folder on disk (INSTALLER_LOCAL_STORE), used by dev/server.js so
              the whole sign-in flow can be tested without touching stled03.

   Interface (all async):
     get(path)                        -> { data, etag } | null
     put(path, data, { ifMatch, ifNoneMatch, compact })  -> etag   (throws CONFLICT)
                                      compact: no indentation, for big files
     list(prefix)                     -> [path, ...]
     putBytes(path, buffer, contentType, { overwrite })  -> etag
                                      create-only unless overwrite (photos
                                      never overwrite)
     getBytes(path)                   -> { buf, contentType } | null
     listDetailed(prefix)             -> [{ name, size, modified }]
     putBlock(path, blockId, buffer)  -> staged part of a big file
     commitBlocks(path, [blockId], contentType) -> etag  (joins the parts,
                                      replacing the file; for files bigger
                                      than one request)
     del(path)                        -> true | false
   `ifNoneMatch: '*'` means "create only"; `ifMatch: etag` means "only if
   nobody changed it since I read it". Both are what keep two people from
   silently overwriting each other. */
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

class StoreError extends Error {
  constructor(code, message) { super(message || code); this.code = code; }
}

/* Paths are built by our own code from validated ids, but check anyway: a
   path that escapes its prefix would read or overwrite someone else's file. */
function checkPath(p) {
  if (typeof p !== "string" || !p || p.startsWith("/") || p.includes("..") || p.includes("\\") || /[\0-\x1f]/.test(p)) {
    throw new StoreError("BAD_PATH", "invalid storage path: " + p);
  }
  return p;
}

/* ── Azure Blob backend ─────────────────────────────────────────────────── */
function blobStore() {
  const account = process.env.INSTALLER_STORAGE_ACCOUNT || "stled03";
  const container = process.env.INSTALLER_CONTAINER || "installer-app";
  const sasRaw = process.env.INSTALLER_STORAGE_SAS || "";
  if (!sasRaw) throw new StoreError("NOT_CONFIGURED", "INSTALLER_STORAGE_SAS app setting is not configured");
  const sas = sasRaw.replace(/^\?/, "");
  const base = "https://" + account + ".blob.core.windows.net/" + container;
  const blobUrl = p => base + "/" + checkPath(p).split("/").map(encodeURIComponent).join("/") + "?" + sas;
  const VER = { "x-ms-version": "2021-08-06" };

  async function fail(r, what) {
    const t = await r.text().catch(() => "");
    if (r.status === 412 || r.status === 409) throw new StoreError("CONFLICT", what + " conflict");
    throw new StoreError("STORAGE", what + " failed (" + r.status + "): " + t.slice(0, 200));
  }

  return {
    kind: "blob",
    async get(p) {
      const r = await fetch(blobUrl(p), { headers: VER, cache: "no-store" });
      if (r.status === 404) return null;
      if (!r.ok) await fail(r, "read " + p);
      return { data: JSON.parse(await r.text()), etag: r.headers.get("etag") };
    },
    async put(p, data, opt) {
      opt = opt || {};
      const headers = Object.assign({
        "x-ms-blob-type": "BlockBlob",
        "x-ms-blob-content-type": "application/json; charset=utf-8",
        "Content-Type": "application/json; charset=utf-8"
      }, VER);
      if (opt.ifMatch) headers["If-Match"] = opt.ifMatch;
      if (opt.ifNoneMatch) headers["If-None-Match"] = opt.ifNoneMatch;
      const r = await fetch(blobUrl(p), { method: "PUT", headers, body: JSON.stringify(data, null, opt.compact ? 0 : 2) });
      if (!r.ok) await fail(r, "write " + p);
      return r.headers.get("etag");
    },
    async list(prefix) {
      checkPath(prefix);
      const out = [];
      let marker = "";
      do {
        const url = base + "?restype=container&comp=list&prefix=" + encodeURIComponent(prefix) +
          (marker ? "&marker=" + encodeURIComponent(marker) : "") + "&" + sas;
        const r = await fetch(url, { headers: VER, cache: "no-store" });
        if (!r.ok) await fail(r, "list " + prefix);
        const xml = await r.text();
        const re = /<Name>([^<]*)<\/Name>/g;
        let m;
        while ((m = re.exec(xml))) out.push(m[1].replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&apos;/g, "'"));
        const nm = /<NextMarker>([^<]*)<\/NextMarker>/.exec(xml);
        marker = nm ? nm[1] : "";
      } while (marker);
      return out;
    },
    async putBytes(p, buf, contentType, opt) {
      const h = { "x-ms-blob-type": "BlockBlob", "x-ms-blob-content-type": contentType, "Content-Type": contentType };
      if (!(opt && opt.overwrite)) h["If-None-Match"] = "*";
      const r = await fetch(blobUrl(p), { method: "PUT", body: buf, headers: Object.assign(h, VER) });
      if (!r.ok) await fail(r, "write " + p);
      return r.headers.get("etag");
    },
    async putBlock(p, blockId, buf) {
      const r = await fetch(blobUrl(p) + "&comp=block&blockid=" + encodeURIComponent(blockId), { method: "PUT", body: buf, headers: VER });
      if (!r.ok) await fail(r, "stage " + p);
    },
    async commitBlocks(p, ids, contentType) {
      const xml = '<?xml version="1.0" encoding="utf-8"?><BlockList>' + ids.map(i => "<Latest>" + i + "</Latest>").join("") + "</BlockList>";
      const r = await fetch(blobUrl(p) + "&comp=blocklist", { method: "PUT", body: xml,
        headers: Object.assign({ "x-ms-blob-content-type": contentType, "Content-Type": "application/xml" }, VER) });
      if (!r.ok) await fail(r, "commit " + p);
      return r.headers.get("etag");
    },
    async listDetailed(prefix) {
      checkPath(prefix);
      const out = [];
      let marker = "";
      do {
        const url = base + "?restype=container&comp=list&prefix=" + encodeURIComponent(prefix) +
          (marker ? "&marker=" + encodeURIComponent(marker) : "") + "&" + sas;
        const r = await fetch(url, { headers: VER, cache: "no-store" });
        if (!r.ok) await fail(r, "list " + prefix);
        const xml = await r.text();
        const re = /<Blob>([\s\S]*?)<\/Blob>/g;
        let m;
        while ((m = re.exec(xml))) {
          const b = m[1], tag = t => { const x = new RegExp("<" + t + ">([^<]*)</" + t + ">").exec(b); return x ? x[1] : ""; };
          out.push({ name: tag("Name").replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&apos;/g, "'"),
                     size: +tag("Content-Length") || 0, modified: new Date(tag("Last-Modified")).toISOString() });
        }
        const nm = /<NextMarker>([^<]*)<\/NextMarker>/.exec(xml);
        marker = nm ? nm[1] : "";
      } while (marker);
      return out;
    },
    async getBytes(p) {
      const r = await fetch(blobUrl(p), { headers: VER, cache: "no-store" });
      if (r.status === 404) return null;
      if (!r.ok) await fail(r, "read " + p);
      return { buf: Buffer.from(await r.arrayBuffer()), contentType: r.headers.get("content-type") || "application/octet-stream" };
    },
    async del(p) {
      const r = await fetch(blobUrl(p), { method: "DELETE", headers: VER });
      if (r.status === 404) return false;
      if (!r.ok) await fail(r, "delete " + p);
      return true;
    }
  };
}

/* ── Local folder backend (dev only) ────────────────────────────────────── */
function localStore(root) {
  root = path.resolve(root);
  const file = p => path.join(root, ...checkPath(p).split("/"));
  const etagOf = buf => '"' + crypto.createHash("sha1").update(buf).digest("hex") + '"';
  function walk(dir, rel, out) {
    if (!fs.existsSync(dir)) return out;
    for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
      const r = rel ? rel + "/" + e.name : e.name;
      if (e.isDirectory()) walk(path.join(dir, e.name), r, out); else out.push(r);
    }
    return out;
  }
  return {
    kind: "local",
    async get(p) {
      const f = file(p);
      if (!fs.existsSync(f)) return null;
      const buf = fs.readFileSync(f);
      return { data: JSON.parse(buf.toString("utf8")), etag: etagOf(buf) };
    },
    async put(p, data, opt) {
      opt = opt || {};
      const f = file(p);
      const exists = fs.existsSync(f);
      if (opt.ifNoneMatch === "*" && exists) throw new StoreError("CONFLICT", "write " + p + " conflict");
      if (opt.ifMatch && (!exists || etagOf(fs.readFileSync(f)) !== opt.ifMatch)) throw new StoreError("CONFLICT", "write " + p + " conflict");
      fs.mkdirSync(path.dirname(f), { recursive: true });
      const buf = Buffer.from(JSON.stringify(data, null, opt.compact ? 0 : 2), "utf8");
      fs.writeFileSync(f, buf);
      return etagOf(buf);
    },
    async list(prefix) {
      checkPath(prefix);
      return walk(root, "", []).filter(n => n.startsWith(prefix)).sort();
    },
    async putBytes(p, buf, contentType, opt) {
      const f = file(p);
      if (fs.existsSync(f) && !(opt && opt.overwrite)) throw new StoreError("CONFLICT", "write " + p + " conflict");
      fs.mkdirSync(path.dirname(f), { recursive: true });
      fs.writeFileSync(f, buf);
      return etagOf(buf);
    },
    async getBytes(p) {
      const f = file(p);
      if (!fs.existsSync(f)) return null;
      return { buf: fs.readFileSync(f), contentType: /\.jpe?g$/i.test(p) ? "image/jpeg" : "application/octet-stream" };
    },
    /* Staged parts live outside the listed tree (a sibling ".blocks" root),
       as Azure keeps uncommitted blocks out of a listing. */
    async putBlock(p, blockId, buf) {
      const d = path.join(root, ".blocks", crypto.createHash("sha1").update(checkPath(p)).digest("hex"));
      fs.mkdirSync(d, { recursive: true });
      fs.writeFileSync(path.join(d, Buffer.from(blockId, "base64").toString("hex")), buf);
    },
    async commitBlocks(p, ids, contentType) {
      const d = path.join(root, ".blocks", crypto.createHash("sha1").update(checkPath(p)).digest("hex"));
      const parts = ids.map(i => { const f = path.join(d, Buffer.from(i, "base64").toString("hex"));
        if (!fs.existsSync(f)) throw new StoreError("STORAGE", "missing part of " + p); return fs.readFileSync(f); });
      const buf = Buffer.concat(parts), f = file(p);
      fs.mkdirSync(path.dirname(f), { recursive: true });
      fs.writeFileSync(f, buf);
      fs.rmSync(d, { recursive: true, force: true });
      return etagOf(buf);
    },
    async listDetailed(prefix) {
      checkPath(prefix);
      return walk(root, "", []).filter(n => n.startsWith(prefix)).sort().map(n => {
        const st = fs.statSync(file(n)); return { name: n, size: st.size, modified: st.mtime.toISOString() }; });
    },
    async del(p) {
      const f = file(p);
      if (!fs.existsSync(f)) return false;
      fs.unlinkSync(f);
      return true;
    }
  };
}

let _store = null;
function store() {
  if (_store) return _store;
  _store = process.env.INSTALLER_LOCAL_STORE ? localStore(process.env.INSTALLER_LOCAL_STORE) : blobStore();
  return _store;
}

module.exports = { store, StoreError };
