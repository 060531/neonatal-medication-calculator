const CACHE = 'neo-medcalc-v1';
const ASSETS = [
  './',
  './index.html',
  './404.html',
  './static/manifest.webmanifest',
  './static/icons/icon-192.png',
  './static/icons/icon-512.png'
];

self.addEventListener('install', e=>{
  e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)));
});

self.addEventListener('activate', e=>{
  e.waitUntil(
    caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k))))
  );
});

self.addEventListener('fetch', e=>{
  e.respondWith(
    caches.match(e.request).then(cached => cached || fetch(e.request).catch(()=>{
      if (e.request.mode === 'navigate') return caches.match('./404.html');
    }))
  );
});
