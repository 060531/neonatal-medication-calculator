// ===============================
// Compatibility Result (Flask + Pages)
// ===============================
(function () {
  const STATUS_MAP = {
    C: { en: "Compatible", th: "ผสมร่วมได้", cls: "st-c" },
    I: { en: "Incompatible", th: "ห้ามผสม", cls: "st-i" },
    U: { en: "Uncertain", th: "ไม่ชัดเจน", cls: "st-u" },
    ND:{ en: "No data", th: "ไม่มีข้อมูล", cls: "st-nd" },
  };

  const $ = (id) => document.getElementById(id);

  function normDrug(s) {
    s = (s || "").trim().toLowerCase();
    s = s.replace(/&/g, " and ");
    s = s.replace(/[^\w]+/g, " "); // word chars -> a-z0-9_
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

  async function runCompatResult() {
    const root = $("compatResultRoot");
    if (!root) return; // not on this page

    const qs = new URLSearchParams(location.search);
    const drugA = qs.get("drug_a") || "";
    const drugB = qs.get("drug_b") || "";
    const debug = qs.get("debug") === "1";

    $("drugA").textContent = drugA || "—";
    $("drugB").textContent = drugB || "—";

    // status pill initial
    const pill = $("statusPill");
    pill.className = "status-pill st-loading";
    $("statusText").textContent = "Loading";
    $("noteText").textContent = "กำลังโหลดข้อมูล...";
    $("refWrap").hidden = true;

    const v = qs.get("v") || Date.now();
    const rel = new URL("./static/compat_lookup.json?v=" + v, location.href).href;

    // Flask fallback: /static/compat_lookup.json (absolute root)
    const abs = new URL("/static/compat_lookup.json?v=" + v, location.origin).href;

    const data = await fetchJsonFallback([rel, abs]);

    const key = `${normDrug(drugA)}||${normDrug(drugB)}`;
    const rec = asRecord(data[key]);

    if (debug) {
      $("debugLine").hidden = false;
      $("debugLine").textContent = `Source: ${rel}  Key: ${key}`;
    } else {
      $("debugLine").hidden = true;
    }

    const statusCode = (rec?.status || "ND").toUpperCase();
    const meta = STATUS_MAP[statusCode] || STATUS_MAP.ND;

    pill.className = `status-pill ${meta.cls}`;
    $("statusText").textContent = meta.en;

    const noteTH = (rec?.summary_th || "").trim();
    const noteEN = (rec?.summary_en || "").trim();
    const note = noteTH || (noteEN ? noteEN : defaultNoteTH(statusCode));
    $("noteText").textContent = note;

    const ref = (rec?.reference || "").trim();
    if (ref) {
      $("refWrap").hidden = false;
      $("refText").textContent = ref;
    } else {
      $("refWrap").hidden = true;
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    runCompatResult().catch((e) => {
      const pill = $("statusPill");
      if (pill) {
        pill.className = "status-pill st-nd";
        $("statusText").textContent = "No data";
        $("noteText").textContent = "โหลดข้อมูลไม่สำเร็จ (อาจติด cache/service worker) กรุณารีเฟรชแบบ hard reload หรือ clear site data";
        $("refWrap").hidden = true;
        $("debugLine").hidden = false;
        $("debugLine").textContent = String(e);
      }
      console.error(e);
    });
  });
})();
