const CACHE_NAME = 'pdei-exocortex-v1';
const ASSETS = [
  '/web',
  '/web/index.html',
  'https://unpkg.com/react@18/umd/react.development.js',
  'https://unpkg.com/react-dom@18/umd/react-dom.development.js',
  'https://unpkg.com/@babel/standalone/babel.min.js',
  'https://cdn.jsdelivr.net/npm/marked/marked.min.js'
];

// Install: Cache critical UI shell
self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
  );
});

// Fetch: Smart routing for Exocortex telemetry
self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);

  // 1. API Calls: Network First (Critical for Live Forge Math)
  if (url.pathname.startsWith('/api/')) {
    e.respondWith(
      fetch(e.request).catch(() => caches.match(e.request))
    );
    return;
  }

  // 2. Static Assets: Stale-While-Revalidate
  e.respondWith(
    caches.match(e.request).then((response) => {
      const fetchPromise = fetch(e.request).then((networkResponse) => {
        caches.open(CACHE_NAME).then((cache) => {
          cache.put(e.request, networkResponse.clone());
        });
        return networkResponse;
      });
      return response || fetchPromise;
    })
  );
});