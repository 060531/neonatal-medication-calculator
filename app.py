# app.py
import os
import argparse
from datetime import date
from pathlib import Path

from flask import Flask, render_template, send_from_directory, redirect, url_for, request

# ===== optional extensions =====
try:
    from extensions import db, migrate
except Exception:
    db = None
    migrate = None


ROOT = Path(__file__).resolve().parent
DOCS_DIR = ROOT / "docs"


def group_meds_by_letter(meds):
    groups = {}
    for m in meds:
        label = (m.get("label") or "").strip()
        ch = (label[0].upper() if label else "#")
        if not ("A" <= ch <= "Z"):
            ch = "#"
        groups.setdefault(ch, []).append(m)

    for ch, items in groups.items():
        items.sort(key=lambda x: x.get("label") or "")

    ordered = {ch: groups[ch] for ch in sorted(k for k in groups.keys() if k != "#")}
    if "#" in groups:
        ordered["#"] = groups["#"]
    return ordered


def _pick_update_date(cli_value: str = None) -> str:
    if cli_value:
        return cli_value.strip()
    env_v = os.getenv("UPDATE_DATE")
    if env_v:
        return env_v.strip()
    return date.today().strftime("%Y-%m-%d")


# ---------- Jinja filters ----------
def jinja_fmt(value, digits=2):
    try:
        return f"{float(value):.{int(digits)}f}"
    except Exception:
        return value

def jinja_fmt_int(value):
    try:
        return str(int(round(float(value))))
    except Exception:
        return value

def jinja_nz(value, default=0):
    if value is None or value == "":
        return default
    try:
        return float(value)
    except Exception:
        return default


def create_app(testing: bool = False, update_date: str = None):
    app = Flask(__name__)

    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI="sqlite:///app.db",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        TESTING=testing,
        SECRET_KEY="dev",
    )

    # ✅ เก็บ update date “ค่าเดียว” ที่นี่
    app.config["UPDATE_DATE"] = _pick_update_date(update_date)

    # ✅ filters
    app.jinja_env.filters["fmt"] = jinja_fmt
    app.jinja_env.filters["fmt_int"] = jinja_fmt_int
    app.jinja_env.filters["nz"] = jinja_nz

    # ✅ inject ให้ทุก template (ส่งทั้ง 2 ชื่อ กันหน้าเก่า/ใหม่)
    @app.context_processor
    def inject_update_date():
        ud = app.config.get("UPDATE_DATE", "")
        return {"UPDATE_DATE": ud, "update_date": ud}

    # ✅ init extensions
    if db:
        db.init_app(app)
    if migrate and db:
        migrate.init_app(app, db)

    # ==============================
    # ✅ Register Blueprints
    # ==============================
    from routes.routes_medications import meds_bp
    app.register_blueprint(meds_bp)

    try:
        from routes.core import bp as core_bp
        app.register_blueprint(core_bp)
    except Exception:
        pass

    # ==============================
    # ✅ Template globals: has_endpoint / resolve_endpoint / u
    # (ทำหลัง register blueprint เสมอ)
    # ==============================
    def has_endpoint(name: str) -> bool:
        if name in app.view_functions:
            return True
        return any(f"{bp}.{name}" in app.view_functions for bp in app.blueprints.keys())

    def resolve_endpoint(name: str):
        if name in app.view_functions:
            return name
        for bp in app.blueprints.keys():
            full = f"{bp}.{name}"
            if full in app.view_functions:
                return full
        return None

    def u(name: str, **values):
        resolved = resolve_endpoint(name)
        if not resolved:
            return "#"
        return url_for(resolved, **values)

    # ✅ สำคัญ: ใส่ลง globals เพื่อให้ "macro" มองเห็นแน่นอนทุกหน้า
    app.jinja_env.globals["has_endpoint"] = has_endpoint
    app.jinja_env.globals["resolve_endpoint"] = resolve_endpoint
    app.jinja_env.globals["u"] = u

    # ==============================
    # ✅ routes (local dev)
    # ==============================
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/medication_administration")
    def medication_administration():
        meds = [
            {"label": "Acyclovir", "endpoint": "acyclovir_route"},
            {"label": "Amikacin", "endpoint": "amikin_route"},
            {"label": "Aminophylline", "endpoint": "aminophylline_route", "danger": True},
            {"label": "Amoxicillin / Clavimoxy", "endpoint": "amoxicillin_clavimoxy_route"},
            {"label": "Amphotericin B", "endpoint": "amphotericinB_route"},
            {"label": "Ampicillin", "endpoint": "ampicillin_route"},
            {"label": "Benzathine_penicillin_g", "endpoint": "benzathine_penicillin_g_route"},
            {"label": "Cefazolin", "endpoint": "cefazolin_dose"},
            {"label": "Cefotaxime", "endpoint": "cefotaxime_route"},
            {"label": "Ceftazidime", "endpoint": "ceftazidime_route"},
            {"label": "Ciprofloxacin", "endpoint": "ciprofloxacin_route"},
            {"label": "Clindamycin", "endpoint": "clindamycin_route"},
            {"label": "Cloxacillin", "endpoint": "cloxacillin_route"},
            {"label": "Colistin", "endpoint": "colistin_route"},
            {"label": "Dexamethasone", "endpoint": "dexamethasone_route"},
            {"label": "Dobutamine", "endpoint": "dobutamine_route", "danger": True},
            {"label": "Dopamine", "endpoint": "dopamine_route", "danger": True},
            {"label": "Fentanyl", "endpoint": "fentanyl_route", "danger": True},
            {"label": "Furosemide", "endpoint": "furosemide_route"},
            {"label": "Gentamicin", "endpoint": "gentamicin_route"},
            {"label": "Hydrocortisone", "endpoint": "hydrocortisone_route"},
            {"label": "Insulin Human Regular", "endpoint": "insulin_route"},
            {"label": "Levofloxacin", "endpoint": "levofloxacin_route"},
            {"label": "Meropenem", "endpoint": "meropenem_route"},
            {"label": "Metronidazole (Flagyl)", "endpoint": "metronidazole"},
            {"label": "Midazolam", "endpoint": "midazolam_route", "danger": True},
            {"label": "Midazolam + Fentanyl", "endpoint": "midazolam_fentanyl_route", "danger": True},
            {"label": "Morphine", "endpoint": "morphine_route", "danger": True},
            {"label": "Nimbex (Cisatracurium)", "endpoint": "nimbex_route"},
            {"label": "Omeprazole", "endpoint": "omeprazole_route"},
            {"label": "Penicillin G sodium", "endpoint": "penicillin_g_sodium_route"},
            {"label": "Phenobarbital", "endpoint": "phenobarbital_route"},
            {"label": "Phenytoin (Dilantin)", "endpoint": "phenytoin_route"},
            {"label": "Remdesivir", "endpoint": "remdesivir_route"},
            {"label": "Sul-am®", "endpoint": "sul_am_route"},
            {"label": "Sulbactam", "endpoint": "sulbactam_route"},
            {"label": "Sulperazone", "endpoint": "sulperazone_route"},
            {"label": "Tazocin", "endpoint": "tazocin_route"},
            {"label": "Unasyn", "endpoint": "unasyn_route"},
            {"label": "Vancomycin", "endpoint": "vancomycin_route"},
        ]
        groups = group_meds_by_letter(meds)
        letters = list(groups.keys())
        return render_template(
            "medication_administration.html",
            groups=groups, letters=letters, meds=meds
        )

    # ✅ serve docs (สำหรับเปิด static html ตอน dev)
    @app.route("/docs/<path:filename>")
    def docs_static(filename):
        return send_from_directory(str(DOCS_DIR), filename)

    # ✅ กัน /None
    @app.route("/None")
    def _fix_none_route():
        print("DEBUG /None called, Referer=", request.headers.get("Referer"))
        return redirect(url_for("index"))

    return app


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=os.getenv("HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", 5000)))
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--update-date", default=None,
                        help="กำหนดข้อความวันที่สำหรับ {{ UPDATE_DATE }}")
    args = parser.parse_args()

    app = create_app(update_date=args.update_date)
    app.run(host=args.host, port=args.port, debug=args.debug)
