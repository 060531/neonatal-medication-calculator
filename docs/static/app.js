/* =========================
 * Compat Result Page (Pages + Flask) - COMPLETE
 * ========================= */
(function initCompatResultPage() {
  const root = document.getElementById("compatResultRoot");
  if (!root) return;

  const $ = (id) => document.getElementById(id);

  // UI nodes
  const elDrugA = $("drugA");
  const elDrugB = $("drugB");
  const pill = $("statusPill");
  const statusText = $("statusText");
  const noteText = $("noteText");
  const refWrap = $("refWrap");
  const refText = $("refText");
  const debugLine = $("debugLine");

  // Support both old buttons + new floating buttons
  const btnNew =
    $("btnNewCheck") || $("fabNewCheck") || document.querySelector('[data-role="new-check"]');
  const btnHome =
    $("btnHome") || $("fabHome") || document.querySelector('[data-role="home"]');

  // Detect Pages vs Flask
  const isPages = () =>
    location.hostname.endsWith("github.io") || /\.html(\?|#|$)/.test(location.pathname);

  // URL resolver (safe, works both Pages + Flask)
  function resolveNavUrls() {
    const URLS = window.__URLS || window.URLS || {};
    const nav = {
      newCheck: URLS.newCheck || "./compatibility.html",
      home: URLS.home || "./index.html",
      lookup: URLS.lookup || "./static/compat_lookup.json",
    };

    // If Flask: allow per-element dataset override (best practice)
    // <a id="btnNewCheck" data-flask-href="{{ url_for('compat.compat_index') }}">
    if (!isPages()) {
      if (btnNew && btnNew.dataset && btnNew.dataset.flaskHref) nav.newCheck = btnNew.dataset.flaskHref;
      if (btnHome && btnHome.dataset && btnHome.dataset.flaskHref) nav.home = btnHome.dataset.flaskHref;
      if (URLS.lookup) nav.lookup = URLS.lookup; // typically url_for('static', filename='compat_lookup.json')
    }

    return nav;
  }

  function setHref(el, href) {
    if (!el || !href) return;
    el.setAttribute("href", href);
  }

  function hardNav(href) {
    if (!href) return;
    window.location.assign(href);
  }

  function bindHardNav(el) {
    if (!el) return;
    el.addEventListener(
      "click",
      (e) => {
        // allow open in new tab, etc
        if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
        e.preventDefault();
        hardNav(el.getAttribute("href"));
      },
      { passive: false }
    );
  }

  // Patch links robustly (prevents compat_index.html leaks)
  function patchLinks() {
    const nav = resolveNavUrls();

    // set href on the available buttons
    setHref(btnNew, nav.newCheck);
    setHref(btnHome, nav.home);

    // bind hard navigation
    bindHardNav(btnNew);
    bindHardNav(btnHome);

    // if any anchor accidentally points to compat_index.html, rewrite it
    document.querySelectorAll('a[href*="compat_index.html"]').forEach((a) => {
      a.setAttribute("href", nav.newCheck);
    });
  }

  // run link patch after DOM ready just in case other scripts mutate href
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", patchLinks);
  } else {
    patchLinks();
  }

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
    const c = (code || "ND").toUpperCase();
    const s = STATUS_MAP[c] || STATUS_MAP.ND;

    // for CSS theming
    root.dataset.status = c;

    if (pill) {
      pill.classList.remove("st-loading", "st-c", "st-i", "st-u", "st-nd");
      pill.classList.add(s.cls);
    }
    if (statusText) statusText.textContent = s.text;
  }

  async function loadJson(url) {
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) throw new Error(`fetch failed: ${res.status} (${url})`);
    return await res.json();
  }

  async function loadLookupDb() {
    const nav = resolveNavUrls();

    // Try multiple paths (GitHub Pages sometimes needs ./docs/static if mislinked)
    const candidates = [];
    if (nav.lookup) candidates.push(nav.lookup);

    // common fallbacks
    candidates.push("./static/compat_lookup.json");
    candidates.push("static/compat_lookup.json");
    candidates.push("./docs/static/compat_lookup.json");
    candidates.push("docs/static/compat_lookup.json");

    let lastErr = null;
    for (const u of candidates) {
      try {
        return await loadJson(u);
      } catch (e) {
        lastErr = e;
      }
    }
    throw lastErr || new Error("lookup db not found");
  }

  // --- main ---
  (async () => {
    try {
      const aRaw = getQueryParam("drug_a");
      const bRaw = getQueryParam("drug_b");
      const aKey = normalizeName(aRaw);
      const bKey = normalizeName(bRaw);

      // Show names from query first
      if (elDrugA) elDrugA.textContent = aRaw || "—";
      if (elDrugB) elDrugB.textContent = bRaw || "—";

      // Load db
      const db = await loadLookupDb();

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

      // Prefer canonical drug names from db
      if (elDrugA) elDrugA.textContent = rec.drug_a || aRaw || "—";
      if (elDrugB) elDrugB.textContent = rec.drug_b || bRaw || "—";

      const code = String(rec.status || "ND").toUpperCase();
      setStatus(code);

      const fallback = (STATUS_MAP[code] || STATUS_MAP.ND).fallbackNote;
      const note = String(rec.note_th || rec.summary_th || "").trim() || fallback;
      if (noteText) noteText.textContent = note;

      const ref = String(rec.reference || "").trim();
      if (ref && refWrap && refText) {
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
      if (debugLine) {
        debugLine.hidden = false;
        debugLine.textContent = `error: ${err && err.message ? err.message : String(err)}`;
      }
    }
  })();
})();
