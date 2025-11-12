# tools/jinja_render.py
# -*- coding: utf-8 -*-
import os
import pathlib
from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATES_DIR = "templates"
OUTPUT_DIR = "docs"

# แผนที่เส้นทางสำหรับแทน u('route_name') -> ไฟล์ปลายทางใน docs
URL_MAP = {
    "index": "./index.html",
    "medication_administration": "./index.html",  # ปุ่ม back ให้กลับหน้าหลัก static
}

def u(name: str) -> str:
    return URL_MAP.get(name, "./index.html")

# สร้าง Jinja Environment
env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html", "xml"]),
)

# Context เริ่มต้น (ทำให้เงื่อนไขในเทมเพลตไม่พังเวลา prerender)
BASE_CTX = {
    "dose": None,
    "result_ml": None,
    "multiplication": None,
    "error": None,
    "content_extra": None,
    "UPDATE_DATE": "",
    "u": u,        # ฟังก์ชันแทน url_for
    "order": {},   # ป้องกัน {{ order|tojson }} พังจาก Undefined
}

def ensure_docs_dir():
    """เตรียม docs/ และไฟล์ .nojekyll ให้พร้อม"""
    out = pathlib.Path(OUTPUT_DIR)
    out.mkdir(parents=True, exist_ok=True)
    nojekyll = out / ".nojekyll"
    if not nojekyll.exists():
        nojekyll.write_text("", encoding="utf-8")

def render_all():
    """เรนเดอร์ทุกไฟล์ .html ใน templates/ ไปยัง docs/ ด้วย BASE_CTX"""
    ensure_docs_dir()

    for root, _, files in os.walk(TEMPLATES_DIR):
        for fname in files:
            if not fname.endswith(".html"):
                continue
            # ข้ามไฟล์ส่วนประกอบ/พาร์เชียลที่ตั้งชื่อขึ้นต้นด้วย '_' หากมี
            if fname.startswith("_"):
                continue

            src_path = pathlib.Path(root) / fname
            rel_path = src_path.relative_to(TEMPLATES_DIR)  # path ภายใต้ templates/
            out_path = pathlib.Path(OUTPUT_DIR) / rel_path  # path ปลายทางใน docs/

            # ให้มีโฟลเดอร์ย่อยครบก่อนเขียนไฟล์
            out_path.parent.mkdir(parents=True, exist_ok=True)

            # โหลดเทมเพลตตาม path สัมพัทธ์
            tmpl = env.get_template(str(rel_path))

            # เรนเดอร์ด้วย context เริ่มต้น
            html = tmpl.render(**BASE_CTX)

            # เคสพิเศษ: ถ้าไฟล์คือ templates/index.html → ต้องการเป็น docs/index.html
            if str(rel_path) == "index.html":
                out_path = pathlib.Path(OUTPUT_DIR) / "index.html"

            # เขียนไฟล์ผลลัพธ์
            with open(out_path, "w", encoding="utf-8") as fp:
                fp.write(html)

            print("rendered ->", out_path)

if __name__ == "__main__":
    render_all()
