
const CACHE_NAME = "student-info-v1";

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) =>
      cache.addAll(["/login", "/static/manifest.json"])
    )
  );

  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== CACHE_NAME)
          .map((key) => caches.delete(key))
      )
    )
  );

  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  const url = new URL(request.url);

  // Never cache login submissions or other POST requests.
  if (request.method !== "GET") return;

  // Do not cache authenticated pages or student records.
  if (
    url.origin !== self.location.origin ||
    url.pathname === "/login" ||
    url.pathname === "/logout" ||
    url.pathname.includes("student")
  ) {
    return;
  }

  // Only cache static assets.
  if (url.pathname.startsWith("/static/")) {
    event.respondWith(
      caches.match(request).then((cached) => {
        return cached || fetch(request);
      })
    );
  }
});
