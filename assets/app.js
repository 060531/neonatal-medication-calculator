(function () {
  function calcVancoDose(bw, pma) {
    // ตัวอย่างสมมติ: ปรับตาม guideline/สูตรจริงของคุณนัท
    // ควรยกตรรกะจาก Flask มาคำนวณบน client ตรงนี้
    if (!bw || !pma) return { ok: false, msg: "กรอกน้ำหนักและ PMA ให้ครบ" };
    let doseMgPerKg = pma < 29 ? 10 : 15;   // ตัวอย่าง
    let intervalHr  = pma < 29 ? 24 : 12;   // ตัวอย่าง
    let dose = doseMgPerKg * bw;
    return { ok: true, dose, doseMgPerKg, intervalHr };
  }

  document.addEventListener("DOMContentLoaded", () => {
    const bw = document.getElementById("bw");
    const pma = document.getElementById("pma");
    const btn = document.getElementById("calcVanco");
    const out = document.getElementById("vancoResult");

    btn?.addEventListener("click", () => {
      const r = calcVancoDose(parseFloat(bw.value), parseFloat(pma.value));
      if (!r.ok) { out.textContent = r.msg; return; }
      out.innerHTML = `
        <b>Dose:</b> ${r.dose.toFixed(1)} mg
        <br><b>Schedu​le:</b> ${r.doseMgPerKg} mg/kg q${r.intervalHr}h
      `;
    });
  });
})();
