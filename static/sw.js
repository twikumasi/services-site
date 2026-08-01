/* Service worker for AH Automation Services.
   Caches the shell so the app opens instantly and shows a useful page when
   the phone has no signal — common inside plants and basements. */

const CACHE = 'ahauto-v2';
const SHELL = [
  '/',
  '/static/style.css',
  '/static/logo.svg',
  '/static/offline.html',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE)
      .then((cache) => cache.addAll(SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  // Never cache the admin area — stale client data would be misleading, and
  // cached pages must not survive a logout.
  if (url.pathname.startsWith('/admin')) return;

  // Pages: try the network first so content is fresh, fall back to cache.
  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req)
        .then((res) => {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(req, copy));
          return res;
        })
        .catch(() => caches.match(req).then((hit) => hit || caches.match('/static/offline.html')))
    );
    return;
  }

  // Stylesheets and scripts: network first. Serving these from cache would
  // freeze the site's appearance — a deployed CSS change would stay invisible
  // to anyone who had already loaded the old file.
  if (/\.(css|js)$/i.test(url.pathname)) {
    event.respondWith(
      fetch(req)
        .then((res) => {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(req, copy));
          return res;
        })
        .catch(() => caches.match(req))
    );
    return;
  }

  // Images and fonts: cache first. Uploaded photos and icons get unique
  // filenames, so a cached copy can never be out of date.
  event.respondWith(
    caches.match(req).then((hit) => hit || fetch(req).then((res) => {
      const copy = res.clone();
      caches.open(CACHE).then((c) => c.put(req, copy));
      return res;
    }))
  );
});
