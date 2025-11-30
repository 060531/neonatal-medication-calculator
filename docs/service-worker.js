/* docs/service-worker.js */
const VERSION = "2025-11-30-07";          // เปลี่ยนเลขนี้เมื่อปล่อยเวอร์ชันใหม่
const CACHE_NAME = `nmc-${VERSION}`;
const CACHE_PREFIX = "nmc-";

const CORE = [
  "./",
  "./index.html",
  "./home.html",
  "./compatibility.html",
  "./compatibility_result.html",
  "./static/style.css",
  "./static/app.js",
  "./static/manifest.webmanifest",
  "./static/icons/icon-192.png",
  "./static/icons/icon-512.png",
  "./static/compat_lookup.json"
];

self.addEventListener("install", (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE_NAME);

    // cache ทีละไฟล์: ไฟล์ไหนพังให้ข้าม (กัน install ล้ม)
    for (const u of CORE) {
      try {
        await cache.add(new Request(u, { cache: "reload" }));
      } catch (e) {
        console.warn("[SW] skip cache:", u, e);
      }
    }

    await self.skipWaiting();
  })());
});

self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(
      keys.map((k) => (k.startsWith(CACHE_PREFIX) && k !== CACHE_NAME ? caches.delete(k) : null))
    );
    await self.clients.claim();
  })());
});

// ให้หน้าเว็บสั่งข้าม waiting ได้
self.addEventListener("message", (event) => {
  if (event.data && event.data.type === "SKIP_WAITING") self.skipWaiting();
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;

  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  // compat_lookup.json = network-first (กันข้อมูลค้าง)
  if (url.pathname.endsWith("/static/compat_lookup.json")) {
    event.respondWith((async () => {
      const cache = await caches.open(CACHE_NAME);
      try {
        const fresh = await fetch(req, { cache: "no-store" });
        cache.put(req, fresh.clone());
        return fresh;
      } catch (e) {
        const cached = await cache.match(req);
        return cached || new Response("{}", { headers: { "content-type": "application/json" } });
      }
    })());
    return;
  }

  // HTML navigation = network-first (กันหน้าเก่า)
  const accept = req.headers.get("accept") || "";
  const isHTML = req.mode === "navigate" || accept.includes("text/html");
  if (isHTML) {
    event.respondWith((async () => {
      const cache = await caches.open(CACHE_NAME);
      try {
        const fresh = await fetch(req);
        cache.put(req, fresh.clone());
        return fresh;
      } catch (e) {
        const cached = await cache.match(req);
        return cached || cache.match("./index.html") || fetch("./index.html");
      }
    })());
    return;
  }

  // asset อื่น ๆ = cache-first
  event.respondWith((async () => {
    const cache = await caches.open(CACHE_NAME);
    const cached = await cache.match(req);
    if (cached) return cached;

    const fresh = await fetch(req);
    cache.put(req, fresh.clone());
    return fresh;
  })());
});
