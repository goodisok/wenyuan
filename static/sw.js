const CACHE = "wenyuan-v11";
const PRECACHE = ["/static/manifest.json"];

const HTML_PATHS = new Set(["/", "/chart", "/privacy"]);

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(PRECACHE)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

function isStatic(pathname) {
  return pathname.startsWith("/static/");
}

self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  const url = new URL(e.request.url);
  if (url.origin !== self.location.origin) return;
  if (url.pathname.startsWith("/api/")) return;

  // HTML: always prefer network so template/CSS updates ship immediately.
  if (e.request.mode === "navigate" || HTML_PATHS.has(url.pathname)) {
    e.respondWith(
      fetch(e.request).catch(() => caches.match(e.request))
    );
    return;
  }

  if (!isStatic(url.pathname)) return;

  // Static: stale-while-revalidate
  e.respondWith(
    caches.open(CACHE).then(async (cache) => {
      const cached = await cache.match(e.request);
      const networkPromise = fetch(e.request).then((res) => {
        if (res.ok) cache.put(e.request, res.clone());
        return res;
      });
      return cached || networkPromise;
    })
  );
});
