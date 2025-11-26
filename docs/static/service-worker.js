/* docs/static/service-worker.js */
const VERSION = "2025-11-27-03";
const CACHE_STATIC = `static-${VERSION}`;
const CACHE_PAGES  = `pages-${VERSION}`;

// ใส่เฉพาะไฟล์ที่ "มีจริงแน่" และอยู่ใน repo
const PRECACHE = [
  "./static/style.css",
  "./static/manifest.webmanifest",
  "./static/icons/icon-192.png",
  "./static/icons/icon-512.png"
];

// --- helpers ---
async function safePrecache() {
  const cache = await caches.open(CACHE_STATIC);
  for (const url of PRECACHE) {
    try {
      // cache:reload ช่วยให้ SW ดึงไฟล์ใหม่จริงเวลาอัปเดต
      await cache.add(new Request(url, { cache: "reload" }));
    } catch (e) {
      // สำคัญ: "ห้ามล่ม" ถ้าไฟล์ไหนโหลดไม่ได้
      // ไม่งั้น install จะ fail แล้ว SW จะค้างวงจรเดิม
    }
  }
}

async function networkFirst(req, cacheName, ignoreSearch = false) {
  const cache = await caches.open(cacheName);
  try {
    const res = await fetch(req);
    if (res && res.ok) await cache.put(req, res.clone());
    return res;
  } catch (e) {
    const cached = await cache.match(req, { ignoreSearch });
    return cached || new Response("Offline", { status: 503 });
  }
}

async function staleWhileRevalidate(req, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(req);
  const freshPromise = fetch(req).then(res => {
    if (res && res.ok) cache.put(req, res.clone());
    return res;
  }).catch(() => null);

  return cached || (await freshPromise) || new Response("Offline", { status: 503 });
}

// --- lifecycle ---
self.addEventListener("install", (event) => {
  self.skipWaiting();
  event.waitUntil(safePrecache());
});

self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(k => !k.includes(VERSION)).map(k => caches.delete(k)));
    await self.clients.claim();
  })());
});

// --- fetch strategy ---
self.addEventListener("fetch", (event) => {
  const req = event.request;
  const url = new URL(req.url);

  // เฉพาะ same-origin
  if (url.origin !== self.location.origin) return;

  // หน้า purge ให้ผ่าน network ตรง ๆ
  if (url.pathname.endsWith("/purge_sw.html")) return;

  // *** สำคัญ: compat_lookup.json ให้ network-first เสมอ ***
  if (url.pathname.endsWith("/static/compat_lookup.json")) {
    event.respondWith(networkFirst(req, CACHE_PAGES, false));
    return;
  }

  // HTML/documents => network-first (กันติดหน้าเก่า)
  if (req.mode === "navigate" || req.destination === "document") {
    // ignoreSearch=true เพื่อไม่สร้าง cache แยกเป็นร้อยอันตาม ?drug_a=
    event.respondWith(networkFirst(req, CACHE_PAGES, true));
    return;
  }

  // assets => SWR
  if (["style", "script", "image", "font"].includes(req.destination)) {
    event.respondWith(staleWhileRevalidate(req, CACHE_STATIC));
    return;
  }
});
