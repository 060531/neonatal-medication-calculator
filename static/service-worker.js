const CACHE_VERSION = 'v1.0.0';
const STATIC_CACHE  = `static-${CACHE_VERSION}`;

const APP_SHELL = [
  '/', // หน้าแรก (Flask route '/')
  '/static/style.css',
  '/static/app.js',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/static/manifest.webmanifest',
  // ถ้าต้องการให้ออฟไลน์หน้าอื่น ๆ ด้วย ให้เพิ่ม path ของไฟล์นั้น ๆ อีก (เช่น /templates ที่เสิร์ฟเป็น route)
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then(cache => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== STATIC_CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const isHTML = req.headers.get('accept')?.includes('text/html');

  // HTML = network-first
  if (isHTML) {
    event.respondWith(
      fetch(req).then(res => {
        const copy = res.clone();
        caches.open(STATIC_CACHE).then(cache => cache.put(req, copy));
        return res;
      }).catch(() => caches.match(req).then(cached => cached || caches.match('/')))
    );
    return;
  }

  // Static = cache-first
  event.respondWith(
    caches.match(req).then(cached => {
      if (cached) return cached;
      return fetch(req).then(res => {
        if (res && (res.status === 200 || res.type === 'opaque')) {
          const copy = res.clone();
          caches.open(STATIC_CACHE).then(cache => cache.put(req, copy));
        }
        return res;
      }).catch(() => undefined);
    })
  );
});
