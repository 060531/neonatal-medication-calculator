# tools/jinja_render.py
# -*- coding: utf-8 -*-
import os
import shutil
import pathlib
from datetime import datetime
from collections import defaultdict

from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATES_DIR = "templates"
STATIC_DIR = "static"
OUTPUT_DIR = "docs"
OUTPUT_STATIC_DIR = f"{OUTPUT_DIR}/static"

# ---------- URL mapping ----------
# หมายเหตุ: เก็บเป็น "ชื่อไฟล์" (ไม่ต้องใส่ ./) จะนิ่งที่สุด
URL_MAP = {
    # core pages
    "index": "index.html",
    "pma_template": "pma_template.html",
    "compatibility": "compatibility.html",
    "compatibility_result": "compatibility_result.html",
    "Medication_administration": "Medication_administration.html",
    "time_management": "time_management.html",
    "run_time": "run_time.html",
    "run_time_stop": "run_time_stop.html",
    "verify_result": "verify_result.html",

    # examples / specific pages
    "vancomycin": "vancomycin.html",
    "insulin": "insulin.html",
    "fentanyl_continuous": "fentanyl_continuous.html",
    "penicillin_g_sodium": "penicillin_g_sodium.html",
    "scan_server": "scan_server.html",

    # special
    "static": "static/",

    # === endpoints ที่เคยใช้ร่วมกับ Flask ===
    "calculate_pma_page": "pma_template.html",
    "core.compatibility_page": "compatibility.html",
    "core.time_management_route": "time_management.html",
    "medication_administration": "Medication_administration.html",

    # ✅ สำคัญ: ปุ่ม New check จากหน้า result ให้กลับไปหน้า compatibility
    "compat.compat_index": "compatibility.html",
}

# >>> รายการยา (ให้แม็ป endpoint -> หน้า .html อัตโนมัติ)
MEDS = [
    {"label": "Acyclovir", "endpoint": "acyclovir_route"},
    {"label": "Amikacin", "endpoint": "amikin_route"},
    {"label": "Aminophylline", "endpoint": "aminophylline_route", "danger": True},
    {"label": "Amoxicillin / Clavimoxy", "endpoint": "amoxicillin_clavimoxy_route"},
    {"label": "Amphotericin B", "endpoint": "amphotericinB_route"},
    {"label": "Ampicillin", "endpoint": "ampicillin_route"},
    {"label": "Benzathine penicillin G", "endpoint": "benzathine_penicillin_g_route"},
    {"label": "Cefazolin", "endpoint": "cefazolin_route"},
    {"label": "Cefotaxime", "endpoint": "cefotaxime_route"},
    {"label": "Ceftazidime", "endpoint": "ceftazidime_route"},
    {"label": "Ciprofloxacin", "endpoint": "ciprofloxacin_route"},
    {"label": "Clindamycin", "endpoint": "clindamycin_route"},
    {"label": "Cloxacillin", "endpoint": "cloxacillin_route"},
    {"label": "Colistin", "endpoint": "colistin_route"},
    {"label": "Dexamethasone", "endpoint": "dexamethasone_route"},
    {"label": "Dobutamine", "endpoint": "dobutamine_route", "danger": True},
    {"label": "Dopamine", "endpoint": "dopamine_route", "danger": True},
    {"label": "Fentanyl", "endpoint": "fentanyl_route", "danger": True},
    {"label": "Furosemide", "endpoint": "furosemide_route"},
    {"label": "Gentamicin", "endpoint": "gentamicin_route"},
    {"label": "Hydrocortisone", "endpoint": "hydrocortisone_route"},
    {"label": "Insulin Human Regular", "endpoint": "insulin_route"},
    {"label": "Levofloxacin", "endpoint": "levofloxacin_route"},
    {"label": "Meropenem", "endpoint": "meropenem_route"},
    {"label": "Metronidazole (Flagyl)", "endpoint": "metronidazole"},
    {"label": "Midazolam", "endpoint": "midazolam_route", "danger": True},
    {"label": "Midazolam + Fentanyl", "endpoint": "midazolam_fentanyl_route", "danger": True},
    {"label": "Morphine", "endpoint": "morphine_route", "danger": True},
    {"label": "Nimbex (Cisatracurium)", "endpoint": "nimbex_route"},
    {"label": "Omeprazole", "endpoint": "omeprazole_route"},
    {"label": "Penicillin G sodium", "endpoint": "penicillin_g_sodium_route"},
    {"label": "Phenobarbital", "endpoint": "phenobarbital_route"},
    {"label": "Phenytoin (Dilantin)", "endpoint": "phenytoin_route"},
    {"label": "Remdesivir", "endpoint": "remdesivir_route"},
    {"label": "Sul-am®", "endpoint": "sul_am_route"},
    {"label": "Sulbactam", "endpoint": "sulbactam_route"},
    {"label": "Sulperazone", "endpoint": "sulperazone_route"},
    {"label": "Tazocin", "endpoint": "tazocin_route"},
    {"label": "Unasyn", "endpoint": "unasyn_route"},
    {"label": "Vancomycin", "endpoint": "vancomycin_route"},
]

# เติม endpoint->html ของยาทั้งหมด
for m in MEDS:
    ep = m["endpoint"]
    if ep.endswith("_route"):
        page = ep[:-6] + ".html"
    else:
        page = ep + ".html"
    URL_MAP.setdefault(ep, page)

# ---------- Helpers for URLs ----------
def _strip_leading_dots(path: str) -> str:
    s = (path or "").strip()
    while s.startswith("./"):
        s = s[2:]
    return s

def _ensure_html_file(name_or_file: str) -> str:
    s = _strip_leading_dots(name_or_file)
    if not s:
        return "index.html"
    if s.endswith("/"):
        return s
    return s if s.endswith(".html") else f"{s}.html"

def u(name: str, **kwargs) -> str:
    """
    ใช้แทน url_for สำหรับ static build:
    - u("index") -> ./index.html
    - u("static", filename="style.css") -> ./static/style.css
    - u("compat.compat_index") -> ./compatibility.html
    """
    if not name:
        return "./index.html"

    if name == "static":
        fn = kwargs.get("filename", "") or ""
        return f"./static/{fn}" if fn else "./static/"

    target = URL_MAP.get(name, f"{name}.html")
    target = _ensure_html_file(target)
    return f"./{_strip_leading_dots(target)}"

def static_url(endpoint: str, filename: str = "") -> str:
    # ให้ template ที่เคยเรียก url_for('static', filename='...') ยังทำงานได้
    if endpoint == "static":
        return u("static", filename=filename)
    return u(endpoint)

def resolve_endpoint(endpoint: str) -> str:
    if not endpoint:
        return "./index.html"
    if isinstance(endpoint, str) and endpoint.startswith(("http://", "https://", "#")):
        return endpoint
    return u(endpoint)

# ---------- Safe numeric helpers & filters ----------
def nz(v, default=0):
    try:
        return default if v is None else v
    except Exception:
        return default

def fmt(v, nd=2):
    try:
        if v is None or v == "":
            return ""
        x = float(v)
    except Exception:
        return ""
    try:
        nd = int(nd)
    except Exception:
        nd = 2
    return f"{x:.{nd}f}"

def fmt_int(v):
    try:
        if v is None or v == "":
            return ""
        return f"{int(round(float(v)))}"
    except Exception:
        return ""

def sig(v, n=3):
    try:
        if v is None or v == "":
            return ""
        x = float(v)
    except Exception:
        return ""
    try:
        n = int(n)
    except Exception:
        n = 3
    return f"{x:.{n}g}"

def safe_fmt(value, fmt_pattern="%.2f"):
    try:
        return fmt_pattern % (value,)
    except Exception:
        try:
            return fmt_pattern % (0,)
        except Exception:
            return str(value)

# ---------- Jinja env ----------
env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html", "xml"]),
)

env.filters["nz"] = nz
env.filters["fmt"] = fmt
env.filters["fmt2"] = lambda v: fmt(v, 2)
env.filters["fmt_int"] = fmt_int
env.filters["sig"] = sig
env.filters["safe_fmt"] = safe_fmt

env.globals.update({
    "u": u,
    "url_for": static_url,       # ทำให้ template ที่ใช้ url_for ยังใช้งานได้ใน static
    "static_build": True,
    "resolve_endpoint": resolve_endpoint,
})

def build_med_ctx():
    groups = defaultdict(list)
    for m in MEDS:
        groups[m["label"][0].upper()].append(m)
    for k in list(groups.keys()):
        groups[k].sort(key=lambda x: x["label"].lower())
    groups = dict(sorted(groups.items()))
    letters = list(groups.keys())
    return {"meds": MEDS, "groups": groups, "letters": letters}

# ---------- Base context ----------
_NOW = datetime.now().strftime("%Y-%m-%d %H:%M")
BASE_CTX = {
    "error": None,
    "content_extra": None,
    "UPDATE_DATE": os.environ.get("UPDATE_DATE", _NOW),
    "update_date": os.environ.get("update_date", _NOW),

    "u": u,
    "static_build": True,
    "request": {"path": "/"},
    "session": {},
    "order": {},

    # สำหรับ compatibility.html (+ result) ให้มี dropdown ได้
    "groups": {},

    # defaults used in drug pages
    "bw": None,
    "pma_weeks": None,
    "pma_days": None,
    "postnatal_days": None,
    "dose": None,
    "dose_ml": None,
    "dose_mgkg": None,
    "result_ml": None,
    "multiplication": None,

    # ตัวเลขที่บาง template format(...) ตรง ๆ
    "min_dose": 0.0,
    "max_dose": 0.0,
    "loading_dose": 0.0,
    "maintenance_dose_min": 0.0,
    "maintenance_dose_max": 0.0,
    "dose_min_mg": 0.0,
    "dose_max_mg": 0.0,
    "dose_min_per_kg": 0.0,
    "dose_max_per_kg": 0.0,
    "dose_per_kg": 0.0,
    "total_dose": 0.0,
    "actual_dose": 0.0,
    "interval": "",
}

def ensure_docs_dir():
    out = pathlib.Path(OUTPUT_DIR)
    out.mkdir(parents=True, exist_ok=True)
    (out / ".nojekyll").write_text("", encoding="utf-8")

def copy_static():
    if os.path.isdir(STATIC_DIR):
        if os.path.isdir(OUTPUT_STATIC_DIR):
            shutil.rmtree(OUTPUT_STATIC_DIR)
        shutil.copytree(STATIC_DIR, OUTPUT_STATIC_DIR, dirs_exist_ok=True)
        print(f"copied static -> {OUTPUT_STATIC_DIR}")
    else:
        print("skip: no static/ folder found")

def should_render(filename: str) -> bool:
    return filename.endswith(".html") and not filename.startswith("_")

def normalize_html(html: str) -> str:
    # safety net กัน path พังจากการต่อสตริง
    html = html.replace(".html.html", ".html")
    html = html.replace('href="././', 'href="./')
    html = html.replace('href=".//', 'href="./')
    html = html.replace('src="././', 'src="./')
    html = html.replace('src=".//', 'src="./')
    return html

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
            out_path.parent.mkdir(parents=True, exist_ok=True)

            tmpl = env.get_template(str(rel_path))
            ctx = dict(BASE_CTX)

            # หน้า list ยา
            if str(rel_path) == "Medication_administration.html":
                ctx.update(build_med_ctx())

            # ✅ หน้า compatibility ต้องมี groups ด้วย
            if str(rel_path) in ("compatibility.html", "compatibility_result.html"):
                ctx.update(build_med_ctx())

            # ✅ เฉพาะ vancomycin_dose.html ให้ไม่ error ตอน build static
            if str(rel_path) == "vancomycin_dose.html":
                ctx.update(
                    pma_weeks=None,
                    pma_days=None,
                    calc=None,
                    postnatal_days=None,
                    bw=None,
                    dose_min_per_kg=10.0,
                    dose_max_per_kg=15.0,
                    dose_min_mg=0.0,
                    dose_max_mg=0.0,
                    interval="every 6–18 hours",
                    active_row=None,
                )

            html = tmpl.render(**ctx)
            html = normalize_html(html)

            with open(out_path, "w", encoding="utf-8") as fp:
                fp.write(html)
            print("rendered ->", out_path)

if __name__ == "__main__":
    render_all()
