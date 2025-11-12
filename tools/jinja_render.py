# tools/jinja_render.py
# -*- coding: utf-8 -*-
import os
import shutil
import pathlib
from collections import defaultdict
from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATES_DIR = "templates"
STATIC_DIR = "static"
OUTPUT_DIR = "docs"
OUTPUT_STATIC_DIR = f"{OUTPUT_DIR}/static"

# ---------- URL mapping ----------
URL_MAP = {
    "index": "index.html",
    "pma_template": "pma_template.html",
    "compatibility": "compatibility.html",
    "Medication_administration": "Medication_administration.html",
    "time_management": "time_management.html",
    "compatibility_result": "compatibility_result.html",
    "run_time": "run_time.html",
    "run_time_stop": "run_time_stop.html",
    "verify_result": "verify_result.html",
    "vancomycin": "vancomycin.html",
    "insulin": "insulin.html",
    "fentanyl_continuous": "fentanyl_continuous.html",
    "penicillin_g_sodium": "penicillin_g_sodium.html",
    "scan_server": "scan_server.html",
    "static": "static/",
}

# >>> NEW: รายการยาแบบเดียวกับใน Flask route
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

# >>> NEW: เติม URL_MAP ของ endpoint ยา → ชื่อไฟล์ .html อัตโนมัติ
for m in MEDS:
    ep = m["endpoint"]
    if ep.endswith("_route"):
        page = ep[:-6] + ".html"   # ตัด "_route"
    else:
        page = ep + ".html"
    URL_MAP.setdefault(ep, page)

# ---------- Helpers ----------
def _strip_leading_dots(path: str) -> str:
    while path.startswith("./"):
        path = path[2:]
    return path

def _ensure_html_file(name_or_file: str) -> str:
    s = name_or_file.strip()
    s = _strip_leading_dots(s)
    if s.endswith(".html"): return s
    return f"{s}.html"

def u(name: str, **kwargs) -> str:
    if not name:
        return "./index.html"
    if name == "static":
        fn = kwargs.get("filename", "")
        return f"./static/{fn}" if fn else "./static/"
    target = URL_MAP.get(name, f"{name}.html")
    target = _ensure_html_file(target)
    return f"./{_strip_leading_dots(target)}"

def static_url(endpoint: str, filename: str = "") -> str:
    if endpoint == "static":
        return f"./static/{filename}" if filename else "./static/"
    return u(endpoint)

def resolve_endpoint(endpoint: str) -> str:
    if not endpoint:
        return "./index.html"
    if isinstance(endpoint, str) and endpoint.startswith(("http://", "https://", "#")):
        return endpoint
    target = URL_MAP.get(endpoint, f"{endpoint}.html")
    target = _ensure_html_file(target)
    return f"./{_strip_leading_dots(target)}"

# ---------- Jinja env ----------
def safe_fmt(value, fmt="%.2f"):
    try:
        return fmt % (value,)
    except Exception:
        try:
            return fmt % (0,)
        except Exception:
            return str(value)

env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html", "xml"]),
)
env.filters["safe_fmt"] = safe_fmt
env.globals.update({
    "u": u,
    "url_for": static_url,
    "static_build": True,
    "resolve_endpoint": resolve_endpoint,
})

# ---------- Base context ----------
# ---------- Base context ----------
BASE_CTX = {
    "error": None,
    "content_extra": None,
    "UPDATE_DATE": "",
    "u": u,
    "static_build": True,
    "request": {"path": "/"},
    "session": {},
    "order": {},  # for verify_result.html

    # defaults used in drug pages
    # ใส่ None เพื่อไม่ให้เทมเพลตแสดง 0.0 ตั้งแต่แรก
    "bw": None,
    "pma_weeks": None,
    "pma_days": None,
    "postnatal_days": None,

    "dose": None,
    "dose_ml": None,
    "dose_mgkg": None,

    "result_ml": None,
    "result_ml_1": None,
    "result_ml_2": None,
    "result_ml_3": None,

    "final_result_1": None,
    "final_result_2": None,
    "final_result_3": None,

    "calculated_ml": None,
    "vol_ml": None,

    "multiplication": None,          # ให้ผู้ใช้เลือกเอง ไม่เติม 1.0 ล่วงหน้า
    "rate_ml_hr": None,
    "concentration_mg_ml": None,
    "target_conc": None,
    "stock_conc": None,

    "loading_dose_ml": None,
    "maintenance_dose_ml": None,
    "infusion_rate_ml_hr": None,
    "total_volume_ml": None,
    "dilution_volume_ml": None,
}

DEFAULT_NUM_KEYS = {
    "bw": None,
    "pma_weeks": None,
    "pma_days": None,
    "postnatal_days": None,
    "dose": None,
    "dose_ml": None,
    "dose_mgkg": None,
    "result_ml": None,
    "result_ml_1": None,
    "result_ml_2": None,
    "final_result_1": None,
    "final_result_2": None,
    "final_result_3": None,
    "calculated_ml": None,
    "vol_ml": None,
    "multiplication": 1.0,
    "rate_ml_hr": None,
    "concentration_mg_ml": None,
    "target_conc": None,
    "stock_conc": None,
    "loading_dose_ml": None,
    "maintenance_dose_ml": None,
    "infusion_rate_ml_hr": None,
    "total_volume_ml": None,
    "dilution_volume_ml": None,
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

# >>> NEW: สร้าง context ของหน้าการบริหารยา (A–Z)
def build_med_ctx():
    groups = defaultdict(list)
    for m in MEDS:
        groups[m["label"][0].upper()].append(m)
    for k in list(groups.keys()):
        groups[k].sort(key=lambda x: x["label"].lower())
    groups = dict(sorted(groups.items()))
    letters = list(groups.keys())
    return {"meds": MEDS, "groups": groups, "letters": letters}

# ---------- Render all ----------
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

            if str(rel_path) == "index.html":
                out_path = pathlib.Path(OUTPUT_DIR) / "index.html"
            else:
                out_path.parent.mkdir(parents=True, exist_ok=True)

            tmpl = env.get_template(str(rel_path))

            ctx = dict(BASE_CTX)
            # >>> NEW: อัด groups/letters/meds เข้าเฉพาะหน้านี้
            if str(rel_path) == "Medication_administration.html":
                ctx.update(build_med_ctx())

            html = tmpl.render(**ctx)

            # safety net
            html = html.replace(".html.html", ".html")
            html = html.replace('href="././', 'href="./')
            html = html.replace('href=".//', 'href="./')

            with open(out_path, "w", encoding="utf-8") as fp:
                fp.write(html)
            print("rendered ->", out_path)

if __name__ == "__main__":
    render_all()
