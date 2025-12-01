// ===============================
// Compatibility Result (Flask + Pages) - v2 (note_th first + reverse key)
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
    s = s.replace(/&/g, " and ");
    s = s.replace(/[^\w]+/g, " ");   // keep a-z0-9_
    s = s.replace(/_/g, " ");
    s = s.replace(/\s+/g, " ").trim();
    return s;
  }

  async function fetchJsonFallback(urls) {
    let lastErr = null;
    for (const url of urls) {
      try {
        const r = await fetch(url, {
          cache: "no-store",
          headers: { "cache-control": "no-cache" },
        });
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

  function setSafeText(id, text) {
    const el = $(id);
    if (el) el.textContent = text;
  }

  function setHidden(id, hidden) {
    const el = $(id);
    if (el) el.hidden = !!hidden;
  }

  async function runCompatResult() {
    const root = $("compatResultRoot");
    if (!root) return; // not on this page

    const drugAEl = $("drugA");
    const drugBEl = $("drugB");
    const pill = $("statusPill");
    const statusTextEl = $("statusText");
    const noteTextEl = $("noteText");
    const refTextEl = $("refText");

    if (!pill || !statusTextEl || !noteTextEl || !drugAEl || !drugBEl) return;

    const qs = new URLSearchParams(location.search);
    const drugA = (qs.get("drug_a") || "").trim();
    const drugB = (qs.get("drug_b") || "").trim();
    const debug = qs.get("debug") === "1";

    drugAEl.textContent = drugA || "—";
    drugBEl.textContent = drugB || "—";

    // initial state
    pill.className = "status-pill st-loading";
    statusTextEl.textContent = "Loading";
    noteTextEl.textContent = "กำลังโหลดข้อมูล...";
    setHidden("refWrap", true);

    // cache-bust
    const v = qs.get("v") || String(Date.now());

    // Pages: ./static/compat_lookup.json
    const rel = new URL("./static/compat_lookup.json?v=" + encodeURIComponent(v), location.href).href;
    // Flask: /static/compat_lookup.json
    const abs = new URL("/static/compat_lookup.json?v=" + encodeURIComponent(v), location.origin).href;

    const data = await fetchJsonFallback([rel, abs]);

    // try forward + reverse
    const key1 = `${normDrug(drugA)}||${normDrug(drugB)}`;
    const key2 = `${normDrug(drugB)}||${normDrug(drugA)}`;

    const rec = asRecord(data[key1]) || asRecord(data[key2]);

    // debug line
    if (debug) {
      setHidden("debugLine", false);
      setSafeText(
        "debugLine",
        `Source tried: [${rel}] then [${abs}] | Keys tried: ${k1} , ${k2} | Found: ${foundKey || "none"}`
      );
    } else {
      setHidden("debugLine", true);
    }

    const statusCode = String((rec && rec.status) ? rec.status : "ND").toUpperCase();
    const meta = STATUS_MAP[statusCode] || STATUS_MAP.ND;

    pill.className = `status-pill ${meta.cls}`;
    // จะโชว์อังกฤษหรือไทยก็ได้—เวอร์ชันนี้โชว์อังกฤษ + ไทยในวงเล็บ
    statusTextEl.textContent = `${meta.en} (${meta.th})`;

    // IMPORTANT: note_th/note_en มาก่อน summary_th/summary_en
    const noteTH = (rec?.note_th || rec?.summary_th || "").trim();
    const noteEN = (rec?.note_en || rec?.summary_en || "").trim();
    const note = noteTH || (noteEN ? noteEN : defaultNoteTH(statusCode));
    $("noteText").textContent = note;

    const ref = String((rec && rec.reference) || "").trim();
    if (ref && refTextEl) {
      setHidden("refWrap", false);
      refTextEl.textContent = ref;
    } else {
      setHidden("refWrap", true);
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    runCompatResult().catch((e) => {
      const pill = $("statusPill");
      if (pill) pill.className = "status-pill st-nd";
      setSafeText("statusText", "No data (ไม่มีข้อมูล)");
      setSafeText(
        "noteText",
        "โหลดข้อมูลไม่สำเร็จ: อาจติด cache / service worker ให้ลอง Hard Reload หรือ Clear site data"
      );
      setHidden("refWrap", true);
      setHidden("debugLine", false);
      setSafeText("debugLine", String(e));
      console.error(e);
    });
  });
})();
