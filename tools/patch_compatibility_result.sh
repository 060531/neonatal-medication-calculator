#!/usr/bin/env bash
set -euo pipefail

F="docs/compatibility_result.html"
[ -f "$F" ] || exit 0

python3 - <<'PY'
from pathlib import Path
import re

F = Path("docs/compatibility_result.html")
html = F.read_text(encoding="utf-8")

# ลบของเดิมที่เคย inject (กันซ้ำ)
html = re.sub(r'<style[^>]*id="compat-theme-style"[^>]*>.*?</style>\s*', "", html, flags=re.S)
html = re.sub(r'<script[^>]*id="compat-lookup-patch"[^>]*>.*?</script>\s*', "", html, flags=re.S)

inject = r'''
<style id="compat-theme-style">
/* ===== Compatibility theme ===== */
.compat-note{
  margin: 14px auto 0;
  max-width: 760px;
  text-align: left;
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid rgba(15,23,42,.18);
  background: rgba(255,255,255,.88);
  line-height: 1.5;
  font-size: 15px;
}
.compat-note .hd{ font-weight: 700; margin-bottom: 6px; }
.compat-note .en{ opacity: .95; }
.compat-note .th{ margin-top: 6px; }
.compat-note .ref{ margin-top: 10px; font-size: 13px; opacity: .85; }

.compat-status-pill[data-status="C"]{ background:#16a34a; color:#fff; }
.compat-status-pill[data-status="I"]{ background:#dc2626; color:#fff; }
.compat-status-pill[data-status="U"]{ background:#f59e0b; color:#111827; }
.compat-status-pill[data-status="ND"]{ background:#64748b; color:#fff; }

.compat-note[data-code="C"]{ border-color: rgba(22,163,74,.45); background: rgba(22,163,74,.10); }
.compat-note[data-code="I"]{ border-color: rgba(220,38,38,.45); background: rgba(220,38,38,.10); }
.compat-note[data-code="U"]{ border-color: rgba(245,158,11,.55); background: rgba(245,158,11,.12); }
.compat-note[data-code="ND"]{ border-color: rgba(100,116,139,.45); background: rgba(100,116,139,.10); }
</style>

<script id="compat-lookup-patch">
(async function () {
  function normDrug(s){
    return String(s || "")
      .replace(/\\+/g, " ")
      .trim()
      .toLowerCase()
      .replace(/\\s+/g, " ");
  }

  const params = new URLSearchParams(location.search);
  const drugA = params.get("drug_a") || "";
  const drugB = params.get("drug_b") || "";

  const a = normDrug(drugA);
  const b = normDrug(drugB);
  const k1 = a + "|" + b;
  const k2 = b + "|" + a;

  const sCodeEl  = document.querySelector("[data-status-code]");
  const sLabelEl = document.querySelector("[data-status-label]");
  if (!sCodeEl || !sLabelEl) return;

  const label = {
    C: "Compatible / ผสมร่วมได้",
    I: "Incompatible / ห้ามผสม",
    U: "Uncertain / ไม่ชัดเจน",
    ND: "No data / ไม่มีข้อมูล"
  };

  function splitCombinedNote(note){
    // รองรับ note แบบ "EN / TH"
    const s = String(note || "").trim();
    if (!s) return { en:"", th:"" };
    const parts = s.split(" / ");
    if (parts.length >= 2) return { en: parts[0].trim(), th: parts.slice(1).join(" / ").trim() };
    return { en: s, th: "" };
  }

  function hideFallbackIfAny(){
    const cand = Array.from(document.querySelectorAll("p,div,span"))
      .find(el => (el.textContent || "").includes("ยังไม่พบรายละเอียดคู่นี้ในระบบ"));
    if (cand) cand.style.display = "none";
  }

  function ensureNoteBox(){
    let box = document.querySelector("[data-compat-note]");
    if (box) return box;

    box = document.createElement("div");
    box.className = "compat-note";
    box.setAttribute("data-compat-note", "1");

    const anchor =
      document.querySelector(".compat-status-line") ||
      sLabelEl.parentElement || sLabelEl;

    anchor.insertAdjacentElement("afterend", box);
    return box;
  }

  function renderNote(row, code){
    const box = ensureNoteBox();
    box.dataset.code = code;
    box.replaceChildren();

    const hd = document.createElement("div");
    hd.className = "hd";
    hd.textContent = "Notes / ข้อสรุปเชิงปฏิบัติ";
    box.appendChild(hd);

    let en = (row && (row.summary_en || row.note_en)) || "";
    let th = (row && (row.summary_th || row.note_th)) || "";
    const ref = (row && (row.reference || row.source)) || "";

    if (!en && !th && row && row.note){
      const s = splitCombinedNote(row.note);
      en = s.en; th = s.th;
    }

    if (en){
      const d = document.createElement("div");
      d.className = "en";
      d.textContent = en;
      box.appendChild(d);
    }
    if (th){
      const d = document.createElement("div");
      d.className = "th";
      d.textContent = th;
      box.appendChild(d);
    }
    if (ref){
      const d = document.createElement("div");
      d.className = "ref";
      d.textContent = "Reference: " + ref;
      box.appendChild(d);
    }

    if (!en && !th && !ref){
      const d = document.createElement("div");
      d.className = "th";
      d.textContent = "พบสถานะในระบบแล้ว แต่ยังไม่มีรายละเอียดเงื่อนไข (กำลังทยอยเติมข้อมูล)";
      box.appendChild(d);
    }
  }

  try {
    const res = await fetch("./static/compat_lookup.json?x=" + Date.now(), { cache: "no-store" });
    const lookup = await res.json();
    const row = lookup[k1] || lookup[k2];

    const code = (row && row.status ? String(row.status).toUpperCase() : "ND");
    sCodeEl.textContent = code;
    sCodeEl.setAttribute("data-status", code);
    sLabelEl.textContent = label[code] || label.ND;

    if (row) hideFallbackIfAny();
    renderNote(row, code);
  } catch (e) {
    sCodeEl.textContent = "ND";
    sCodeEl.setAttribute("data-status", "ND");
    sLabelEl.textContent = label.ND;
    renderNote(null, "ND");
  }
})();
</script>
'''.strip()

if "</body>" in html:
    html = html.replace("</body>", inject + "\n\n</body>")
else:
    html += "\n\n" + inject + "\n"

F.write_text(html, encoding="utf-8")
print("patched:", F)
PY
