from app import create_app        # หรือ from app import app ถ้าไม่ได้ใช้ factory
from flask import url_for
from werkzeug.routing import BuildError

PAGES = [
    # ("compat_index", "compat_index.html"),  # ← ตอนนี้ยังไม่รู้ endpoint จริง ตัดทิ้งไปก่อน
    ("ampicillin_route", "ampicillin.html"),
    ("amikin_route", "amikin.html"),
    ("aminophylline_route", "aminophylline.html"),
    ("amphotericinB_route", "amphotericinB.html"),
    ("benzathine_penicillin_g_route", "benzathine_penicillin_g.html"),
    ("cefotaxime_route", "cefotaxime.html"),
    ("ceftazidime_route", "ceftazidime.html"),
    ("ciprofloxacin_route", "ciprofloxacin.html"),
    ("clindamycin_route", "clindamycin.html"),
    ("cloxacillin_route", "cloxacillin.html"),
    ("colistin_route", "colistin.html"),
    ("compatibility_route", "compatibility.html"),
    ("compatibility_result_route", "compatibility_result.html"),
    ("dexamethasone_route", "dexamethasone.html"),
    ("furosemide_route", "furosemide.html"),
    ("gentamicin_route", "gentamicin.html"),
    ("hydrocortisone_route", "hydrocortisone.html"),
]

app = create_app()   # ถ้าใช้ factory; ถ้าไม่ใช้ → เปลี่ยนเป็น: app = app

with app.app_context():
    client = app.test_client()
    with app.test_request_context():
        for endpoint, filename in PAGES:
            try:
                url = url_for(endpoint)
            except BuildError as e:
                print(f"⚠️ ข้าม {endpoint}: {e}")
                continue

            resp = client.get(url)
            out_path = f"docs/{filename}"
            with open(out_path, "wb") as f:
                f.write(resp.data)
            print(f"✓ {endpoint} → {out_path}")
