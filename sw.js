const C={"prefix":"/MPHILL-research-2026/","namespace":"ted2-public-b147d8a1feab-","cache":"ted2-public-b147d8a1feab-43a818f09fa15917d8fa","enabled":true,"limit":60};
/* Only versioned public images/CSS/JS are cached. HTML, API, admin, forms and media documents never enter CacheStorage. */
self.addEventListener('install', event => { self.skipWaiting(); });
self.addEventListener('activate', event => event.waitUntil((async () => {
  for (const name of await caches.keys()) if (name.startsWith(C.namespace) && (!C.enabled || name !== C.cache)) await caches.delete(name);
  await self.clients.claim();
})()));
function allowed(request) {
  if (!C.enabled || request.method !== 'GET' || request.headers.has('range')) return false;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin || !url.pathname.startsWith(C.prefix)) return false;
  const path = url.pathname.slice(C.prefix.length);
  return /^public-media\/[a-f0-9]{64}\.(jpg|png|webp)$/.test(path) ||
    (/^assets\/(site\.css|site\.js|experience\.js)$/.test(path) && /^[a-f0-9]{16}$/.test(url.searchParams.get('v') || ''));
}
self.addEventListener('fetch', event => {
  if (!allowed(event.request)) return;
  event.respondWith((async () => {
    let cache;
    try { cache = await caches.open(C.cache); const existing = await cache.match(event.request); if (existing) return existing; }
    catch { return fetch(event.request); }
    const response = await fetch(event.request);
    const length = Number(response.headers.get('Content-Length') || 0);
    if (response.ok && response.type === 'basic' && !/no-store|private/i.test(response.headers.get('Cache-Control') || '') && length > 0 && length <= 1048576) {
      try {
        await cache.put(event.request, response.clone());
        const keys = await cache.keys(); for (const key of keys.slice(0, Math.max(0, keys.length - C.limit))) await cache.delete(key);
      } catch { /* Storage limits must never prevent a valid network response. */ }
    }
    return response;
  })());
});
