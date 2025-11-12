# app.py
from flask import Flask, render_template
from datetime import date

# ใช้ extensions จริงถ้ามี; ถ้าไม่มีให้ข้ามได้
try:
    from extensions import db, migrate
except Exception:
    db = None
    migrate = None


def create_app(testing: bool = False):
    app = Flask(__name__)

    # ===== Config พื้นฐาน =====
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI="sqlite:///app.db",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        TESTING=testing,
        SECRET_KEY="dev",
    )

    # ===== init extensions (ถ้ามี) =====
    if db:
        db.init_app(app)
    if migrate and db:
        migrate.init_app(app, db)

    # ===== Register Blueprints =====
    # นำเข้า “ภายในฟังก์ชัน” เพื่อเลี่ยงวงจร import
    from routes.routes_medications import meds_bp
    app.register_blueprint(meds_bp)

    # (ถ้ามี core blueprint ค่อยลงทะเบียนแบบ try/except)
    try:
        from routes.core import bp as core_bp
        app.register_blueprint(core_bp)
    except Exception:
        pass

    # ===== Context processor / Template globals =====
    @app.context_processor
    def inject_update_date():
        return {"UPDATE_DATE": date.today().strftime("%Y-%m-%d")}

    @app.template_global()
    def has_endpoint(name: str) -> bool:
        from flask import current_app
        return name in current_app.view_functions

    @app.template_global()
    def resolve_endpoint(name: str):
        """คืนชื่อ endpoint แบบเต็ม (เติม prefix blueprint ให้อัตโนมัติถ้าต้อง)"""
        from flask import current_app
        if name in current_app.view_functions:
            return name
        for bp_name in current_app.blueprints.keys():
            full = f"{bp_name}.{name}"
            if full in current_app.view_functions:
                return full
        return None

    @app.template_global()
    def u(name: str, **values):
        """url_for ที่ยอมรับชื่อสั้นของ endpoint ได้ (auto-prefix blueprint)"""
        from flask import current_app, url_for
        if name in current_app.view_functions:
            return url_for(name, **values)
        for bp_name in current_app.blueprints.keys():
            full = f"{bp_name}.{name}"
            if full in current_app.view_functions:
                return url_for(full, **values)
        return "#"

    # ===== หน้าแรก (ทดสอบ) =====
    @app.route("/")
    def index():
        # ให้หน้าแรกลองแสดงฟอร์ม Acyclovir
        return render_template("acyclovir.html", dose=None)

    return app


# รองรับรันแบบ: python app.py
# app.py (ส่วนท้ายไฟล์)
if __name__ == "__main__":
    import argparse, os
    app = create_app()

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=os.getenv("HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", 5000)))
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    app.run(host=args.host, port=args.port, debug=args.debug or True)
