from pathlib import Path
from datetime import datetime
import shutil, json
from jinja2 import Environment, FileSystemLoader, Undefined

# ---------- PATHS ----------
ROOT   = Path(__file__).resolve().parents[1]
TPL    = ROOT / "templates"
DOCS   = ROOT / "docs"
STATIC = ROOT / "static"
DOCS.mkdir(exist_ok=True)

# ---------- Undefined -> 0 (safe math/str/round) ----------
class ZeroUndefined(Undefined):
    def __int__(self): return 0
    def __float__(self): return 0.0
    def __str__(self): return ""
    # arithmetic fallbacks
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
    def __round__(self, n=0): 
        try:
            return round(float(0.0), n)
        except Exception:
            return 0

# ---------- Jinja env ----------
env = Environment(
    loader=FileSystemLoader(str(TPL)),
    autoescape=False,
    undefined=ZeroUndefined,
)

# ---------- Filters ----------
def nz(x):
    try:
        if x is None: return 0.0
        return float(x)
    except Exception:
        return 0.0

def safe_round(value, ndigits=0):
    # แทนที่ฟิลเตอร์ round ของ Jinja เพื่อกันค่า None/Undefined
    try:
        return round(float(nz(value)), int(ndigits))
    except Exception:
        return 0

def tojson_safe(value):
    def default(o):
        # รับมือ ZeroUndefined/Undefined/อื่น ๆ
        if isinstance(o, ZeroUndefined):
            return 0
        try:
            str(o)
            return str(o)
        except Exception:
            return None
    return json.dumps(value, ensure_ascii=False, default=default)

env.filters["nz"] = nz
env.filters["round"] = safe_round          # override ฟิลเตอร์ round เดิม
env.filters["tojson"] = tojson_safe        # override tojson ให้ปลอดภัย

# ---------- url_for stub (offline build) ----------
ROUTE_MAP = {
    "index": "index.html",
    "calculate_pma_route": "pma_template.html",
    "compatibility_page": "compatibility.html",
    "medication_administration": "Medication_administration.html",
    "time_management_route": "time_management.html",
    "scan": "scan.html",
    "scan_server": "scan_server.html",
    # เติมเพิ่มได้หากมี endpoint อื่น
}
def url_for_stub(endpoint, **values):
    if endpoint == "static":
        return f"./static/{values.get('filename','')}"
    return f"./{ROUTE_MAP.get(endpoint, endpoint + '.html')}"
env.globals["url_for"] = url_for_stub

# ---------- ค่า default สำหรับ template ที่ต้องมีตัวเลขใช้คำนวณ ----------
default_context = {
    # ตัวแปร dosing ทั่วไป
    "bw": 0, "age_days": 0, "ga_weeks": 0, "pma_weeks": 0, "pma_days": 0,
    "dose": 0, "dose_mgkg": 0, "volume": 0, "rate": 0,
    "final_result_1": 0, "final_result_2": 0,
    # เผื่อชื่ออื่น ๆ ที่ใช้บ่อย
    "result": 0, "result2": 0, "infusion_rate": 0, "dilution": 0,
}

# ---------- build steps ----------
def render_one(template_name: str):
    tpl = env.get_template(template_name)
    html = tpl.render(
        static_build=True,
        update_date=datetime.now().strftime("%Y-%m-%d %H:%M"),
        **default_context,       # อัด default context กัน undefined
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
    # ล้าง placeholder เก่า ๆ ใน docs ถ้าต้องการ (คอมเมนต์/ยกเลิกได้)
    # for old in DOCS.glob("*.html"): old.unlink(missing_ok=True)

    # เรนเดอร์ทุกไฟล์ *.html ยกเว้น base.html และที่ขึ้นต้นด้วย "_"
    for p in sorted(TPL.glob("*.html")):
        name = p.name
        if name == "base.html" or name.startswith("_"):
            continue
        try:
            render_one(name)
        except Exception as e:
            print(f"✗ skip {name} : {e!r}")
    copy_static()
    print("Built docs/ from templates ✅")

if __name__ == "__main__":
    main()
