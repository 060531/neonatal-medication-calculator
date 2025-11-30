/* docs/service-worker.js */
const VERSION = "2025-11-30-04";
const CACHE_NAME = `nmc-${VERSION}`;

const CORE = [
  "./",
  "./index.html",
  "./compatibility.html",
  "./compatibility_result.html",
  "./static/style.css",
  "./static/manifest.webmanifest",
  "./static/icons/icon-192.png",
  "./static/icons/icon-512.png",
];

async function cachePutSafe(req, res) {
  try {
    const cache = await caches.open(CACHE_NAME);
    await cache.put(req, res.clone());
  } catch (_) {}
}

self.addEventListener("install", (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE_NAME);
    for (const u of CORE) {
      try { await cache.add(new Request(u, { cache: "reload" })); } catch (_) {}
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

  // ✅ JSON lookup = network-only / no-store (กันค้าง)
  if (url.pathname.endsWith("/static/compat_lookup.json")) {
    event.respondWith(fetch(req, { cache: "no-store" }));
    return;
  }

  const accept = req.headers.get("accept") || "";
  const isHTML = req.mode === "navigate" || accept.includes("text/html");

  // ✅ HTML = network-first
  if (isHTML) {
    event.respondWith((async () => {
      try {
        const fresh = await fetch(req, { cache: "no-store" });
        await cachePutSafe(req, fresh);
        return fresh;
      } catch (e) {
        const cached = await caches.match(req);
        return cached || caches.match("./index.html");
      }
    })());
    return;
  }

  // assets = cache-first
  event.respondWith((async () => {
    const cached = await caches.match(req);
    if (cached) return cached;
    const fresh = await fetch(req);
    await cachePutSafe(req, fresh);
    return fresh;
  })());
});
