/* docs/static/app.js  (single source of truth)
   - Single SW registration (root ./service-worker.js)
   - Unregister old/duplicate SW
   - Stamp build text into any element with [data-build]
*/
(() => {
  "use strict";

  const BUILD = "2025-12-01-01"; // เปลี่ยนตรงนี้เมื่ออยากให้ stamp เปลี่ยนชัด ๆ
  window.APP_BUILD = BUILD;

  // stamp footer / any place
  try {
    document.querySelectorAll("[data-build]").forEach(el => {
      el.textContent = `update ${BUILD}`;
    });
  } catch (_) {}

  if (!("serviceWorker" in navigator)) return;

  const SW_URL = `./service-worker.js?v=${encodeURIComponent(BUILD)}`;

  (async () => {
    try {
      // 1) Unregister SW เก่าทั้งหมดที่ไม่ใช่ตัวปัจจุบัน (กันค้าง/ซ้อน)
      const regs = await navigator.serviceWorker.getRegistrations();
      await Promise.all(
        regs.map(async (r) => {
          const u =
            (r.active && r.active.scriptURL) ||
            (r.waiting && r.waiting.scriptURL) ||
            (r.installing && r.installing.scriptURL) ||
            "";
          // เก็บเฉพาะที่เป็น root service-worker.js (จะมี ?v=... ก็ได้)
          const ok = u.includes("/service-worker.js");
          if (!ok) await r.unregister();
        })
      );

      // 2) Register ตัวเดียวที่ root
      const reg = await navigator.serviceWorker.register(SW_URL, { scope: "./" });

      // 3) ขอ update เพื่อดึงไฟล์ SW ใหม่ทันที
      if (reg && reg.update) reg.update();
    } catch (e) {
      console.error("SW bootstrap failed:", e);
    }
  })();
})();
