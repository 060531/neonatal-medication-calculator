# export_docs.py
from pathlib import Path
from datetime import date

# ------ สร้าง Flask app (รองรับทั้ง app และ create_app) ------
try:
    from app import app as flask_app
except ImportError:
    from app import create_app
    flask_app = create_app()

OUTPUT_DIR = Path("docs")
OUTPUT_DIR.mkdir(exist_ok=True)

update_date = date.today().isoformat()

# รายการหน้า ที่จะ export
PAGES = [
    ("aminophylline.html", "aminophylline.html"),
    ("benzathine_penicillin_g.html", "benzathine_penicillin_g.html"),
    ("cefotaxime.html", "cefotaxime.html"),
    ("ceftazidime.html", "ceftazidime.html"),
    ("colistin.html", "colistin.html"),
    ("gentamicin.html", "gentamicin.html"),
]

# context เพิ่มเติมรายหน้า (กัน undefined variable)
TEMPLATE_EXTRA_CONTEXT = {
    "cefotaxime.html": {
        "result_ml": None,
        "multiplication": None,
    },
    "ceftazidime.html": {
        "result_ml": None,
        "multiplication": None,
    },
    "colistin.html": {
        "result_ml": None,
        "multiplication": None,
    },
    "gentamicin.html": {
        "result_ml": None,
        "multiplication": None,
    },
}

def export_pages():
    from flask import render_template

    with flask_app.app_context():
        # จำลอง request ให้ url_for(), u() ใช้งานได้
        with flask_app.test_request_context("/"):
            for template_name, output_name in PAGES:
                print(f"Rendering {template_name} -> docs/{output_name}")

                # context พื้นฐานที่ทุกหน้าใช้ร่วมกัน
                ctx = {
                    "dose": None,
                    "result_ml": None,
                    "error": None,
                    "scheme": None,
                    "scheme_label": None,
                    "volume_ml": None,
                    "total_vol": None,
                    "strength": None,
                    "update_date": update_date,
                    "UPDATE_DATE": update_date,
                }


                # ถ้ามี context เพิ่มเฉพาะหน้า ให้ merge เข้ามา
                extra = TEMPLATE_EXTRA_CONTEXT.get(template_name, {})
                ctx.update(extra)

                html = render_template(template_name, **ctx)
                out_path = OUTPUT_DIR / output_name
                out_path.write_text(html, encoding="utf-8")

    print("✅ Export docs เสร็จแล้ว")

if __name__ == "__main__":
    export_pages()
