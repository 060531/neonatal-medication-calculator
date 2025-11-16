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
import math 


meds_bp = Blueprint("meds", __name__)

meds_bp = Blueprint("meds_bp", __name__)

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
                "กำหนดให้ปริมาณสารละลายยา (ปริมาณยา + สารละลายเชื้อจางยา) = 8 ml.",
                "(ความจุของ Extension Tube ประมาณ 5 ml. + Volume ที่ต้องบริหารเข้าผู้ป่วย 3 ml.)",
                "<div style='text-align:center'>(3X + สารละลายเจือจางยา Up to 9 mL)</div>",
                "การเตรียมยา:",
                "1) คำนวณปริมาณยาที่ต้องการใช้เป็นมิลลิลิตร (ml.) แทนค่าในสูตร",
                "2) ใช้ Syringe ขนาดที่เหมาะสม ดูดปริมาณยาที่ต้องการเตรียมไว้",
                "3) ใช้ Syringe ขนาด 10 ml. หรือ 20 ml. ดูดปริมาณสารละลายเชื้อจางยาเตรียมไว้",
                "4) ผสมยาใน Syringe ที่มีสารละลายเชื้อจางยาอยู่ Mixed ให้เข้ากัน",
                "5) ต่อ Syringe กับ Extension Tube นำไปวางบน Syringe pump กด Start ตั้งอัตรา ~6 mL/hr.",
                "6) Purge ยาให้ทั่วท่อโดยการดัน Syringe 3 ml. แล้วจึงบริหารผู้ป่วย",
            ],
        }
    if mult == 6:
        return {
            "message": "การบริหารยาโดย Intermittent intravenous infusion",
            "details": [
                "สำหรับทารกที่มีน้ำหนักน้อยกว่า 1,500 กรัม",
                "1) กำหนดให้สารละลายยาซึ่งบริหารเข้าสู้ผู้ป่วยปริมาณเท่ากับ = 1 mL",
                "2) ให้ X คือ ปริมาณยาที่ต้องการเตรียม กำหนดสูตรในการเตรียมสารละลายยา ดังนี้:",
                "<div style='text-align:center'>6X + สารละลายเจือจางยา Up to 6 mL</div>",
                "3) จากข้อ 2 จะได้สารละลายทั้งหมด 6 ml. ซึ่งหมายถึง ความจุของ Extension Tube ประมาณ 5 ml. + Volume ที่ต้องการบริหารเข้าสู่ผู้ป่วย 1 ml.",
                "4) บริหารโดยใช้ Syringe pump ตั้งอัตราเร็ว ~2 mL/hr",
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
    dose (mg) → result_ml_1 = (dose*5)/250   # ปริมาณตัวสาร (จาก stock 250 mg/5 ml)
                result_ml_2 = dose/5         # ปริมาณสารละลายเป้าหมาย (5 mg/ml)
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
            # รับ dose จากฟอร์ม (ทั้งฟอร์มแรกและฟอร์มคูณ ใช้ name="dose")
            raw_dose = (request.form.get("dose") or "").strip()
            if not raw_dose:
                raise ValueError("ไม่พบค่าขนาดยา (dose)")

            dose = float(raw_dose)

            # คำนวณผลลัพธ์รอบแรก
            result_ml_1 = round((dose * 5.0) / 250.0, 2)  # stock 250 mg / 5 ml
            result_ml_2 = round(dose / 5.0, 2)            # target 5 mg/ml

            # ถ้ามีการเลือก multiplication (ฟอร์มที่ 2)
            mult_raw = (request.form.get("multiplication") or "").strip()
            if mult_raw:
                multiplication = float(mult_raw)
                final_result_1 = round(result_ml_1 * multiplication, 2)
                final_result_2 = round(result_ml_2 * multiplication, 2)

        except Exception as e:
            error = f"กรุณาใส่ข้อมูลที่ถูกต้อง: {e}"

    # Flask mode → static_build = False
    return render_template(
        "acyclovir.html",
        static_build=False,
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

            # -------------------------------
            # ขั้นที่ 1: รับ dose (mg) -> คำนวณ mL
            # -------------------------------
            if action == 'dose':
                raw = (request.form.get('dose') or '').strip()
                if not raw:
                    raise ValueError("กรุณาระบุ dose (mg)")
                dose = float(raw)
                if dose < 0:
                    raise ValueError("dose ต้องเป็นตัวเลข ≥ 0")

                # stock 500 mg / 2 mL  ⇒ mL = mg * 2 / 500
                result_ml = round((dose * 2.0) / 500.0, 2)

            # -------------------------------
            # ขั้นที่ 2: รับเงื่อนไขการคูณ (3 หรือ 6)
            # -------------------------------
            elif action == 'condition':
                dose_raw = (request.form.get('dose_hidden') or '').strip()
                result_raw = (request.form.get('result_ml_hidden') or '').strip()
                mult_raw = (request.form.get('multiplication') or '').strip()

                if not dose_raw or not result_raw:
                    raise ValueError("ข้อมูลคำนวณเดิมไม่ครบ โปรดคำนวณขั้นแรกก่อน")

                dose = float(dose_raw)
                result_ml = float(result_raw)
                multiplication = int(mult_raw)

                if multiplication not in (3, 6):
                    raise ValueError("multiplication ต้องเป็น 3 หรือ 6")

                # ปริมาณยาหลังคูณ (mL)
                final_result = round(result_ml * multiplication, 2)

                # กำหนดเป้าปริมาณรวม และข้อความกำกับ
                if multiplication == 3:
                    target_total = 9.0
                    msg_block = "ปริมาณที่บริหารเข้าทารก ≈ 3 mL → ตั้งอัตรา 6 mL/hr"
                    content_extra = {
                        "message": "การบริหารยาโดย Intermittent intravenous infusion pump",
                        "details": [
                            "สำหรับทารกที่มีน้ำหนักมากกว่า 1,500 กรัม",
                            "กำหนดให้ปริมาณสารละลายยา (ปริมาณยา + สารละลายเชื้อจางยา) = 8 ml.",
                            "(ความจุของ Extension Tube ประมาณ 5 ml. + Volume ที่ต้องบริหารเข้าผู้ป่วย 3 ml.)",
                            "<div style='text-align:center'>(3X + สารละลายเจือจาง Up to 9 ml.)</div>",
                            "การเตรียมยา:",
                            "1. คำนวณปริมาณยาที่ต้องการใช้เป็นมิลลิลิตร (ml.) แทนค่าในสูตร",
                            "2. ใช้ Syringe ขนาดที่เหมาะสม ดูดปริมาณยาที่ต้องการเตรียมไว้",
                            "3. ใช้ Syringe ขนาด 10 ml. หรือ 20 ml. ดูดปริมาณสารละลายเชื้อจางยาเตรียมไว้",
                            "4. ผสมยาใน Syringe ที่มีสารละลายเชื้อจางยาอยู่ Mixed ให้เข้ากัน",
                            "5. ต่อ Syringe กับ Extension Tube นำไปวางบน Syringe pump กด Start ตั้งอัตราเร็ว 6 ml/hr.",
                            "6. Purge ยาให้ทั่วท่อโดยการดัน Syringe 3 ml. แล้วจึงบริหารผู้ป่วย",
                        ],
                    }
                else:  # multiplication == 6
                    target_total = 6.0
                    msg_block = "ปริมาณที่บริหารเข้าทารก ≈ 1 mL → ตั้งอัตรา 2 mL/hr"
                    content_extra = {
                        "message": "การบริหารยาโดย Intermittent intravenous infusion",
                        "details": [
                            "สำหรับทารกที่มีน้ำหนักน้อยกว่า 1,500 กรัม",
                            "1. กำหนดให้สารละลายยาซึ่งบริหารเข้าสู่ผู้ป่วยปริมาณเท่ากับ 1 ml.",
                            "2. ให้ X คือ ปริมาณยาที่ต้องการเตรียม กำหนดสูตรในการเตรียมสารละลายยา ดังนี้:",
                            "<div style='text-align:center'>(6X + สารละลายเจือจาง Up to 6 ml.)</div>",
                            "3. จากข้อ 2 จะได้สารละลายทั้งหมด 6 ml. ซึ่งหมายถึง ความจุของ Extension Tube ประมาณ 5 ml. + Volume ที่ต้องการบริหารเข้าสู่ผู้ป่วย 1 ml.",
                            "4. บริหารยาโดยใช้ Syringe pump ตั้งอัตราเร็ว 2 ml/hr.",
                        ],
                    }

                # ปริมาณ diluent ที่ต้องเติม
                if target_total is not None and final_result is not None:
                    need = target_total - final_result
                    diluent_to_add = round(need, 2) if need > 0 else 0.0

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
        UPDATE_DATE=UPDATE_DATE,
    )

@meds_bp.route('/aminophylline', methods=['GET', 'POST'])
def aminophylline_route():
    dose = result_ml = None
    error = None

    if request.method == 'POST':
        try:
            # รับค่าจากฟอร์ม
            raw = (request.form.get('dose') or '').strip()
            if not raw:
                raise ValueError("กรุณากรอกขนาดยา (mg)")

            dose = float(raw)
            if dose < 0:
                raise ValueError("ขนาดยาต้องมากกว่าหรือเท่ากับ 0")

            # สูตรในหน้า: u = mg × 10  → ให้คิดเป็นจำนวนหน่วย u
            # ถ้าอยากให้เป็นจำนวนเต็ม ให้ใช้ int(round(...))
            result_ml = int(round(dose * 10))

        except Exception as e:
            error = f"กรุณากรอกขนาดยาที่ถูกต้อง: {e}"

    return render_template(
        'aminophylline.html',
        dose=dose,
        result_ml=result_ml,
        error=error,
        UPDATE_DATE=UPDATE_DATE,  # ให้ตรงกับชื่อที่ใช้ใน template
    )


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
    dose = None
    result_ml = None
    multiplication = None
    content_extra = None
    error = None

    if request.method == 'POST':
        try:
            # ใช้ชื่อ field ตาม template: step = 'dose' หรือ 'condition'
            step = (request.form.get('step') or '').strip().lower()

            # -------------------------
            # รอบที่ 1: รับ dose (mg)
            # -------------------------
            if step == 'dose':
                raw = (request.form.get('dose') or '').strip()
                if not raw:
                    raise ValueError("กรุณากรอกขนาดยา (mg)")

                dose = float(raw)
                if dose < 0:
                    raise ValueError("ขนาดยาต้องมากกว่าหรือเท่ากับ 0")

                # stock 1000 mg / 10 mL → (dose * 10) / 1000
                result_ml = round((dose * 10.0) / 1000.0, 2)

            # -------------------------
            # รอบที่ 2: ใช้ค่าที่คำนวณแล้ว + เงื่อนไขคูณ
            # -------------------------
            elif step == 'condition':
                # hidden dose / result_ml จากฟอร์มรอบที่ 2
                dose_raw = (request.form.get('dose') or '').strip()
                if not dose_raw:
                    raise ValueError("ไม่พบข้อมูล dose เดิม โปรดคำนวณรอบแรกก่อน")

                dose = float(dose_raw)

                result_raw = (request.form.get('result_ml') or '').strip()
                if result_raw:
                    result_ml = float(result_raw)
                else:
                    # เผื่อกรณีไม่มี hidden result_ml
                    result_ml = round((dose * 10.0) / 1000.0, 2)

                mult_raw = (request.form.get('multiplication') or '').strip()
                if not mult_raw:
                    raise ValueError("กรุณาเลือกเงื่อนไขการคูณ")

                multiplication = int(mult_raw)

                # -------------------------
                # กล่องคำอธิบายเพิ่มเติม
                # -------------------------
                if multiplication == 3:
                    content_extra = {
                        "message": "การบริหารยาโดย Intermittent intravenous infusion pump",
                        "details": [
                            "สำหรับทารกที่มีน้ำหนักมากกว่า 1,500 กรัม",
                            "กำหนดให้ปริมาณสารละลายยา (ปริมาณยา + สารละลายเชื้อจางยา) = 8 ml.",
                            "(ความจุของ Extension Tube ประมาณ 5 ml. + Volume ที่ต้องบริหารเข้าผู้ป่วย 3 ml.)",
                            "<div style='text-align:center'>(3X + สารละลายเจือจางยา Up to 9 mL)</div>",
                            "การเตรียมยา:",
                            "1) คำนวณปริมาณยาที่ต้องการใช้เป็นมิลลิลิตร (ml.) แทนค่าในสูตร",
                            "2) ใช้ Syringe ขนาดที่เหมาะสม ดูดปริมาณยาที่ต้องการเตรียมไว้",
                            "3) ใช้ Syringe ขนาด 10 ml. หรือ 20 ml. ดูดปริมาณสารละลายเชื้อจางยาเตรียมไว้",
                            "4) ผสมยาใน Syringe ที่มีสารละลายเชื้อจางยาอยู่ Mixed ให้เข้ากัน",
                            "5) ต่อ Syringe กับ Extension Tube นำไปวางบน Syringe pump กด Start ตั้งอัตรา ~6 mL/hr.",
                            "6) Purge ยาให้ทั่วท่อโดยการดัน Syringe 3 ml. แล้วจึงบริหารผู้ป่วย",
                        ],
                    }
                elif multiplication == 6:
                    content_extra = {
                        "message": "การบริหารยาโดย Intermittent intravenous infusion",
                        "details": [
                            "สำหรับทารกที่มีน้ำหนักน้อยกว่า 1,500 กรัม",
                            "1) กำหนดให้สารละลายยาซึ่งบริหารเข้าสู้ผู้ป่วยปริมาณเท่ากับ = 1 mL",
                            "2) ให้ X คือ ปริมาณยาที่ต้องการเตรียม กำหนดสูตรในการเตรียมสารละลายยา ดังนี้:",
                            "<div style='text-align:center'>6X + สารละลายเจือจางยา Up to 6 mL</div>",
                            "3) จากข้อ 2 จะได้สารละลายทั้งหมด 6 ml. ซึ่งหมายถึง ความจุของ Extension Tube ประมาณ 5 ml. + Volume ที่ต้องการบริหารเข้าสู่ผู้ป่วย 1 ml.",
                            "4) บริหารโดยใช้ Syringe pump ตั้งอัตราเร็ว ~2 mL/hr",
                        ],
                    }

            # เผื่อกรณี POST แบบไม่ส่ง step (ฟอร์มเก่า)
            else:
                if 'dose' in request.form:
                    dose = float(request.form['dose'])
                    result_ml = round((dose * 10.0) / 1000.0, 2)
                if 'multiplication' in request.form:
                    multiplication = int(request.form['multiplication'])

        except (ValueError, TypeError) as e:
            error = f"กรุณากรอกข้อมูลให้ถูกต้อง: {e}"

    return render_template(
        'cefotaxime.html',
        dose=dose,
        result_ml=result_ml,
        multiplication=multiplication,
        content_extra=content_extra,
        error=error,
        UPDATE_DATE=UPDATE_DATE,
    )

@meds_bp.route('/ceftazidime', methods=['GET', 'POST'])
def ceftazidime_route():
    dose = None
    result_ml = None
    multiplication = None
    content_extra = None
    error = None

    if request.method == 'POST':
        try:
            # ใช้ชื่อ field ที่ template ส่งมา: step = 'dose' หรือ 'condition'
            step = (request.form.get('step') or '').strip().lower()

            # ---------- รอบที่ 1: คำนวณ mg → mL ----------
            if step == 'dose':
                raw = (request.form.get('dose') or '').strip()
                if not raw:
                    raise ValueError("กรุณากรอกขนาดยา (mg)")

                dose = float(raw)
                if dose < 0:
                    raise ValueError("ขนาดยาต้องมากกว่าหรือเท่ากับ 0")

                # stock 1000 mg/10 mL → mL = (mg × 10) / 1000
                result_ml = round((dose * 10.0) / 1000.0, 2)

            # ---------- รอบที่ 2: ใช้ผลคำนวณ + เงื่อนไข ----------
            elif step == 'condition':
                dose_raw = (request.form.get('dose') or '').strip()
                if not dose_raw:
                    raise ValueError("ไม่พบข้อมูล dose เดิม โปรดคำนวณรอบแรกก่อน")

                dose = float(dose_raw)

                result_raw = (request.form.get('result_ml') or '').strip()
                if result_raw:
                    result_ml = float(result_raw)
                else:
                    result_ml = round((dose * 10.0) / 1000.0, 2)

                mult_raw = (request.form.get('multiplication') or '').strip()
                if not mult_raw:
                    raise ValueError("กรุณาเลือกเงื่อนไขการคูณ")

                multiplication = int(mult_raw)

                # กล่องคำอธิบายเพิ่มเติม
                if multiplication == 3:
                    content_extra = {
                        "message": "การบริหารยาโดย Intermittent intravenous infusion pump",
                        "details": [
                            "สำหรับทารกที่มีน้ำหนักมากกว่า 1,500 กรัม",
                            "กำหนดให้ปริมาณสารละลายยา (ปริมาณยา + สารละลายเชื้อจางยา) = 8 ml.",
                            "(ความจุของ Extension Tube ประมาณ 5 ml. + Volume ที่ต้องบริหารเข้าผู้ป่วย 3 ml.)",
                            "<div style='text-align:center'>(3X + สารละลายเจือจางยา Up to 9 mL)</div>",
                            "การเตรียมยา:",
                            "1) คำนวณปริมาณยาที่ต้องการใช้เป็นมิลลิลิตร (ml.) แทนค่าในสูตร",
                            "2) ใช้ Syringe ขนาดที่เหมาะสม ดูดปริมาณยาที่ต้องการเตรียมไว้",
                            "3) ใช้ Syringe ขนาด 10 ml. หรือ 20 ml. ดูดปริมาณสารละลายเชื้อจางยาเตรียมไว้",
                            "4) ผสมยาใน Syringe ที่มีสารละลายเชื้อจางยาอยู่ Mixed ให้เข้ากัน",
                            "5) ต่อ Syringe กับ Extension Tube นำไปวางบน Syringe pump กด Start ตั้งอัตรา ~6 mL/hr.",
                            "6) Purge ยาให้ทั่วท่อโดยการดัน Syringe 3 ml. แล้วจึงบริหารผู้ป่วย",
                        ],
                    }
                elif multiplication == 6:
                    content_extra = {
                        "message": "การบริหารยาโดย Intermittent intravenous infusion",
                        "details": [
                            "สำหรับทารกที่มีน้ำหนักน้อยกว่า 1,500 กรัม",
                            "1) กำหนดให้สารละลายยาซึ่งบริหารเข้าสู้ผู้ป่วยปริมาณเท่ากับ = 1 mL",
                            "2) ให้ X คือ ปริมาณยาที่ต้องการเตรียม กำหนดสูตรในการเตรียมสารละลายยา ดังนี้:",
                            "<div style='text-align:center'>6X + สารละลายเจือจางยา Up to 6 mL</div>",
                            "3) จากข้อ 2 จะได้สารละลายทั้งหมด 6 ml. ซึ่งหมายถึง ความจุของ Extension Tube ประมาณ 5 ml. + Volume ที่ต้องการบริหารเข้าสู่ผู้ป่วย 1 ml.",
                            "4) บริหารโดยใช้ Syringe pump ตั้งอัตราเร็ว ~2 mL/hr",
                        ],
                    }

            # fallback เผื่อ form เก่า (ไม่ส่ง step)
            else:
                if 'dose' in request.form:
                    dose = float(request.form['dose'])
                    result_ml = round((dose * 10.0) / 1000.0, 2)
                if 'multiplication' in request.form:
                    multiplication = int(request.form['multiplication'])

        except (ValueError, TypeError) as e:
            error = f"กรุณากรอกข้อมูลให้ถูกต้อง: {e}"

    return render_template(
        'ceftazidime.html',
        dose=dose,
        result_ml=result_ml,
        multiplication=multiplication,
        content_extra=content_extra,
        error=error,
        UPDATE_DATE=UPDATE_DATE,   # ให้ key ตรงกับ {{ UPDATE_DATE }}
    )

@meds_bp.route('/ciprofloxacin', methods=['GET', 'POST'])
def ciprofloxacin_route():
    dose = None
    result_ml = None
    error = None

    if request.method == 'POST':
        try:
            raw = (request.form.get('dose') or '').strip()
            if not raw:
                raise ValueError("กรุณากรอกขนาดยา (mg)")

            dose = float(raw)
            if dose < 0:
                raise ValueError("ขนาดยาต้องมากกว่าหรือเท่ากับ 0")

            # ความแรง 2 mg/mL → mL = mg ÷ 2
            result_ml = round(dose / 2.0, 2)

        except (ValueError, TypeError) as e:
            error = f"กรุณากรอกข้อมูลให้ถูกต้อง: {e}"
            dose = None
            result_ml = None

    return render_template(
        'ciprofloxacin.html',
        dose=dose,
        result_ml=result_ml,
        error=error,
        UPDATE_DATE=UPDATE_DATE,   # ชื่อ key ตรงกับใน template
    )

@meds_bp.route('/clindamycin', methods=['GET', 'POST'])
def clindamycin_route():
    dose = result_ml_1 = result_ml_2 = None
    multiplication = final_result_1 = final_result_2 = None
    error = None

    if request.method == 'POST':
        action = (request.form.get('action') or '').strip().lower()

        try:
            if action == 'dose':
                # รอบที่ 1: คำนวณจาก dose
                dose = _as_float(request.form.get('dose'), 'dose')
                # 600 mg / 4 ml
                result_ml_1 = _round2(dose * 4.0 / 600.0)
                # เป้าหมาย 6 mg/ml
                result_ml_2 = _round2(dose / 6.0)

            elif action == 'condition':
                # รอบที่ 2: ใช้ค่าที่ได้จากรอบแรก + ตัวคูณ
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

    return render_template(
        'clindamycin.html',
        dose=dose,
        result_ml_1=result_ml_1,
        result_ml_2=result_ml_2,
        multiplication=multiplication,
        final_result_1=final_result_1,
        final_result_2=final_result_2,
        error=error,
        update_date=UPDATE_DATE,   # ตรงกับ {{ update_date }}
    )

@meds_bp.route('/cloxacillin', methods=['GET', 'POST'])
def cloxacillin_route():
    dose = None
    result_ml = None
    multiplication = None
    content_extra = None
    error = None

    if request.method == "POST":
        action = (request.form.get("action") or "").strip().lower()
        try:
            if action == "dose":
                # รอบที่ 1: คำนวณจากสต็อก 1000 mg / 5 mL
                dose = _as_float(request.form.get("dose"), "dose")
                # 1000 mg / 5 mL → 200 mg/mL
                result_ml = _ml_from_stock(dose, 1000, 5)

            elif action == "condition":
                # รอบที่ 2: ใช้ค่าจากรอบแรก + คูณ 3 หรือ 6 เท่า
                dose = _as_float(request.form.get("dose_hidden"), "dose_hidden")
                result_ml = _as_float(request.form.get("result_ml_hidden"), "result_ml_hidden")
                multiplication = _as_int(request.form.get("multiplication"), "multiplication")

                # กล่องคำอธิบาย (ข้อความวิธีเตรียม/ให้ยา)
                content_extra = _content_extra_by_mult(multiplication)

            else:
                error = "คำขอไม่ถูกต้อง"

        except ValueError as e:
            error = f"กรุณาใส่ข้อมูลที่ถูกต้อง: {e}"
        except Exception as e:
            error = f"เกิดข้อผิดพลาด: {e}"

    return render_template(
        "cloxacillin.html",
        dose=dose,
        result_ml=result_ml,
        multiplication=multiplication,
        content_extra=content_extra,
        error=error,
        update_date=UPDATE_DATE,
    )

@meds_bp.route('/colistin', methods=['GET', 'POST'])
def colistin_route():
    dose = None
    result_ml = None
    multiplication = None
    error = None
    content_extra = None

    if request.method == "POST":
        action = (request.form.get("action") or "dose").strip().lower()
        try:
            if action == "dose":
                # รอบที่ 1: 150 mg / 2 mL → ml = (mg × 2) / 150
                dose = _as_float(request.form.get("dose"), "dose")
                result_ml = _round2((dose * 2) / 150.0)

            elif action == "condition":
                # รอบที่ 2: ใช้ค่าเดิม + คูณ 3 หรือ 6 เท่า
                dose = _as_float(request.form.get("dose_hidden"), "dose_hidden")
                result_ml = _as_float(
                    request.form.get("result_ml_hidden"),
                    "result_ml_hidden",
                )
                multiplication = _as_int(
                    request.form.get("multiplication"),
                    "multiplication",
                )

                # เอาไว้สร้างกล่องคำอธิบายเพิ่มเติม
                content_extra = _content_extra_by_mult(multiplication)

            else:
                error = "คำสั่งไม่ถูกต้อง"

        except ValueError as e:
            error = f"กรุณาใส่ข้อมูลที่ถูกต้อง: {e}"
        except Exception as e:
            error = f"เกิดข้อผิดพลาด: {e}"

    return render_template(
        "colistin.html",
        dose=dose,
        result_ml=result_ml,
        multiplication=multiplication,
        content_extra=content_extra,
        error=error,
        update_date=UPDATE_DATE,
    )

@meds_bp.route('/dexamethasone', methods=['GET', 'POST'])
def dexamethasone_route():
    dose = None
    result_ml = None   # ที่จริงคือ "หน่วย u" = mg × 100
    error = None

    if request.method == 'POST':
        try:
            # ใช้ helper เดิมในโปรเจกต์
            dose = _as_float(request.form.get('dose'), 'dose')
            # 1 mg = 100 u (small dose: 0.2 ml drug + 0.8 ml D5W = 1 mg/1 ml = 100 u)
            result_ml = _round2(dose * 100.0)
        except Exception as e:
            error = f"กรุณากรอกขนาดยาที่ถูกต้อง: {e}"

    return render_template(
        'dexamethasone.html',
        dose=dose,
        result_ml=result_ml,
        error=error,
        update_date=UPDATE_DATE,
    )

@meds_bp.route('/dobutamine', methods=['GET', 'POST'])
def dobutamine_route():
    # รอบที่ 1
    desired_dosage = None      # mg
    original_volume = None     # ml (ปริมาตรรวมเป้าหมาย)
    dose_ml = None             # ml ยาที่ต้องใช้
    diluent_ml = None          # ml ตัวทำละลาย

    # รอบที่ 2
    multiplication = None
    dose_ml_mult = None
    totalVol_mult = None
    diluent_mult = None

    error = None

    if request.method == 'POST':
        try:
            action = (request.form.get('action') or 'dose').strip()

            if action == 'dose':
                # รอบแรก: คำนวณจาก stock 50 mg/ml
                desired_dosage = _as_float(request.form.get('desired_dosage'), 'desired_dosage')
                original_volume = _as_float(request.form.get('original_volume'), 'original_volume')

                dose_ml = _round2(desired_dosage / 50.0)             # 250 mg/5 ml → 50 mg/ml
                diluent_ml = _round2(original_volume - dose_ml)

            elif action == 'condition':
                # รอบสอง: ดึงค่ารอบแรกจาก hidden field
                desired_dosage = _as_float(request.form.get('desired_dosage_hidden'), 'desired_dosage_hidden')
                original_volume = _as_float(request.form.get('original_volume_hidden'), 'original_volume_hidden')
                dose_ml = _as_float(request.form.get('dose_ml_hidden'), 'dose_ml_hidden')

                multiplication = _as_float(request.form.get('multiplication'), 'multiplication')

                totalVol_mult = _round2(original_volume * multiplication)
                dose_ml_mult = _round2(dose_ml * multiplication)
                diluent_mult = _round2(totalVol_mult - dose_ml_mult)
            else:
                error = "คำสั่งไม่ถูกต้อง"

        except Exception as e:
            error = f"กรุณากรอกข้อมูลที่ถูกต้อง: {e}"

    return render_template(
        'dobutamine.html',
        desired_dosage=desired_dosage,
        original_volume=original_volume,
        dose_ml=dose_ml,
        diluent_ml=diluent_ml,
        multiplication=multiplication,
        dose_ml_mult=dose_ml_mult,
        totalVol_mult=totalVol_mult,
        diluent_mult=diluent_mult,
        error=error,
        update_date=UPDATE_DATE,
    )

@meds_bp.route('/dopamine', methods=['GET', 'POST'])
def dopamine_route():
    # รอบที่ 1
    desired_dosage = None    # mg
    original_volume = None   # ml (ปริมาตรรวมเป้าหมาย)
    dose_ml = None           # ml ยาที่ต้องใช้จาก stock
    diluent_ml = None        # ml ตัวทำละลาย

    # รอบที่ 2
    multiplication = None
    dose_ml_mult = None
    totalVol_mult = None
    diluent_mult = None

    error = None

    if request.method == 'POST':
        try:
            action = (request.form.get('action') or 'dose').strip()

            if action == 'dose':
                # stock Dopamine: 250 mg/10 ml = 25 mg/ml
                desired_dosage = _as_float(request.form.get('desired_dosage'), 'desired_dosage')
                original_volume = _as_float(request.form.get('original_volume'), 'original_volume')

                dose_ml = _round2(desired_dosage / 25.0)     # ml ยา
                diluent_ml = _round2(original_volume - dose_ml)

            elif action == 'condition':
                # รอบที่ 2: ใช้ค่าที่คำนวณจากรอบแรก + ตัวคูณ
                desired_dosage = _as_float(request.form.get('desired_dosage_hidden'), 'desired_dosage_hidden')
                original_volume = _as_float(request.form.get('original_volume_hidden'), 'original_volume_hidden')
                dose_ml = _as_float(request.form.get('dose_ml_hidden'), 'dose_ml_hidden')

                multiplication = _as_float(request.form.get('multiplication'), 'multiplication')

                totalVol_mult = _round2(original_volume * multiplication)
                dose_ml_mult = _round2(dose_ml * multiplication)
                diluent_mult = _round2(totalVol_mult - dose_ml_mult)
            else:
                error = "คำสั่งไม่ถูกต้อง"
        except Exception as e:
            error = f"กรุณากรอกข้อมูลที่ถูกต้อง: {e}"

    return render_template(
        'dopamine.html',
        desired_dosage=desired_dosage,
        original_volume=original_volume,
        dose_ml=dose_ml,
        diluent_ml=diluent_ml,
        multiplication=multiplication,
        dose_ml_mult=dose_ml_mult,
        totalVol_mult=totalVol_mult,
        diluent_mult=diluent_mult,
        error=error,
        update_date=UPDATE_DATE,
    )

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
    dose = result_ml = None
    error = None
    if request.method == 'POST':
        try:
            dose = _as_float(request.form.get('dose'), 'dose')
            # stock: 20 mg / 2 ml → 10 mg/ml  ⇒ ml = mg / 10
            result_ml = _round2(dose / 10.0)
        except Exception as e:
            error = f"กรุณากรอกขนาดยาที่ถูกต้อง: {e}"
            dose = None
            result_ml = None

    return render_template(
        'furosemide.html',
        dose=dose,
        result_ml=result_ml,
        error=error,
        update_date=UPDATE_DATE,
    )

@meds_bp.route('/gentamicin', methods=['GET', 'POST'])
def gentamicin_route():
    dose = result_ml = final_result = multiplication = None
    error = None
    content_extra = None
    formula_display = "ml = mg ÷ 40  (เพราะ 80 mg / 2 ml ⇒ 40 mg/ml)"

    if request.method == 'POST':
        try:
            action = (request.form.get('action') or '').strip()

            # รอบที่ 1: คำนวณ mg → ml
            if action in ('dose', ''):
                dose = _as_float(request.form.get('dose'), "ขนาดยา (mg)")
                if dose <= 0:
                    raise ValueError("ขนาดยาต้องมากกว่า 0")
                result_ml = _round2(dose / 40.0)

            # รอบที่ 2: เลือกเงื่อนไขตัวคูณ 3× หรือ 6×
            elif action == 'condition':
                dose = _as_float(
                    request.form.get('dose_hidden') or request.form.get('dose'),
                    "ขนาดยา (mg)",
                )
                if dose <= 0:
                    raise ValueError("ขนาดยาต้องมากกว่า 0")

                # ถ้ามี result_ml_hidden ก็ใช้เลย ไม่งั้นคำนวณใหม่
                result_ml_hidden = request.form.get('result_ml_hidden')
                if result_ml_hidden not in (None, ""):
                    result_ml = float(result_ml_hidden)
                else:
                    result_ml = _round2(dose / 40.0)

                multiplication = _as_int(
                    request.form.get('multiplication'),
                    "เงื่อนไขตัวคูณ (3×/6×)",
                )
                if multiplication not in (3, 6):
                    raise ValueError("เงื่อนไขตัวคูณต้องเป็น 3 หรือ 6")

                final_result = _round2(float(result_ml) * multiplication)
                content_extra = _content_extra_by_mult(multiplication)

            else:
                error = "รูปแบบคำขอไม่ถูกต้อง (action ไม่รองรับ)"

        except Exception as e:
            error = f"กรุณาใส่ข้อมูลที่ถูกต้อง: {e}"

    return render_template(
        'gentamicin.html',
        dose=dose,
        result_ml=result_ml,
        final_result=final_result,
        multiplication=multiplication,
        content_extra=content_extra,
        formula_display=formula_display,
        error=error,
        update_date=UPDATE_DATE,
    )

@meds_bp.route('/hydrocortisone', methods=['GET', 'POST'])
def hydrocortisone_route():
    dose = result_ml = units = None
    error = None

    MG_PER_ML = 50.0   # 100 mg / 2 ml → 50 mg/ml
    U_PER_MG = 4.0     # 25 mg = 100 u → 1 mg = 4 u

    if request.method == 'POST':
        try:
            dose = _as_float(request.form.get('dose'), 'dose')
            if dose <= 0:
                raise ValueError("ขนาดยาต้องมากกว่า 0")

            # คำนวณไว้ให้ template ใช้ (แต่ template ก็มี fallback เผื่อ None)
            result_ml = _round2(dose / MG_PER_ML)
            units = _round2(dose * U_PER_MG)

        except Exception as e:
            error = f"กรุณากรอกตัวเลขที่ถูกต้อง: {e}"
            dose = result_ml = units = None

    return render_template(
        'hydrocortisone.html',
        dose=dose,
        result_ml=result_ml,
        units=units,
        error=error,
        update_date=UPDATE_DATE,
    )

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


# routes/routes_medications.py

@meds_bp.route("/time_management")
def time_management_route():
    return render_template("time_management.html", update_date=UPDATE_DATE)


@meds_bp.route("/run_time")
def run_time():
    return render_template("run_time.html", update_date=UPDATE_DATE)


@meds_bp.route("/run_time_stop")
def run_time_stop():
    return render_template("run_time_stop.html", update_date=UPDATE_DATE)

# ฟังก์ชันช่วยคำนวณ PMA (ใช้ต่อ)
def _pma_helper(gestational_age_weeks, gestational_age_days, postnatal_age_days):
    total_days = (gestational_age_weeks * 7) + gestational_age_days + postnatal_age_days
    pma_weeks = total_days // 7
    pma_days = total_days % 7
    calc = pma_weeks + round(pma_days / 7, 0)
    return pma_weeks, pma_days, calc


@meds_bp.route("/calculate_pma", methods=["GET", "POST"])
def calculate_pma_route():
    # ค่าตั้งต้น (ให้ template ใช้เติมช่อง input กลับ)
    ga_w_val = ga_d_val = pna_d_val = None
    bw_val = None
    pma_weeks = pma_days = calc_unit = None
    postnatal_days = None
    error = None

    if request.method == "POST":
        try:
            ga_w_val = int(request.form.get("gestational_age_weeks", "0"))
            ga_d_val = int(request.form.get("gestational_age_days", "0"))
            pna_d_val = int(request.form.get("postnatal_age_days", "0"))
            bw_val = float(request.form.get("bw", "0"))

            # ใช้ helper คำนวณ PMA
            pma_weeks, pma_days, calc_unit = _pma_helper(
                ga_w_val, ga_d_val, pna_d_val
            )
            postnatal_days = pna_d_val
        except (TypeError, ValueError):
            error = "Invalid input, please check your values."

    return render_template(
        "pma_template.html",
        ga_w_val=ga_w_val,
        ga_d_val=ga_d_val,
        pna_d_val=pna_d_val,
        bw=bw_val,
        pma_weeks=pma_weeks,
        pma_days=pma_days,
        calc_unit=calc_unit,        # ใช้ชื่อ calc_unit ใน template
        postnatal_days=postnatal_days,
        error=error,
        update_date=UPDATE_DATE,
    )


    # ====== ส่วนล่างสุดของ routes/routes_medications.py ======

from flask import request, render_template, current_app

@meds_bp.route("/drug_calculation", methods=["GET", "POST"])
def drug_calculation():
    # ใช้ values เพื่อรองรับทั้ง GET และ POST
    src = request.values

    pma_weeks = src.get("pma_weeks", type=int)
    pma_days = src.get("pma_days", type=int)
    calc = src.get("calc", type=float)
    bw = src.get("bw", type=float)
    postnatal_days = src.get("postnatal_days", type=int)

    # ถ้าขาดตัวใดตัวหนึ่งให้ error
    if None in (pma_weeks, pma_days, calc, bw, postnatal_days):
        return "Invalid data received", 400

    bw_round = round(bw, 2)
    # ตัวอย่างสูตรรวม (ใช้ calc เป็นสัปดาห์ × BW)
    dose = calc * bw_round

    return render_template(
        "drug_calculation.html",
        pma_weeks=pma_weeks,
        pma_days=pma_days,
        calc=calc,
        bw=bw_round,
        postnatal_days=postnatal_days,
        dose=dose,
        update_date=current_app.config["UPDATE_DATE"],
    )


@meds_bp.route("/acyclovir_dose")
def acyclovir_dose():
    # รับค่าจาก query string
    pma_weeks = request.args.get("pma_weeks", type=int)
    pma_days = request.args.get("pma_days", type=int)
    calc = request.args.get("calc", type=float)
    postnatal_days = request.args.get("postnatal_days", type=int)
    bw = request.args.get("bw", type=float)

    if None in (pma_weeks, pma_days, calc, postnatal_days, bw):
        return "Invalid data received - missing parameters", 400

    # 20 mg/kg/dose → แปลงเป็น mg/dose ตาม BW
    dose_mg = round(bw * 20, 2)

    # ตัวอย่างเงื่อนไข interval ตาม PMA
    if pma_weeks < 30:
        interval = "every 12 hours"
    else:
        interval = "every 8 hours"

    return render_template(
        "acyclovir_dose.html",
        pma_weeks=pma_weeks,
        pma_days=pma_days,
        calc=calc,
        postnatal_days=postnatal_days,
        bw=bw,
        min_dose=dose_mg,          # mg/dose
        interval=interval,
        update_date=current_app.config["UPDATE_DATE"],
    )


@meds_bp.route("/amikin_dose")
def amikin_dose():
    # รับค่าจาก query parameters
    pma_weeks = request.args.get("pma_weeks")
    pma_days = request.args.get("pma_days")
    calc = request.args.get("calc")
    postnatal_days = request.args.get("postnatal_days")
    bw = request.args.get("bw")

    # ตรวจสอบว่ามีพารามิเตอร์มาครบไหม
    if not all([pma_weeks, pma_days, calc, postnatal_days, bw]):
        return "Invalid data received - missing parameters", 400

    # แปลงเป็นตัวเลข
    try:
        pma_weeks = int(pma_weeks)
        pma_days = int(pma_days)
        calc = float(calc)
        postnatal_days = int(postnatal_days)
        bw = float(bw)
    except (ValueError, TypeError):
        return "Invalid input parameters", 400

    # ===== Logic คำนวณ dose ตามน้ำหนัก + postnatal age (เหมือนที่คุณเขียน) =====
    if postnatal_days < 14:
        if bw <= 0.8:
            dose_per_kg = 16
        elif 0.8 < bw <= 1.2:
            dose_per_kg = 16
        elif 1.2 < bw <= 2.0:
            dose_per_kg = 15
        elif 2.0 < bw <= 2.8:
            dose_per_kg = 15
        else:
            dose_per_kg = 15
    else:  # postnatal_days >= 14
        if bw <= 0.8:
            dose_per_kg = 20
        elif 0.8 < bw <= 1.2:
            dose_per_kg = 20
        elif 1.2 < bw <= 2.0:
            dose_per_kg = 18
        elif 2.0 < bw <= 2.8:
            dose_per_kg = 18
        else:
            dose_per_kg = 18

    # คำนวณปริมาณยา (mg/dose)
    calculated_dose = round(dose_per_kg * bw, 2)

    return render_template(
        "amikin_dose.html",
        pma_weeks=pma_weeks,
        pma_days=pma_days,
        calc=calc,
        postnatal_days=postnatal_days,
        bw=bw,
        dose_per_kg=dose_per_kg,          # ส่งไปให้ template ใช้แสดงสูตร
        calculated_dose=calculated_dose,  # mg/dose
        update_date=current_app.config.get("UPDATE_DATE"),
    )

@meds_bp.route('/aminophylline_dose')
def aminophylline_dose():
    # รับค่าจาก query parameters
    pma_weeks = request.args.get('pma_weeks')
    pma_days = request.args.get('pma_days')
    calc = request.args.get('calc')
    postnatal_days = request.args.get('postnatal_days')
    bw = request.args.get('bw')

    # ตรวจสอบค่าที่ได้รับ
    if not all([pma_weeks, pma_days, calc, postnatal_days, bw]):
        return "Invalid data received - missing parameters", 400

    try:
        pma_weeks = int(pma_weeks)
        pma_days = int(pma_days)
        calc = float(calc)
        postnatal_days = int(postnatal_days)
        bw = float(bw)
    except ValueError:
        return "Invalid data received - value error", 400

    # คำนวณ Loading dose และ Maintenance dose
    loading_dose = round(bw * 8, 2)
    maintenance_dose_min = round(bw * 1.5, 2)
    maintenance_dose_max = round(bw * 3, 2)

    # ส่งค่าไปที่ template
    return render_template(
        'aminophylline_dose.html',
        pma_weeks=pma_weeks,
        pma_days=pma_days,
        calc=calc,
        postnatal_days=postnatal_days,
        bw=bw,
        loading_dose=loading_dose,
        maintenance_dose_min=maintenance_dose_min,
        maintenance_dose_max=maintenance_dose_max,
        update_date=UPDATE_DATE,
    )

@meds_bp.route('/amoxicillin_clavimoxy_dose')
def amoxicillin_clavimoxy_dose():
    pma_weeks = request.args.get('pma_weeks')
    pma_days = request.args.get('pma_days')
    calc = request.args.get('calc')
    postnatal_days = request.args.get('postnatal_days')
    bw = request.args.get('bw')

    if not all([pma_weeks, pma_days, calc, postnatal_days, bw]):
        return "Invalid data received - missing parameters", 400

    try:
        pma_weeks = int(pma_weeks)
        pma_days = int(pma_days)
        calc = float(calc)
        postnatal_days = int(postnatal_days)
        bw = float(bw)
    except ValueError:
        return "Invalid data received - value error", 400

    min_dose = None
    interval = None
    scenario = None
    explanation = ""

    # 1) Anthrax GA 32–37 wk
    if 32 <= pma_weeks < 37:
        if postnatal_days < 7:
            min_dose = 25
            interval = "every 12 hours"
            scenario = "anthrax_32_37_wk_0_1"
            explanation = ("Anthrax prophylaxis/treatment for GA 32–37 wk, age 0–1 wk: "
                           "50 mg/kg/day divided q12h ⇒ 25 mg/kg/dose.")
        else:
            min_dose = 25
            interval = "every 8 hours"
            scenario = "anthrax_32_37_wk_1_4"
            explanation = ("Anthrax prophylaxis/treatment for GA 32–37 wk, age ≥1–4 wk: "
                           "75 mg/kg/day divided q8h ⇒ 25 mg/kg/dose.")

    # 2) Term ≥ 37 wk, 0–4 wk
    elif pma_weeks >= 37 and postnatal_days <= 28:
        min_dose = 25
        interval = "every 8 hours"
        scenario = "anthrax_term_0_4"
        explanation = ("Anthrax prophylaxis/treatment for term newborn (GA ≥ 37 wk, 0–4 wk): "
                       "75 mg/kg/day divided q8h ⇒ 25 mg/kg/dose.")

    # 3) UTI prophylaxis (ตัวอย่าง)
    elif 0 <= postnatal_days < 60:
        min_dose = 10
        interval = "once daily"
        scenario = "uti_prophylaxis"
        explanation = ("UTI prophylaxis: 10–15 mg/kg/day orally once daily "
                       "(ใช้ค่าต่ำสุด 10 mg/kg/dose).")

    # 4) Usual dose default
    else:
        min_dose = 15
        interval = "every 12 hours"
        scenario = "usual_dose"
        explanation = ("Usual dose (manufacturer): max 30 mg/kg/day orally, divided q12h ⇒ "
                       "ประมาณ 15 mg/kg/dose.")

    actual_dose = round(min_dose * bw, 2)

    return render_template(
        'amoxicillin_clavimoxy_dose.html',
        pma_weeks=pma_weeks,
        pma_days=pma_days,
        calc=calc,
        postnatal_days=postnatal_days,
        bw=bw,
        min_dose=min_dose,
        interval=interval,
        actual_dose=actual_dose,
        scenario=scenario,
        explanation=explanation,
        update_date=UPDATE_DATE,
    )

@meds_bp.route('/amphotericinB_dose')
def amphotericinB_dose():
    # รับค่าจาก query parameters
    pma_weeks = request.args.get('pma_weeks')
    pma_days = request.args.get('pma_days')
    calc = request.args.get('calc')
    postnatal_days = request.args.get('postnatal_days')
    bw = request.args.get('bw')

    # ตรวจสอบว่าข้อมูลครบไหม
    if not all([pma_weeks, pma_days, calc, postnatal_days, bw]):
        return "Invalid data received - missing parameters", 400

    # แปลงชนิดข้อมูล
    try:
        pma_weeks = int(pma_weeks)
        pma_days = int(pma_days)
        calc = float(calc)
        postnatal_days = int(postnatal_days)
        bw = float(bw)
    except ValueError:
        return "Invalid data received - value error", 400

    # คำนวณ maintenance dose (mg/dose) ตามช่วง 1–1.5 mg/kg
    maintenance_dose_min = round(bw * 1.0, 2)  # 1 mg/kg
    maintenance_dose_max = round(bw * 1.5, 2)  # 1.5 mg/kg

    # ส่งค่าไปยัง template
    return render_template(
        'amphotericinB_dose.html',
        pma_weeks=pma_weeks,
        pma_days=pma_days,
        calc=calc,
        postnatal_days=postnatal_days,
        bw=bw,
        maintenance_dose_min=maintenance_dose_min,
        maintenance_dose_max=maintenance_dose_max,
        update_date=UPDATE_DATE,
    )

@meds_bp.route('/ampicillin_dose')
def ampicillin_dose():
    # รับค่าจาก query parameters
    pma_weeks = request.args.get('pma_weeks')
    pma_days = request.args.get('pma_days')
    calc = request.args.get('calc')
    postnatal_days = request.args.get('postnatal_days')
    bw = request.args.get('bw')

    # ตรวจสอบค่าที่ได้รับ
    if not all([pma_weeks, pma_days, calc, postnatal_days, bw]):
        return "Invalid data received - missing parameters", 400

    try:
        pma_weeks = int(pma_weeks)
        pma_days = int(pma_days)
        calc = float(calc)
        postnatal_days = int(postnatal_days)
        bw = float(bw)
    except ValueError:
        return "Invalid data received - value error", 400

    # คำนวณ dose ตัวอย่าง (100 mg/kg/dose)
    avg_dose_per_kg = 100
    calculated_dose = math.ceil(avg_dose_per_kg * bw)

    # หาว่า row ไหนควร highlight ในตาราง
    active_row = None
    if pma_weeks <= 29 and postnatal_days <= 28:
        active_row = '29_0_28'
    elif pma_weeks <= 29 and postnatal_days > 28:
        active_row = '29_29plus'
    elif 30 <= pma_weeks <= 36 and postnatal_days <= 14:
        active_row = '30_36_0_14'
    elif 30 <= pma_weeks <= 36 and postnatal_days > 14:
        active_row = '30_36_15plus'
    elif 37 <= pma_weeks <= 44 and postnatal_days <= 7:
        active_row = '37_44_0_7'
    elif 37 <= pma_weeks <= 44 and postnatal_days > 7:
        active_row = '37_44_8plus'
    elif pma_weeks > 44:
        active_row = '45plus_all'

    # ส่งค่าไปที่ template
    return render_template(
        'ampicillin_dose.html',
        pma_weeks=pma_weeks,
        pma_days=pma_days,
        calc=calc,
        postnatal_days=postnatal_days,
        bw=bw,
        calculated_dose=calculated_dose,
        active_row=active_row,
        update_date=UPDATE_DATE
    )


@meds_bp.route('/cefazolin_dose')
def cefazolin_dose():
    # ----- 1) รับค่าจาก query parameters -----
    pma_weeks = request.args.get('pma_weeks')
    pma_days = request.args.get('pma_days')
    calc = request.args.get('calc')
    postnatal_days = request.args.get('postnatal_days')
    bw = request.args.get('bw')

    # Debug log (จะเห็นใน console เวลาเรียกหน้าเพจ)
    print(f"[cefazolin_dose] raw params: "
          f"pma_weeks={pma_weeks}, pma_days={pma_days}, "
          f"calc={calc}, postnatal_days={postnatal_days}, bw={bw}")

    # ----- 2) ตรวจสอบว่ามีข้อมูลครบไหม -----
    if not all([pma_weeks, pma_days, calc, postnatal_days, bw]):
        return "Invalid data received - missing parameters", 400

    try:
        # แปลงค่าให้เป็นตัวเลข
        pma_weeks = int(pma_weeks)
        pma_days = int(pma_days)
        calc = float(calc)
        postnatal_days = int(postnatal_days)
        bw = float(bw)   # น้ำหนักเป็นทศนิยมได้
    except ValueError:
        return "Invalid input: Parameters must be numeric.", 400

    # ----- 3) กำหนด interval จาก PMA + Postnatal age ตามตาราง -----
    # ตารางในหน้า HTML:
    # <29 wk:  0–28 d -> q12h,  >28 d -> q8h
    # 30–36 wk: 0–14 d -> q12h, >14 d -> q8h
    # 37–44 wk: 0–7 d  -> q12h, >7 d  -> q8h
    # >45 wk: ALL -> q6h

    pw = pma_weeks
    pna = postnatal_days

    # NOTE: ใส่ 29 wk ไว้กลุ่มแรกเหมือน pattern ยาอื่น ๆ (≤29)
    if pw <= 29:
        if pna <= 28:
            interval_hours = 12
        else:
            interval_hours = 8
    elif 30 <= pw <= 36:
        if pna <= 14:
            interval_hours = 12
        else:
            interval_hours = 8
    elif 37 <= pw <= 44:
        if pna <= 7:
            interval_hours = 12
        else:
            interval_hours = 8
    else:  # pw > 44
        interval_hours = 6

    # แปลงเป็นข้อความสำหรับแสดงผล
    interval = f"every {interval_hours} hours"

    # ----- 4) คำนวณ dose -----
    # จาก text: 25 mg/kg/dose IV หรือ IM
    dose_per_kg = 25  # mg/kg/dose

    # จำนวนครั้งต่อวัน = 24 / interval_hours
    doses_per_day = 24 / interval_hours
    mg_per_kg_per_day = dose_per_kg * doses_per_day  # mg/kg/day

    # กำหนดช่วง min–max mg/kg/day (เช่น 50–100 mg/kg/day ตาม range ปกติใน neonate)
    # ที่ง่ายสุด: ใช้ min = 50 mg/kg/day, max = 100 mg/kg/day สำหรับ neonate
    min_mg_per_kg_per_day = 50
    max_mg_per_kg_per_day = 100

    # คูณน้ำหนักให้เป็น mg/day
    min_dose = round(min_mg_per_kg_per_day * bw, 2)
    max_dose = round(max_mg_per_kg_per_day * bw, 2)

    print(f"[cefazolin_dose] bw={bw} kg -> min_dose={min_dose} mg/day, "
          f"max_dose={max_dose} mg/day, interval={interval}")

    # ----- 5) ส่งค่าไปที่ Template -----
    return render_template(
        'cefazolin_dose.html',
        pma_weeks=pma_weeks,
        pma_days=pma_days,
        calc=calc,
        postnatal_days=postnatal_days,
        bw=bw,
        # สำหรับ block "Calculated Dosage"
        min_dose=min_dose,
        max_dose=max_dose,
        interval=interval,
        # ถ้าอยากใช้ใน text เพิ่มเติม ก็ส่ง dose_per_kg ด้วยได้
        dose_per_kg=dose_per_kg,
        update_date=UPDATE_DATE
    )

@meds_bp.route('/cefotaxime_dose')
def cefotaxime_dose():
    # รับค่าจาก query parameters
    pma_weeks = request.args.get('pma_weeks')
    pma_days = request.args.get('pma_days')
    calc = request.args.get('calc')
    postnatal_days = request.args.get('postnatal_days')
    bw = request.args.get('bw')

    # กันกรณี missing parameter
    if not all([pma_weeks, pma_days, calc, postnatal_days, bw]):
        return "Invalid input parameters - missing data", 400

    try:
        pma_weeks = int(pma_weeks)
        pma_days = int(pma_days)
        calc = float(calc)
        postnatal_days = int(postnatal_days)
        bw = float(bw)
    except (ValueError, TypeError):
        return "Invalid input parameters - must be numeric", 400

    # ตัวอย่าง logic: ตอนนี้ทุกช่วงใช้ 50 mg/kg นอกจาก PNA > 28 ใช้ 100 mg/kg
    if postnatal_days <= 28:
        dose_per_kg = 50.0
    else:
        dose_per_kg = 100.0

    # คำนวณปริมาณยา (mg/dose)
    calculated_dose = round(dose_per_kg * bw)

    # ส่งค่ากลับไปที่ HTML template
    return render_template(
        'cefotaxime_dose.html',
        pma_weeks=pma_weeks,
        pma_days=pma_days,
        calc=calc,
        postnatal_days=postnatal_days,
        bw=bw,
        calculated_dose=calculated_dose,
        update_date=UPDATE_DATE
    )

@meds_bp.route('/cloxacillin_dose')
def cloxacillin_dose():
    # รับค่าจาก query parameters
    pma_weeks = request.args.get('pma_weeks')
    pma_days = request.args.get('pma_days')
    calc = request.args.get('calc')
    postnatal_days = request.args.get('postnatal_days')
    bw = request.args.get('bw')

    # ตรวจสอบว่ามีค่าครบไหม
    if not all([pma_weeks, pma_days, calc, postnatal_days, bw]):
        return "Invalid data received - missing parameters", 400

    # แปลงเป็นตัวเลข
    try:
        pma_weeks = int(pma_weeks)
        pma_days = int(pma_days)
        calc = float(calc)
        postnatal_days = int(postnatal_days)
        bw = float(bw)
    except ValueError:
        return "Invalid data received - value error", 400

    # ---- เลือกแถวในตารางสำหรับ highlight ----
    active_row = None
    if pma_weeks <= 29 and postnatal_days <= 28:
        active_row = '29_0_28'
    elif 30 <= pma_weeks <= 36 and postnatal_days <= 14:
        active_row = '30_36_0_14'
    elif 30 <= pma_weeks <= 36 and postnatal_days > 14:
        active_row = '30_36_15plus'
    elif 37 <= pma_weeks <= 44 and postnatal_days <= 7:
        active_row = '37_44_0_7'
    elif 37 <= pma_weeks <= 44 and postnatal_days > 7:
        active_row = '37_44_8plus'
    elif pma_weeks >= 45:
        active_row = '45plus_all'

    # ---- คำนวณ dose (mg/dose) ----
    # protocol ตอนนี้ใช้ 40 mg/kg/dose ทุกกลุ่ม
    recommended_dose_per_kg = 40.0
    calculated_dose = round(recommended_dose_per_kg * bw)

    print(f"[cloxacillin] PMA={pma_weeks}+{pma_days} PNA={postnatal_days} BW={bw} "
          f"-> {calculated_dose} mg, row={active_row}")

    return render_template(
        'cloxacillin_dose.html',
        pma_weeks=pma_weeks,
        pma_days=pma_days,
        calc=calc,
        postnatal_days=postnatal_days,
        bw=bw,
        calculated_dose=calculated_dose,
        active_row=active_row,
        update_date=UPDATE_DATE
    )

@meds_bp.route('/colistin_dose')
def colistin_dose():
    # รับค่าจาก query parameters
    pma_weeks = request.args.get('pma_weeks')
    pma_days = request.args.get('pma_days')
    calc = request.args.get('calc')
    postnatal_days = request.args.get('postnatal_days')
    bw = request.args.get('bw')

    # debug ดูค่าที่ได้รับ
    print(
        f"[colistin] raw params: pma_weeks={pma_weeks}, "
        f"pma_days={pma_days}, calc={calc}, "
        f"postnatal_days={postnatal_days}, bw={bw}"
    )

    # ตรวจสอบว่าครบทุกค่าไหม
    if not all([pma_weeks, pma_days, calc, postnatal_days, bw]):
        return "Invalid data received - missing parameters", 400

    try:
        # แปลงเป็นตัวเลข
        pma_weeks = int(pma_weeks)
        pma_days = int(pma_days)
        calc = float(calc)
        postnatal_days = int(postnatal_days)
        bw = float(bw)
    except ValueError:
        return "Invalid input: Parameters must be numeric.", 400

    # กำหนดค่า dose และ interval ตาม PNA + PMA
    min_dose_per_kg = None
    max_dose_per_kg = None
    interval = None

    if postnatal_days < 7:
        min_dose_per_kg = 2.5
        max_dose_per_kg = 5.0
        interval = "q 12 hr(s)"
    elif postnatal_days >= 7 and pma_weeks < 32:
        min_dose_per_kg = 2.5
        max_dose_per_kg = 5.0
        interval = "q 8 hr(s)"
    elif postnatal_days >= 7 and pma_weeks >= 32:
        min_dose_per_kg = 2.5
        max_dose_per_kg = 5.0
        interval = "q 6 hr(s)"

    if min_dose_per_kg is None or max_dose_per_kg is None or interval is None:
        return "No suitable dose found for the given PMA and postnatal age.", 400

    # คำนวณช่วงปริมาณยา (mg/day)
    calculated_min_dose = round(min_dose_per_kg * bw, 2)
    calculated_max_dose = round(max_dose_per_kg * bw, 2)

    print(
        f"[colistin] PMA={pma_weeks}+{pma_days}, PNA={postnatal_days}, BW={bw} "
        f"-> {calculated_min_dose}-{calculated_max_dose} mg/day, interval={interval}"
    )

    return render_template(
        'colistin_dose.html',
        pma_weeks=pma_weeks,
        pma_days=pma_days,
        calc=calc,
        postnatal_days=postnatal_days,
        bw=bw,
        min_dose=calculated_min_dose,
        max_dose=calculated_max_dose,
        interval=interval,
        update_date=UPDATE_DATE,
    )


# Route สำหรับการคำนวณปริมาณยา Gentamicin
@meds_bp.route('/gentamicin_dose')
def gentamicin_dose():
    # รับค่าจาก query parameters
    pma_weeks      = request.args.get('pma_weeks')
    pma_days       = request.args.get('pma_days')
    calc           = request.args.get('calc')
    postnatal_days = request.args.get('postnatal_days')
    bw             = request.args.get('bw')

    # ตรวจสอบพารามิเตอร์ว่าครบไหม
    if not all([pma_weeks, pma_days, calc, postnatal_days, bw]):
        return "Invalid data received - missing parameters", 400

    try:
        pma_weeks      = int(pma_weeks)
        pma_days       = int(pma_days)
        calc           = float(calc)
        postnatal_days = int(postnatal_days)
        bw             = float(bw)
    except ValueError:
        return "Invalid data received - value error", 400

    # กำหนด dose per kg ตามช่วงอายุ (ให้ตรงกับตารางด้านบน)
    if pma_weeks <= 29 and postnatal_days <= 7:
        dose_per_kg = 5.0          # q 48h
    elif pma_weeks <= 29 and 8 <= postnatal_days <= 28:
        dose_per_kg = 4.0          # q 36h
    elif pma_weeks <= 29 and postnatal_days > 28:
        dose_per_kg = 4.0          # q 24h
    elif 30 <= pma_weeks <= 34 and postnatal_days <= 7:
        dose_per_kg = 4.5          # q 36h
    elif 30 <= pma_weeks <= 34 and postnatal_days > 7:
        dose_per_kg = 4.0          # q 24h
    elif pma_weeks >= 35:
        dose_per_kg = 4.0          # q 24h
    else:
        return "No suitable dose found", 400

    # คำนวณปริมาณยา แล้ว “ตัดเศษลง”
    raw_dose        = dose_per_kg * bw
    calculated_dose = math.floor(raw_dose)

    # ส่งไปแสดงผล
    return render_template(
        'gentamicin_dose.html',
        pma_weeks=pma_weeks,
        pma_days=pma_days,
        calc=calc,
        postnatal_days=postnatal_days,
        bw=bw,
        calculated_dose=calculated_dose,
        update_date=UPDATE_DATE,
    )

@meds_bp.route('/meropenem_dose')
def meropenem_dose():
    """
    รับค่า PMA (pma_weeks, pma_days), postnatal age (postnatal_days),
    น้ำหนักตัว (bw) และ calc จาก query parameters
    จากนั้นคำนวณขนาดยาสำหรับ intra-abdominal and non-CNS infections
    และส่งค่าไปยัง template พร้อม scenario เพื่อ highlight บรรทัดที่ตรงช่วง GA/PNA
    """

    # 1) รับค่าจาก query parameters
    pma_weeks      = request.args.get('pma_weeks')
    pma_days       = request.args.get('pma_days')
    calc           = request.args.get('calc')
    postnatal_days = request.args.get('postnatal_days')
    bw             = request.args.get('bw')

    # 2) ตรวจสอบว่ามีข้อมูลครบถ้วนหรือไม่
    if not all([pma_weeks, pma_days, calc, postnatal_days, bw]):
        return "Invalid data received - missing parameters", 400

    # 3) แปลงประเภทข้อมูล
    try:
        pma_weeks      = int(pma_weeks)
        pma_days       = int(pma_days)
        calc           = float(calc)
        postnatal_days = int(postnatal_days)
        bw             = float(bw)
    except ValueError:
        return "Invalid input: Parameters must be numeric.", 400

    # 4) เลือก scenario + dose ตาม Intra-abdominal and non-CNS infections
    scenario    = None   # ใช้ไป highlight ใน template
    dose_per_kg = None   # mg/kg/dose
    interval    = None   # text เช่น "every 8 hours"

    # - Less than 32 weeks GA and less than 14 days PNA => 20 mg/kg q12h
    if pma_weeks < 32 and postnatal_days < 14:
        scenario    = 'intra1'
        dose_per_kg = 20
        interval    = "every 12 hours"

    # - Less than 32 weeks GA and 14 days PNA and older => 20 mg/kg q8h
    elif pma_weeks < 32 and postnatal_days >= 14:
        scenario    = 'intra2'
        dose_per_kg = 20
        interval    = "every 8 hours"

    # - 32 weeks GA and older, and less than 14 days PNA => 20 mg/kg q8h
    elif pma_weeks >= 32 and postnatal_days < 14:
        scenario    = 'intra3'
        dose_per_kg = 20
        interval    = "every 8 hours"

    # - 32 weeks GA and older, and 14 days PNA and older => 30 mg/kg q8h
    elif pma_weeks >= 32 and postnatal_days >= 14:
        scenario    = 'intra4'
        dose_per_kg = 30
        interval    = "every 8 hours"

    # ถ้าไม่เข้าเคสใดเลย
    if scenario is None or dose_per_kg is None or interval is None:
        return (
            "No suitable dose found for the given PMA and postnatal age "
            "(Intra-abdominal scenario).",
            400,
        )

    # 5) คำนวณขนาดยาเป็น mg/dose ตามน้ำหนักจริง
    total_dose = round(dose_per_kg * bw, 2)   # mg/dose

    # 6) ส่งค่าไปที่ template
    return render_template(
        'meropenem_dose.html',
        pma_weeks=pma_weeks,
        pma_days=pma_days,
        calc=calc,
        postnatal_days=postnatal_days,
        bw=bw,
        dose_per_kg=dose_per_kg,   # mg/kg/dose guideline
        total_dose=total_dose,     # mg/dose สำหรับเด็กคนนี้
        interval=interval,
        scenario=scenario,
        update_date=UPDATE_DATE,
    )

@meds_bp.route('/vancomycin_dose')
def vancomycin_dose():
    # Retrieve values from query parameters
    pma_weeks      = request.args.get('pma_weeks')
    pma_days       = request.args.get('pma_days')
    calc           = request.args.get('calc')
    postnatal_days = request.args.get('postnatal_days')
    bw             = request.args.get('bw')

    # Debug
    print(
        f"pma_weeks={pma_weeks}, pma_days={pma_days}, "
        f"calc={calc}, postnatal_days={postnatal_days}, bw={bw}"
    )

    # Check if all necessary parameters are present
    if not all([pma_weeks, pma_days, calc, postnatal_days, bw]):
        print("Missing parameters, returning 400")
        return "Invalid data received - missing parameters", 400

    # Convert to appropriate data types
    try:
        pma_weeks      = int(pma_weeks)
        pma_days       = int(pma_days)
        calc           = float(calc)
        postnatal_days = int(postnatal_days)
        bw             = float(bw)
    except ValueError:
        print("Value error occurred, returning 400")
        return "Invalid data received - value error", 400

    # ---- Dose per kg (guideline 10–15 mg/kg/dose) ----
    dose_min_per_kg = 10.0
    dose_max_per_kg = 15.0

    # คำนวณเป็น mg/dose จริงจากน้ำหนัก
    dose_min_mg = math.floor(bw * dose_min_per_kg)
    dose_max_mg = math.floor(bw * dose_max_per_kg)

    # ---- เลือก interval ตาม PMA / postnatal age (ตามตาราง) ----
    interval   = None
    active_row = None

    if pma_weeks <= 29 and postnatal_days <= 14:
        interval   = "every 18 hours"
        active_row = "29_0_14"
    elif pma_weeks <= 29 and postnatal_days > 14:
        interval   = "every 12 hours"
        active_row = "29_15plus"
    elif 30 <= pma_weeks <= 36 and postnatal_days <= 14:
        interval   = "every 12 hours"
        active_row = "30_36_0_14"
    elif 30 <= pma_weeks <= 36 and postnatal_days > 14:
        interval   = "every 8 hours"
        active_row = "30_36_15plus"
    elif 37 <= pma_weeks <= 44 and postnatal_days <= 7:
        interval   = "every 12 hours"
        active_row = "37_44_0_7"
    elif 37 <= pma_weeks <= 44 and postnatal_days > 7:
        interval   = "every 8 hours"
        active_row = "37_44_8plus"
    elif pma_weeks >= 45:
        interval   = "every 6 hours"
        active_row = "45plus_all"

    if interval is None or active_row is None:
        return "No suitable dosing interval found for the given PMA and postnatal age", 400

    # Render template
    return render_template(
        'vancomycin_dose.html',
        pma_weeks=pma_weeks,
        pma_days=pma_days,
        calc=calc,
        postnatal_days=postnatal_days,
        bw=bw,
        dose_min_mg=dose_min_mg,
        dose_max_mg=dose_max_mg,
        dose_min_per_kg=dose_min_per_kg,
        dose_max_per_kg=dose_max_per_kg,
        interval=interval,
        active_row=active_row,
        update_date=UPDATE_DATE,
    )
