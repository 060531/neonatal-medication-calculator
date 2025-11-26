/* docs/static/service-worker.js */
const VERSION = "2025-11-27-02";
const CACHE = `nmc-${VERSION}`;

// ใส่เฉพาะไฟล์ที่ "มีจริง" และเป็น same-origin เท่านั้น
const PRECACHE = [
  "./",
  "./index.html",
  "./compatibility.html",
  "./compatibility_result.html",
  "./static/style.css",
  "./static/compat_lookup.json",
  "./static/icons/icon-192.png",
  "./static/icons/icon-512.png",
  "./static/manifest.webmanifest",
];

self.addEventListener("install", (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE);
    // ทนพลาด: ไฟล์ไหนพังคือข้าม ไม่ทำให้ install ล้มทั้งชุด
    await Promise.allSettled(PRECACHE.map((u) => cache.add(u)));
    self.skipWaiting();
  })());
});

self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)));
    await self.clients.claim();
  })());
});

async function networkFirst(req) {
  const cache = await caches.open(CACHE);
  try {
    const fresh = await fetch(req, { cache: "no-store" });
    if (fresh && fresh.ok) cache.put(req, fresh.clone());
    return fresh;
  } catch (e) {
    const cached = await cache.match(req);
    if (cached) return cached;
    // fallback อย่างน้อยให้กลับหน้า index
    return cache.match("./index.html");
  }
}

async function cacheFirst(req) {
  const cached = await caches.match(req);
  if (cached) return cached;

  const fresh = await fetch(req);
  if (req.method === "GET" && fresh && fresh.ok) {
    const cache = await caches.open(CACHE);
    cache.put(req, fresh.clone());
  }
  return fresh;
}

self.addEventListener("fetch", (event) => {
  const req = event.request;
  const url = new URL(req.url);

  // network-first สำหรับหน้า HTML (กันหน้าเก่าค้าง)
  if (req.mode === "navigate" || req.destination === "document") {
    event.respondWith(networkFirst(req));
    return;
  }

  // network-first สำหรับ compat_lookup.json (อยากได้ข้อมูลล่าสุดเสมอ)
  if (url.pathname.endsWith("/compat_lookup.json")) {
    event.respondWith(networkFirst(req));
    return;
  }

  // ที่เหลือ cache-first
  event.respondWith(cacheFirst(req));
});
