/* static/patient_ctx.js
 * Neonatal Medication Calculator - Patient Context helper
 * - Reads ctx from URL query and/or sessionStorage
 * - Normalizes numbers
 * - Applies ctx to internal links (append query params)
 */
(function (global) {
  "use strict";

  const KEY = "nmc_patient_ctx_v1";
  const FIELDS = ["pma_weeks", "pma_days", "calc", "postnatal_days", "bw"];

  function isNil(v) { return v === null || v === undefined || v === ""; }

  function toNum(v) {
    if (isNil(v)) return null;
    const x = Number(v);
    return Number.isFinite(x) ? x : null;
  }

  function toInt(v) {
    const x = toNum(v);
    return x === null ? null : Math.trunc(x);
  }

  function clampInt(x, min, max) {
    if (x === null) return null;
    return Math.min(max, Math.max(min, x));
  }

  function normalize(raw) {
    if (!raw || typeof raw !== "object") return null;

    let pma_weeks = toInt(raw.pma_weeks);
    let pma_days  = toInt(raw.pma_days);
    let postnatal_days = toInt(raw.postnatal_days);
    let bw = toNum(raw.bw);

    // calc อาจเป็น "30.1 weeks" -> parseFloat
    let calc = null;
    if (!isNil(raw.calc)) {
      const s = String(raw.calc).trim();
      const f = Number.parseFloat(s);
      calc = Number.isFinite(f) ? f : toNum(raw.calc);
    }

    // sanitize ranges
    pma_weeks = clampInt(pma_weeks, 0, 80);
    pma_days  = clampInt(pma_days, 0, 6);
    postnatal_days = clampInt(postnatal_days, 0, 3650);
    bw = (bw !== null && bw >= 0 && bw <= 20) ? bw : (bw === null ? null : bw); // allow but keep realistic-ish

    // ถ้า calc ไม่มา แต่มี weeks/days -> คำนวณให้
    if (calc === null && pma_weeks !== null && pma_days !== null) {
      calc = pma_weeks + (pma_days / 7);
    }

    const ctx = { pma_weeks, pma_days, calc, postnatal_days, bw };

    // ถ้าทุกค่าเป็น null -> ถือว่าไม่มี ctx
    if (!FIELDS.some(k => ctx[k] !== null)) return null;

    return ctx;
  }

  function merge(a, b) {
    const out = Object.assign({}, a || {});
    if (b && typeof b === "object") {
      for (const k of FIELDS) {
        if (!isNil(b[k]) && b[k] !== null) out[k] = b[k];
      }
    }
    return normalize(out);
  }

  function readQuery(search) {
    const sp = new URLSearchParams(search || global.location.search || "");
    const obj = {};
    for (const k of FIELDS) {
      if (sp.has(k)) obj[k] = sp.get(k);
    }
    return normalize(obj);
  }

  function readStorage() {
    try {
      const s = global.sessionStorage.getItem(KEY);
      if (!s) return null;
      return normalize(JSON.parse(s));
    } catch (e) {
      return null;
    }
  }

  function setStorage(ctx) {
    const n = normalize(ctx);
    if (!n) return;
    try {
      global.sessionStorage.setItem(KEY, JSON.stringify(n));
    } catch (e) {}
  }

  function get() {
    const q = readQuery();
    const st = readStorage();
    const merged = merge(st, q); // query override storage
    if (merged) setStorage(merged);
    return merged;
  }

  // Apply ctx to internal links
  function applyToLinks(selector, ctx) {
    const c = normalize(ctx);
    if (!c) return;

    const nodes = global.document.querySelectorAll(selector);
    nodes.forEach(a => {
      const href = a.getAttribute("href");
      if (!href) return;

      // skip anchors / js / mailto / tel
      const low = href.trim().toLowerCase();
      if (low.startsWith("#") || low.startsWith("javascript:") || low.startsWith("mailto:") || low.startsWith("tel:")) return;

      // skip external absolute http(s)
      if (low.startsWith("http://") || low.startsWith("https://")) return;

      // split base / query / hash (รักษา relative path เดิมไว้)
      const hashIdx = href.indexOf("#");
      const qIdx = href.indexOf("?");
      const base = href.split("?")[0].split("#")[0];

      const oldQuery = (qIdx >= 0)
        ? href.slice(qIdx + 1, hashIdx >= 0 ? hashIdx : href.length)
        : "";

      const hash = (hashIdx >= 0) ? href.slice(hashIdx) : "";

      const sp = new URLSearchParams(oldQuery);
      // เติม/ทับด้วย ctx ล่าสุด
      for (const k of FIELDS) {
        if (c[k] !== null && c[k] !== undefined) {
          if (k === "bw") sp.set(k, Number(c[k]).toFixed(3));
          else if (k === "calc") sp.set(k, Number(c[k]).toFixed(1));
          else sp.set(k, String(c[k]));
        }
      }

      const newHref = base + "?" + sp.toString() + hash;
      a.setAttribute("href", newHref);
    });
  }

  global.NMC = {
    KEY,
    normalize,
    merge,
    readQuery,
    readStorage,
    set: setStorage,
    get,
    applyToLinks,
  };
})(window);
