from pathlib import Path
from datetime import datetime
import os
import argparse
import shutil
import json
from typing import Optional

from jinja2 import Environment, FileSystemLoader, Undefined

# ---------- PATHS ----------
ROOT   = Path(__file__).resolve().parents[1]
TPL    = ROOT / "templates"
DOCS   = ROOT / "docs"
STATIC = ROOT / "static"
DOCS.mkdir(exist_ok=True)

# ---------- meds catalog (single source of truth) ----------
MEDS_CATALOG = ROOT / "data" / "meds_catalog.json"

# ✅ สำคัญ: บังคับ state เริ่มต้นให้ “ยังไม่คำนวณ” (None) เพื่อไม่ให้ template render ผลลัพธ์ออกมาใน GitHub Pages
EMPTY_CALC_STATE = {
    # common inputs/outputs across pages
    "dose": None,
    "dose_mgkg": None,
    "volume": None,
    "rate": None,
    "infusion_rate": None,
    "dilution": None,

    "result": None,
    "result2": None,
    "result_ml": None,

    "final_result": None,
    "final_result_1": None,
    "final_result_2": None,

    "multiplication": None,
    "target_total": None,
    "diluent_to_add": None,

    "msg_block": None,
    "content_extra": None,
    "error": None,
}

def load_meds_catalog():
    if not MEDS_CATALOG.exists():
        raise FileNotFoundError(f"Missing {MEDS_CATALOG} (create meds_catalog.json first)")
    meds = json.loads(MEDS_CATALOG.read_text(encoding="utf-8"))

    # validation กันพังเงียบ ๆ เวลาเพิ่มข้อมูล
    seen = set()
    for i, m in enumerate(meds, start=1):
        label = (m.get("label") or "").strip()
        ep = (m.get("endpoint") or "").strip()
        if not label or not ep:
            raise ValueError(f"[meds_catalog] item#{i} ต้องมี label และ endpoint")
        if ep in seen:
            raise ValueError(f"[meds_catalog] endpoint ซ้ำ: {ep}")
        seen.add(ep)
        # ensure danger exists
        if "danger" not in m:
            m["danger"] = False
    return meds

def group_meds_by_letter(meds):
    groups = {}
    for m in meds:
        label = (m.get("label") or "").strip()
        ch = (label[0].upper() if label else "#")
        if not ("A" <= ch <= "Z"):
            ch = "#"
        groups.setdefault(ch, []).append(m)

    for ch, items in groups.items():
        items.sort(key=lambda x: (x.get("label") or "").lower())

    ordered = {ch: groups[ch] for ch in sorted(k for k in groups.keys() if k != "#")}
    if "#" in groups:
        ordered["#"] = groups["#"]
    return ordered

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
        return 0

# ---------- Jinja env ----------
env = Environment(
    loader=FileSystemLoader(str(TPL)),
    autoescape=False,
    undefined=ZeroUndefined,
)

# ---------- Filters / Helpers ----------
def nz(x, default=0.0):
    """Null-safe numeric convert; supports nz(x, 0)"""
    if isinstance(x, ZeroUndefined):
        return default
    if x is None or x == "":
        return default
    try:
        return float(x)
    except Exception:
        return default

def safe_round(value, ndigits=0):
    try:
        return round(float(nz(value, 0.0)), int(ndigits))
    except Exception:
        return 0

def fmt(value, ndigits=2, default=""):
    if isinstance(value, ZeroUndefined) or value is None or value == "":
        return default
    try:
        return f"{float(value):.{int(ndigits)}f}"
    except Exception:
        return str(value)

def fmt_int(value, default=""):
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
env.filters["round"] = safe_round
env.filters["tojson"] = tojson_safe
env.filters["fmt"] = fmt
env.filters["fmt_int"] = fmt_int

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
}

def _normalize_endpoint_name(endpoint: str) -> str:
    if not isinstance(endpoint, str):
        return "index"
    if "." in endpoint:
        endpoint = endpoint.split(".")[-1]
    return endpoint.strip()

def resolve_endpoint(endpoint: str, **values) -> str:
    ep = _normalize_endpoint_name(endpoint)

    if ep == "static":
        return f"./static/{values.get('filename','')}".rstrip("/")

    if ep in ROUTE_MAP:
        return f"./{ROUTE_MAP[ep]}"

    if ep.endswith(".html"):
        return f"./{ep}"

    if ep.endswith("_route"):
        return f"./{ep[:-6]}.html"

    if ep.endswith("_page"):
        return f"./{ep[:-5]}.html"

    return f"./{ep}.html"

def url_for_stub(endpoint, **values):
    return resolve_endpoint(endpoint, **values)

def u(endpoint, **values):
    return resolve_endpoint(endpoint, **values)

env.globals["url_for"] = url_for_stub
env.globals["u"] = u
env.globals["resolve_endpoint"] = resolve_endpoint
env.globals["nz"] = nz

# ---------- default context ----------
# NOTE: ค่าพวก calc result/dose ไม่ควรถูกตั้งเป็น 0 ที่นี่ หากไม่อยากให้หน้า static แสดงผลลัพธ์ตั้งแต่แรก
# แต่เรายังเก็บค่าพื้นฐานพวก BW/age ไว้ได้
default_context = {
    "bw": 0, "age_days": 0, "ga_weeks": 0, "pma_weeks": 0, "pma_days": 0,
}

# ---------- update date picker ----------
def pick_update_date(cli_value: Optional[str] = None) -> str:
    """
    priority:
    1) --update-date "..."
    2) ENV UPDATE_DATE
    3) now "YYYY-MM-DD HH:MM"
    """
    if cli_value and cli_value.strip():
        return cli_value.strip()
    env_v = os.getenv("UPDATE_DATE")
    if env_v and env_v.strip():
        return env_v.strip()
    return datetime.now().strftime("%Y-%m-%d %H:%M")

# ---------- build steps ----------
def render_one(template_name: str, update_date_str: str):
    tpl = env.get_template(template_name)

    # base ctx
    ctx = dict(
        static_build=True,
        update_date=update_date_str,
        UPDATE_DATE=update_date_str,
        **default_context,
    )

    # inject เฉพาะหน้าที่ต้องใช้ข้อมูล dynamic ตอน build
    if template_name in ("Medication_administration.html", "medication_administration.html"):
        meds = load_meds_catalog()
        groups = group_meds_by_letter(meds)
        letters = list(groups.keys())
        ctx.update({"meds": meds, "groups": groups, "letters": letters})

    # ✅ สำคัญที่สุด: บังคับให้ state คำนวณเป็น None ก่อน render (เหมือนเข้า Flask ครั้งแรก)
    ctx.update(EMPTY_CALC_STATE)

    html = tpl.render(**ctx)

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
    parser = argparse.ArgumentParser()
    parser.add_argument("--update-date", dest="update_date", default=None,
                        help='Override update date shown in footer, e.g. "2025-12-01" or "2025-12-01 18:30"')
    args = parser.parse_args()

    update_date_str = pick_update_date(args.update_date)

    for p in sorted(TPL.glob("*.html")):
        name = p.name
        if name == "base.html" or name.startswith("_"):
            continue
        try:
            render_one(name, update_date_str)
        except Exception as e:
            print(f"✗ skip {name} : {e!r}")

    copy_static()
    print(f"Built docs/ from templates ✅ (update_date={update_date_str})")

if __name__ == "__main__":
    main()
