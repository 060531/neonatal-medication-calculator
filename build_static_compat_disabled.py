# build_static_compat.py
from pathlib import Path

from flask import render_template
from app import create_app
from extensions import db
from models import Drug, Compatibility


def build_compat_page():
    app = create_app()

    with app.app_context():
        # 1) ดึงรายชื่อยาใน DB ไปใส่ dropdown
        drugs = Drug.query.order_by(Drug.generic_name).all()

        # 2) ดึงคู่ยา + status ทั้งหมดจากตาราง Compatibility
        rows = db.session.query(
            Compatibility.drug_id,
            Compatibility.co_drug_id,
            Compatibility.status,
            Compatibility.source,
            Compatibility.note,
        ).all()

        compat_pairs = [
            {
                "drug_id": r.drug_id,
                "co_drug_id": r.co_drug_id,
                "status": r.status,
                "source": r.source,
                "note": r.note,
            }
            for r in rows
        ]

        # 3) URL_MAP สำหรับ static mode (กัน template ไปเรียก url_for)
        URL_MAP = {
            "index": "./index.html",
            "compatibility_page": "./compatibility.html",
        }

        # 4) ใช้ request context ปลอม ให้ Jinja ทำงานสบาย
        with app.test_request_context("/compatibility"):
            html = render_template(
                "compatibility.html",
                static_build=True,     # ทำให้ base.html เซ็ต use_static = True
                drugs=drugs,
                compat_pairs=compat_pairs,
                status_code=None,
                status_text=None,
                drug_a_name=None,
                drug_b_name=None,
                compat=None,
                URL_MAP=URL_MAP,      # ส่งให้ compatibility.html ใช้แทน url_for
            )

        # 5) เขียนออกไปที่ docs/compatibility.html
        out_path = Path("docs/compatibility.html")
        out_path.write_text(html, encoding="utf-8")
        print(f"✅ wrote {out_path.resolve()}")


if __name__ == "__main__":
    build_compat_page()
