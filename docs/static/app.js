(() => {
  // ปิด PWA/SW สำหรับ GitHub Pages (docs) เพื่อตัดปัญหาเด้ง/รีโหลดวน
  const ENABLE_PWA = false;

  if (!("serviceWorker" in navigator)) return;

  if (!ENABLE_PWA) {
    // ถ้ามี SW เก่าค้างไว้ ให้ถอนออกแบบเงียบ ๆ (ไม่ reload เพื่อกัน loop)
    navigator.serviceWorker.getRegistrations()
      .then((regs) => Promise.all(regs.map((r) => r.unregister())))
      .catch(() => {});
    return;
  }

  // เปิดใช้เมื่อพร้อมเท่านั้น
  navigator.serviceWorker
    .register("./service-worker.js", { scope: "./" })
    .catch(console.error);
})();
