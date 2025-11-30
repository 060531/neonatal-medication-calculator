/* docs/static/app.js */
(() => {
  if (!("serviceWorker" in navigator)) return;

  const SW_URL = "./service-worker.js?v=2025-11-30-06";
// (removed) legacy hint for old SW path

  window.addEventListener("load", async () => {
    try {
      // ล้างตัวเก่าที่เคย register ที่ /static/
      const regs = await navigator.serviceWorker.getRegistrations();
      await Promise.all(
        regs
          .filter(r => (r.active?.scriptURL || r.scriptURL || "").includes(OLD_SW_HINT))
          .map(r => r.unregister())
      );

      // ลงทะเบียนตัวใหม่ที่ root
      await navigator.serviceWorker.register(SW_URL, { scope: "./" });
    } catch (e) {
      console.error("SW init error:", e);
    }
  });
})();
