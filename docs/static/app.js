/* docs/static/app.js
   Single place for:
   - SW cleanup + single SW registration
   - footer build/version stamp
*/
(() => {
  "use strict";

  // เปลี่ยนเลขนี้ทุกครั้งที่ต้องการบังคับ refresh client
  const BUILD = "2025-11-30-01";
  const SW_URL = `./service-worker.js?v=${encodeURIComponent(BUILD)}`;
  const SW_SCOPE = "./";

  // ---------------------------
  // Footer: auto stamp build
  // ---------------------------
  function stampFooter() {
    try {
      const p = document.querySelector("footer p");
      if (!p) return;

      const base = (p.textContent || "").trim();
      // ถ้ามี "| update" ให้แทนที่ต่อท้ายด้วย BUILD
      if (/\|\s*update/i.test(base)) {
        p.textContent = base.replace(/\|\s*update.*$/i, `| update ${BUILD}`);
      } else {
        p.textContent = `${base} | update ${BUILD}`.trim();
      }
    } catch (_) {}
  }

  // ---------------------------
  // Service Worker: harden
  // ---------------------------
  async function cleanupOldSW() {
    if (!("serviceWorker" in navigator)) return;

    const regs = await navigator.serviceWorker.getRegistrations();
    await Promise.all(regs.map(async (reg) => {
      const u = String(reg.active?.scriptURL || reg.installing?.scriptURL || reg.waiting?.scriptURL || "");

      // ล้าง SW เก่าที่เคย register ผิด path (เช่น ./static/service-worker.js) หรือเวอร์ชันเก่า
      const isOld =
        u.includes("/static/service-worker.js") ||
        u.includes("static/service-worker.js") ||
        u.includes("service-worker.js?v=2025-11-12-01");

      if (isOld) {
        try { await reg.unregister(); } catch (_) {}
      }
    }));
  }

  async function registerSW() {
    if (!("serviceWorker" in navigator)) return;

    try {
      await cleanupOldSW();

      const reg = await navigator.serviceWorker.register(SW_URL, { scope: SW_SCOPE });
      // ขอให้เช็ค update ทันที (ช่วยลดอาการหน้าเว็บค้างเวอร์ชันเก่า)
      try { await reg.update(); } catch (_) {}
    } catch (err) {
      console.warn("SW register failed:", err);
    }
  }

  // run
  stampFooter();
  window.addEventListener("load", () => { registerSW(); });
})();
