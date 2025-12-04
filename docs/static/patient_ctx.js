// static/patient_ctx.js
(function () {
  const KEY = "nmc_ctx_v1";

  function num(v) {
    const x = Number(v);
    return Number.isFinite(x) ? x : null;
  }

  function readFromUrl() {
    const p = new URLSearchParams(location.search);
    // รองรับชื่อ key ที่คุณใช้จริง
    const ctx = {
      pma_weeks: num(p.get("pma_weeks")),
      pma_days: num(p.get("pma_days")),
      calc: num(p.get("calc")),
      postnatal_days: num(p.get("postnatal_days")),
      bw: num(p.get("bw")),
    };
    // ถ้าไม่มีข้อมูลจริงๆ
    const hasAny = Object.values(ctx).some(v => v !== null);
    return hasAny ? ctx : null;
  }

  function readFromSession() {
    try {
      const raw = sessionStorage.getItem(KEY);
      if (!raw) return null;
      const obj = JSON.parse(raw);
      // sanitize
      const ctx = {
        pma_weeks: num(obj.pma_weeks),
        pma_days: num(obj.pma_days),
        calc: num(obj.calc),
        postnatal_days: num(obj.postnatal_days),
        bw: num(obj.bw),
      };
      const hasAny = Object.values(ctx).some(v => v !== null);
      return hasAny ? ctx : null;
    } catch {
      return null;
    }
  }

  function get() {
    return readFromUrl() || readFromSession();
  }

  function save(ctx) {
    sessionStorage.setItem(KEY, JSON.stringify(ctx));
  }

  function toQuery(ctx) {
    const p = new URLSearchParams();
    for (const [k, v] of Object.entries(ctx)) {
      if (v !== null && v !== undefined && v !== "") p.set(k, String(v));
    }
    return p.toString();
  }

  // เติม query ให้ลิงก์ทั้งหมด (กันซ้ำด้วยการเช็กว่าปลายทางมี pma_weeks/bw แล้วหรือยัง)
  function applyToLinks(selector, ctx) {
    const qs = toQuery(ctx);
    if (!qs) return;

    document.querySelectorAll(selector).forEach(a => {
      try {
        const u = new URL(a.getAttribute("href"), location.href);
        if (u.searchParams.has("pma_weeks") || u.searchParams.has("bw")) return;

        const add = new URLSearchParams(qs);
        for (const [k, v] of add.entries()) u.searchParams.set(k, v);

        a.setAttribute("href", u.pathname + "?" + u.searchParams.toString());
      } catch {
        // ignore
      }
    });
  }

  window.NMC = { get, save, toQuery, applyToLinks };
})();
