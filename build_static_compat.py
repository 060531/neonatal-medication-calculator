# build_static_compat.py
from pathlib import Path

from flask import render_template
from sqlalchemy.orm import aliased

from app import create_app
from extensions import db
from models import Drug, Compatibility


def build_compat_page():
    app = create_app()
    with app.app_context():
        # 1) ดึงรายชื่อยาไว้เติม dropdown
        drugs = Drug.query.order_by(Drug.generic_name).all()
        print(f"🔍 static build: found {len(drugs)} drugs in DB")

        # 2) ดึงผล compatibility + ชื่อยาแบบ join ถูกต้อง
        DrugA = aliased(Drug)
        DrugB = aliased(Drug)

        rows = (
            db.session.query(
                DrugA.generic_name.label("drug_a"),
                DrugB.generic_name.label("drug_b"),
                Compatibility.status,
                Compatibility.source,
                Compatibility.note,
            )
            .join(DrugA, Compatibility.drug_id == DrugA.id)
            .join(DrugB, Compatibility.co_drug_id == DrugB.id)
            .order_by(DrugA.generic_name, DrugB.generic_name)
            .all()
        )

        compat_pairs = []
        for r in rows:
            compat_pairs.append(
                {
                    "drug_a": r.drug_a,
                    "drug_b": r.drug_b,
                    "status": (r.status or "ND"),
                    "source": (r.source or ""),
                    "note": (r.note or ""),
                }
            )

        print(f"🔍 static build: found {len(compat_pairs)} compat pairs")

        # 3) context ที่ส่งเข้า template compatibility.html
        ctx = dict(
            use_static=True,
            static_build=True,
            URL_MAP={"index": "./index.html"},
            drugs=drugs,
            selected_drug_id=None,
            selected_co_drug_id=None,
            status_code=None,
            status_text="",
            compat=None,
            drug_a_name=None,
            drug_b_name=None,
            compat_pairs=compat_pairs,
        )

        html = render_template("compatibility.html", **ctx)

        # 4) เขียนออกไปที่ docs/compatibility.html (สำหรับ GitHub Pages)
        out_path = Path(app.root_path).parent / "docs" / "compatibility.html"
        out_path.parent.mkdir(exist_ok=True)
        out_path.write_text(html, encoding="utf-8")
        print(f"✅ wrote {out_path}")


if __name__ == "__main__":
    build_compat_page()
