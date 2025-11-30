/* docs/service-worker.js */
const VERSION = "2025-11-30-03";
const CACHE_NAME = `nmc-${VERSION}`;

const CORE = [
  "./",
  "./index.html",
  "./compatibility.html",
  "./compatibility_result.html",
  "./pma_template.html",
  "./drug_calculation.html",
  "./static/style.css",
  "./static/app.js",
  "./static/manifest.webmanifest",
  "./static/icons/icon-192.png",
  "./static/icons/icon-512.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE_NAME);
    for (const u of CORE) {
      try {
        await cache.add(new Request(u, { cache: "reload" }));
      } catch (_) {
        // ไม่ให้ SW ติดตั้งล้มทั้งชุด
      }
    }
    self.skipWaiting();
  })());
});

self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.map(k => (k !== CACHE_NAME ? caches.delete(k) : null)));
    await self.clients.claim();
  })());
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  const url = new URL(req.url);

  if (url.origin !== self.location.origin) return;

  // ✅ JSON lookup: network-only (กันค้าง) + no-store
  if (url.pathname.endsWith("/static/compat_lookup.json")) {
    event.respondWith(fetch(new Request(req.url, { cache: "no-store" })));
    return;
  }

  // ✅ HTML: network-first
  const accept = req.headers.get("accept") || "";
  const isHTML = req.mode === "navigate" || accept.includes("text/html");
  if (isHTML) {
    event.respondWith((async () => {
      try {
        const fresh = await fetch(req);
        const cache = await caches.open(CACHE_NAME);
        cache.put(req, fresh.clone());
        return fresh;
      } catch (_) {
        const cached = await caches.match(req);
        return cached || caches.match("./index.html");
      }
    })());
    return;
  }

  // ✅ assets: cache-first
  event.respondWith((async () => {
    const cached = await caches.match(req);
    if (cached) return cached;

    const fresh = await fetch(req);
    const cache = await caches.open(CACHE_NAME);
    cache.put(req, fresh.clone());
    return fresh;
  })());
});
