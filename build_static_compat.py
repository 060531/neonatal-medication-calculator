# build_static_compat.py
"""
สร้างไฟล์ docs/compatibility.html สำหรับ GitHub Pages
โดยดึง:
  - รายชื่อยา (Drug) สำหรับ dropdown
  - คู่ยา + status (Compatibility) สำหรับ STATIC_COMPAT ใน JS
"""

from pathlib import Path
import json

from flask import render_template

from app import create_app
from models import Drug, Compatibility

ROOT_DIR = Path(__file__).resolve().parent
DOCS_DIR = ROOT_DIR / "docs"
DATA_DIR = ROOT_DIR / "data"


def load_url_map():
    """
    โหลด URL_MAP เดิมที่ใช้ตอน build static หน้าอื่น ๆ
    ถ้าไม่มีไฟล์ก็ส่ง {} ไป (template จะ fallback เอง)
    """
    url_map_path = DATA_DIR / "url_map.json"
    if not url_map_path.exists():
        return {}

    try:
        return json.loads(url_map_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def build_static_compat():
    app = create_app()

    with app.app_context():
        # ----- รายชื่อยา สำหรับ dropdown -----
        drugs = Drug.query.order_by(Drug.generic_name).all()
        print(f"🔍 static build: found {len(drugs)} drugs in DB")

        # ----- คู่ยา + status สำหรับ STATIC_COMPAT -----
        compat_rows = Compatibility.query.all()
        compat_pairs = []

        for row in compat_rows:
            drug_a = Drug.query.get(row.drug_id)
            drug_b = Drug.query.get(row.co_drug_id)
            if not drug_a or not drug_b:
                continue

            compat_pairs.append(
                {
                    "drug_a": (drug_a.generic_name or "").strip(),
                    "drug_b": (drug_b.generic_name or "").strip(),
                    "status": (row.status or "ND").strip(),
                    "source": row.source or "",
                    "note": row.note or "",
                }
            )

        print(f"🔍 static build: found {len(compat_pairs)} compatibility pairs")

        url_map = load_url_map()

        html = render_template(
            "compatibility.html",
            # flags สำหรับ template
            static_build=True,
            use_static=True,
            home_page=False,
            # data สำหรับ dropdown + JS
            drugs=drugs,
            compat_pairs=compat_pairs,
            URL_MAP=url_map,
        )

    DOCS_DIR.mkdir(exist_ok=True)
    out_path = DOCS_DIR / "compatibility.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"✅ wrote {out_path}")


if __name__ == "__main__":
    build_static_compat()
