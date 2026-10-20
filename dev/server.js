/* LC Installer App - local dev server (copied from lc-customer-portal).

   Serves the site AND runs api/ the way Azure Static Web Apps does, so the
   sign-in flow can be tested end to end on this machine. Storage is a folder
   (dev/.data, gitignored) instead of stled03, so nothing here touches the
   real records.

     node dev/server.js            -> http://localhost:4310

   It reads each api/<name>/function.json for the route and methods and calls
   the function with a minimal Azure Functions (v3 model) context. Only what
   our functions use is emulated: req.method/headers/query/params/body and
   context.res. Not for production; this folder is blocked from the deployed
   site in staticwebapp.config.json. */
const http = require("http");
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const ROOT = path.resolve(__dirname, "..");
/* Only app/ is the website, as on Azure (app_location "app"): the dev server
   cannot serve anything the live site would not. */
const SITE = path.join(ROOT, "app");
const PORT = Number(process.env.PORT || 4310);

/* Local-only settings. These are test values for this dev server, never the
   production ones, which live only in the Azure app settings. */
process.env.INSTALLER_LOCAL_STORE = process.env.INSTALLER_LOCAL_STORE || path.join(__dirname, ".data");
process.env.INSTALLER_JWT_SECRET = process.env.INSTALLER_JWT_SECRET || crypto.randomBytes(32).toString("hex");
process.env.INSTALLER_SETUP_KEY = process.env.INSTALLER_SETUP_KEY || "local-dev-setup-key";
/* The customer portal's container, read-only. A real site copied from the
   portal (Walmart 2741: projects/{id}.json + projects/{id}/site.json and
   portal.json) goes in dev/.portal, which git ignores; otherwise the
   synthetic test site in dev/fixtures/portal. */
process.env.INSTALLER_PORTAL_LOCAL_STORE = process.env.INSTALLER_PORTAL_LOCAL_STORE ||
  (fs.existsSync(path.join(__dirname, ".portal")) ? path.join(__dirname, ".portal") : path.join(__dirname, "fixtures", "portal"));

const MIME = {
  ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8", ".webmanifest": "application/manifest+json", ".png": "image/png",
  ".svg": "image/svg+xml", ".ico": "image/x-icon", ".md": "text/plain; charset=utf-8"
};

/* ── Load the functions ─────────────────────────────────────────────────── */
/* Re-read on every API call, so a function added while the server runs is
   routed without a restart (the first version read them once at start-up,
   and a new endpoint answered "no such api" until restarted). */
const apiDir = path.join(ROOT, "api");
function loadRoutes() {
const routes = [];
for (const name of fs.readdirSync(apiDir)) {
  const fj = path.join(apiDir, name, "function.json");
  if (!fs.existsSync(fj)) continue;
  const b = JSON.parse(fs.readFileSync(fj, "utf8")).bindings.find(x => x.type === "httpTrigger");
  const keys = [];
  const re = new RegExp("^" + b.route.split("/").map(seg => {
    const m = /^\{(\w+)(\?)?\}$/.exec(seg);
    if (!m) return "/" + seg.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    keys.push(m[1]);
    return m[2] ? "(?:/([^/]+))?" : "/([^/]+)";
  }).join("").slice(1) + "$");
  routes.push({ name, re, keys, methods: (b.methods || []).map(m => m.toUpperCase()), file: path.join(apiDir, name, "index.js") });
}
return routes;
}

function fresh(file) {
  /* Re-require on every call so an edit to api/ shows up without a restart. */
  for (const k of Object.keys(require.cache)) if (k.startsWith(apiDir)) delete require.cache[k];
  return require(file);
}

async function runApi(req, res, url) {
  const sub = decodeURIComponent(url.pathname.slice("/api/".length));
  const r = loadRoutes().find(x => x.re.test(sub));
  if (!r) { res.writeHead(404, { "Content-Type": "application/json" }); return res.end('{"error":"no such api"}'); }
  if (!r.methods.includes(req.method)) { res.writeHead(405, { "Content-Type": "application/json" }); return res.end('{"error":"method not allowed"}'); }
  const m = r.re.exec(sub), params = {};
  r.keys.forEach((k, i) => { if (m[i + 1] !== undefined) params[k] = m[i + 1]; });

  const chunks = [];
  for await (const c of req) chunks.push(c);
  const raw = Buffer.concat(chunks).toString("utf8");
  let body = raw;
  if (raw && /json/i.test(req.headers["content-type"] || "")) { try { body = JSON.parse(raw); } catch (e) { /* function reports it */ } }

  const context = { res: null, log: Object.assign((...a) => console.log("[" + r.name + "]", ...a), { error: (...a) => console.error("[" + r.name + "]", ...a) }) };
  const freq = { method: req.method, url: url.href, headers: req.headers, query: Object.fromEntries(url.searchParams), params, body, rawBody: raw };
  try { await fresh(r.file)(context, freq); }
  catch (e) { console.error(e); context.res = { status: 500, body: '{"error":"function crashed"}' }; }

  const out = context.res || { status: 204 };
  const payload = out.body == null ? "" : (Buffer.isBuffer(out.body) || typeof out.body === "string" ? out.body : JSON.stringify(out.body));
  res.writeHead(out.status || 200, out.headers || {});
  res.end(payload);
  console.log(req.method, url.pathname, "->", out.status || 200);
}

function serveStatic(req, res, url) {
  let p = decodeURIComponent(url.pathname);
  if (p.endsWith("/")) p += "index.html";
  const f = path.join(SITE, p);
  if (!f.startsWith(SITE + path.sep)) { res.writeHead(404); return res.end("Not found"); }
  fs.readFile(f, (err, buf) => {
    if (err) { res.writeHead(404, { "Content-Type": "text/plain" }); return res.end("Not found: " + p); }
    res.writeHead(200, { "Content-Type": MIME[path.extname(f).toLowerCase()] || "application/octet-stream", "Cache-Control": "no-store" });
    res.end(buf);
  });
}

function onRequest(req, res) {
  const url = new URL(req.url, "http://localhost:" + PORT);
  if (url.pathname.startsWith("/api/")) runApi(req, res, url).catch(e => { console.error(e); res.writeHead(500); res.end(); });
  else serveStatic(req, res, url);
}

/* Loopback only, on both IPv4 and IPv6: browsers resolve localhost to ::1
   first, and listening on every interface would put the dev API on the LAN. */
http.createServer(onRequest).listen(PORT, "127.0.0.1", () => {
  console.log("LC Installer App dev server: http://localhost:" + PORT);
  console.log("Storage: " + process.env.INSTALLER_LOCAL_STORE + "  (local folder, not stled03)");
  console.log("Portal (read-only): " + process.env.INSTALLER_PORTAL_LOCAL_STORE);
  console.log("API routes: " + loadRoutes().map(r => r.name).join(", "));
});
http.createServer(onRequest).listen(PORT, "::1").on("error", () => { /* no IPv6 loopback; IPv4 still serves */ });
