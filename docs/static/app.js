// ==========================
// Service Worker (single source of truth)
// ==========================
(() => {
  if (!("serviceWorker" in navigator)) return;

  const SW_VERSION = "2025-11-30-07";
  const SW_URL = `./service-worker.js?v=${SW_VERSION}`;
  const SCOPE = "./";

  async function cleanupOldSW() {
    try {
      const regs = await navigator.serviceWorker.getRegistrations();
      await Promise.all(regs.map(async (r) => {
        const u = (r && r.active && r.active.scriptURL) || r.scriptURL || "";
        const isBad =
          u.includes("/static/service-worker.js") ||
          u.includes("static/service-worker.js") ||
          (u.includes("/service-worker.js") && !u.includes(`v=${SW_VERSION}`));
        if (isBad) await r.unregister();
      }));
    } catch (_) {}
  }

  async function registerSW() {
    await cleanupOldSW();
    const reg = await navigator.serviceWorker.register(SW_URL, { scope: SCOPE });
    try { await reg.update(); } catch (_) {}
  }

  window.addEventListener("load", () => {
    registerSW().catch(console.error);
  });
})();
