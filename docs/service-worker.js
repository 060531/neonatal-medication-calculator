/* docs/service-worker.js
   - Resilient: no cache.addAll hard-fail
   - Network-first with cache fallback
*/
"use strict";

const url = new URL(self.location.href);
const VERSION = url.searchParams.get("v") || "dev";
const CACHE_NAME = `nmc-${VERSION}`;

const CORE_ASSETS = [
  "./",
  "./index.html",
  "./static/style.css",
  "./static/app.js",
  "./static/manifest.webmanifest",
  "./static/compat_lookup.json",
  "./static/icons/icon-192.png",
  "./static/icons/icon-512.png",
];

self.addEventListener("install", (event) => {
  self.skipWaiting();
  event.waitUntil(
    (async () => {
      const cache = await caches.open(CACHE_NAME);
      // ใช้ allSettled กันพัง ถ้ามีบางไฟล์ 404
      await Promise.allSettled(
        CORE_ASSETS.map((p) => cache.add(p))
      );
    })()
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      const keys = await caches.keys();
      await Promise.all(
        keys
          .filter((k) => k.startsWith("nmc-") && k !== CACHE_NAME)
          .map((k) => caches.delete(k))
      );
      await self.clients.claim();
    })()
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;

  const reqUrl = new URL(req.url);

  // ทำเฉพาะ same-origin เพื่อไม่ยุ่งกับ CDN
  if (reqUrl.origin !== self.location.origin) return;

  event.respondWith(
    (async () => {
      const cache = await caches.open(CACHE_NAME);

      try {
        const fresh = await fetch(req);
        // cache เฉพาะ response ที่ OK
        if (fresh && fresh.ok) cache.put(req, fresh.clone());
        return fresh;
      } catch (_) {
        const cached = await cache.match(req, { ignoreSearch: false });
        if (cached) return cached;

        // fallback สำหรับหน้าเว็บ
        if (req.mode === "navigate") {
          const fallback = await cache.match("./index.html");
          if (fallback) return fallback;
        }
        throw _;
      }
    })()
  );
});
