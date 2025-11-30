// docs/static/app.js (หรือแก้เฉพาะส่วนนี้)
(function () {
  if (!("serviceWorker" in navigator)) return;
  navigator.serviceWorker
    .register("./service-worker.js?v=2025-11-30-04", { scope: "./" })
    .catch(console.error);
})();
