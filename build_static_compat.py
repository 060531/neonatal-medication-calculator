# build_static_compat.py
#
# สคริปต์สำหรับ build หน้า compatibility.html แบบ static
# ใช้ได้แม้ฐานข้อมูล Drug จะว่าง เพราะมี fallback รายชื่อยา
# เขียนออกเป็น docs/compatibility.html สำหรับ GitHub Pages

from pathlib import Path
from flask import render_template

# ---------- ดึง Flask app ----------
try:
    # กรณีใน app.py มีตัวแปร app = create_app()
    from app import app as flask_app
except ImportError:
    # กรณีใช้ factory แบบ create_app()
    from app import create_app
    flask_app = create_app()

from models import Drug

OUTPUT_DIR = Path(__file__).resolve().parent / "docs"

URL_MAP = {
    "index": "index.html",
    "compatibility_page": "compatibility.html",
}


def build_compatibility_page():
    OUTPUT_DIR.mkdir(exist_ok=True)

    with flask_app.app_context():
        # 1) ลองดึงจากฐานข้อมูลก่อน
        try:
            rows = Drug.query.order_by(Drug.generic_name).all()
        except Exception as e:
            print(f"⚠️ DB query failed: {e}")
            rows = []

        print(f"🔍 static build: found {len(rows)} drugs in DB")

        drugs = rows

        # 2) ถ้า DB ว่าง → ใช้ fallback list แทน
        if not drugs:
            print("ℹ️ DB is empty for static build. Using fallback drug list.")
            fallback_names = [
                # ชุดเดียวกับหน้า Medication_administration + ที่ใช้ใน compatibility
                "Acyclovir",
                "Amikacin",
                "Aminophylline",
                "Amoxicillin / Clavimoxy",
                "Amphotericin B",
                "Ampicillin",
                "Benzathine penicillin G",
                "Calcium gluconate",
                "Cefazolin",
                "Cefotaxime",
                "Ceftazidime",
                "Ciprofloxacin",
                "Clindamycin",
                "Cloxacillin",
                "Colistin",
                "Dexamethasone",
                "Dobutamine",
                "Dopamine",
                "Fentanyl",
                "Furosemide",
                "Gentamicin",
                "Hydrocortisone",
                "Insulin Human Regular",
                "Levofloxacin",
                "Meropenem",
                "Metronidazole (Flagyl)",
                "Midazolam",
                "Midazolam + Fentanyl",
                "Morphine",
                "Nimbex (Cisatracurium)",
                "Omeprazole",
                "Penicillin G sodium",
                "Phenobarbital",
                "Phenytoin (Dilantin)",
                "Remdesivir",
                "Sul-am®",
                "Sulbactam",
                "Sulperazone",
                "Tazocin",
                "Unasyn",
                "Vancomycin",
            ]

            class SimpleDrug:
                def __init__(self, id_, name):
                    self.id = id_
                    self.generic_name = name

            drugs = [SimpleDrug(i + 1, name) for i, name in enumerate(fallback_names)]

        # 3) render template โหมด static
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

        out_path = OUTPUT_DIR / "compatibility.html"
        out_path.write_text(html, encoding="utf-8")
        print(f"✅ wrote {out_path}")


if __name__ == "__main__":
    build_compatibility_page()
