#!/usr/bin/env bash
set -euo pipefail

F="docs/compatibility_result.html"
[ -f "$F" ] || exit 0

python - <<'PY'
from pathlib import Path
import re

F = Path("docs/compatibility_result.html")
html = F.read_text(encoding="utf-8")

# 1) ลบของเก่าที่เคย inject (กันซ้ำ)
html = re.sub(r'<style[^>]*id="compat-theme-style"[^>]*>.*?</style>\s*', '', html, flags=re.S|re.I)
html = re.sub(r'<script[^>]*id="compat-lookup-patch"[^>]*>.*?</script>\s*', '', html, flags=re.S|re.I)

# 2) ย้อน/ลบ patch เก่าที่เคย "return;" ตัด legacy (เพราะทำให้การ์ดไม่ถูกโชว์)
html = re.sub(
    r'\s*//\s*PATCH:\s*disable legacy status mapping\s*\(use compat-lookup-patch\)\s*return;\s*',
    '\n',
    html,
    flags=re.I
)

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
(function(){
  const label = {
    C: "Compatible / ผสมร่วมได้",
    I: "Incompatible / ห้ามผสม",
    U: "Uncertain / ไม่ชัดเจน",
    ND:"No data / ไม่มีข้อมูล",
  };

  function normDrug(s){
    return String(s || "")
      .replace(/\\+/g, " ")
      .trim()
      .toLowerCase()
      .replace(/\\s+/g, " ");
  }

  // สำคัญ: บังคับโชว์ element ที่ถูกซ่อน (แก้หน้าโล่ง)
  function forceUnhide(fromEl){
    let el = fromEl;
    while (el && el !== document.body){
      try{
        el.hidden = false;
        el.classList && el.classList.remove("hidden");
        const cs = getComputedStyle(el);
        if (cs.display === "none") el.style.display = "block";
        if (cs.visibility === "hidden") el.style.visibility = "visible";
        if (cs.opacity === "0") el.style.opacity = "1";
      }catch(e){}
      el = el.parentElement;
    }
  }

  function hideFallbackIfAny(){
    const cand = Array.from(document.querySelectorAll("p,div,span"))
      .find(el => (el.textContent || "").includes("ยังไม่พบรายละเอียดคู่นี้ในระบบ"));
    if (cand) cand.style.display = "none";
  }

  function ensureNoteBox(anchorEl){
    let box = document.querySelector("[data-compat-note]");
    if (box) return box;

    box = document.createElement("div");
    box.className = "compat-note";
    box.setAttribute("data-compat-note", "1");

    // วางต่อจากบรรทัดสถานะ ถ้ามี
    const anchor =
      document.querySelector(".compat-status-line") ||
      anchorEl?.parentElement ||
      anchorEl ||
      document.body;

    anchor.insertAdjacentElement("afterend", box);
    return box;
  }

  function renderNote(row, code, sLabelEl){
    const box = ensureNoteBox(sLabelEl);
    box.dataset.code = code;
    box.replaceChildren();

    const hd = document.createElement("div");
    hd.className = "hd";
    hd.textContent = "Notes / ข้อสรุปเชิงปฏิบัติ";
    box.appendChild(hd);

    const en = (row && row.summary_en) || "";
    const th = (row && row.summary_th) || "";
    const ref = (row && row.reference) || "";

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

  async function run(){
    const sCodeEl  = document.querySelector("[data-status-code]");
    const sLabelEl = document.querySelector("[data-status-label]");

    // ถ้าหน้าไม่พบ element เหล่านี้ แปลว่า template เปลี่ยน/ถูกซ่อนหนักมาก
    if (!sCodeEl || !sLabelEl) return;

    // บังคับโชว์การ์ดที่ครอบ status pill
    forceUnhide(sCodeEl);

    const params = new URLSearchParams(location.search);
    const drugA = params.get("drug_a") || "";
    const drugB = params.get("drug_b") || "";
    const a = normDrug(drugA);
    const b = normDrug(drugB);
    const k1 = a + "|" + b;
    const k2 = b + "|" + a;

    try{
      const res = await fetch("./static/compat_lookup.json?x=" + Date.now(), { cache: "no-store" });
      const lookup = await res.json();
      const row = lookup[k1] || lookup[k2];

      const code = (row && row.status ? String(row.status).toUpperCase() : "ND");

      // เก็บไว้เผื่อ legacy มาเขียนทับทีหลัง แล้วเราจะ apply ซ้ำ
      window.__compatLookupLast = { row, code };

      sCodeEl.textContent = code;
      sCodeEl.setAttribute("data-status", code);
      sLabelEl.textContent = label[code] || label.ND;

      if (row) hideFallbackIfAny();
      renderNote(row, code, sLabelEl);

      // กัน legacy มาเขียนทับหลังโหลด: เฝ้า mutation แล้ว apply ซ้ำ
      const obs = new MutationObserver(() => {
        const last = window.__compatLookupLast;
        if (!last) return;
        sCodeEl.textContent = last.code;
        sCodeEl.setAttribute("data-status", last.code);
        sLabelEl.textContent = label[last.code] || label.ND;
      });
      obs.observe(sCodeEl, { childList: true, subtree: true, characterData: true });
      obs.observe(sLabelEl, { childList: true, subtree: true, characterData: true });

    }catch(e){
      // ถ้าโหลด lookup ไม่ได้ อย่างน้อยต้องไม่หน้าโล่ง
      sCodeEl.textContent = "ND";
      sCodeEl.setAttribute("data-status", "ND");
      sLabelEl.textContent = label.ND;
      forceUnhide(sCodeEl);
    }
  }

  if (document.readyState === "loading"){
    document.addEventListener("DOMContentLoaded", run, { once:true });
  } else {
    run();
  }
})();
</script>
'''

# 3) Inject ก่อน </body>
if not re.search(r'</body\s*>', html, flags=re.I):
    raise SystemExit("ERROR: </body> not found in docs/compatibility_result.html")

html = re.sub(r'</body\s*>', inject + '\n</body>', html, flags=re.I, count=1)

F.write_text(html, encoding="utf-8")
print("patched:", F)
PY
