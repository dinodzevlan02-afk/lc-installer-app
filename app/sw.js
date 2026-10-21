/* LC Installer App - service worker. Makes the app installable as a
   standalone tablet app and lets its own pages open with a weak signal.

   Network first, cache as the fallback, for the app's own files only:
   a deploy is picked up on the next load with a signal, and nothing old is
   pinned. Never cached: /api/* (session-bound, may carry another person's
   data on a shared tablet), map tiles (Google's terms), anything cross-site. */
const CACHE = "lci-shell-v2";
const SHELL = ["./", "./index.html", "./home.html", "./job.html", "./lci.css", "./lci.js", "./lci-job.js", "./manual.html", "./lci-manual.js",
  "./manifest.webmanifest", "./lc-logo.png", "./icon-192.png", "./icon-512.png", "./icon-512-maskable.png",
  "./favicon-32.png", "./apple-touch-icon-180.png"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL).catch(() => {})).then(() => self.skipWaiting()));
});

self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin || url.pathname.startsWith("/api/")) return;
  e.respondWith(
    fetch(req).then(res => {
      if (res.ok) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)); }
      return res;
    }).catch(() => caches.match(req, { ignoreSearch: true }).then(r => r || Response.error()))
  );
});
