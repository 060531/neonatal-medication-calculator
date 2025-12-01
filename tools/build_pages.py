from pathlib import Path
from datetime import datetime, date
import os
import argparse
import shutil
import json

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
default_context = {
    "bw": 0, "age_days": 0, "ga_weeks": 0, "pma_weeks": 0, "pma_days": 0,
    "dose": 0, "dose_mgkg": 0, "volume": 0, "rate": 0,
    "final_result_1": 0, "final_result_2": 0,
    "result": 0, "result2": 0, "infusion_rate": 0, "dilution": 0,
}

# ---------- update date picker ----------
from typing import Optional

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
    html = tpl.render(
        static_build=True,
        update_date=update_date_str,
        UPDATE_DATE=update_date_str,
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
