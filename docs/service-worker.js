/* docs/service-worker.js */
const VERSION = "2025-11-30-06";
const CACHE_NAME = `nmc-${VERSION}`;

// cache เฉพาะไฟล์ที่มีจริงใน docs/
const CORE = [
  "./",
  "./index.html",
  "./home.html",
  "./compatibility.html",
  "./compatibility_result.html",
  "./pma_template.html",
  "./drug_calculation.html",
  "./Medication_administration.html",
  "./static/style.css",
  "./static/manifest.webmanifest",
  "./static/icons/icon-192.png",
  "./static/icons/icon-512.png"
];

self.addEventListener("install", (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE_NAME);

    // cache ทีละไฟล์ ถ้าไฟล์ไหนพังก็ข้าม ไม่ให้ install ล้มทั้งชุด
    for (const u of CORE) {
      try {
        await cache.add(new Request(u, { cache: "reload" }));
      } catch (e) {
        // แค่ log ไว้ (จะเห็นใน DevTools > Console ของ service worker)
        console.warn("[SW] skip asset:", u, e);
      }
    }
    self.skipWaiting();
  })());
});

self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(
      keys.map(k => (k !== CACHE_NAME ? caches.delete(k) : null))
    );
    await self.clients.claim();
  })());
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  const url = new URL(req.url);

  // handle เฉพาะ same-origin
  if (url.origin !== self.location.origin) return;

  // 1) JSON lookup = network-only (กัน data ค้าง)
  if (url.pathname.endsWith("/static/compat_lookup.json")) {
    event.respondWith(fetch(req));
    return;
  }

  // 2) HTML = network-first แล้ว fallback cache
  const accept = req.headers.get("accept") || "";
  const isHTML = req.mode === "navigate" || accept.includes("text/html");

  if (isHTML) {
    event.respondWith((async () => {
      try {
        const fresh = await fetch(req);
        const cache = await caches.open(CACHE_NAME);
        cache.put(req, fresh.clone());
        return fresh;
      } catch (e) {
        const cached = await caches.match(req);
        return cached || caches.match("./index.html");
      }
    })());
    return;
  }

  // 3) asset อื่น ๆ = cache-first
  event.respondWith((async () => {
    const cached = await caches.match(req);
    if (cached) return cached;

    try {
      const fresh = await fetch(req);
      const cache = await caches.open(CACHE_NAME);
      cache.put(req, fresh.clone());
      return fresh;
    } catch (e) {
      // offline แล้วไม่เคย cache – ก็ปล่อย fail ไป
      throw e;
    }
  })());
});
