/* =========================
 * Compat Result Page (Pages + Flask)
 * ========================= */
(function initCompatResultPage() {
  const root = document.getElementById("compatResultRoot");
  if (!root) return;

  const $ = (id) => document.getElementById(id);

  const elDrugA = $("drugA");
  const elDrugB = $("drugB");
  const pill = $("statusPill");
  const statusText = $("statusText");
  const noteText = $("noteText");
  const refWrap = $("refWrap");
  const refText = $("refText");
  const debugLine = $("debugLine");

  const btnNew = $("btnNewCheck");
  const btnHome = $("btnHome");

  // --- Fix links (กันหลุดไป compat_index.html) ---
  const URLS = window.__URLS || {};
  const safeNew = URLS.newCheck || "./compatibility.html";
  const safeHome = URLS.home || "./index.html";
  if (btnNew) btnNew.setAttribute("href", safeNew);
  if (btnHome) btnHome.setAttribute("href", safeHome);

  // บังคับนำทางแบบชัดเจน (กันโค้ดอื่น intercept)
  function hardNav(href) {
    if (!href) return;
    window.location.assign(href);
  }
  if (btnNew) btnNew.addEventListener("click", (e) => { e.preventDefault(); hardNav(btnNew.getAttribute("href")); });
  if (btnHome) btnHome.addEventListener("click", (e) => { e.preventDefault(); hardNav(btnHome.getAttribute("href")); });

  // --- helpers ---
  const STATUS_MAP = {
    C: { cls: "st-c", text: "Compatible (ผสมร่วมได้)", fallbackNote: "ยาสามารถผสมร่วมกันได้" },
    I: { cls: "st-i", text: "Incompatible (ห้ามผสม)", fallbackNote: "ไม่ควรให้ร่วมกันใน line เดียวกัน (เสี่ยงไม่เข้ากัน/ความคงตัว)" },
    U: { cls: "st-u", text: "Uncertain (ไม่ชัดเจน)", fallbackNote: "ข้อมูลยังไม่ชัดเจน ควรหลีกเลี่ยงการผสมร่วมกัน" },
    ND:{ cls: "st-nd", text: "No data (ไม่มีข้อมูล)", fallbackNote: "ไม่พบข้อมูลความเข้ากันได้ของคู่นี้" }
  };

  function normalizeName(x) {
    return String(x || "")
      .trim()
      .replace(/\s+/g, " ")
      .toLowerCase();
  }

  function getQueryParam(name) {
    const u = new URL(window.location.href);
    return u.searchParams.get(name) || "";
  }

  function setStatus(code) {
    const s = STATUS_MAP[code] || STATUS_MAP.ND;
    root.dataset.status = code || "ND";

    pill.classList.remove("st-loading", "st-c", "st-i", "st-u", "st-nd");
    pill.classList.add(s.cls);

    statusText.textContent = s.text;
  }

  async function loadJson(url) {
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) throw new Error(`fetch failed: ${res.status}`);
    return await res.json();
  }

  // --- main ---
  (async () => {
    try {
      const aRaw = getQueryParam("drug_a");
      const bRaw = getQueryParam("drug_b");

      const aKey = normalizeName(aRaw);
      const bKey = normalizeName(bRaw);

      // แสดงชื่อจาก query ก่อน
      if (elDrugA) elDrugA.textContent = aRaw || "—";
      if (elDrugB) elDrugB.textContent = bRaw || "—";

      const lookupUrl = (window.__URLS && window.__URLS.lookup) ? window.__URLS.lookup : "./static/compat_lookup.json";
      const db = await loadJson(lookupUrl);

      const key1 = `${aKey}||${bKey}`;
      const key2 = `${bKey}||${aKey}`;
      const rec = db[key1] || db[key2] || null;

      if (debugLine) {
        debugLine.hidden = false;
        debugLine.textContent = `lookup key = ${rec ? (db[key1] ? key1 : key2) : key1}`;
      }

      if (!rec) {
        setStatus("ND");
        noteText.textContent = STATUS_MAP.ND.fallbackNote;
        refWrap.hidden = true;
        return;
      }

      // ใช้ชื่อมาตรฐานจากฐานข้อมูล ถ้ามี
      if (elDrugA) elDrugA.textContent = rec.drug_a || aRaw || "—";
      if (elDrugB) elDrugB.textContent = rec.drug_b || bRaw || "—";

      const code = (rec.status || "ND").toUpperCase();
      setStatus(code);

      const note = (rec.note_th || rec.summary_th || "").trim() || (STATUS_MAP[code] || STATUS_MAP.ND).fallbackNote;
      noteText.textContent = note;

      const ref = (rec.reference || "").trim();
      if (ref) {
        refText.textContent = ref;
        refWrap.hidden = false;
      } else {
        refWrap.hidden = true;
      }
    } catch (err) {
      console.error(err);
      setStatus("ND");
      noteText.textContent = "เกิดข้อผิดพลาดในการโหลดข้อมูล กรุณาลองใหม่อีกครั้ง";
      if (refWrap) refWrap.hidden = true;
    }
  })();
})();
