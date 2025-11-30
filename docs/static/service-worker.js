// static/service-worker.js
const DISABLE_SW = true;

self.addEventListener("install", (event) => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    if (DISABLE_SW) {
      try { await self.registration.unregister(); } catch (e) {}
      try {
        const keys = await caches.keys();
        await Promise.all(keys.map((k) => caches.delete(k)));
      } catch (e) {}
      return;
    }
  })());
});
