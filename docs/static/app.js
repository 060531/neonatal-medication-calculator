// ===============================
// Compatibility Result (Flask + Pages) - FINAL
// ===============================
(function () {
  const STATUS_MAP = {
    C:  { en: "Compatible",   th: "ผสมร่วมได้",  cls: "st-c"  },
    I:  { en: "Incompatible", th: "ห้ามผสม",     cls: "st-i"  },
    U:  { en: "Uncertain",    th: "ไม่ชัดเจน",   cls: "st-u"  },
    ND: { en: "No data",      th: "ไม่มีข้อมูล", cls: "st-nd" },
  };

  const $ = (id) => document.getElementById(id);

  function normDrug(s) {
    s = (s || "").trim().toLowerCase();
    s = s.replace(/\+/g, " ");        // เผื่อกรณี + หลุดมา
    s = s.replace(/&/g, " and ");
    s = s.replace(/[^\w]+/g, " ");    // keep a-z0-9_
    s = s.replace(/_/g, " ");
    s = s.replace(/\s+/g, " ").trim();
    return s;
  }

  async function fetchJsonFallback(urls) {
    let lastErr = null;
    for (const url of urls) {
      try {
        const r = await fetch(url, { cache: "no-store" });
        if (!r.ok) continue;
        return await r.json();
      } catch (e) {
        lastErr = e;
      }
    }
    if (lastErr) throw lastErr;
    throw new Error("Cannot fetch compat_lookup.json from all candidates.");
  }

  function asRecord(v) {
    if (!v) return null;
    if (typeof v === "string") return { status: v };
    if (typeof v === "object") return v;
    return null;
  }

  function defaultNoteTH(code) {
    switch (code) {
      case "C":  return "สามารถให้ร่วมสาย (Y-site) ได้ ภายใต้เงื่อนไขตามแหล่งอ้างอิง";
      case "I":  return "ไม่เข้ากัน/ห้ามผสมร่วมสาย (Y-site) แนะนำแยก line หรือ flush ก่อน-หลัง";
      case "U":  return "ข้อมูลยังไม่ชัดเจน แนะนำหลีกเลี่ยงการให้ร่วมสาย ใช้แยก line หรือ flush ก่อน-หลัง";
      case "ND": return "ไม่มีข้อมูลที่เชื่อถือได้ แนะนำหลีกเลี่ยงการให้ร่วมสาย (Y-site) ใช้แยก line หรือ flush ก่อน-หลัง";
      default:   return "ไม่มีข้อมูลที่เพียงพอ";
    }
  }

  function safeSetText(id, text) {
    const el = $(id);
    if (el) el.textContent = text;
  }

  async function runCompatResult() {
    const root = $("compatResultRoot");
    if (!root) return;

    const qs = new URLSearchParams(location.search);
    const drugA = qs.get("drug_a") || "";
    const drugB = qs.get("drug_b") || "";
    const debug = qs.get("debug") === "1";

    safeSetText("drugA", drugA || "—");
    safeSetText("drugB", drugB || "—");

    // loading state
    root.dataset.status = "LOADING";
    const pill = $("statusPill");
    if (pill) pill.className = "status-pill st-loading";
    safeSetText("statusText", "Loading");
    safeSetText("noteText", "กำลังโหลดข้อมูล...");
    if ($("refWrap")) $("refWrap").hidden = true;

    const v = qs.get("v") || Date.now();

    // Pages relative: .../docs/compatibility_result.html -> .../docs/static/compat_lookup.json
    const rel = new URL("./static/compat_lookup.json?v=" + v, location.href).href;

    // Flask absolute: /static/compat_lookup.json
    const abs = new URL("/static/compat_lookup.json?v=" + v, location.origin).href;

    const data = await fetchJsonFallback([rel, abs]);

    const keyAB = `${normDrug(drugA)}||${normDrug(drugB)}`;
    const keyBA = `${normDrug(drugB)}||${normDrug(drugA)}`; // เผื่ออนาคตมี lookup กลับด้าน
    const rec = asRecord(data[keyAB] || data[keyBA]);

    if (debug && $("debugLine")) {
      $("debugLine").hidden = false;
      $("debugLine").textContent = `Source: ${rel}  Key: ${keyAB}`;
    } else if ($("debugLine")) {
      $("debugLine").hidden = true;
    }

    const statusCode = (rec?.status || "ND").toUpperCase();
    const meta = STATUS_MAP[statusCode] || STATUS_MAP.ND;

    // ✅ ตั้ง theme ของหน้า (ภาพที่ 2: พื้นหลังตามเงื่อนไข)
    root.dataset.status = statusCode;

    if (pill) pill.className = `status-pill ${meta.cls}`;
    safeSetText("statusText", `${meta.en} (${meta.th})`);

    // ✅ priority: note_th > summary_th > note_en > summary_en > default
    const noteTH = (rec?.note_th || rec?.summary_th || "").trim();
    const noteEN = (rec?.note_en || rec?.summary_en || "").trim();
    const note = noteTH || noteEN || defaultNoteTH(statusCode);
    safeSetText("noteText", note);

    const ref = (rec?.reference || "").trim();
    if ($("refWrap")) {
      $("refWrap").hidden = !ref;
      if (ref) safeSetText("refText", ref);
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    runCompatResult().catch((e) => {
      const root = $("compatResultRoot");
      if (root) root.dataset.status = "ND";

      const pill = $("statusPill");
      if (pill) pill.className = "status-pill st-nd";

      safeSetText("statusText", "No data (ไม่มีข้อมูล)");
      safeSetText(
        "noteText",
        "โหลดข้อมูลไม่สำเร็จ (อาจติด cache/service worker) กรุณา Hard Reload หรือ Clear site data"
      );
      if ($("refWrap")) $("refWrap").hidden = true;

      if ($("debugLine")) {
        $("debugLine").hidden = false;
        $("debugLine").textContent = String(e);
      }
      console.error(e);
    });
  });
})();
