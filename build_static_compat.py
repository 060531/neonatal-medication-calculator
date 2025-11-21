# build_static_compat.py
#
# สคริปต์สำหรับ build หน้า compatibility.html แบบ static
# เพื่อใช้กับ GitHub Pages โดยดึงรายการยา Drug จากฐานข้อมูล
# และใช้ app จาก app.py (รองรับทั้งแบบมีตัวแปร app และแบบ factory create_app)

from pathlib import Path
from flask import render_template

# ---------- ดึง Flask app ----------
try:
    # กรณี app.py มีตัวแปร app = create_app()
    from app import app as flask_app
except ImportError:
    # กรณีใช้ factory อย่างเดียว
    from app import create_app
    flask_app = create_app()

from models import Drug

# ---------- CONFIG ----------
OUTPUT_DIR = Path(__file__).resolve().parent / "docs"

URL_MAP = {
    "index": "index.html",
    "compatibility_page": "compatibility.html",
    # เติม route อื่นได้ ถ้าต้องใช้ใน base.html
    # "medication_administration": "Medication_administration.html",
}


def build_compatibility_page():
    """เรนเดอร์ compatibility.html ออกมาเป็น docs/compatibility.html"""
    OUTPUT_DIR.mkdir(exist_ok=True)

    with flask_app.app_context():
        # 1) ดึงรายชื่อยาเรียงตามชื่อ เหมือน core.compatibility_page
        drugs = Drug.query.order_by(Drug.generic_name).all()

        # 2) render template โหมด static
        html = render_template(
            "compatibility.html",
            static_build=True,
            use_static=True,
            URL_MAP=URL_MAP,

            drugs=drugs,
            selected_drug_id=None,
            selected_co_drug_id=None,
            compat=None,
            status_code=None,
            status_text=None,
            drug_a_name=None,
            drug_b_name=None,
        )

        # 3) เขียนไฟล์ไปที่ docs/
        out_path = OUTPUT_DIR / "compatibility.html"
        out_path.write_text(html, encoding="utf-8")
        print(f"✅ wrote {out_path}")


if __name__ == "__main__":
    build_compatibility_page()
