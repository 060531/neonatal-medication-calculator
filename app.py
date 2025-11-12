# app.py
import os
import argparse
from datetime import date
from flask import Flask, render_template

# ===== optional extensions =====
try:
    from extensions import db, migrate
except Exception:
    db = None
    migrate = None


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


def create_app(testing: bool = False, update_date: str = None):
    app = Flask(__name__)

    # ===== Config พื้นฐาน =====
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI="sqlite:///app.db",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        TESTING=testing,
        SECRET_KEY="dev",
    )

    # เก็บ UPDATE_DATE ใน config เพื่อให้แก้/อัปเดตได้ภายหลัง
    app.config["UPDATE_DATE"] = _pick_update_date(update_date)

    # ===== init extensions (ถ้ามี) =====
    if db:
        db.init_app(app)
    if migrate and db:
        migrate.init_app(app, db)

    # ===== Register Blueprints =====
    # นำเข้าในฟังก์ชันเพื่อเลี่ยงวงจร import
    from routes.routes_medications import meds_bp
    app.register_blueprint(meds_bp)

    # ลงทะเบียน core blueprint ถ้ามี
    try:
        from routes.core import bp as core_bp
        app.register_blueprint(core_bp)
    except Exception:
        pass

    # ===== Context processor / Template globals =====
    @app.context_processor
    def inject_update_date():
        # ฉีดให้ทุกเทมเพลต: {{ UPDATE_DATE }}
        return {"UPDATE_DATE": app.config.get("UPDATE_DATE", "")}

    @app.template_global()
    def has_endpoint(name: str) -> bool:
        return name in app.view_functions or any(
            f"{bp}.{name}" in app.view_functions for bp in app.blueprints.keys()
        )

    @app.template_global()
    def resolve_endpoint(name: str):
        """คืนชื่อ endpoint แบบเต็ม (เติม prefix blueprint ให้อัตโนมัติถ้าจำเป็น)"""
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
        """
        from flask import url_for

        if name in app.view_functions:
            return url_for(name, **values)
        for bp_name in app.blueprints.keys():
            full = f"{bp_name}.{name}"
            if full in app.view_functions:
                return url_for(full, **values)
        return "#"

    # ===== หน้าแรก (สำหรับทดสอบ) =====
    @app.route("/")
    def index():
        # ตัวอย่าง: เปิดหน้า Acyclovir โดยตั้งค่าเริ่มต้นว่าง ๆ
        return render_template("acyclovir.html", dose=None)

    return app


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
    app.run(host=args.host, port=args.port, debug=args.debug or True)
