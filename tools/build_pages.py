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

# ---------- Filters / Helpers ----------
def nz(x, default=0.0):
    """
    Null-safe numeric convert:
    - nz(None) -> default
    - nz("1.2") -> 1.2
    - nz(value, default) supports templates that call nz(x, 0)
    """
    if isinstance(x, ZeroUndefined):
        return default
    if x is None or x == "":
        return default
    try:
        return float(x)
    except Exception:
        return default

def safe_round(value, ndigits=0):
    # override Jinja round เพื่อกัน None/Undefined
    try:
        return round(float(nz(value, 0.0)), int(ndigits))
    except Exception:
        return 0

def fmt(value, ndigits=2, default=""):
    """format float with fixed decimals; safe for None/Undefined/empty"""
    if isinstance(value, ZeroUndefined) or value is None or value == "":
        return default
    try:
        return f"{float(value):.{int(ndigits)}f}"
    except Exception:
        return str(value)

def fmt_int(value, default=""):
    """format int; safe for None/Undefined/empty"""
    if isinstance(value, ZeroUndefined) or value is None or value == "":
        return default
    try:
        return str(int(round(float(value))))
    except Exception:
        try:
            return str(int(value))
        except Exception:
            return str(value)

def tojson_safe(value):
    def default(o):
        if isinstance(o, (ZeroUndefined, Undefined)):
            return 0
        try:
            return str(o)
        except Exception:
            return None
    return json.dumps(value, ensure_ascii=False, default=default)

env.filters["nz"] = nz
env.filters["round"] = safe_round          # override round
env.filters["tojson"] = tojson_safe        # override tojson
env.filters["fmt"] = fmt                   # add fmt
env.filters["fmt_int"] = fmt_int           # add fmt_int

# ---------- url_for / u / resolve_endpoint (offline build) ----------
ROUTE_MAP = {
    "index": "index.html",
    "calculate_pma_route": "pma_template.html",
    "compatibility_page": "compatibility.html",
    "compatibility_result": "compatibility_result.html",
    "medication_administration": "Medication_administration.html",
    "time_management_route": "time_management.html",
    "scan": "scan.html",
    "scan_server": "scan_server.html",
    # เติมแบบเฉพาะกิจได้ แต่มี heuristic กันพังอยู่แล้ว
}

def _normalize_endpoint_name(endpoint: str) -> str:
    # รองรับ blueprint.endpoint -> endpoint
    if not isinstance(endpoint, str):
        return "index"
    if "." in endpoint:
        endpoint = endpoint.split(".")[-1]
    return endpoint.strip()

def resolve_endpoint(endpoint: str, **values) -> str:
    """
    Resolve flask-like endpoint to html path for GitHub Pages.
    Heuristics:
    - static -> ./static/filename
    - endpoint in ROUTE_MAP -> ./<mapped>
    - already *.html -> as-is
    - endswith _route -> ./<name>.html
    - otherwise -> ./<endpoint>.html
    """
    ep = _normalize_endpoint_name(endpoint)

    if ep == "static":
        return f"./static/{values.get('filename','')}".rstrip("/")

    # ตรงแมพ
    if ep in ROUTE_MAP:
        return f"./{ROUTE_MAP[ep]}"

    # ถ้าเป็นไฟล์อยู่แล้ว
    if ep.endswith(".html"):
        return f"./{ep}"

    # pattern: xxx_route -> xxx.html
    if ep.endswith("_route"):
        return f"./{ep[:-6]}.html"

    # เผื่อชื่อที่ลงท้ายด้วย _page -> .html
    if ep.endswith("_page"):
        return f"./{ep[:-5]}.html"

    return f"./{ep}.html"

def url_for_stub(endpoint, **values):
    return resolve_endpoint(endpoint, **values)

def u(endpoint, **values):
    # ให้ templates ใช้ {{ u('amikin_route') }} ได้
    return resolve_endpoint(endpoint, **values)

env.globals["url_for"] = url_for_stub
env.globals["u"] = u
env.globals["resolve_endpoint"] = resolve_endpoint
env.globals["nz"] = nz  # เผื่อบางที่เรียกเป็น function ไม่ผ่าน filter

# ---------- ค่า default สำหรับ template ที่ต้องมีตัวเลขใช้คำนวณ ----------
default_context = {
    "bw": 0, "age_days": 0, "ga_weeks": 0, "pma_weeks": 0, "pma_days": 0,
    "dose": 0, "dose_mgkg": 0, "volume": 0, "rate": 0,
    "final_result_1": 0, "final_result_2": 0,
    "result": 0, "result2": 0, "infusion_rate": 0, "dilution": 0,
}

# ---------- build steps ----------
def render_one(template_name: str):
    tpl = env.get_template(template_name)
    html = tpl.render(
        static_build=True,
        update_date=datetime.now().strftime("%Y-%m-%d %H:%M"),
        **default_context,
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
