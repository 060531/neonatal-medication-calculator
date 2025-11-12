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
# เก็บ "ค่าเป็นชื่อไฟล์ .html จริง" เพื่อให้ tools/check_links.py ทำงานถูกต้อง
URL_MAP = {
    # หน้าแรก
    "index": "index.html",

    # ปุ่มหลักจากหน้า Home
    "pma_template": "pma_template.html",
    "compatibility": "compatibility.html",
    "Medication_administration": "Medication_administration.html",
    "time_management": "time_management.html",

    # เส้นทางย่อย/ผลลัพธ์
    "compatibility_result": "compatibility_result.html",
    "run_time": "run_time.html",
    "run_time_stop": "run_time_stop.html",
    "verify_result": "verify_result.html",

    # ตัวอย่างหน้า drug ต่าง ๆ (เติมได้ตามจริงของโปรเจกต์)
    "vancomycin": "vancomycin.html",
    "insulin": "insulin.html",
    "fentanyl_continuous": "fentanyl_continuous.html",
    "penicillin_g_sodium": "penicillin_g_sodium.html",
    "scan_server": "scan_server.html",

    # static (พิเศษ)
    "static": "static/",
}

# ---------- Helpers (Normalization) ----------
def _strip_leading_dots(path: str) -> str:
    """ตัด './' นำหน้าซ้ำ ๆ ออก"""
    while path.startswith("./"):
        path = path[2:]
    return path

def _ensure_html_file(name_or_file: str) -> str:
    """รับชื่อไฟล์หรือ slug -> คืนชื่อไฟล์ลงท้าย .html ครั้งเดียว"""
    s = name_or_file.strip()
    s = _strip_leading_dots(s)
    if s.endswith(".html"):
        return s
    return f"{s}.html"

def u(name: str, **kwargs) -> str:
    """
    ตัวแทน url_for แบบ static:
      - u('static', filename='x.css') -> ./static/x.css
      - u('<endpoint>') -> map เป็นไฟล์ .html; ไม่เจอ -> เดาเป็น ./<endpoint>.html
      - u(None) / u('') -> ./index.html
    คืนค่าเป็นพาธสัมพัทธ์เสมอ และไม่มี .html ซ้ำ
    """
    if not name:
        return "./index.html"
    if name == "static":
        fn = kwargs.get("filename", "")
        return f"./static/{fn}" if fn else "./static/"
    target = URL_MAP.get(name, f"{name}.html")
    target = _ensure_html_file(target)
    return f"./{_strip_leading_dots(target)}"

def static_url(endpoint: str, filename: str = "") -> str:
    """รองรับรูปแบบเดิม url_for('static', filename=...) และ endpoint ใน URL_MAP"""
    if endpoint == "static":
        return f"./static/{filename}" if filename else "./static/"
    return u(endpoint)

def resolve_endpoint(endpoint: str) -> str:
    """
    ใช้ใน macro/button ที่รับได้ทั้ง URL และ endpoint
    - http(s) URL / anchor -> คืนตรง ๆ
    - endpoint -> map เป็นไฟล์ .html
    - ค่าว่าง -> ./index.html
    """
    if not endpoint:
        return "./index.html"
    if isinstance(endpoint, str) and endpoint.startswith(("http://", "https://", "#")):
        return endpoint
    target = URL_MAP.get(endpoint, f"{endpoint}.html")
    target = _ensure_html_file(target)
    return f"./{_strip_leading_dots(target)}"

# ---------- Jinja filters & env ----------
def safe_fmt(value, fmt="%.2f"):
    """ป้องกัน format error เวลา value เป็น None/ไม่ใช่ตัวเลข"""
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

# ---------- Context ตั้งต้น ----------
BASE_CTX = {
    "error": None,
    "content_extra": None,
    "UPDATE_DATE": "",
    "u": u,
    "static_build": True,
    "request": {"path": "/"},
    "session": {},
    "order": {},  # <- สำคัญ: กัน {{ order|tojson }} พัง

    # ป้องกันตัวเลขที่บางหน้าเรียกใช้
    "bw": 0.0, "pma_weeks": 0, "pma_days": 0, "postnatal_days": 0,
    "dose": 0.0, "dose_ml": 0.0, "dose_mgkg": 0.0,
    "result_ml": 0.0, "result_ml_1": 0.0, "result_ml_2": 0.0, "result_ml_3": 0.0,
    "final_result_1": 0.0, "final_result_2": 0.0, "final_result_3": 0.0,
    "calculated_ml": 0.0, "vol_ml": 0.0,
    "multiplication": 1.0, "rate_ml_hr": 0.0, "concentration_mg_ml": 0.0,
    "target_conc": 0.0, "stock_conc": 0.0,
    "loading_dose_ml": 0.0, "maintenance_dose_ml": 0.0,
    "infusion_rate_ml_hr": 0.0, "total_volume_ml": 0.0, "dilution_volume_ml": 0.0,
}

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

            # templates/index.html -> docs/index.html (ไม่สร้างโฟลเดอร์ซ้อน)
            if str(rel_path) == "index.html":
                out_path = pathlib.Path(OUTPUT_DIR) / "index.html"
            else:
                out_path.parent.mkdir(parents=True, exist_ok=True)

            tmpl = env.get_template(str(rel_path))
            html = tmpl.render(**BASE_CTX)

            # safety nets: กัน .html.html และ ././ ที่หลุดมาจาก template
            html = html.replace(".html.html", ".html")
            html = html.replace('href="././', 'href="./')
            html = html.replace('href=".//', 'href="./')

            with open(out_path, "w", encoding="utf-8") as fp:
                fp.write(html)
            print("rendered ->", out_path)

if __name__ == "__main__":
    render_all()
