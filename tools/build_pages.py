# tools/build_pages.py (ส่วนสำคัญ)
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TPL  = ROOT / "templates"
DOCS = ROOT / "docs"

env = Environment(loader=FileSystemLoader(str(TPL)), autoescape=True)

# ไฟล์ที่จะ build -> output
PAGES = [
    ("index.html",                 "index.html"),
    ("pma_template.html",          "pma.html"),
    ("compatibility_result.html",  "compatibility.html"),
    ("Medication_administration.html", "admin.html"),
    ("time_management.html",       "time.html"),
    ("404.html",                   "404.html"),
]

def render(src, dst):
    t = env.get_template(src)
    html = t.render(static_build=True)   # <<< สำคัญ
    (DOCS / dst).write_text(html, encoding="utf-8")

if __name__ == "__main__":
    DOCS.mkdir(exist_ok=True)
    # ก็อป assets ที่ต้องใช้ (ถ้ายัง)
    (DOCS / "static").mkdir(exist_ok=True)
    # service worker/manifest อยู่ตรงนี้ (ถ้ามี)
    for s in ["static/service-worker.js", "static/manifest.webmanifest"]:
        p = ROOT / s
        if p.exists():
            (DOCS / s).parent.mkdir(parents=True, exist_ok=True)
            (DOCS / s).write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
    for src, dst in PAGES:
        render(src, dst)
    print("Built docs/ from templates ✅")
