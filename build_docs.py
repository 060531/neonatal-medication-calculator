import os

# ถ้าโปรเจกต์คุณใช้ factory pattern (มี create_app() ใน app.py)
from app import create_app
app = create_app()

# ถ้าโปรเจกต์คุณเป็นแบบ app = Flask(__name__) ใน app.py:
# from app import app

# ========== เลือกเฉพาะหน้า ที่ต้องการ sync ==========

PAGES = [
    # (path บน Flask,           ชื่อไฟล์ใน docs)
    ("/ampicillin",             "ampicillin.html"),
    ("/aminophylline",          "aminophylline.html"),
    ("/amikin",                 "amikin.html"),
    ("/amphotericinB",          "amphotericinB.html"),
    ("/benzathine-penicillin-g", "benzathine_penicillin_g.html"),
    ("/cefotaxime",             "cefotaxime.html"),
    ("/ceftazidime",            "ceftazidime.html"),
    ("/ciprofloxacin",          "ciprofloxacin.html"),
    ("/clindamycin",            "clindamycin.html"),
    ("/cloxacillin",            "cloxacillin.html"),
    ("/colistin",               "colistin.html"),
    ("/dexamethasone",          "dexamethasone.html"),
    ("/furosemide",             "furosemide.html"),
    ("/gentamicin",             "gentamicin.html"),
    ("/hydrocortisone",         "hydrocortisone.html"),
    # เพิ่ม/ลดได้ตามต้องการ
]

def main():
    with app.app_context():
        client = app.test_client()

        os.makedirs("docs", exist_ok=True)

        for path, filename in PAGES:
            resp = client.get(path)
            if resp.status_code != 200:
                print(f"⚠️ ข้าม {path}: status {resp.status_code}")
                continue

            out_path = os.path.join("docs", filename)
            with open(out_path, "wb") as f:
                f.write(resp.data)

            print(f"✓ {path} → {out_path}")

if __name__ == "__main__":
    main()
