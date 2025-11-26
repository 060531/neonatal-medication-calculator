/* eslint-disable no-restricted-globals */
const CACHE_NAME = "nmcal-v2025-11-27-02";

// install: ไม่ต้อง precache หนัก ๆ ก็ได้ แต่ให้ข้าม waiting เพื่ออัปเดตเร็ว
self.addEventListener("install", (event) => {
  self.skipWaiting();
});

// activate: ล้าง cache เก่า + claim clients
self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.map(k => (k !== CACHE_NAME ? caches.delete(k) : Promise.resolve())));
    await self.clients.claim();
  })());
});

// fetch strategy:
// - ถ้าเป็น "navigate" (หน้า HTML) => network-first (แก้ปัญหา GH ค้างหน้าเก่า)
// - ไฟล์อื่น => stale-while-revalidate (ไว + อัปเดตได้)
self.addEventListener("fetch", (event) => {
  const req = event.request;

  // HTML pages
  if (req.mode === "navigate") {
    event.respondWith((async () => {
      try {
        return await fetch(req);
      } catch (e) {
        const cached = await caches.match(req);
        return cached || Response.error();
      }
    })());
    return;
  }

  // Static assets
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  event.respondWith((async () => {
    const cache = await caches.open(CACHE_NAME);
    const cached = await cache.match(req);

    const fetchPromise = fetch(req).then((res) => {
      if (res && res.ok) cache.put(req, res.clone());
      return res;
    }).catch(() => cached);

    return cached || fetchPromise;
  })());
});
