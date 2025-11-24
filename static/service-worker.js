// static/service-worker.js

// 1) เปลี่ยน version ทุกครั้งที่ deploy (ช่วยบังคับให้ browser โหลด cache ใหม่)
const CACHE_VERSION = "v2025-11-24-01";
const CACHE_NAME = `app-cache-${CACHE_VERSION}`;

// prefix สำหรับไฟล์ static บน GitHub Pages
// เช่น /neonatal-medication-calculator/static/
const STATIC_PREFIX = new URL("./static/", self.location).pathname;

// ถ้าเดิมคุณมี ASSETS เป็น array ของไฟล์อื่น ๆ ก็สามารถเพิ่มเข้าไปได้
const ASSETS = [
  `${STATIC_PREFIX}style.css`,
  `${STATIC_PREFIX}app.js`,
  `${STATIC_PREFIX}manifest.webmanifest`,
  // เพิ่มไฟล์ static อื่น ๆ ที่อยาก cache ล่วงหน้าได้ที่นี่
];

// ========== INSTALL ==========
self.addEventListener("install", (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
  );
});

// ========== ACTIVATE ==========
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((key) => key !== CACHE_NAME)
            .map((key) => caches.delete(key))
        )
      )
      .then(() => self.clients.claim())
  );
});

// ========== FETCH ==========
// ดักเฉพาะไฟล์ใต้ /static/ เท่านั้น ไม่ยุ่งกับ HTML/หน้า result
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // ทำงานเฉพาะ static files ของเรา
  if (
    url.origin === self.location.origin &&
    url.pathname.startsWith(STATIC_PREFIX)
  ) {
    event.respondWith(
      caches.match(event.request).then((cached) => {
        if (cached) return cached;

        return fetch(event.request).then((response) => {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, clone);
          });
          return response;
        });
      })
    );
  }
});
