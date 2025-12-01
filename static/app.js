/* =========================
   Compat Result Page Module
   ========================= */
(function () {
  function el(id) { return document.getElementById(id); }

  function keyVariants(s) {
    const raw = (s || "").toString().trim().toLowerCase();
    if (!raw) return [];
    const plusToSpace = raw.replace(/\+/g, " ");
    const cleaned = plusToSpace.replace(/\s+/g, " ").trim();
    const alnumSpace = cleaned.replace(/[^a-z0-9 ]/g, "").replace(/\s+/g, " ").trim();
    const noSpace = alnumSpace.replace(/ /g, "");
    const underscore = alnumSpace.replace(/ /g, "_");
    const out = [alnumSpace, noSpace, underscore].filter(Boolean);
    return Array.from(new Set(out));
  }

  function findRecord(db, a, b) {
    const av = keyVariants(a);
    const bv = keyVariants(b);
    for (const x of av) for (const y of bv) {
      const k1 = `${x}||${y}`;
      if (db[k1]) return { rec: db[k1], key: k1, swapped: false };
      const k2 = `${y}||${x}`;
      if (db[k2]) return { rec: db[k2], key: k2, swapped: true };
    }
    return null;
  }

  function statusMeta(code) {
    switch ((code || "").toUpperCase()) {
      case "C": return { cls: "st-c",  text: "Compatible (ผสมร่วมได้)",   status: "C"  };
      case "I": return { cls: "st-i",  text: "Incompatible (ห้ามผสม)",    status: "I"  };
      case "U": return { cls: "st-u",  text: "Uncertain (ไม่ชัดเจน)",      status: "U"  };
      default:  return { cls: "st-nd", text: "No data (ไม่มีข้อมูล)",      status: "ND" };
    }
  }

  async function initCompatResultPage() {
    const root = el("compatResultRoot");
    if (!root) return;

    // เซ็ตลิงก์ปุ่มให้ “ชัวร์” ทั้ง Pages/Flask (แก้ปัญหาไป compat_index.html แล้ว 404)
    const urls = (window.__URLS || {});
    const btnNew = el("btnNewCheck");
    const btnHome = el("btnHome");
    if (btnNew) btnNew.href = urls.newCheck || "./compatibility.html";
    if (btnHome) btnHome.href = urls.home || "./index.html";

    // Querystring
    const qs = new URLSearchParams(window.location.search);
    const drugA = qs.get("drug_a") || qs.get("drugA") || "";
    const drugB = qs.get("drug_b") || qs.get("drugB") || "";

    el("drugA").textContent = drugA || "—";
    el("drugB").textContent = drugB || "—";

    // Loading state
    root.dataset.status = "LD";
    const statusPill = el("statusPill");
    const statusText = el("statusText");
    const noteText = el("noteText");
    const refWrap = el("refWrap");
    const refText = el("refText");
    const debugLine = el("debugLine");

    if (statusPill) statusPill.className = "status-pill st-loading";
    if (statusText) statusText.textContent = "Loading...";
    if (noteText) noteText.textContent = "กำลังโหลดข้อมูล...";
    if (refWrap) refWrap.hidden = true;
    if (debugLine) debugLine.hidden = true;

    // Fetch lookup db
    const lookupUrl = urls.lookup || "./static/compat_lookup.json";

    try {
      const res = await fetch(lookupUrl, { cache: "no-store" });
      if (!res.ok) throw new Error(`lookup fetch failed: ${res.status}`);
      const db = await res.json();

      const found = findRecord(db, drugA, drugB);
      const rec = found ? found.rec : null;

      const code = rec && rec.status ? rec.status : "ND";
      const meta = statusMeta(code);

      // IMPORTANT: ตั้งค่า data-status เพื่อให้ CSS เปลี่ยนสีตามเงื่อนไข
      root.dataset.status = meta.status;

      if (statusPill) statusPill.className = `status-pill ${meta.cls}`;
      if (statusText) statusText.textContent = meta.text;

      // Note priority: summary_th > note_th > fallback
      const summaryTh = (rec && rec.summary_th) ? String(rec.summary_th).trim() : "";
      const noteTh = (rec && rec.note_th) ? String(rec.note_th).trim() : "";
      const note = summaryTh || noteTh || "ไม่พบข้อมูลความเข้ากันได้ของยาคู่นี้ (No data).";

      if (noteText) noteText.textContent = note;

      const ref = (rec && rec.reference) ? String(rec.reference).trim() : "";
      if (refWrap) {
        refWrap.hidden = !ref;
        if (refText) refText.textContent = ref;
      }

      // Debug (ถ้าต้องการดู key ที่เจอ)
      if (debugLine && found) {
        debugLine.hidden = false;
        debugLine.textContent = `lookup key = ${found.key}${found.swapped ? " (swapped)" : ""}`;
      }
    } catch (err) {
      // Fail-safe
      root.dataset.status = "ND";
      if (statusPill) statusPill.className = "status-pill st-nd";
      if (statusText) statusText.textContent = "No data (ไม่มีข้อมูล)";
      if (noteText) noteText.textContent = "โหลดฐานข้อมูลความเข้ากันได้ไม่สำเร็จ กรุณาลองใหม่";
      if (refWrap) refWrap.hidden = true;

      if (debugLine) {
        debugLine.hidden = false;
        debugLine.textContent = `error: ${err && err.message ? err.message : err}`;
      }
    }
  }

  document.addEventListener("DOMContentLoaded", initCompatResultPage);
})();
