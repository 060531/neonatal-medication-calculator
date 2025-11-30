/* docs/service-worker.js */
const VERSION = "2025-11-30-01";
const CACHE = `nmcalc-${VERSION}`;

// cache เฉพาะไฟล์ที่ “ต้องมี” และมีอยู่จริง
const CORE = [
  "./",
  "./index.html",
  "./static/style.css",
  "./static/app.js",
  "./static/manifest.webmanifest",
  "./static/icons/icon-192.png",
  "./static/icons/icon-512.png",
];

self.addEventListener("install", (event) => {
  self.skipWaiting();
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE);

    // สำคัญ: ใช้ allSettled + fetch ทีละไฟล์ → มีไฟล์ใดพัง จะไม่ทำให้ install พังทั้งชุด
    await Promise.allSettled(
      CORE.map(async (url) => {
        try {
          const res = await fetch(new Request(url, { cache: "no-store" }));
          if (res.ok) await cache.put(url, res.clone());
        } catch (_) {}
      })
    );
  })());
});

self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(
      keys
        .filter((k) => k.startsWith("nmcalc-") && k !== CACHE)
        .map((k) => caches.delete(k))
    );
    await self.clients.claim();
  })());
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  const url = new URL(req.url);

  // 1) ไฟล์ฐานข้อมูล compatibility ต้อง "network ตลอด" เพื่อลดปัญหาอ่านค่าเก่า
  if (url.pathname.endsWith("/static/compat_lookup.json")) {
    event.respondWith(fetch(req, { cache: "no-store" }));
    return;
  }

  // 2) HTML ใช้ network-first (ถ้าล่มค่อย fallback cache)
  if (req.method === "GET" && req.headers.get("accept")?.includes("text/html")) {
    event.respondWith((async () => {
      const cache = await caches.open(CACHE);
      try {
        const fresh = await fetch(req, { cache: "no-store" });
        if (fresh.ok) cache.put(req, fresh.clone()).catch(() => {});
        return fresh;
      } catch (_) {
        return (await cache.match(req, { ignoreSearch: true })) || Response.error();
      }
    })());
    return;
  }

  // 3) ไฟล์อื่น ๆ cache-first
  event.respondWith((async () => {
    const cache = await caches.open(CACHE);
    const cached = await cache.match(req, { ignoreSearch: true });
    if (cached) return cached;

    const res = await fetch(req);
    if (res.ok) cache.put(req, res.clone()).catch(() => {});
    return res;
  })());
});
