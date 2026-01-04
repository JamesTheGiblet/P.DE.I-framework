self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open('pdei-store').then((cache) => cache.addAll([
      '/',
      '/index.html',
    ])),
  );
});

self.addEventListener('fetch', (e) => {});