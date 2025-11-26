/* docs/static/service-worker.js */
const VERSION = "2025-11-27-04";
const CACHE_NAME = `nmc-cache-${VERSION}`;

// ✅ cache เฉพาะไฟล์ใน origin เดียวกัน (ห้ามใส่ลิงก์ข้ามโดเมน) เพื่อลด addAll fail
const PRECACHE_URLS = [
  "./",
  "./index.html",
  "./compatibility.html",
  "./compatibility_result.html",
  "./static/style.css",
  "./static/compat_lookup.json",
  "./static/manifest.webmanifest",
  "./static/icons/icon-192.png",
  "./static/icons/icon-512.png"
];

self.addEventListener("install", (event) => {
  self.skipWaiting();
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE_NAME);

    // ✅ อย่าใช้ cache.addAll() เพราะถ้าไฟล์ใดไฟล์หนึ่งพัง = พังทั้งชุด
    for (const url of PRECACHE_URLS) {
      try {
        await cache.add(new Request(url, { cache: "reload" }));
      } catch (err) {
        // ปล่อยผ่านเพื่อไม่ให้ install fail
        // console.warn("[SW] precache failed:", url, err);
      }
    }
  })());
});

self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)));
    await self.clients.claim();
  })());
});

async function networkFirst(request, { noStore = false } = {}) {
  const cache = await caches.open(CACHE_NAME);

  // ✅ บังคับ JSON สำคัญให้ network มากที่สุด
  const req = noStore ? new Request(request, { cache: "no-store" }) : request;

  try {
    const fresh = await fetch(req);
    if (fresh && fresh.ok) {
      cache.put(request, fresh.clone());
      return fresh;
    }
    // ถ้าได้ response แปลก ๆ ก็ fallback
    const cached = await cache.match(request);
    return cached || fresh;
  } catch (err) {
    const cached = await cache.match(request);
    if (cached) return cached;
    return new Response("Offline", { status: 503, headers: { "Content-Type": "text/plain" } });
  }
}

async function staleWhileRevalidate(request) {
  const cache = await caches.open(CACHE_NAME);
  const cached = await cache.match(request);

  const fetchPromise = fetch(request)
    .then((res) => {
      if (res && res.ok) cache.put(request, res.clone());
      return res;
    })
    .catch(() => null);

  return cached || fetchPromise || new Response("", { status: 504 });
}

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;

  const url = new URL(req.url);

  // ✅ ไม่ cache ของข้าม origin (ลดปัญหา request failed)
  if (url.origin !== self.location.origin) return;

  const accept = req.headers.get("accept") || "";
  const isHTML = req.mode === "navigate" || accept.includes("text/html");
  const isCompatJSON = url.pathname.endsWith("/static/compat_lookup.json");

  if (isHTML) {
    event.respondWith(networkFirst(req));
    return;
  }

  // ✅ JSON ตัวนี้ต้องชนะ cache เสมอ (เวลาคุณแก้ compat_lookup.json)
  if (isCompatJSON) {
    event.respondWith(networkFirst(req, { noStore: true }));
    return;
  }

  // ไฟล์อื่น ๆ (css/js/png) ใช้ SWR
  event.respondWith(staleWhileRevalidate(req));
});
