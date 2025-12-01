/* =========================
 * Compat Result Page (Pages + Flask)
 * ========================= */
(function initCompatResultPage() {
  const root = document.getElementById("compatResultRoot");
  if (!root) return;

  const $ = (id) => document.getElementById(id);

  const elDrugA = $("drugA");
  const elDrugB = $("drugB");
  const pairPill = $("pairPill");
  const pill = $("statusPill");
  const statusText = $("statusText");
  const noteText = $("noteText");
  const refWrap = $("refWrap");
  const refText = $("refText");
  const debugLine = $("debugLine");

  // ปุ่ม “แบบใหม่” (FAB) + เผื่อ legacy ids
  const btnNew = $("fabNewCheck") || $("btnNewCheck");
  const btnHome = $("fabHome") || $("btnHome");

  // --- helpers ---
  const STATUS_MAP = {
    C: { cls: "st-c",  text: "Compatible (ผสมร่วมได้)",  fallbackNote: "ยาสามารถผสมร่วมกันได้" },
    I: { cls: "st-i",  text: "Incompatible (ห้ามผสม)",  fallbackNote: "ไม่ควรให้ร่วมกันใน line เดียวกัน (เสี่ยงไม่เข้ากัน/ความคงตัว)" },
    U: { cls: "st-u",  text: "Uncertain (ไม่ชัดเจน)",  fallbackNote: "ข้อมูลยังไม่ชัดเจน ควรหลีกเลี่ยงการผสมร่วมกัน" },
    ND:{ cls: "st-nd", text: "No data (ไม่มีข้อมูล)",    fallbackNote: "ไม่พบข้อมูลความเข้ากันได้ของคู่นี้" }
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
    const c = (code || "ND").toUpperCase();
    const s = STATUS_MAP[c] || STATUS_MAP.ND;

    root.dataset.status = c;

    if (pill) {
      pill.classList.remove("st-loading", "st-c", "st-i", "st-u", "st-nd");
      pill.classList.add(s.cls);
    }
    if (statusText) statusText.textContent = s.text;
  }

  async function loadJson(url) {
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) throw new Error(`fetch failed: ${res.status}`);
    return await res.json();
  }

  // --- robust nav (Pages + Flask) ---
  function isPages() {
    return (
      location.hostname.endsWith("github.io") ||
      location.protocol === "file:" ||
      location.pathname.endsWith(".html")
    );
  }

  function resolveHref(kind) {
    const u = window.__URLS || {};
    // 1) ค่า __URLS (แนะนำให้ใช้)
    if (u[kind]) return u[kind];

    // 2) fallback
    if (kind === "newCheck") return isPages() ? "./compatibility.html" : "/compat";
    if (kind === "home") return isPages() ? "./index.html" : "/";
    if (kind === "lookup") return "./static/compat_lookup.json";
    return "";
  }

  function hardNav(href) {
    if (!href) return;
    window.location.assign(href);
  }

  function bindNav(aEl, href) {
    if (!aEl) return;
    aEl.setAttribute("href", href);

    // กันสคริปต์อื่น intercept
    aEl.addEventListener(
      "click",
      (e) => {
        e.preventDefault();
        hardNav(href);
      },
      true
    );
  }

  // เซ็ตลิงก์ปุ่มทันที
  bindNav(btnNew, resolveHref("newCheck"));
  bindNav(btnHome, resolveHref("home"));

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

      // ให้ tooltip ตอนชื่อโดน ...
      if (pairPill) pairPill.title = `${aRaw || "—"} × ${bRaw || "—"}`;

      const lookupUrl = resolveHref("lookup");
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
        if (noteText) noteText.textContent = STATUS_MAP.ND.fallbackNote;
        if (refWrap) refWrap.hidden = true;
        return;
      }

      // ใช้ชื่อมาตรฐานจากฐานข้อมูล ถ้ามี
      const showA = rec.drug_a || aRaw || "—";
      const showB = rec.drug_b || bRaw || "—";
      if (elDrugA) elDrugA.textContent = showA;
      if (elDrugB) elDrugB.textContent = showB;
      if (pairPill) pairPill.title = `${showA} × ${showB}`;

      const code = (rec.status || "ND").toUpperCase();
      setStatus(code);

      const note =
        (rec.note_th || rec.summary_th || "").trim() ||
        (STATUS_MAP[code] || STATUS_MAP.ND).fallbackNote;

      if (noteText) noteText.textContent = note;

      const ref = (rec.reference || "").trim();
      if (ref && refText && refWrap) {
        refText.textContent = ref;
        refWrap.hidden = false;
      } else if (refWrap) {
        refWrap.hidden = true;
      }
    } catch (err) {
      console.error(err);
      setStatus("ND");
      if (noteText) noteText.textContent = "เกิดข้อผิดพลาดในการโหลดข้อมูล กรุณาลองใหม่อีกครั้ง";
      if (refWrap) refWrap.hidden = true;
    }
  })();
})();
