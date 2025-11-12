# tools/jinja_render.py
# -*- coding: utf-8 -*-
import os
import shutil
import pathlib
from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATES_DIR = "templates"
STATIC_DIR = "static"
OUTPUT_DIR = "docs"
OUTPUT_STATIC_DIR = f"{OUTPUT_DIR}/static"

# ---------- URL mapping (แทน url_for ในโหมด static) ----------
# ชื่อ key = ชื่อ endpoint ฝั่ง Flask/Jinja, value = ไฟล์ .html จริงภายใต้ docs/
URL_MAP = {
    # root/landing
    "index": "./index.html",
    # ชื่อ route เดิมชี้ไปไฟล์ที่มีจริง (คงตัวพิมพ์ใหญ่ตามไฟล์)
    "medication_administration": "./Medication_administration.html",

    # ปุ่มบนหน้าแรกที่เคย 404
    "calculate_pma_route": "./pma_template.html",
    "compatibility_page": "./compatibility.html",
    "time_management_route": "./time_management.html",

    # route อื่นที่หน้าแรก/ในเพจเรียกใช้
    "drug_calculation_route": "./drug_calculation.html",
    "compatibility": "./compatibility.html",
    "compatibility_result": "./compatibility_result.html",
    "run_time_route": "./run_time.html",
    "run_time_stop_route": "./run_time_stop.html",

    # เพจเดี่ยวที่มักอ้างถึงตรง ๆ (มี fallback ด้านล่างอยู่แล้ว แต่ระบุไว้เพื่อชัดเจน)
    "insulin": "./insulin.html",
    "vancomycin": "./vancomycin.html",
    "penicillin_g_sodium": "./penicillin_g_sodium.html",
    "fentanyl_continuous": "./fentanyl_continuous.html",
    "scan_server": "./scan_server.html",
    "verify_result": "./verify_result.html",

    # static helper
    "static": "./static/",
}

def u(name: str, **kwargs) -> str:
    """
    ตัวแทน url_for แบบย่อ:
      - u('static', filename='x.css') -> ./static/x.css
      - u('<endpoint>') -> map ตาม URL_MAP, ไม่เจอ -> เดาเป็น ./<endpoint>.html
      - u(None) / u('') -> ./index.html
    """
    if not name:
        return "./index.html"
    if name == "static":
        fn = kwargs.get("filename", "")
        return f"./static/{fn}" if fn else "./static/"
    # ถ้าเจอใน URL_MAP ใช้เลย; ไม่งั้นเดาเป็นไฟล์ .html ชื่อเดียวกับ endpoint
    return URL_MAP.get(name, f"./{name}.html")

def static_url(endpoint: str, filename: str = "") -> str:
    """รองรับรูปแบบเดิม url_for('static', filename=...) และ endpoint ใน URL_MAP"""
    if endpoint == "static":
        return f"./static/{filename}" if filename else "./static/"
    return u(endpoint)

def resolve_endpoint(endpoint: str) -> str:
    """
    ใช้ใน macro safe_button(...)
    - http(s) URL -> คืนตรง ๆ
    - endpoint -> map ตาม URL_MAP; ไม่เจอ -> เดาเป็น ./<endpoint>.html
    - ค่าว่าง -> ./index.html
    """
    if not endpoint:
        return "./index.html"
    if isinstance(endpoint, str) and endpoint.startswith(("http://", "https://")):
        return endpoint
    return URL_MAP.get(endpoint, f"./{endpoint}.html")

# ---------- Jinja environment & filters ----------
def safe_fmt(value, fmt="%.2f"):
    """
    ป้องกัน format error เวลา value เป็น None/ไม่ใช่ตัวเลข:
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
    # ทั่วไป
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

DEFAULT_NUM_KEYS = {
    # สถานะผู้ป่วย/อายุ
    "bw": 0.0,
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
    "result_ml_3": 0.0,
    "final_result_1": 0.0,
    "final_result_2": 0.0,
    "final_result_3": 0.0,

    "calculated_ml": 0.0,      # กันหน้า benzathine_penicillin_g.html
    "vol_ml": 0.0,             # กันหน้า phenobarbital.html

    # infusion/ความเข้มข้น/ตัวคูณ
    "multiplication": 1.0,
    "rate_ml_hr": 0.0,
    "concentration_mg_ml": 0.0,

    # ตัวแปรเฉพาะบางหน้า
    "target_conc": 0.0,
    "stock_conc": 0.0,
    "loading_dose_ml": 0.0,
    "maintenance_dose_ml": 0.0,
    "infusion_rate_ml_hr": 0.0,
    "total_volume_ml": 0.0,
    "dilution_volume_ml": 0.0,
}
BASE_CTX.update(DEFAULT_NUM_KEYS)

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
