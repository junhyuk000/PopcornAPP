const CACHE_NAME = "popcorn-cache-v1";
const urlsToCache = [
  "/",
  "/static/css/styles.css",
  // "/static/js/main.js",
  "/static/icons/icon-128x128.png",
  "/static/icons/icon-512x512.png"
];

// 설치 이벤트: 파일 캐싱
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(urlsToCache);
    })
  );
});

// 요청 가로채기 및 캐싱된 데이터 제공
self.addEventListener("fetch", (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request);
    })
  );
});

// 새로운 캐시 적용 시 기존 캐시 삭제
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      );
    })
  );
});
