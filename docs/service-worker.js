// docs/service-worker.js  (NO-CACHE SW)
const CACHE_PREFIX = "nmc-cache-";

self.addEventListener("install", () => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    // ลบ cache เก่าทั้งหมดของโปรเจกต์ (ถ้ามี)
    const keys = await caches.keys();
    await Promise.all(keys.filter(k => k.startsWith(CACHE_PREFIX)).map(k => caches.delete(k)));
    await self.clients.claim();
  })());
});

// ไม่ต้องมี fetch handler => เบราว์เซอร์ไป network ตรง ๆ, ไม่ดัก ไม่ cache
