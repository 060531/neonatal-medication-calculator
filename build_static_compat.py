# build_static_compat.py
#
# build หน้า docs/compatibility.html สำหรับ GitHub Pages
# - ใช้ fallback list สำหรับ dropdown (อยู่ใน template)
# - ใช้ data/seed_compatibility.json สำหรับผลลัพธ์คู่ยา (ฝั่ง static)

from pathlib import Path
import json

from flask import render_template

# ดึง Flask app
try:
    from app import app as flask_app
except ImportError:
    from app import create_app
    flask_app = create_app()

ROOT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT_DIR / "docs"
DATA_PATH = ROOT_DIR / "data" / "seed_compatibility.json"


def build_compatibility_page():
    OUTPUT_DIR.mkdir(exist_ok=True)

    # อ่านไฟล์ JSON สำหรับคู่ยา
    try:
        raw = DATA_PATH.read_text(encoding="utf-8")
        compat_pairs = json.loads(raw)
        if not isinstance(compat_pairs, list):
            compat_pairs = []
    except Exception as e:
        print(f"⚠️ cannot read seed_compatibility.json: {e}")
        compat_pairs = []

    with flask_app.app_context():
        html = render_template(
            "compatibility.html",
            static_build=True,
            use_static=True,
            URL_MAP={
                "index": "index.html",
                "compatibility_page": "compatibility.html",
            },
            # dropdown จะใช้ fallback_names ใน template เอง
            drugs=None,
            compat_pairs=compat_pairs,
            selected_drug_id=None,
            selected_co_drug_id=None,
            compat=None,
            status_code=None,
            status_text=None,
            drug_a_name=None,
            drug_b_name=None,
        )

    out_path = OUTPUT_DIR / "compatibility.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"✅ wrote {out_path}")


if __name__ == "__main__":
    build_compatibility_page()
