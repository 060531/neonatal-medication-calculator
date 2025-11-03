from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
TPL  = ROOT / "templates"
DOCS = ROOT / "docs"
STATIC_SRC = ROOT / "static"
STATIC_DST = DOCS / "static"

env = Environment(
    loader=FileSystemLoader(str(TPL)),
    autoescape=False
)

def render_one(name: str):
    tpl = env.get_template(name)
    html = tpl.render(
        static_build=True,
        update_date=datetime.now().strftime("%Y-%m-%d %H:%M")
    )
    out = DOCS / name
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"✓ {name} -> {out}")

def copy_static():
    STATIC_DST.mkdir(parents=True, exist_ok=True)
    if STATIC_SRC.exists():
        # คัดลอกทั้งโฟลเดอร์ static ไป docs/static (ทับไฟล์เก่า)
        for p in STATIC_SRC.rglob("*"):
            rel = p.relative_to(STATIC_SRC)
            dest = STATIC_DST / rel
            if p.is_dir():
                dest.mkdir(parents=True, exist_ok=True)
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, dest)
    print("✓ copied static/ -> docs/static/")

def main():
    DOCS.mkdir(exist_ok=True)
    # เรนเดอร์ทุกไฟล์ .html ยกเว้น base.html และไฟล์ที่ขึ้นต้นด้วย _
    for p in sorted(TPL.glob("*.html")):
        name = p.name
        if name == "base.html" or name.startswith("_"):
            continue
        render_one(name)
    copy_static()
    print("Built docs/ from templates ✅")

if __name__ == "__main__":
    main()
