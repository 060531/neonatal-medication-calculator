/* docs/static/app.js */
(() => {
  if (!("serviceWorker" in navigator)) return;

  const params = new URLSearchParams(location.search);
  const RESET = params.has("reset_sw");
  const SW_URL = "./service-worker.js"; // อยู่ที่ docs/service-worker.js

  async function nukeAllSWAndCaches() {
    const regs = await navigator.serviceWorker.getRegistrations();
    await Promise.all(regs.map((r) => r.unregister()));
    const keys = await caches.keys();
    await Promise.all(keys.map((k) => caches.delete(k)));
  }

  async function unregisterLegacyOnly() {
    const regs = await navigator.serviceWorker.getRegistrations();
    await Promise.all(
      regs
        .filter((r) => {
          const url =
            r?.active?.scriptURL ||
            r?.waiting?.scriptURL ||
            r?.installing?.scriptURL ||
            "";
          return url.includes("/static/service-worker.js");
        })
        .map((r) => r.unregister())
    );
  }

  async function main() {
    if (RESET) {
      await nukeAllSWAndCaches();
      params.delete("reset_sw");
      const q = params.toString();
      location.replace(location.pathname + (q ? `?${q}` : "") + location.hash);
      return;
    }

    await unregisterLegacyOnly();
    await navigator.serviceWorker.register(SW_URL, { scope: "./" });
  }

  main().catch(console.error);
})();

document.querySelectorAll("[data-build]").forEach((el) => {
  const d = new Date(document.lastModified);
  el.textContent = isNaN(d) ? document.lastModified : d.toISOString().slice(0, 10);
});
