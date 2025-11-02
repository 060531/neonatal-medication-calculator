const CACHE = 'neo-medcalc-v1';
const ASSETS = [
  '/docs/',
  '/docs/index.html',
  '/docs/404.html',
  '/static/manifest.webmanifest',
  '/static/style.css',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png'
];

self.addEventListener('install', e=>{
  e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)));
});

self.addEventListener('activate', e=>{
  e.waitUntil(
    caches.keys().then(keys=>Promise.all(
      keys.filter(k=>k!==CACHE).map(k=>caches.delete(k))
    ))
  );
});

self.addEventListener('fetch', e=>{
  const req = e.request;
  e.respondWith(
    caches.match(req).then(cached => cached || fetch(req).catch(()=> {
      if (req.mode === 'navigate') return caches.match('/docs/404.html');
    }))
  );
});
