# app.py
import os
import argparse
from datetime import date
from flask import Flask, render_template
from routes.routes_medications import meds_bp
from flask import send_from_directory, redirect


# ===== optional extensions =====
try:
    from extensions import db, migrate
except Exception:
    db = None
    migrate = None

def group_meds_by_letter(meds):
    """
    จัดกลุ่มรายการยาเป็น A..Z (ตามตัวอักษรแรกของ label)
    ถ้าไม่ใช่ A-Z ให้ไปอยู่กลุ่ม '#'
    """
    groups = {}

    for m in meds:
        label = (m.get("label") or "").strip()
        if not label:
            ch = "#"
        else:
            ch = label[0].upper()
            if not ("A" <= ch <= "Z"):
                ch = "#"

        groups.setdefault(ch, []).append(m)

    # เรียงยาภายในแต่ละกลุ่มตาม label
    for ch, items in groups.items():
        items.sort(key=lambda x: x.get("label") or "")

    # จัดลำดับให้เป็น A..Z และค่อยตามด้วย '#'
    ordered = {}
    for ch in sorted(k for k in groups.keys() if k != "#"):
        ordered[ch] = groups[ch]
    if "#" in groups:
        ordered["#"] = groups["#"]

    return ordered


def _pick_update_date(cli_value: str = None) -> str:
    """
    ลำดับความสำคัญของวันที่ที่จะแสดงใน {{ UPDATE_DATE }}:
    1) --update-date "YYYY-MM-DD" (หรือข้อความใด ๆ ที่ต้องการ)
    2) ENV UPDATE_DATE
    3) วันนี้ (YYYY-MM-DD)
    """
    if cli_value:
        return cli_value.strip()
    env_v = os.getenv("UPDATE_DATE")
    if env_v:
        return env_v.strip()
    return date.today().strftime("%Y-%m-%d")


# ---------- Jinja filters สำหรับตัวเลข (ประกาศนอก create_app) ----------
def jinja_fmt(value, digits=2):
    """
    ใช้ใน template: {{ bw|fmt(3) }}
    จะ format เป็นทศนิยม digits ตำแหน่ง
    """
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return value


def jinja_fmt_int(value):
    """
    ใช้ใน template: {{ result_ml|fmt_int }}
    ปัดเป็นจำนวนเต็ม
    """
    try:
        return str(int(round(float(value))))
    except (TypeError, ValueError):
        return value
    
def jinja_nz(value, default=0):
    """
    none → default, string/number → float
    ใช้ใน template: {{ bw|nz(0) }}
    """
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
# ----------------------------------------------------------------------


def create_app(testing: bool = False, update_date: str = None):
    app = Flask(__name__)

    # ===== Config พื้นฐาน =====
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI="sqlite:///app.db",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        TESTING=testing,
        SECRET_KEY="dev",
    )

    # เก็บ UPDATE_DATE ใน config
    app.config["UPDATE_DATE"] = _pick_update_date(update_date)

    # ===== ลงทะเบียน Jinja filters =====
    app.jinja_env.filters["fmt"] = jinja_fmt
    app.jinja_env.filters["fmt_int"] = jinja_fmt_int
    app.jinja_env.filters["nz"] = jinja_nz


    # ถ้าอยาก inject UPDATE_DATE เข้า template อัตโนมัติทุกหน้า
    @app.context_processor
    def inject_update_date():
        return {"UPDATE_DATE": app.config["UPDATE_DATE"]}

    # ===== init extensions (ถ้ามี) =====
    if db:
        db.init_app(app)
    if migrate and db:
        migrate.init_app(app, db)

    # ===== Register CLI commands (compat import-compat) =====
    try:
        from compat_cli import compat as compat_cli
        app.cli.add_command(compat_cli)
    except Exception as e:
        print("WARN: cannot register compat CLI:", e)

    # ===== Register Blueprints =====
    from routes.routes_medications import meds_bp
    app.register_blueprint(meds_bp)

    try:
        from routes.core import bp as core_bp
        app.register_blueprint(core_bp)
    except Exception:
        pass


    @app.template_global()
    def has_endpoint(name: str) -> bool:
        """
        เช็คว่ามี endpoint นี้จริงไหม (รองรับทั้งชื่อสั้น และ blueprint.name)
        ใช้ในเทมเพลตเพื่อตรวจสอบก่อนสร้างลิงก์
        """
        if name in app.view_functions:
            return True
        return any(
            f"{bp}.{name}" in app.view_functions for bp in app.blueprints.keys()
        )

    @app.template_global()
    def resolve_endpoint(name: str):
        """
        คืนชื่อ endpoint แบบเต็ม (เติม prefix blueprint ให้อัตโนมัติถ้าจำเป็น)
        เช่น "acyclovir_route" → "meds.acyclovir_route" (ถ้าอยู่ใน blueprint meds)
        """
        if name in app.view_functions:
            return name
        for bp_name in app.blueprints.keys():
            full = f"{bp_name}.{name}"
            if full in app.view_functions:
                return full
        return None

    @app.template_global()
    def u(name: str, **values):
        """
        url_for แบบยอมรับชื่อสั้น:
          - ถ้าพบ endpoint ชื่อนั้นตรง ๆ ใช้ทันที
          - ถ้าไม่พบ ลองเติม prefix เป็น <blueprint>.<name>
          - ถ้ายังไม่พบ คืน "#"
        ใช้ในเทมเพลต: <a href="{{ u('acyclovir_route') }}">Acyclovir</a>
        """
        from flask import url_for

        # กรณีใช้ชื่อเต็มอยู่แล้ว
        if name in app.view_functions:
            return url_for(name, **values)

        # ลองเติม prefix blueprint
        for bp_name in app.blueprints.keys():
            full = f"{bp_name}.{name}"
            if full in app.view_functions:
                return url_for(full, **values)

        # ไม่เจอ endpoint จริง ๆ
        return "#"

    # ===== หน้าแรก (สำหรับทดสอบ) =====
    @app.route("/")
    def index():
        return render_template("index.html")  # ใช้ safe_button แบบ u(endpoint)



    def create_app(testing: bool = False, update_date: str = None):
        app = Flask(__name__)
    ...
    # ===== หน้าเมนู “การบริหารยา” =====
    @app.route("/medication_administration")
    def medication_administration():
        meds = [
            # A
            {"label": "Acyclovir", "endpoint": "acyclovir_route"},
            {"label": "Amikacin", "endpoint": "amikin_route"},
            {"label": "Aminophylline", "endpoint": "aminophylline_route", "danger": True},
            {"label": "Amoxicillin / Clavimoxy", "endpoint": "amoxicillin_clavimoxy_route"},
            {"label": "Amphotericin B", "endpoint": "amphotericinB_route"},
            {"label": "Ampicillin", "endpoint": "ampicillin_route"},

            # B
            {"label": "Benzathine_penicillin_g", "endpoint": "benzathine_penicillin_g_route"},

            # C
            {"label": "Cefazolin", "endpoint": "cefazolin_dose"},
            {"label": "Cefotaxime", "endpoint": "cefotaxime_route"},
            {"label": "Ceftazidime", "endpoint": "ceftazidime_route"},
            {"label": "Ciprofloxacin", "endpoint": "ciprofloxacin_route"},
            {"label": "Clindamycin", "endpoint": "clindamycin_route"},
            {"label": "Cloxacillin", "endpoint": "cloxacillin_route"},
            {"label": "Colistin", "endpoint": "colistin_route"},

            # D
            {"label": "Dexamethasone", "endpoint": "dexamethasone_route"},
            {"label": "Dobutamine", "endpoint": "dobutamine_route", "danger": True},
            {"label": "Dopamine", "endpoint": "dopamine_route", "danger": True},

            # F
            {"label": "Fentanyl", "endpoint": "fentanyl_route", "danger": True},
            {"label": "Furosemide", "endpoint": "furosemide_route"},

            # G
            {"label": "Gentamicin", "endpoint": "gentamicin_route"},

            # H
            {"label": "Hydrocortisone", "endpoint": "hydrocortisone_route"},

            # I
            {"label": "Insulin Human Regular", "endpoint": "insulin_route"},

            # L
            {"label": "Levofloxacin", "endpoint": "levofloxacin_route"},

            # M
            {"label": "Meropenem", "endpoint": "meropenem_route"},
            {"label": "Metronidazole (Flagyl)", "endpoint": "metronidazole"},
            {"label": "Midazolam", "endpoint": "midazolam_route", "danger": True},
            {"label": "Midazolam + Fentanyl", "endpoint": "midazolam_fentanyl_route", "danger": True},
            {"label": "Morphine", "endpoint": "morphine_route", "danger": True},

            # N
            {"label": "Nimbex (Cisatracurium)", "endpoint": "nimbex_route"},

            # O
            {"label": "Omeprazole", "endpoint": "omeprazole_route"},

            # P
            {"label": "Penicillin G sodium", "endpoint": "penicillin_g_sodium_route"},
            {"label": "Phenobarbital", "endpoint": "phenobarbital_route"},
            {"label": "Phenytoin (Dilantin)", "endpoint": "phenytoin_route"},

            # R
            {"label": "Remdesivir", "endpoint": "remdesivir_route"},

            # S
            {"label": "Sul-am®", "endpoint": "sul_am_route"},
            {"label": "Sulbactam", "endpoint": "sulbactam_route"},
            {"label": "Sulperazone", "endpoint": "sulperazone_route"},

            # T
            {"label": "Tazocin", "endpoint": "tazocin_route"},

            # U
            {"label": "Unasyn", "endpoint": "unasyn_route"},

            # V
            {"label": "Vancomycin", "endpoint": "vancomycin_route"},
        ]

        groups = group_meds_by_letter(meds)
        letters = list(groups.keys())

        # ไม่ต้องส่ง update_date เพราะเรามี {{ UPDATE_DATE }} จาก context_processor แล้ว
        return render_template(
            "medication_administration.html",
            groups=groups,
            letters=letters,
            meds=meds,
        )

    # ===== แก้ปัญหา request /None ชั่วคราว: redirect กลับหน้าแรก =====
    @app.route("/None")
    def _fix_none_route():
        from flask import redirect, url_for, request
        # debug ดูว่าใครเป็นคนเรียก /None
        print("DEBUG /None called, Referer=", request.headers.get("Referer"))
        return redirect(url_for("index"))


    return app
    @app.route("/docs/<path:filename>")
    def docs_static(filename):
        docs_dir = os.path.join(app.root_path, "docs")
        return send_from_directory(docs_dir, filename)


    @app.route("/compatibility")
    def compat_redirect():
        # ให้ /compatibility กระโดดไปใช้ static viewer ตัวใหม่
        return redirect("/docs/compatibility.html", code=302)

    @core_bp.route("/compatibility")
    def compatibility_page():
        return render_template("compatibility.html")


# รองรับรันแบบ: python app.py
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=os.getenv("HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", 5000)))
    parser.add_argument("--debug", action="store_true")
    parser.add_argument(
        "--update-date",
        help="กำหนดข้อความวันที่สำหรับ {{ UPDATE_DATE }} (เช่น 2025-11-12 หรือ 'Nov 12, 2025')",
        default=None,
    )
    args = parser.parse_args()

    app = create_app(update_date=args.update_date)
    # debug บังคับให้ True เวลารัน python app.py
    app.run(host=args.host, port=args.port, debug=args.debug or True)
