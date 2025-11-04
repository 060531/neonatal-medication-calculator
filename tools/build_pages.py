from pathlib import Path
from datetime import datetime
import shutil

from jinja2 import Environment, FileSystemLoader, Undefined

# ---------- PATHS ----------
ROOT   = Path(__file__).resolve().parents[1]
TPL    = ROOT / "templates"
DOCS   = ROOT / "docs"
STATIC = ROOT / "static"

DOCS.mkdir(exist_ok=True)

# ---------- Undefined -> 0 (safe math) ----------
class ZeroUndefined(Undefined):
    def __int__(self): return 0
    def __float__(self): return 0.0
    def __str__(self): return ""
    # arithmetic
    def __add__(self, other): return other
    def __radd__(self, other): return other
    def __sub__(self, other): return 0
    def __rsub__(self, other): return other
    def __mul__(self, other): return 0
    def __rmul__(self, other): return 0
    def __truediv__(self, other): return 0
    def __rtruediv__(self, other): return 0
    def __floordiv__(self, other): return 0
    def __rfloordiv__(self, other): return 0
    def __pow__(self, other): return 0
    def __rpow__(self, other): return 0

# ---------- Jinja env ----------
env = Environment(
    loader=FileSystemLoader(str(TPL)),
    autoescape=False,
    undefined=ZeroUndefined,          # ป้องกัน 'UndefinedError'
)

# ฟิลเตอร์เสริม: nz(x) -> float หรือ 0.0 (กันค่า None/ว่าง)
def nz(x):
    try:
        return float(x)
    except Exception:
        return 0.0
env.filters["nz"] = nz

# ---------- url_for stub (offline build) ----------
ROUTE_MAP = {
    "index": "index.html",
    "calculate_pma_route": "pma_template.html",
    "compatibility_page": "compatibility.html",
    "medication_administration": "Medication_administration.html",
    "time_management_route": "time_management.html",
    "scan": "scan.html",
    "scan_server": "scan_server.html",
    # เพิ่ม route ชื่ออื่นๆ ตามที่มีในโปรเจกต์ได้
}
def url_for_stub(endpoint, **values):
    if endpoint == "static":
        return f"./static/{values.get('filename','')}"
    return f"./{ROUTE_MAP.get(endpoint, endpoint + '.html')}"
env.globals["url_for"] = url_for_stub

# ---------- build steps ----------
def render_one(template_name: str):
    tpl = env.get_template(template_name)
    html = tpl.render(
        static_build=True,                               # ธงให้ template ใช้ path แบบ static
        update_date=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )
    out = DOCS / template_name
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"✓ {template_name} -> {out}")

def copy_static():
    dst = DOCS / "static"
    dst.mkdir(parents=True, exist_ok=True)
    if STATIC.exists():
        for p in STATIC.rglob("*"):
            to = dst / p.relative_to(STATIC)
            if p.is_dir():
                to.mkdir(parents=True, exist_ok=True)
            else:
                to.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, to)
    print("✓ static/ -> docs/static/")

def main():
    # เรนเดอร์ทุกไฟล์ *.html ใน templates (ยกเว้น base.html และชื่อขึ้นต้นด้วย '_')
    for p in sorted(TPL.glob("*.html")):
        name = p.name
        if name == "base.html" or name.startswith("_"):
            continue
        try:
            render_one(name)
        except Exception as e:
            # ไม่ล้มทั้งงาน: log แล้วไปต่อ (ถ้ามีหน้าไหน error)
            print(f"✗ skip {name} : {e!r}")
    copy_static()
    print("Built docs/ from templates ✅")

if __name__ == "__main__":
    main()
