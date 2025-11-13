# routes_medications.py
# -*- coding: utf-8 -*-
"""
Blueprint รวมเส้นทางคำนวณยาสำหรับทารกแรกเกิด
- โครงสร้าง POST 2 รอบ (action=dose / action=condition) ทำเป็นมาตรฐานเดียว
- กัน UndefinedError ใน Jinja2 ด้วย default None เสมอ
- รวม helper สำหรับแปลงค่า/ปัดทศนิยม/ข้อความคำอธิบาย 3X & 6X
- โค้ดนี้ออกแบบให้ "แทนที่" ของเดิมได้ทันที: template name เหมือนเดิมทุกหน้า
"""

from flask import Blueprint, render_template, request
from datetime import date

meds_bp = Blueprint("meds", __name__)

# =========================
# ==== Global Settings ====
# =========================
UPDATE_DATE = date.today().strftime("%Y-%m-%d")


# =========================
# ======== Helpers ========
# =========================
def _as_float(val, name="value"):
    """แปลงเป็น float และแจ้ง error กรณีว่าง/ไม่ใช่ตัวเลข"""
    if val is None:
        raise ValueError(f"missing {name}")
    s = str(val).strip()
    if s == "":
        raise ValueError(f"empty {name}")
    return float(s)


def _as_int(val, name="value"):
    if val is None:
        raise ValueError(f"missing {name}")
    s = str(val).strip()
    if s == "":
        raise ValueError(f"empty {name}")
    return int(float(s))


def _round2(x):
    return None if x is None else round(float(x), 2)


def _content_extra_by_mult(mult):
    """ข้อความมาตรฐานสำหรับ 3X/6X (ใช้ร่วมกันได้หลายยา)"""
    if mult == 3:
        return {
            "message": "การบริหารยาโดย Intermittent intravenous infusion pump",
            "details": [
                "สำหรับทารกที่มีน้ำหนักมากกว่า 1,500 กรัม",
                "กำหนดให้ปริมาณสารละลายยา (ปริมาณยา + สารละลายเจือจางยา) = 8–9 mL",
                "(ความจุของ Extension Tube ประมาณ 5 mL + ปริมาณที่บริหารเข้าผู้ป่วย 3 mL)",
                "<div style='text-align:center'>(3X + สารละลายเจือจางยา Up to 9 mL)</div>",
                "การเตรียมยา:",
                "1) คำนวณ mL, 2) ดูดยา, 3) เติมสารละลายเจือจางใน Syringe",
                "4) ผสมให้เข้ากัน, 5) ต่อกับ Extension Tube ตั้งอัตรา ~6 mL/hr",
                "6) Purge สาย ~3 mL ก่อนเริ่มบริหารผู้ป่วย",
            ],
        }
    if mult == 6:
        return {
            "message": "การบริหารยาโดย Intermittent intravenous infusion",
            "details": [
                "เหมาะกับทารกน้ำหนัก < 1,500 กรัม",
                "1) ปริมาณที่บริหารเข้าผู้ป่วย = 1 mL",
                "<div style='text-align:center'>6X + สารละลายเจือจางยา Up to 6 mL</div>",
                "รวมสารละลาย ~6 mL (Tube ~5 mL + ให้ผู้ป่วย 1 mL)",
                "ใช้ Syringe pump ตั้งอัตรา ~2 mL/hr",
            ],
        }
    return None


def _ml_from_stock(dose_mg, stock_mg, stock_ml):
    """คำนวณ mL จากยาที่ละลายแล้ว: ml = dose * stock_ml / stock_mg"""
    return _round2((dose_mg * stock_ml) / stock_mg)


def _ml_from_conc(dose_mg, mg_per_ml):
    """คำนวณ mL จากความเข้มข้น mg/mL: ml = dose / mg_per_ml"""
    return _round2(dose_mg / mg_per_ml)


# ===================================================================
# ============= Routes (เรียงตามตัวอักษรจากที่คุณให้มา) ==========
# ===================================================================

# routes/routes_medications.py
# -*- coding: utf-8 -*-
@meds_bp.route("/acyclovir", methods=["GET", "POST"])
@meds_bp.route("/acyclovir_route", methods=["GET", "POST"])  # รองรับ URL เก่า
def acyclovir_route():
    """
    dose (mg) → result_ml_1 = (dose*5)/250
                result_ml_2 = (dose*1)/5
    """
    dose = None
    result_ml_1 = None
    result_ml_2 = None
    final_result_1 = None
    final_result_2 = None
    multiplication = None
    error = None

    if request.method == "POST":
        try:
            dose = float((request.form.get("dose") or "").strip())
            result_ml_1 = round((dose * 5) / 250.0, 2)
            result_ml_2 = round(dose / 5.0, 2)   # ✅ แก้เป็น 5

            mult_raw = (request.form.get("multiplication") or "").strip()
            if mult_raw:
                multiplication = float(mult_raw)
                final_result_1 = round(result_ml_1 * multiplication, 2)
                final_result_2 = round(result_ml_2 * multiplication, 2)
        except Exception as e:
            error = f"กรุณาใส่ข้อมูลที่ถูกต้อง: {e}"

    return render_template(
        "acyclovir.html",
        static_build=False,             # ✅ บอกเทมเพลตว่าเป็น Flask
        dose=dose,
        result_ml_1=result_ml_1,
        result_ml_2=result_ml_2,
        final_result_1=final_result_1,
        final_result_2=final_result_2,
        multiplication=multiplication,
        error=error,
    )




@meds_bp.route('/amikin', methods=['GET', 'POST'])
def amikin_route():
    dose = result_ml = multiplication = final_result = None
    target_total = diluent_to_add = None
    msg_block = content_extra = error = None

    try:
        if request.method == 'POST':
            action = (request.form.get('action') or '').strip().lower()

            if action == 'dose':
                # 1) รับ dose (mg) แล้วคำนวณ mL จาก stock 500 mg / 2 mL  ⇒ mL = mg × 2 / 500
                dose = _as_float(request.form.get('dose'), 'dose')
                if dose is None or dose < 0:
                    raise ValueError("dose ต้องเป็นตัวเลข ≥ 0")
                result_ml = _round2((dose * 2.0) / 500.0)

            elif action == 'condition':
                # 2) รับค่าจาก hidden field + ตัวเลือก multiplication (3 หรือ 6)
                dose = _as_float(request.form.get('dose_hidden'), 'dose_hidden')
                result_ml = _as_float(request.form.get('result_ml_hidden'), 'result_ml_hidden')
                multiplication = _as_int(request.form.get('multiplication'), 'multiplication')

                if dose is None or result_ml is None:
                    raise ValueError("ข้อมูลคำนวณเดิมไม่ครบ โปรดคำนวณขั้นแรกก่อน")
                if multiplication not in (3, 6):
                    raise ValueError("multiplication ต้องเป็น 3 หรือ 6")

                # 3) ปริมาณยาหลังคูณ (mL)
                final_result = _round2(result_ml * multiplication)

                # 4) ตั้งเป้า total volume ตามเงื่อนไข และเตรียม block ข้อความ
                if multiplication == 3:
                    target_total = 9.0
                    msg_block = "ปริมาณที่บริหารเข้าทารก ≈ 3 mL → ตั้งอัตรา 6 mL/hr"
                    content_extra = {
                        "message": "การบริหารยาโดย Intermittent intravenous infusion pump",
                        "details": [
                            "สำหรับทารกที่มีน้ำหนักมากกว่า 1,500 กรัม",
                            "กำหนดให้ปริมาณสารละลายยา (ปริมาณยา + สารละลายเจือจาง) = 8–9 ml",
                            "<div style='text-align:center'>(3X + สารละลายเจือจาง Up to 9 ml.)</div>",
                            "ขั้นตอนย่อ: คำนวณ X (mL) → ดูดยา X → เติม diluent จนรวม ≈ 9 mL → ตั้ง 6 mL/hr",
                        ],
                    }
                else:  # multiplication == 6
                    target_total = 6.0
                    msg_block = "ปริมาณที่บริหารเข้าทารก ≈ 1 mL → ตั้งอัตรา 2 mL/hr"
                    content_extra = {
                        "message": "การบริหารยาโดย Intermittent intravenous infusion",
                        "details": [
                            "สำหรับทารกที่มีน้ำหนักน้อยกว่า 1,500 กรัม",
                            "กำหนดให้ปริมาณสารละลายทั้งหมด 6 ml",
                            "<div style='text-align:center'>(6X + สารละลายเจือจาง Up to 6 ml.)</div>",
                            "ขั้นตอนย่อ: คำนวณ X (mL) → ดูดยา X → เติม diluent จนรวม 6 mL → ตั้ง 2 mL/hr",
                        ],
                    }

                # 5) คำนวณ diluent ที่ต้องเติม: max(0, target_total - final_result)
                if target_total is not None and final_result is not None:
                    need = target_total - final_result
                    diluent_to_add = _round2(need) if need > 0 else 0.0

    except Exception as e:
        error = f"ข้อมูลไม่ถูกต้อง: {e}"

    return render_template(
        'amikin.html',
        dose=dose,
        result_ml=result_ml,
        multiplication=multiplication,
        final_result=final_result,
        target_total=target_total,
        diluent_to_add=diluent_to_add,
        msg_block=msg_block,
        content_extra=content_extra,
        error=error,
        update_date=UPDATE_DATE,
    )



@meds_bp.route('/aminophylline', methods=['GET', 'POST'])
def aminophylline_route():
    dose = result_ml = None
    error = None
    if request.method == 'POST':
        try:
            dose = _as_float(request.form.get('dose'), 'dose')
            result_ml = _round2(dose * 10)  # placeholder ตามเดิม
        except Exception:
            error = "กรุณากรอกขนาดยาที่ถูกต้อง"
    return render_template('aminophylline.html', dose=dose, result_ml=result_ml, error=error, update_date=UPDATE_DATE)


@meds_bp.route('/amoxicillin_clavimoxy', methods=['GET', 'POST'])
def amoxicillin_clavimoxy_route():
    """
    ขั้นตอนเตรียม: Sterile water 10 mL → ดูดยาทั้งหมด 10 mL + NSS 100 mL = รวม 110 mL = 1,200 mg
    ดังนั้น mg -> mL จากสารละลายสุดท้าย:  ml = mg * 110 / 1200
    """
    dose = None
    result_ml_1 = None
    multiplication = None
    final_result_1 = None
    error = None

    try:
        if request.method == 'POST':
            action = (request.form.get('action') or '').strip()

            if action == 'dose':
                # รอบที่ 1: รับ mg มาคิดเป็น mL
                raw = request.form.get('dose')
                dose = float(raw.strip()) if raw is not None else None
                if dose is None or dose <= 0:
                    raise ValueError("กรุณากรอกขนาดยา (mg) มากกว่า 0")
                result_ml_1 = round(dose * 110.0 / 1200.0, 2)

            elif action == 'condition':
                # รอบที่ 2: คูณเงื่อนไข 1.5–5 เท่า
                dose_hidden = request.form.get('dose_hidden')
                rmh = request.form.get('result_ml_1_hidden')
                mult_raw = request.form.get('multiplication')

                dose = float(dose_hidden) if dose_hidden not in (None, '') else None
                # คำนวณซ้ำให้แน่ใจ/หรือดึงค่าที่ซ่อนมาก็ได้
                if rmh not in (None, ''):
                    result_ml_1 = float(rmh)
                elif dose is not None:
                    result_ml_1 = round(dose * 110.0 / 1200.0, 2)
                else:
                    raise ValueError("ไม่พบค่าตั้งต้น (dose/result_ml_1)")

                multiplication = float(mult_raw) if mult_raw not in (None, '') else None
                final_result_1 = round(result_ml_1 * multiplication, 2)

            else:
                # fallback: หากไม่ส่ง action มา แต่ส่ง dose มา → คิดรอบแรก
                if request.form.get('dose'):
                    dose = float(request.form.get('dose'))
                    if dose <= 0:
                        raise ValueError("กรุณากรอกขนาดยา (mg) มากกว่า 0")
                    result_ml_1 = round(dose * 110.0 / 1200.0, 2)

    except Exception as e:
        error = f"กรุณากรอกข้อมูลให้ถูกต้อง: {e}"

    return render_template('amoxicillin_clavimoxy.html',
                           dose=dose,
                           result_ml_1=result_ml_1,
                           multiplication=multiplication,
                           final_result_1=final_result_1,
                           error=error,
                           UPDATE_DATE=UPDATE_DATE)



@meds_bp.route('/amphotericinB', methods=['GET', 'POST'])
def amphotericinB_route():
    dose = result_ml_1 = result_ml_2 = final_result_1 = final_result_2 = multiplication = None
    error = None
    if request.method == 'POST':
        try:
            dose = _as_float(request.form.get('dose'), 'dose')
            result_ml_1 = _round2((dose * 10) / 50)  # stock 50 mg / 10 mL
            result_ml_2 = _round2(dose / 0.1)        # เป้าหมาย 0.1 mg/mL
            if request.form.get('multiplication'):
                multiplication = _as_float(request.form.get('multiplication'), 'multiplication')
                final_result_1 = _round2(result_ml_1 * multiplication)
                final_result_2 = _round2(result_ml_2 * multiplication)
        except Exception as e:
            error = f"กรุณาใส่ข้อมูลที่ถูกต้อง: {e}"
    return render_template('amphotericinB.html',
                           dose=dose,
                           result_ml_1=result_ml_1,
                           result_ml_2=result_ml_2,
                           final_result_1=final_result_1,
                           final_result_2=final_result_2,
                           multiplication=multiplication,
                           error=error,
                           update_date=UPDATE_DATE)


@meds_bp.route('/ampicillin', methods=['GET', 'POST'])
def ampicillin_route():
    dose = result_ml = None
    error = None
    if request.method == 'POST':
        try:
            dose = _as_float(request.form.get('dose'), 'dose')
            result_ml = _round2((dose * 5) / 1000)  # ตัวอย่าง
        except Exception:
            error = "กรุณากรอกขนาดยาที่ถูกต้อง"
    return render_template('ampicillin.html', dose=dose, result_ml=result_ml, error=error, update_date=UPDATE_DATE)


@meds_bp.route('/benzathine-penicillin-g', methods=['GET', 'POST'])
def benzathine_penicillin_g_route():
    dose = calculated_ml = None
    error = None
    scheme = None
    SCHEMES = {'300k': {'vol': 4.0, 'strength': 300_000},
               '150k': {'vol': 8.0, 'strength': 150_000}}
    if request.method == 'POST':
        try:
            dose = _as_float(request.form.get('dose'), 'dose')
            scheme = (request.form.get('scheme') or '150k').strip()
            if scheme not in SCHEMES:
                scheme = '150k'
            vol = SCHEMES[scheme]['vol']
            strength = SCHEMES[scheme]['strength']
            calculated_ml = _round2((dose * vol) / strength)
        except Exception:
            error = "กรุณากรอกข้อมูลที่ถูกต้อง (ตัวเลขเท่านั้น)"
    return render_template('benzathine_penicillin_g.html',
                           dose=dose, calculated_ml=calculated_ml, error=error,
                           scheme=scheme, update_date=UPDATE_DATE)


@meds_bp.route('/cefazolin', methods=['GET', 'POST'])
def cefazolin_route():
    dose = result_ml = None
    error = None
    if request.method == 'POST':
        try:
            dose = _as_float(request.form.get('dose'), 'dose')
            if dose <= 0:
                raise ValueError("ขนาดยาต้องมากกว่า 0")
            # stock 1000 mg/10 mL -> 100 mg/mL
            result_ml = _round2(dose / 100.0)
        except Exception as e:
            error = f"กรุณากรอกข้อมูลให้ถูกต้อง: {e}"
    return render_template('cefazolin.html',
                           dose=dose, result_ml=result_ml, error=error,
                           update_date=UPDATE_DATE)


@meds_bp.route('/cefotaxime', methods=['GET', 'POST'])
def cefotaxime_route():
    dose = result_ml = multiplication = None
    content_extra = error = None
    action = (request.form.get('action') or '').strip()
    if request.method == 'POST':
        try:
            if action == 'dose':
                dose = _as_float(request.form.get('dose'), 'dose')
                result_ml = _ml_from_stock(dose, 1000, 10)  # 1000 mg/10 mL
            elif action == 'condition':
                dose = _as_float(request.form.get('dose_hidden') or request.form.get('dose'), 'dose_hidden')
                rmh = request.form.get('result_ml_hidden')
                result_ml = float(rmh) if (rmh not in (None, '')) else _ml_from_stock(dose, 1000, 10)
                multiplication = _as_int(request.form.get('multiplication'), 'multiplication')
                _ = _round2(result_ml * multiplication)  # total (ไม่ใช้แสดงก็ได้)
                content_extra = _content_extra_by_mult(multiplication)
            else:
                if request.form.get('dose'):
                    dose = _as_float(request.form.get('dose'), 'dose')
                    result_ml = _ml_from_stock(dose, 1000, 10)
                if request.form.get('multiplication'):
                    multiplication = _as_int(request.form.get('multiplication'), 'multiplication')
        except Exception:
            error = "กรุณากรอกข้อมูลให้ถูกต้อง"
    return render_template('cefotaxime.html',
                           dose=dose, result_ml=result_ml, multiplication=multiplication,
                           content_extra=content_extra, error=error, update_date=UPDATE_DATE)


@meds_bp.route('/ceftazidime', methods=['GET', 'POST'])
def ceftazidime_route():
    dose = result_ml = multiplication = None
    content_extra = error = None
    action = (request.form.get('action') or '').strip()
    if request.method == 'POST':
        try:
            if action == 'dose':
                dose = _as_float(request.form.get('dose'), 'dose')
                result_ml = _ml_from_stock(dose, 1000, 10)  # 1000 mg/10 mL
            elif action == 'condition':
                dose = _as_float(request.form.get('dose_hidden') or 0, 'dose_hidden')
                rmh = request.form.get('result_ml_hidden')
                result_ml = float(rmh) if rmh not in (None, '') else _ml_from_stock(dose, 1000, 10)
                multiplication = _as_int(request.form.get('multiplication'), 'multiplication')
                _ = _round2(result_ml * multiplication)
                content_extra = _content_extra_by_mult(multiplication)
        except Exception:
            error = "กรุณากรอกข้อมูลให้ถูกต้อง"
    return render_template('ceftazidime.html',
                           dose=dose, result_ml=result_ml, multiplication=multiplication,
                           content_extra=content_extra, error=error, update_date=UPDATE_DATE)


@meds_bp.route('/ciprofloxacin', methods=['GET', 'POST'])
def ciprofloxacin_route():
    dose = calculated_ml = None
    if request.method == 'POST':
        try:
            dose = _as_float(request.form.get('dose'), 'dose')
            calculated_ml = _round2(dose / 2.0)  # 2 mg/mL
        except Exception:
            dose = None
            calculated_ml = None
    return render_template('ciprofloxacin.html', dose=dose, calculated_ml=calculated_ml, update_date=UPDATE_DATE)


@meds_bp.route('/clindamycin', methods=['GET', 'POST'])
def clindamycin_route():
    dose = result_ml_1 = result_ml_2 = multiplication = final_result_1 = final_result_2 = None
    error = None
    if request.method == 'POST':
        action = (request.form.get('action') or '').strip()
        try:
            if action == 'dose':
                dose = _as_float(request.form.get('dose'), 'dose')
                result_ml_1 = _round2(dose * 4 / 600)  # 600 mg/4 mL
                result_ml_2 = _round2(dose / 6)       # 6 mg/mL
            elif action == 'condition':
                dose = _as_float(request.form.get('dose_hidden'), 'dose_hidden')
                result_ml_1 = _as_float(request.form.get('result_ml_1_hidden'), 'result_ml_1_hidden')
                result_ml_2 = _as_float(request.form.get('result_ml_2_hidden'), 'result_ml_2_hidden')
                multiplication = _as_float(request.form.get('multiplication'), 'multiplication')
                final_result_1 = _round2(result_ml_1 * multiplication)
                final_result_2 = _round2(result_ml_2 * multiplication)
            else:
                error = 'ส่งข้อมูลไม่ครบ (action หาย)'
        except ValueError:
            error = 'กรุณากรอกตัวเลขให้ถูกต้อง'
        except Exception as e:
            error = f'เกิดข้อผิดพลาด: {e}'
    return render_template('clindamycin.html',
                           dose=dose, result_ml_1=result_ml_1, result_ml_2=result_ml_2,
                           multiplication=multiplication, final_result_1=final_result_1,
                           final_result_2=final_result_2, error=error, update_date=UPDATE_DATE)


@meds_bp.route('/cloxacillin', methods=['GET', 'POST'])
def cloxacillin_route():
    dose = result_ml = multiplication = None
    error = None
    content_extra = None
    action = (request.form.get("action") or "").strip()
    try:
        if request.method == "POST":
            if action == "dose":
                dose = _as_float(request.form.get("dose"), "dose")
                result_ml = _ml_from_stock(dose, 1000, 5)  # 1000 mg/5 mL → 200 mg/mL
            elif action == "condition":
                dose = _as_float(request.form.get("dose_hidden"), "dose_hidden")
                result_ml = _as_float(request.form.get("result_ml_hidden"), "result_ml_hidden")
                multiplication = _as_int(request.form.get("multiplication"), "multiplication")
                content_extra = _content_extra_by_mult(multiplication)
            else:
                error = "คำขอไม่ถูกต้อง"
    except Exception as e:
        error = f"กรุณาใส่ข้อมูลที่ถูกต้อง: {e}"
    return render_template("cloxacillin.html",
                           dose=dose, result_ml=result_ml, multiplication=multiplication,
                           content_extra=content_extra, error=error, update_date=UPDATE_DATE)


@meds_bp.route('/colistin', methods=['GET', 'POST'])
def colistin_route():
    dose = result_ml = multiplication = final_result = None
    error = None
    content_extra = None
    try:
        if request.method == "POST":
            action = (request.form.get("action") or "dose").strip()
            if action == "dose":
                dose = _as_float(request.form.get("dose"), "dose")
                result_ml = _round2((dose * 2) / 150)  # 150 mg/2 mL
            elif action == "condition":
                dose = _as_float(request.form.get("dose_hidden"), "dose_hidden")
                result_ml = _as_float(request.form.get("result_ml_hidden"), "result_ml_hidden")
                multiplication = _as_int(request.form.get("multiplication"), "multiplication")
                final_result = _round2(result_ml * multiplication)
                content_extra = _content_extra_by_mult(multiplication)
            else:
                error = "คำสั่งไม่ถูกต้อง"
    except ValueError as e:
        error = f"กรุณาใส่ข้อมูลที่ถูกต้อง: {e}"
    except Exception as e:
        error = f"เกิดข้อผิดพลาด: {e}"
    return render_template("colistin.html",
                           dose=dose, result_ml=result_ml, multiplication=multiplication,
                           final_result=final_result, content_extra=content_extra,
                           error=error, update_date=UPDATE_DATE)


@meds_bp.route('/dexamethasone', methods=['GET', 'POST'])
def dexamethasone_route():
    dose = result_ml = None
    error = None
    if request.method == 'POST':
        try:
            dose = _as_float(request.form.get('dose'), 'dose')
            result_ml = _round2(dose * 100)  # placeholder
        except Exception:
            error = "กรุณากรอกขนาดยาที่ถูกต้อง"
    return render_template('dexamethasone.html',
                           dose=dose, result_ml=result_ml, error=error, update_date=UPDATE_DATE)


@meds_bp.route('/dobutamine', methods=['GET', 'POST'])
def dobutamine_route():
    dose = result_ml = DobutamineVolume = None
    error = None
    if request.method == 'POST':
        try:
            original_dosage = _as_float(request.form.get('original_dosage'), 'original_dosage')
            original_volume = _as_float(request.form.get('original_volume'), 'original_volume')
            desired_dosage = _as_float(request.form.get('desired_dosage'), 'desired_dosage')
            result_ml = (desired_dosage / original_dosage) * original_volume
            DobutamineVolume = desired_dosage / 50
            result_ml = _round2(result_ml)
            DobutamineVolume = _round2(DobutamineVolume)
        except Exception:
            error = "กรุณากรอกข้อมูลที่ถูกต้อง"
    return render_template('dobutamine.html',
                           dose=dose, result_ml=result_ml, DobutamineVolume=DobutamineVolume,
                           error=error, update_date=UPDATE_DATE)


@meds_bp.route('/dopamine', methods=['GET', 'POST'])
def dopamine_route():
    dose = result_ml = DopamineVolume = None
    error = None
    if request.method == 'POST':
        try:
            original_dosage = _as_float(request.form.get('original_dosage'), 'original_dosage')
            original_volume = _as_float(request.form.get('original_volume'), 'original_volume')
            desired_dosage = _as_float(request.form.get('desired_dosage'), 'desired_dosage')
            result_ml = (desired_dosage / original_dosage) * original_volume
            DopamineVolume = desired_dosage / 25
            result_ml = _round2(result_ml)
            DopamineVolume = _round2(DopamineVolume)
        except Exception:
            error = "กรุณากรอกข้อมูลที่ถูกต้อง"
    return render_template('dopamine.html',
                           dose=dose, result_ml=result_ml, DopamineVolume=DopamineVolume,
                           error=error, update_date=UPDATE_DATE)


@meds_bp.route('/fentanyl', methods=['GET'])
def fentanyl_route():
    return render_template('fentanyl.html', update_date=UPDATE_DATE)


@meds_bp.route('/fentanyl_continuous', methods=['GET', 'POST'])
def fentanyl_continuous_route():
    dose = result = error = None
    if request.method == 'POST':
        try:
            dose = _as_float(request.form.get('dose'), 'dose')
            result = _round2(dose * 0.1)
        except Exception as e:
            error = f"กรุณากรอกข้อมูลที่ถูกต้อง: {e}"
    return render_template('fentanyl_continuous.html',
                           dose=dose, result=result, error=error, update_date=UPDATE_DATE)


@meds_bp.route('/fentanyl_small_dose', methods=['GET', 'POST'])
def fentanyl_small_dose_route():
    dose = result = error = None
    if request.method == 'POST':
        try:
            dose = _as_float(request.form.get('dose'), 'dose')
            result = _round2(dose * 0.05)
        except Exception as e:
            error = f"กรุณากรอกข้อมูลที่ถูกต้อง: {e}"
    return render_template('fentanyl_small_dose.html',
                           dose=dose, result=result, error=error, update_date=UPDATE_DATE)


@meds_bp.route('/furosemide', methods=['GET', 'POST'])
def furosemide_route():
    dose = None
    if request.method == 'POST':
        try:
            dose = _as_float(request.form.get('dose'), 'dose')
        except Exception:
            dose = None
    return render_template('furosemide.html', dose=dose, update_date=UPDATE_DATE)


@meds_bp.route('/gentamicin', methods=['GET', 'POST'])
def gentamicin_route():
    dose = result_ml = final_result = multiplication = None
    error = None
    content_extra = None
    formula_display = "ml = mg ÷ 40  (เพราะ 80 mg / 2 ml ⇒ 40 mg/ml)"
    if request.method == 'POST':
        try:
            action = (request.form.get('action') or '').strip()
            if action in ('dose', ''):
                dose = _as_float(request.form.get('dose'), "ขนาดยา (mg)")
                if dose <= 0: raise ValueError("ขนาดยาต้องมากกว่า 0")
                result_ml = _round2(dose / 40.0)
            elif action == 'condition':
                dose = _as_float(request.form.get('dose_hidden') or request.form.get('dose'), "ขนาดยา (mg)")
                if dose <= 0: raise ValueError("ขนาดยาต้องมากกว่า 0")
                result_ml_hidden = request.form.get('result_ml_hidden')
                result_ml = float(result_ml_hidden) if result_ml_hidden not in (None, "") else _round2(dose / 40.0)
                multiplication = _as_int(request.form.get('multiplication'), "เงื่อนไขตัวคูณ (3×/6×)")
                if multiplication not in (3, 6): raise ValueError("เงื่อนไขตัวคูณต้องเป็น 3 หรือ 6")
                final_result = _round2(float(result_ml) * multiplication)
                content_extra = _content_extra_by_mult(multiplication)
            else:
                error = "รูปแบบคำขอไม่ถูกต้อง (action ไม่รองรับ)"
        except Exception as e:
            error = f"กรุณาใส่ข้อมูลที่ถูกต้อง: {e}"
    return render_template('gentamicin.html',
                           dose=dose, result_ml=result_ml, final_result=final_result,
                           multiplication=multiplication, content_extra=content_extra,
                           formula_display=formula_display, error=error, update_date=UPDATE_DATE)


@meds_bp.route('/hydrocortisone', methods=['GET', 'POST'])
def hydrocortisone_route():
    dose = result_ml = units = error = None
    MG_PER_ML = 50.0
    U_PER_MG = 4.0
    if request.method == 'POST':
        try:
            dose = _as_float(request.form.get('dose'), 'dose')
            result_ml = _round2(dose / MG_PER_ML)
            units = _round2(dose * U_PER_MG)
        except Exception:
            error = "กรุณากรอกตัวเลขที่ถูกต้อง"
    return render_template('hydrocortisone.html',
                           dose=dose, result_ml=result_ml, units=units,
                           error=error, update_date=UPDATE_DATE)


@meds_bp.route('/insulin', methods=['GET', 'POST'])
def insulin_route():
    dose = result = None
    concentration = 1
    if request.method == 'POST':
        try:
            dose = _as_float(request.form.get('dose'), 'dose')
            result = _round2(dose * 100 / concentration)
        except Exception:
            result = "ข้อมูลไม่ถูกต้อง"
    return render_template('insulin.html',
                           dose=dose, result=result, update_date=UPDATE_DATE)


@meds_bp.route('/levofloxacin', methods=['GET', 'POST'])
def levofloxacin_route():
    dose = None
    concentration = 5.0
    multiplication = 3
    result_ml = final_result = error = None
    if request.method == 'POST':
        try:
            dose = _as_float(request.form.get('dose'), 'dose')
            concentration = _as_float(request.form.get('concentration'), 'concentration')
            multiplication = _as_int(request.form.get('multiplication'), 'multiplication')
            if concentration <= 0: raise ValueError("ความเข้มข้นต้องมากกว่า 0")
            result_ml = dose / concentration
            final_result = result_ml * multiplication
            result_ml = _round2(result_ml); final_result = _round2(final_result)
        except Exception as e:
            error = str(e)
    return render_template('levofloxacin.html',
                           dose=dose, concentration=concentration,
                           multiplication=multiplication, result_ml=result_ml,
                           final_result=final_result, update_date=UPDATE_DATE)


@meds_bp.route('/meropenem', methods=['GET', 'POST'])
def meropenem_route():
    dose = result_ml = final_result = multiplication = None
    error = formula_display = None
    content_extra = None
    try:
        if request.method == 'POST':
            action = (request.form.get('action') or '').strip().lower()
            if action == 'dose':
                dose = _as_float(request.form.get('dose'), 'dose')
                if dose <= 0: raise ValueError("ขนาดยาต้องมากกว่า 0 mg")
                result_ml = _round2(dose / 50.0)  # target 50 mg/mL (รวม ~20 mL)
            elif action == 'condition':
                dose = _as_float(request.form.get('dose_hidden'), 'dose_hidden')
                result_ml = _as_float(request.form.get('result_ml_hidden'), 'result_ml_hidden')
                multiplication = _as_int(request.form.get('multiplication'), 'multiplication')
                if multiplication not in (3, 6): raise ValueError("ต้องเป็น 3 หรือ 6")
                final_result = _round2(result_ml * multiplication)
                content_extra = _content_extra_by_mult(multiplication)
            else:
                raw_dose = request.form.get('dose')
                raw_mult = request.form.get('multiplication')
                if raw_dose:
                    dose = _as_float(raw_dose, 'dose')
                    if dose <= 0: raise ValueError("ขนาดยาต้องมากกว่า 0 mg")
                    result_ml = _round2(dose / 50.0)
                if raw_mult:
                    multiplication = _as_int(raw_mult, 'multiplication')
                    if multiplication not in (3, 6):
                        raise ValueError("multiplication ต้องเป็น 3 หรือ 6")
                    if result_ml is None:
                        raise ValueError("ไม่พบผลรอบแรก")
                    final_result = _round2(result_ml * multiplication)
                    content_extra = _content_extra_by_mult(multiplication)
    except Exception as e:
        error = f"กรุณาใส่ข้อมูลที่ถูกต้อง: {e}"
    return render_template('meropenem.html',
                           dose=dose, result_ml=result_ml, final_result=final_result,
                           multiplication=multiplication, content_extra=content_extra,
                           formula_display=formula_display, error=error, update_date=UPDATE_DATE)


@meds_bp.route('/metronidazole', methods=['GET', 'POST'])
def metronidazole():
    dose = calculated_ml = None
    if request.method == 'POST':
        try:
            dose = _as_float(request.form.get('dose'), 'dose')
            calculated_ml = _round2((dose * 100) / 500)  # ตามสูตรที่ให้
        except Exception:
            dose = None; calculated_ml = None
    return render_template('metronidazole.html',
                           dose=dose, calculated_ml=calculated_ml, update_date=UPDATE_DATE)


@meds_bp.route('/midazolam_fentanyl', methods=['GET', 'POST'])
def midazolam_fentanyl_route():
    midazolam_dosage = fentanyl_dosage = original_volume = None
    midazolam_volume = fentanyl_volume = final_volume = error = None
    if request.method == 'POST':
        try:
            midazolam_dosage = _as_float(request.form.get('midazolam_dosage'), 'midazolam_dosage')
            fentanyl_dosage = _as_float(request.form.get('fentanyl_dosage'), 'fentanyl_dosage')
            original_volume = _as_float(request.form.get('original_volume'), 'original_volume')
            midazolam_volume = _round2(midazolam_dosage / 5)
            fentanyl_volume = _round2(fentanyl_dosage / 50)
            final_volume = _round2(original_volume - (midazolam_volume + fentanyl_volume))
        except Exception as e:
            error = f"กรุณาใส่ข้อมูลที่ถูกต้อง: {e}"
    return render_template('midazolam_fentanyl.html',
                           midazolam_dosage=midazolam_dosage,
                           fentanyl_dosage=fentanyl_dosage,
                           original_volume=original_volume,
                           midazolam_volume=midazolam_volume,
                           fentanyl_volume=fentanyl_volume,
                           final_volume=final_volume,
                           error=error,
                           update_date=UPDATE_DATE)


@meds_bp.route('/midazolam', methods=['GET'])
def midazolam_route():
    return render_template('midazolam.html', update_date=UPDATE_DATE)


@meds_bp.route('/midazolam_continuous', methods=['GET', 'POST'])
def midazolam_continuous_route():
    dose = result = error = None
    if request.method == 'POST':
        try:
            dose = _as_float(request.form.get('dose'), 'dose')
            result = _round2(dose * 0.1)
        except Exception as e:
            error = f"กรุณากรอกข้อมูลที่ถูกต้อง: {e}"
    return render_template('midazolam_continuous.html',
                           dose=dose, result=result, error=error, update_date=UPDATE_DATE)


@meds_bp.route('/midazolam_small_dose', methods=['GET', 'POST'])
def midazolam_small_dose_route():
    dose = result = error = None
    if request.method == 'POST':
        try:
            dose = _as_float(request.form.get('dose'), 'dose')
            result = _round2(dose * 0.1)
        except Exception as e:
            error = f"กรุณากรอกข้อมูลที่ถูกต้อง: {e}"
    return render_template('midazolam_small_dose.html',
                           dose=dose, result=result, error=error, update_date=UPDATE_DATE)


@meds_bp.route('/morphine', methods=['GET'])
def morphine_route():
    return render_template('morphine.html', update_date=UPDATE_DATE)


@meds_bp.route('/morphine_continuous', methods=['GET', 'POST'])
def morphine_continuous_route():
    dose = result = error = None
    if request.method == 'POST':
        try:
            dose = _as_float(request.form.get('dose'), 'dose')
            result = _round2(dose * 0.1)
        except Exception as e:
            error = f"กรุณากรอกข้อมูลที่ถูกต้อง: {e}"
    return render_template('morphine_continuous.html',
                           dose=dose, result=result, error=error, update_date=UPDATE_DATE)


@meds_bp.route('/morphine_small_dose', methods=['GET', 'POST'])
def morphine_small_dose_route():
    dose = result = error = None
    if request.method == 'POST':
        try:
            dose = _as_float(request.form.get('dose'), 'dose')
            result = _round2(dose * 0.1)
        except Exception:
            error = "กรุณากรอกข้อมูลที่ถูกต้อง"
    return render_template('morphine_small_dose.html',
                           dose=dose, result=result, error=error, update_date=UPDATE_DATE)


@meds_bp.route('/nimbex', methods=['GET', 'POST'])
def nimbex_route():
    dose = result_ml = final_ml = error = None
    if request.method == 'POST':
        try:
            dose = _as_float(request.form.get('dose'), 'dose')
            result_ml = _round2(dose * 5 / 10)
            final_ml = _round2(10 - result_ml)
        except Exception as e:
            error = f"กรุณาใส่ข้อมูลที่ถูกต้อง: {e}"
    return render_template('nimbex.html',
                           dose=dose, result_ml=result_ml, final_ml=final_ml,
                           error=error, update_date=UPDATE_DATE)


@meds_bp.route('/omeprazole', methods=['GET', 'POST'])
def omeprazole_route():
    dose = result_ml = final_result = multiplication = error = None
    content_extra = None

    def ml_from_dose(d):  # 4 mg/mL
        return _round2(float(d) / 4.0)

    try:
        if request.method == 'POST':
            action = request.form.get('action')
            if action == 'dose':
                dose = _as_float(request.form.get('dose'), 'dose')
                if dose <= 0: raise ValueError("dose ต้องมากกว่า 0")
                result_ml = ml_from_dose(dose)
            elif action == 'condition':
                multiplication = _as_int(request.form.get('multiplication'), 'multiplication')
                dose_hidden = request.form.get('dose_hidden')
                result_ml_hidden = request.form.get('result_ml_hidden')
                if dose_hidden:
                    dose = _as_float(dose_hidden, 'dose_hidden')
                    if dose <= 0: raise ValueError("dose ต้องมากกว่า 0")
                    result_ml = ml_from_dose(dose)
                elif result_ml_hidden:
                    result_ml = _round2(float(result_ml_hidden))
                    dose = _round2(result_ml * 4.0)
                else:
                    raise ValueError("ไม่พบค่าตั้งต้น (dose/result_ml)")
                final_result = _round2(result_ml * multiplication)
                content_extra = _content_extra_by_mult(multiplication)
            else:
                # โหมดโพสต์เดียว
                dose = _as_float(request.form.get('dose'), 'dose')
                multiplication = _as_int(request.form.get('multiplication'), 'multiplication')
                if dose <= 0: raise ValueError("dose ต้องมากกว่า 0")
                result_ml = ml_from_dose(dose)
                final_result = _round2(result_ml * multiplication)
                content_extra = _content_extra_by_mult(multiplication)
    except Exception as e:
        error = f"กรุณาใส่ข้อมูลที่ถูกต้อง: {e}"

    return render_template('omeprazole.html',
                           dose=dose, result_ml=result_ml, final_result=final_result,
                           multiplication=multiplication, content_extra=content_extra,
                           formula_display=None, error=error, update_date=UPDATE_DATE)


@meds_bp.route('/penicillin', methods=['GET', 'POST'])
def penicillin_g_sodium_route():
    dose = calculated_ml = error = None
    if request.method == 'POST':
        try:
            dose = _as_float(request.form.get('dose'), 'dose')
            calculated_ml = _round2((dose * 10) / 5_000_000)
        except Exception:
            error = "กรุณากรอกข้อมูลที่ถูกต้อง"
    return render_template('penicillin_g_sodium.html',
                           dose=dose, calculated_ml=calculated_ml,
                           error=error, update_date=UPDATE_DATE)


@meds_bp.route('/phenobarbital', methods=['GET', 'POST'])
def phenobarbital_route():
    TARGET_CONC = 20.0  # mg/mL
    dose = vol_ml = error = None
    if request.method == "POST":
        try:
            dose = _as_float(request.form.get("dose"), "dose")
            if dose <= 0:
                raise ValueError("กรุณากรอกขนาดยา (mg) มากกว่า 0")
            vol_ml = _round2(dose / TARGET_CONC)
        except Exception as e:
            error = str(e)
    return render_template("phenobarbital.html",
                           target_conc=TARGET_CONC, dose=dose, vol_ml=vol_ml, error=error)


@meds_bp.route('/phenytoin', methods=['GET', 'POST'])
def phenytoin_route():
    dose = result_ml = error = None
    if request.method == 'POST':
        try:
            dose = _as_float(request.form.get('dose'), 'dose')
            result_ml = _round2(dose * 4)  # placeholder
        except Exception:
            error = "กรุณากรอกขนาดยาที่ถูกต้อง"
    return render_template('phenytoin.html',
                           dose=dose, result_ml=result_ml, error=error, update_date=UPDATE_DATE)


@meds_bp.route('/remdesivir', methods=['GET', 'POST'])
def remdesivir_route():
    dose = result_ml_1 = result_ml_2 = final_result_1 = final_result_2 = multiplication = error = None
    if request.method == 'POST':
        try:
            dose = _as_float(request.form.get('dose'), 'dose')
            result_ml_1 = _round2((dose * 20) / 100)  # ตามสูตรเดิม
            result_ml_2 = _round2(dose / 1.25)
            if request.form.get('multiplication'):
                multiplication = _as_float(request.form.get('multiplication'), 'multiplication')
                final_result_1 = _round2(result_ml_1 * multiplication)
                final_result_2 = _round2(result_ml_2 * multiplication)
        except Exception as e:
            error = f"กรุณาใส่ข้อมูลที่ถูกต้อง: {e}"
    return render_template('remdesivir.html',
                           dose=dose, result_ml_1=result_ml_1, result_ml_2=result_ml_2,
                           final_result_1=final_result_1, final_result_2=final_result_2,
                           multiplication=multiplication, error=error, update_date=UPDATE_DATE)


@meds_bp.route('/sul-am', methods=['GET', 'POST'])
def sul_am_route():
    dose = result_ml = multiplication = final_result = None
    content_extra = error = None
    if request.method == 'POST':
        action = (request.form.get('action') or 'dose').strip()
        try:
            if action == 'dose':
                dose = _as_float(request.form.get('dose'), 'dose')
                if dose <= 0: raise ValueError('dose must be > 0')
                # 3 g → เติมรวม 8 mL ⇒ 375 mg/mL  => ml = (dose*8)/3000
                result_ml = _round2((dose * 8.0) / 3000.0)
            elif action == 'condition':
                dose = _as_float(request.form.get('dose_hidden'), 'dose_hidden')
                result_ml = _as_float(request.form.get('result_ml_hidden'), 'result_ml_hidden')
                multiplication = _as_int(request.form.get('multiplication'), 'multiplication')
                final_result = _round2(result_ml * multiplication)
                # กฎพิเศษ: ถ้า final_result ถึง 9 หรือ 6 mL ให้ “ไม่ต้องผสม”
                if multiplication == 3:
                    content_extra = (_content_extra_by_mult(3) if final_result < 9
                                     else {"message": "ดูดยา 9 mL ไม่ต้องผสมสารละลาย",
                                           "details": ["ให้เข้า ~3 mL ตั้งอัตรา ~6 mL/hr"]})
                elif multiplication == 6:
                    content_extra = (_content_extra_by_mult(6) if final_result < 6
                                     else {"message": "ดูดยา 6 mL ไม่ต้องผสมสารละลาย",
                                           "details": ["ให้เข้า ~1 mL ตั้งอัตรา ~2 mL/hr"]})
            else:
                raise ValueError('unknown action')
        except Exception:
            error = "กรุณากรอกข้อมูลที่ถูกต้อง"
    return render_template('sul_am.html',
                           dose=dose, result_ml=result_ml, multiplication=multiplication,
                           final_result=final_result, content_extra=content_extra,
                           error=error, update_date=UPDATE_DATE)


@meds_bp.route('/sulbactam', methods=['GET', 'POST'])
def sulbactam_route():
    dose = result_ml = final_result = multiplication = error = None
    content_extra = None
    try:
        if request.method == 'POST':
            action = (request.form.get('action') or 'dose').strip()
            if action == 'dose':
                dose = _as_float(request.form.get('dose'), 'dose')
                if dose < 0: raise ValueError('dose ต้องเป็นค่าบวก')
                # 2 g/vial เติม 8 mL → 250 mg/mL => (dose*8)/2000
                result_ml = _round2((dose * 8.0) / 2000.0)
            elif action == 'condition':
                dose = _as_float(request.form.get('dose_hidden') or request.form.get('dose'), 'dose_hidden')
                res_h = request.form.get('result_ml_hidden')
                result_ml = float(res_h) if res_h else _round2((dose * 8.0) / 2000.0)
                multiplication = _as_int(request.form.get('multiplication'), 'multiplication')
                if multiplication not in (3, 6): raise ValueError('multiplication ต้องเป็น 3 หรือ 6')
                final_result = _round2(result_ml * multiplication)
                if multiplication == 3:
                    content_extra = (_content_extra_by_mult(3) if final_result < 9 else
                                     {"message": "Intermittent infusion pump",
                                      "details": ["(3X + diluent Up to 9 mL)", "ดูดยา 9 mL (ไม่ต้องผสม)", "ตั้ง ~6 mL/hr"]})
                else:  # 6X
                    content_extra = (_content_extra_by_mult(6) if final_result < 6 else
                                     {"message": "Intermittent infusion",
                                      "details": ["(6X + diluent Up to 6 mL)", "ดูดยา 6 mL (ไม่ต้องผสม)", "ตั้ง ~2 mL/hr"]})
    except Exception as e:
        error = f"กรุณากรอกข้อมูลที่ถูกต้อง: {e}"
    return render_template('sulbactam.html',
                           dose=dose, result_ml=result_ml, final_result=final_result,
                           multiplication=multiplication, content_extra=content_extra,
                           error=error, update_date=UPDATE_DATE)


@meds_bp.route('/sulperazone', methods=['GET', 'POST'])
def sulperazone_route():
    dose = result_ml = final_result = multiplication = error = None
    content_extra = None
    if request.method == 'POST':
        try:
            action = (request.form.get('action') or 'dose').strip()
            if action == 'dose':
                dose = _as_float(request.form.get('dose'), 'dose')
                result_ml = _round2((dose * 10) / 500)
            elif action == 'condition':
                dose_hidden = request.form.get('dose_hidden', '')
                result_ml_hidden = request.form.get('result_ml_hidden', '')
                dose = float(dose_hidden) if dose_hidden != '' else None
                if result_ml_hidden != '':
                    result_ml = float(result_ml_hidden)
                elif dose is not None:
                    result_ml = _round2((dose * 10) / 500)
                multiplication = _as_int(request.form.get('multiplication') or '0', 'multiplication')
                if result_ml is not None and multiplication:
                    final_result = _round2(result_ml * multiplication)
                    content_extra = _content_extra_by_mult(multiplication)
            else:
                error = "คำสั่งไม่ถูกต้อง"
        except Exception as e:
            error = f"กรุณากรอกข้อมูลที่ถูกต้อง: {e}"
    return render_template('sulperazone.html',
                           dose=dose, result_ml=result_ml, final_result=final_result,
                           multiplication=multiplication, content_extra=content_extra,
                           error=error, update_date=UPDATE_DATE)


@meds_bp.route('/tazocin', methods=['GET', 'POST'])
def tazocin_route():
    dose = result_ml = multiplication = error = None
    content_extra = None
    try:
        if request.method == 'POST':
            action = (request.form.get('action') or 'dose').strip()
            if action == 'dose':
                dose = _as_float(request.form.get('dose'), 'dose')
                result_ml = _round2((dose * 20.0) / 4000.0)  # = dose / 200
            elif action == 'condition':
                dose = _as_float(request.form.get('dose_hidden'), 'dose_hidden')
                result_ml = _as_float(request.form.get('result_ml_hidden'), 'result_ml_hidden')
                multiplication = _as_int(request.form.get('multiplication'), 'multiplication')
                _ = _round2(result_ml * multiplication)
                content_extra = _content_extra_by_mult(multiplication)
    except Exception as e:
        error = f"กรุณากรอกข้อมูลที่ถูกต้อง: {e}"
    return render_template('tazocin.html',
                           dose=dose, result_ml=result_ml,
                           multiplication=multiplication, content_extra=content_extra,
                           error=error, update_date=UPDATE_DATE)


@meds_bp.route('/unasyn', methods=['GET', 'POST'])
def unasyn_route():
    dose = result_ml = final_result = multiplication = None
    content_extra = error = None
    try:
        if request.method == 'POST':
            action = (request.form.get('action') or 'dose').strip()
            if action == 'dose':
                dose = _as_float(request.form.get('dose'), 'dose')
                result_ml = _round2((dose * 8.0) / 3000.0)  # (dose*8)/3000
            elif action == 'condition':
                dose = _as_float(request.form.get('dose_hidden'), 'dose_hidden')
                result_ml = _as_float(request.form.get('result_ml_hidden'), 'result_ml_hidden')
                multiplication = _as_int(request.form.get('multiplication'), 'multiplication')
                if multiplication not in (3, 6): raise ValueError("กรุณาเลือก 3 หรือ 6 เท่า")
                final_result = _round2(result_ml * multiplication)
                content_extra = _content_extra_by_mult(multiplication)
    except Exception as e:
        error = f"กรุณาใส่ข้อมูลที่ถูกต้อง: {e}"
    return render_template('unasyn.html',
                           dose=dose, result_ml=result_ml, final_result=final_result,
                           multiplication=multiplication, content_extra=content_extra,
                           error=error, update_date=UPDATE_DATE)


@meds_bp.route('/vancomycin', methods=['GET', 'POST'])
def vancomycin_route():
    dose = concentration = result_ml_1 = result_ml_2 = None
    multiplication = final_result_1 = final_result_2 = None
    error = None
    if request.method == 'POST':
        try:
            action = (request.form.get('action') or '').strip()
            if action == 'dose':
                dose = _as_float(request.form.get('dose'), 'dose')
                concentration = _as_int(request.form.get('concentration'), 'concentration')
                if concentration not in (5, 7):
                    raise ValueError("เลือกระดับความเข้มข้นได้เฉพาะ 5 mg/mL หรือ 7 mg/mL")
                # รอบแรก:
                result_ml_1 = _round2((dose * 10.0) / 500.0)  # 500 mg/10 mL → 50 mg/mL
                result_ml_2 = _round2(dose / float(concentration))
            elif action == 'condition':
                dose = _as_float(request.form.get('dose_hidden'), 'dose_hidden')
                concentration = _as_int(request.form.get('concentration_hidden'), 'concentration_hidden')
                result_ml_1 = _as_float(request.form.get('result_ml_1_hidden'), 'result_ml_1_hidden')
                result_ml_2 = _as_float(request.form.get('result_ml_2_hidden'), 'result_ml_2_hidden')
                multiplication = _as_float(request.form.get('multiplication'), 'multiplication')
                if concentration not in (5, 7):
                    raise ValueError("เลือกระดับความเข้มข้นได้เฉพาะ 5 mg/mL หรือ 7 mg/mL")
                final_result_1 = _round2(result_ml_1 * multiplication)
                final_result_2 = _round2(result_ml_2 * multiplication)
            else:
                # fallback ฟอร์มเก่า
                if request.form.get('dose'):
                    dose = _as_float(request.form.get('dose'), 'dose')
                if request.form.get('concentration'):
                    concentration = _as_int(request.form.get('concentration'), 'concentration')
                if dose is not None and concentration in (5, 7):
                    result_ml_1 = _round2((dose * 10.0) / 500.0)
                    result_ml_2 = _round2(dose / float(concentration))
        except Exception as e:
            error = f"กรุณากรอกข้อมูลที่ถูกต้อง: {e}"

    return render_template('vancomycin.html',
                           dose=dose, concentration=concentration,
                           result_ml_1=result_ml_1, result_ml_2=result_ml_2,
                           multiplication=multiplication, final_result_1=final_result_1,
                           final_result_2=final_result_2, error=error, update_date=UPDATE_DATE)
