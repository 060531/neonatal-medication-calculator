<<<<<<< Updated upstream
(function () {
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("./static/service-worker.js").catch(console.error);
  }
=======
/* docs/static/app.js */
(() => {
  "use strict";

  // เปลี่ยนค่า BUILD ทุกครั้งที่แก้เว็บ จะช่วยดูว่า update มาแล้วจริง
  const BUILD = "2025-11-30-02";

  // ✅ ปิด SW ชั่วคราวเพื่อให้เว็บอัปเดตจริง (แนะนำให้ทำแบบนี้ก่อนจนทุกอย่างนิ่ง)
  const DISABLE_SW = true;
  const SW_URL = "./service-worker.js";

  // ---------- Footer stamp (ให้ทุกหน้าขึ้น update เดียวกัน) ----------
  function stampFooter() {
    const nodes = document.querySelectorAll("[data-build]");
    nodes.forEach(el => (el.textContent = `update ${BUILD}`));
  }

  // ---------- Kill old SW + caches (เห็นผลจริง) ----------
  async function nukeSWAndCaches() {
    if (!("serviceWorker" in navigator)) return;
    try {
      const regs = await navigator.serviceWorker.getRegistrations();
      await Promise.all(regs.map(r => r.unregister()));
    } catch (e) {
      console.warn("SW unregister failed:", e);
    }

    if ("caches" in window) {
      try {
        const keys = await caches.keys();
        await Promise.all(keys.map(k => caches.delete(k)));
      } catch (e) {
        console.warn("Cache delete failed:", e);
      }
    }
  }

  // ---------- Optional: register SW later (ปิดไว้ก่อน) ----------
  async function registerSW() {
    if (!("serviceWorker" in navigator)) return;
    try {
      await navigator.serviceWorker.register(SW_URL, { scope: "./" });
    } catch (e) {
      console.warn("SW register failed:", e);
    }
  }

  window.__APP_BUILD__ = BUILD;

  document.addEventListener("DOMContentLoaded", async () => {
    stampFooter();

    if (DISABLE_SW) {
      await nukeSWAndCaches();
      return;
    }
    await registerSW();
  });
>>>>>>> Stashed changes
})();
