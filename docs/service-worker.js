/* docs/service-worker.js */
const VERSION = "2025-12-01-01";

self.addEventListener("install", (event) => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

// Network passthrough (ไม่ cache) เพื่อไม่ให้ค้างเวอร์ชัน/ไม่พังจาก 404
self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  event.respondWith(fetch(event.request));
});
