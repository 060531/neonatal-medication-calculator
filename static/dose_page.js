cat > static/dose_page.js <<'JS'
/* static/dose_page.js */
(function(){
  function num(x){ const n = Number(x); return Number.isFinite(n) ? n : NaN; }

  const DosePage = {
    // ตั้งค่าเฉพาะ “กติกา” ต่อ drug ไว้ที่นี่ (รวมศูนย์)
    CONFIGS: {
      // ตัวอย่างจากที่คุณให้มา
      acyclovir: {
        doseMgPerKg: 20,
        interval: (ctx) => (num(ctx.calc) < 30 ? "IV every 8–12 hours" : "IV every 8 hours"),
        highlightRules: [
          { id: "ruleLt30", when: (ctx)=> num(ctx.calc) < 30 },
          { id: "ruleGe30", when: (ctx)=> num(ctx.calc) >= 30 }
        ]
      }
      // เพิ่มตัวอื่น ๆ ทีหลังได้: amikacin, ampicillin, ...
    },

    getCtx(){
      if (window.NMC && typeof window.NMC.get === "function") return window.NMC.get();
      return null;
    },

    inferDrug(){
      const last = (location.pathname.split("/").pop() || "").replace(/\.html$/,"");
      // รองรับทั้ง .../acyclovir_dose และ .../acyclovir_dose.html
      return last.replace(/_dose$/,"");
    },

    setText(id, text){
      const el = document.getElementById(id);
      if (el) el.textContent = text;
    },

    toggleClass(id, cls, on){
      const el = document.getElementById(id);
      if (el) el.classList.toggle(cls, !!on);
    },

    run(opts){
      const ctx0 = this.getCtx();
      if (!ctx0) return;

      const pmaW = num(ctx0.pma_weeks);
      const pmaD = num(ctx0.pma_days);
      const bw   = num(ctx0.bw);
      const calc = Number.isFinite(num(ctx0.calc)) ? num(ctx0.calc)
                  : (Number.isFinite(pmaW) && Number.isFinite(pmaD) ? (pmaW + pmaD/7) : NaN);
      const post = num(ctx0.postnatal_days);

      const ctx = { ...ctx0, pmaW, pmaD, bw, calc, post };

      // ฟิลด์มาตรฐาน (ถ้ามี element ก็กรอกให้)
      if (Number.isFinite(pmaW) && Number.isFinite(pmaD)) this.setText("pmaText", `${pmaW} weeks and ${pmaD} days`);
      if (Number.isFinite(calc)) this.setText("calcText", `${calc.toFixed(1)} weeks`);
      if (Number.isFinite(post)) this.setText("postText", `${post} days`);
      if (Number.isFinite(bw))   this.setText("bwText", `${bw.toFixed(2)} kg`);

      // คำนวณ dose ถ้ามี doseMgPerKg และ bw
      const dpk = num(opts?.doseMgPerKg);
      if (Number.isFinite(dpk) && Number.isFinite(bw) && bw > 0){
        const dose = dpk * bw;
        this.setText("doseText", `${dose.toFixed(2)} mg / dose`);
      }

      // interval
      if (typeof opts?.interval === "function"){
        const it = opts.interval(ctx);
        if (typeof it === "string") this.setText("intervalText", it);
      }

      // highlight rules
      if (Array.isArray(opts?.highlightRules)){
        for (const r of opts.highlightRules){
          const ok = typeof r.when === "function" ? !!r.when(ctx) : false;
          this.toggleClass(r.id, r.className || "highlight-green", ok);
        }
      }
    },

    runAuto(){
      const drug = this.inferDrug();
      const cfg = this.CONFIGS[drug];

      // อย่างน้อยให้แสดง ctx (ถ้ามี placeholder)
      if (!cfg){
        this.run({ doseMgPerKg: NaN });
        return;
      }
      this.run(cfg);
    }
  };

  window.DosePage = DosePage;
})();
JS
