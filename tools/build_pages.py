# tools/build_pages.py
import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parent.parent
TPL_DIR = ROOT / "templates"
DOCS_DIR = ROOT / "docs"
STATIC_SRC = ROOT / "static"
STATIC_DST = DOCS_DIR / "static"

# map ชื่อ endpoint ใน Flask → ไฟล์ปลายทางแบบ static
ROUTE_TO_HTML = {
    "calculate_pma_route": "pma.html",
    "compatibility_page": "compatibility.html",
    "medication_administration": "admin.html",
    "time_management_route": "time.html",
    # ถ้ามี route อื่น ให้เติมที่นี่
}

def url_for(name, **kwargs):
    """แทนที่ flask.url_for ด้วยลิงก์ relative เป็นไฟล์ .html"""
    return f"./{ROUTE_TO_HTML.get(name, 'index.html')}"

def main():
    env = Environment(
        loader=FileSystemLoader(str(TPL_DIR)),
        autoescape=True,
    )
    # ส่งฟังก์ชัน url_for เข้าไปเหมือน Flask
    env.globals["url_for"] = url_for

    # 1) เรนเดอร์ index.html จาก templates (ที่ extend base.html ได้เลย)
    template = env.get_template("index.html")
    html = template.render()
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    (DOCS_DIR / "index.html").write_text(html, encoding="utf-8")

    # 2) ทำไฟล์เปล่าหน้าอื่นกัน 404 (หรือจะเรนเดอร์จริงก็ได้)
    for fname in ROUTE_TO_HTML.values():
        p = DOCS_DIR / fname
        if not p.exists():
            p.write_text(
                "<!doctype html><meta charset=utf-8>"
                f"<title>{fname}</title><p><a href='./'>กลับหน้าแรก</a></p>",
                encoding="utf-8"
            )

    # 3) คัดลอก asset PWA → docs/static (ถ้ายังไม่มี)
    STATIC_DST.mkdir(parents=True, exist_ok=True)
    # ไฟล์หลัก ๆ
    for rel in ["service-worker.js", "manifest.webmanifest"]:
        src = STATIC_SRC / rel
        if src.exists():
            dst = STATIC_DST / rel
            dst.write_bytes(src.read_bytes())

    # ไอคอน
    icons_src = STATIC_SRC / "icons"
    icons_dst = STATIC_DST / "icons"
    if icons_src.exists():
        icons_dst.mkdir(exist_ok=True)
        for f in icons_src.iterdir():
            if f.is_file():
                (icons_dst / f.name).write_bytes(f.read_bytes())

    # 4) สร้าง 404.html กัน refresh แล้ว 404
    (DOCS_DIR / "404.html").write_text(
        "<!doctype html><meta charset=utf-8><title>Not Found</title>"
        "<h1>Page Not Found</h1><p><a href='./'>Home</a></p>",
        encoding="utf-8"
    )

    print("Built docs/ from templates/ → docs/index.html + static assets ✅")

if __name__ == "__main__":
    main()
