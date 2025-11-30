/* docs/static/app.js */
/* global window, document, navigator, caches */
(() => {
  const BUILD = "2025-11-30"; // เปลี่ยนวันตรงนี้ที่เดียวพอ
  const SW_URL = new URL("./service-worker.js", window.location.href).href;

  // ===== footer auto update (กันหน้าเก่าชอบขึ้น "update " ว่าง ๆ) =====
  try {
    document.querySelectorAll("footer p").forEach((p) => {
      const t = (p.textContent || "").trim();
      if (/\|\s*update\s*$/i.test(t)) p.textContent = `${t} ${BUILD}`;
    });
  } catch (_) {}

  // ===== Service Worker =====
  if (!("serviceWorker" in navigator)) return;

  (async () => {
    // 1) unregister SW เก่าที่ scriptURL ไม่ตรง (รวมถึงตัวที่เคยใส่ ?v=... และ /static/service-worker.js)
    const regs = await navigator.serviceWorker.getRegistrations();
    await Promise.all(
      regs.map(async (reg) => {
        const activeUrl = reg.active?.scriptURL || reg.installing?.scriptURL || reg.waiting?.scriptURL || "";
        if (activeUrl && activeUrl !== SW_URL) {
          await reg.unregister();
        }
      })
    );

    // 2) ลบ cache เก่า (ชื่อขึ้นต้น nmc-)
    if (window.caches) {
      const keys = await caches.keys();
      await Promise.all(keys.filter((k) => k.startsWith("nmc-")).map((k) => caches.delete(k)));
    }

    // 3) register SW ใหม่ “ตัวเดียว” (ไม่ใส่ ?v=... เพื่อกัน redundant)
    const reg = await navigator.serviceWorker.register("./service-worker.js", {
      scope: "./",
      updateViaCache: "none"
    });

    // 4) บังคับ update ทันที + ถ้ามี waiting ให้ข้าม waiting แล้ว reload 1 ครั้ง
    await reg.update();

    if (reg.waiting) reg.waiting.postMessage({ type: "SKIP_WAITING" });

    let reloaded = false;
    navigator.serviceWorker.addEventListener("controllerchange", () => {
      if (reloaded) return;
      reloaded = true;
      window.location.reload();
    });
  })().catch((e) => console.warn("[app.js] SW setup failed:", e));
})();
