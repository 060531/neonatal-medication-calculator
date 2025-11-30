(() => {
  const qs = new URLSearchParams(location.search);
  if (qs.has("nosw")) return; // ใช้ตอนดีบัก/หลังรีเซ็ต: ?nosw=1

  if (!("serviceWorker" in navigator)) return;

  window.addEventListener("load", async () => {
    try {
      // 1) ล้าง registration เก่าที่เคยชี้ไป /static/service-worker.js
      const regs = await navigator.serviceWorker.getRegistrations();
      for (const r of regs) {
        const url =
          r.active?.scriptURL ||
          r.waiting?.scriptURL ||
          r.installing?.scriptURL ||
          "";
        if (url.includes("/static/service-worker.js")) {
          await r.unregister();
        }
      }

      // 2) register “ตัวเดียว” ที่รากโปรเจกต์ (ต้องมีไฟล์: docs/service-worker.js)
      const SW_URL = "./service-worker.js";
      const reg = await navigator.serviceWorker.register(SW_URL, { scope: "./" });

      // 3) บังคับให้เช็คอัปเดตทันที
      await reg.update();
    } catch (e) {
      console.warn("SW register failed:", e);
    }
  });
})();
