// static/dose_page.js
(() => {
  const qs = new URLSearchParams(window.location.search);

  const num = (v) => {
    if (v === null || v === undefined) return null;
    const n = Number(String(v).trim());
    return Number.isFinite(n) ? n : null;
  };
  const int = (v) => {
    const n = num(v);
    return n === null ? null : Math.trunc(n);
  };

  const getFirst = (...keys) => {
    for (const k of keys) {
      const v = qs.get(k);
      if (v !== null && v !== "") return v;
    }
    return null;
  };

  const setText = (selector, text) => {
    document.querySelectorAll(selector).forEach((el) => (el.textContent = text));
  };

  const fmtKg = (kg) => (kg === null ? "-" : kg.toFixed(3));
  const fmtInt = (x) => (x === null ? "-" : String(Math.round(x)));

  // ---- Read params (support common aliases) ----
  const pmaWeeks = int(getFirst("pma_weeks", "pmaWeeks", "pma_w"));
  const pmaDays  = int(getFirst("pma_days", "pmaDays", "pma_d"));
  const calc     = num(getFirst("calc", "calc_weeks", "calcWeeks"));
  const pnd      = int(getFirst("postnatal_days", "postDays", "pnd", "postnatal"));
  const bw       = num(getFirst("bw", "bw_kg", "weight", "weight_kg"));

  // ---- Fill basics ----
  if (pmaWeeks !== null && pmaDays !== null) {
    setText("#pmaText", `${pmaWeeks} weeks and ${pmaDays} days`);
  }
  if (calc !== null) setText("#calcText", `${calc} weeks`);
  if (pnd !== null) setText("#postText", `${pnd} days`);
  if (bw !== null) setText("#bwText", `${fmtKg(bw)} kg`);

  // ---- Determine page drug (fallback: from title/h1) ----
  const h1 = document.querySelector("h1")?.textContent?.toLowerCase() || "";
  const title = document.title.toLowerCase();
  const isAmikacin = title.includes("amikacin") || h1.includes("amikacin");

  // ---- Drug-specific compute ----
  if (isAmikacin) {
    // Use Weight + Postnatal age (<14 vs >=14) table
    // If pnd missing, assume <14? better: don't compute interval, still compute dose if possible
    const ageGroup = (pnd !== null && pnd >= 14) ? "ge14" : (pnd !== null ? "lt14" : null);

    const pick = (bwKg, group) => {
      if (bwKg === null || group === null) return null;

      // return { mgkg, intervalHours }
      if (bwKg <= 0.8) {
        return group === "lt14" ? { mgkg: 16, ih: 48 } : { mgkg: 20, ih: 42 };
      }
      if (bwKg > 0.8 && bwKg <= 1.2) {
        return group === "lt14" ? { mgkg: 16, ih: 42 } : { mgkg: 20, ih: 36 };
      }
      if (bwKg > 1.2 && bwKg <= 2.0) {
        return group === "lt14" ? { mgkg: 15, ih: 36 } : { mgkg: 18, ih: 30 };
      }
      if (bwKg > 2.0 && bwKg <= 2.8) {
        return group === "lt14" ? { mgkg: 15, ih: 36 } : { mgkg: 18, ih: 24 };
      }
      // >2.8
      return group === "lt14" ? { mgkg: 15, ih: 30 } : { mgkg: 18, ih: 20 };
    };

    const rule = pick(bw, ageGroup);

    if (rule && bw !== null) {
      const doseMg = bw * rule.mgkg;
      setText("#doseText, #doseText2", `${fmtInt(doseMg)} mg/dose`);
      setText("#intervalText", `every ${rule.ih} hours`);
    } else {
      // if BW present but PND missing, at least show BW (already) and leave dose/interval as "-"
      // you can choose to compute dose after user provides pnd
    }
  }
})();
