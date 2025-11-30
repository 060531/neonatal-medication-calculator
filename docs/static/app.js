/* docs/static/app.js */
(() => {
  const SW_VERSION = "2025-11-30-08";
  const SW_URL = `./service-worker.js?v=${SW_VERSION}`;

  async function registerSW() {
    if (!("serviceWorker" in navigator)) return;

    // ล้าง SW เก่าที่เคย register ผิด path (/static/service-worker.js) หรือ scope แปลก ๆ
    try {
      const regs = await navigator.serviceWorker.getRegistrations();
      await Promise.all(
        regs.map(async (r) => {
          const u = (r && r.active && r.active.scriptURL) || (r && r.installing && r.installing.scriptURL) || "";
          if (u.includes("/static/service-worker.js") || u.includes("static/service-worker.js")) {
            await r.unregister();
          }
        })
      );
    } catch (_) {}

    // register ตัวใหม่ (ถูกต้อง: docs/service-worker.js)
    try {
      await navigator.serviceWorker.register(SW_URL, { scope: "./" });
    } catch (e) {
      console.warn("[SW] register failed:", e);
    }
  }

  window.addEventListener("load", registerSW);
})();
