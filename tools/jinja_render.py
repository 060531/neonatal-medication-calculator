# tools/jinja_render.py
# -*- coding: utf-8 -*-
import os
import shutil
import pathlib
from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATES_DIR = "templates"
STATIC_DIR = "static"            # โฟลเดอร์ static ของโปรเจกต์ Flask
OUTPUT_DIR = "docs"
OUTPUT_STATIC_DIR = f"{OUTPUT_DIR}/static"

# ---------- URL mapping (แทน url_for ในโหมด static) ----------
URL_MAP = {
    # หน้า root
    "index": "./index.html",
    "medication_administration": "./index.html",

    # เพจคำนวณ/หน้าเดี่ยวที่ต้องการ build เป็นไฟล์ (เติมเพิ่มได้)
    "insulin": "./insulin.html",
    "vancomycin": "./vancomycin.html",
    "penicillin_g_sodium": "./penicillin_g_sodium.html",
    "fentanyl_continuous": "./fentanyl_continuous.html",
    "scan_server": "./scan_server.html",
    "verify_result": "./verify_result.html",
}

def u(name: str, **kwargs) -> str:
    """
    ตัวแทน url_for แบบย่อ:
      - u('static', filename='x.css') -> ./static/x.css
      - u('index') / u('<endpoint>') -> map ตาม URL_MAP (หรือเดาเป็น ./<endpoint>.html)
    """
    if name == "static":
        fn = kwargs.get("filename", "")
        return f"./static/{fn}" if fn else "./static/"
    if not name:
        return "./index.html"
    return URL_MAP.get(name, f"./{name}.html")

def static_url(endpoint: str, filename: str = "") -> str:
    """รองรับรูปแบบเดิม url_for('static', filename=...) และ endpoint ใน URL_MAP"""
    if endpoint == "static":
        return f"./static/{filename}" if filename else "./static/"
    return u(endpoint)

def resolve_endpoint(endpoint: str) -> str:
    """
    ใช้ใน macro safe_button(...) ของ index.html
    - http(s) URL -> คืนตรง ๆ
    - endpoint ที่รู้จัก -> map ตาม URL_MAP
    - อื่น ๆ -> เดาว่าเป็นไฟล์ .html ใน docs
    """
    if not endpoint:
        return "./index.html"
    if endpoint.startswith(("http://", "https://")):
        return endpoint
    return URL_MAP.get(endpoint, f"./{endpoint}.html")

# ---------- Jinja environment & filters ----------
def safe_fmt(value, fmt="%.2f"):
    """
    ป้องกันการฟอร์แมตตัวเลขแล้วล้มเมื่อ value เป็น None/Undefined/ไม่ใช่ตัวเลข
    ใช้: {{ some_var|safe_fmt('%.2f') }}
    """
    try:
        return fmt % (value,)
    except Exception:
        try:
            return fmt % (0,)
        except Exception:
            return str(value)

env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html", "xml"]),
)
env.filters["safe_fmt"] = safe_fmt
env.globals.update({
    "u": u,
    "url_for": static_url,     # ให้ base.html ใช้ได้
    "static_build": True,      # เงื่อนไขใน base.html
    "resolve_endpoint": resolve_endpoint,
})

# ---------- ค่า context เริ่มต้น + ค่าเริ่มต้นเชิงตัวเลข ----------
BASE_CTX = {
    # ค่าทั่วไป
    "error": None,
    "content_extra": None,
    "UPDATE_DATE": "",
    "u": u,
    "order": {},               # กัน {{ order|tojson }} พัง
    "static_build": True,
    # mock ที่บางเทมเพลตอาจเรียก
    "request": {"path": "/"},
    "session": {},
}

# ค่า default สำหรับตัวเลขที่ถูก format/คำนวณบ่อย ๆ
DEFAULT_NUM_KEYS = {
    # สถานะผู้ป่วย/อายุ
    "bw": 0.0,                 # Birth weight (kg)
    "pma_weeks": 0,
    "pma_days": 0,
    "postnatal_days": 0,

    # ปริมาณ/ผลลัพธ์
    "dose": 0.0,
    "dose_ml": 0.0,
    "dose_mgkg": 0.0,

    "result_ml": 0.0,
    "result_ml_1": 0.0,
    "result_ml_2": 0.0,
    "result_ml_3": 0.0,        # กันเผื่อหลายสเต็ป
    "final_result_1": 0.0,
    "final_result_2": 0.0,
    "final_result_3": 0.0,

    "calculated_ml": 0.0,      # เผื่อหน้า benzathine_penicillin_g.html

    # infusion/ความเข้มข้น/ตัวคูณ
    "multiplication": 1.0,
    "rate_ml_hr": 0.0,
    "concentration_mg_ml": 0.0,

    # ตัวแปรเฉพาะบางหน้า (เช่น phenobarbital)
    "target_conc": 0.0,
    "stock_conc": 0.0,
    "loading_dose_ml": 0.0,
    "maintenance_dose_ml": 0.0,
    "infusion_rate_ml_hr": 0.0,
    "total_volume_ml": 0.0,
    "dilution_volume_ml": 0.0,
    "vol_ml": 0.0, 
}

# ผสาน default เข้ากับ context หลัก
BASE_CTX.update(DEFAULT_NUM_KEYS)

URL_MAP = {
    # root/landing
    "index": "./index.html",
    "medication_administration": "./Medication_administration.html",  # ชื่อไฟล์จริงขึ้นต้น M ใหญ่

    # กลุ่มเมนูหลักบน index
    "compatibility": "./compatibility.html",
    "drug_calculation_route": "./drug_calculation.html",
    "time_management_route": "./time_management.html",
    "calculate_pma_route": "./pma_template.html",

    # เผื่อมีชื่อ route อื่นที่หน้า/ปุ่มเรียกใช้
    "compatibility_result": "./compatibility_result.html",
    "run_time_route": "./run_time.html",
    "run_time_stop_route": "./run_time_stop.html",

    # เพจยาที่ลิงก์ตรงเป็นรายตัว (ตัวอย่าง—เพิ่มได้ตามต้องใช้)
    "vancomycin": "./vancomycin.html",
    "insulin": "./insulin.html",
    "fentanyl_continuous": "./fentanyl_continuous.html",
    "penicillin_g_sodium": "./penicillin_g_sodium.html",
    "scan_server": "./scan_server.html",
    "verify_result": "./verify_result.html",

    # static helper
    "static": "./static/",
}

URL_MAP.update({
    "calculate_pma_route": "./pma_template.html",
    "drug_calculation_route": "./drug_calculation.html",
    "time_management_route": "./time_management.html",
    "compatibility": "./compatibility.html",
    "compatibility_result": "./compatibility_result.html",
    "run_time_route": "./run_time.html",
    "run_time_stop_route": "./run_time_stop.html",
})


# ---------- Utilities ----------
def ensure_docs_dir():
    """สร้าง docs/ และ .nojekyll"""
    out = pathlib.Path(OUTPUT_DIR)
    out.mkdir(parents=True, exist_ok=True)
    (out / ".nojekyll").write_text("", encoding="utf-8")

def copy_static():
    """คัดลอก static/ → docs/static/"""
    if os.path.isdir(STATIC_DIR):
        if os.path.isdir(OUTPUT_STATIC_DIR):
            shutil.rmtree(OUTPUT_STATIC_DIR)
        shutil.copytree(STATIC_DIR, OUTPUT_STATIC_DIR, dirs_exist_ok=True)
        print(f"copied static -> {OUTPUT_STATIC_DIR}")
    else:
        print("skip: no static/ folder found")

def should_render(filename: str) -> bool:
    """ข้าม partial เช่น _header.html และเลือกเฉพาะ .html"""
    return filename.endswith(".html") and not filename.startswith("_")

# ---------- Render all ----------
def render_all():
    ensure_docs_dir()
    copy_static()

    for root, _, files in os.walk(TEMPLATES_DIR):
        for fname in files:
            if not should_render(fname):
                continue

            src_path = pathlib.Path(root) / fname
            rel_path = src_path.relative_to(TEMPLATES_DIR)
            out_path = pathlib.Path(OUTPUT_DIR) / rel_path

            # พิเศษ: templates/index.html -> docs/index.html
            if str(rel_path) == "index.html":
                out_path = pathlib.Path(OUTPUT_DIR) / "index.html"
            else:
                out_path.parent.mkdir(parents=True, exist_ok=True)

            tmpl = env.get_template(str(rel_path))
            html = tmpl.render(**BASE_CTX)

            with open(out_path, "w", encoding="utf-8") as fp:
                fp.write(html)
            print("rendered ->", out_path)

if __name__ == "__main__":
    render_all()
