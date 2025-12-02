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
    "drug_base": "drug_base.html",
    "drug_calculation": "drug_calculation.html",
    "home": "home.html",
    "compat_result": "compat_result.html",

    # meds (บางตัวอาจถูกแม็ปเพิ่มด้านล่างโดยอัตโนมัติ)
    "vancomycin": "vancomycin.html",
    "insulin": "insulin.html",
    "fentanyl_continuous": "fentanyl_continuous.html",
    "penicillin_g_sodium": "penicillin_g_sodium.html",
    "scan_server": "scan_server.html",

    # static
    "static": "static/",

    # === เพิ่มใหม่สำหรับ static build (endpoint ฝั่ง Flask -> หน้าไฟล์) ===
    "calculate_pma_page": "./pma_template.html",
    "core.compatibility_page": "./compatibility.html",
    "core.time_management_route": "./time_management.html",
    "medication_administration": "./Medication_administration.html",

    # ✅ สำคัญ: endpoint ของ compatibility index ใน Flask ให้ชี้ไป compatibility.html (Pages)
    "compat.compat_index": "compatibility.html",

    # (เผื่อมีที่ไหนเรียกชื่อสั้น ๆ)
    "compat_index": "compatibility.html",
}
URL_MAP.update({
    "compat.compat_index": "compatibility.html",
    "compat_index": "compatibility.html",   # กันกรณีโค้ดตัด prefix "compat."
})

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

# เติม URL_MAP อัตโนมัติตาม endpoint รายการยา
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
    if s.endswith("/") or s.endswith(".css") or s.endswith(".js") or s.endswith(".png") or s.endswith(".jpg") or s.endswith(".jpeg") or s.endswith(".svg") or s.endswith(".webmanifest"):
        return s
    if s.endswith(".html"):
        return s
    return f"{s}.html"

def u(name: str, **kwargs) -> str:
    """
    static-build url resolver
    - u('static', filename='app.js') -> ./static/app.js
    - u('compat.compat_index') -> ./compatibility.html (ตาม URL_MAP)
    """
    if not name:
        return "./index.html"

    # static endpoint แบบ Flask: url_for('static', filename='...')
    if name == "static":
        fn = kwargs.get("filename", "") or kwargs.get("path", "")
        if fn:
            fn = _strip_leading_dots(fn).lstrip("/")
            return f"./static/{fn}"
        return "./static/"

    target = URL_MAP.get(name, f"{name}.html")
    target = _ensure_html_file(target)
    return f"./{_strip_leading_dots(target)}"

def static_url(endpoint: str, **kwargs) -> str:
    """
    แทน url_for ใน static build ให้รับ kwargs ได้เหมือนของ Flask
    """
    return u(endpoint, **kwargs)

def resolve_endpoint(endpoint: str) -> str:
    if not endpoint:
        return "./index.html"
    if endpoint.startswith(("http://", "https://", "#")):
        return endpoint

    # ✅ 1) ลองชื่อเต็มก่อน
    target = URL_MAP.get(endpoint)

    # ✅ 2) ค่อย fallback แบบตัด prefix
    if target is None and "." in endpoint:
        target = URL_MAP.get(endpoint.split(".")[-1])

    # ✅ 3) สุดท้ายค่อยเดาเป็น <name>.html
    if target is None:
        target = f"{endpoint.split('.')[-1]}.html"

    target = _ensure_html_file(target)
    return f"./{_strip_leading_dots(target)}"

# ---------- Safe numeric helpers & filters ----------
def nz(v, default=0):
    """None -> default; อย่างอื่นคืนค่าเดิม"""
    return default if v is None else v

def fmt(v, nd=2):
    """format ทศนิยมคงที่; รองรับ None/สตริง -> คืน '' """
    try:
        if v is None or v == "":
            return ""
        x = float(v)
        nd = int(nd)
        return f"{x:.{nd}f}"
    except Exception:
        return ""

def fmt_int(v):
    """format เป็นจำนวนเต็ม; รองรับ None -> '' """
    try:
        if v is None or v == "":
            return ""
        return f"{int(round(float(v)))}"
    except Exception:
        return ""

def sig(v, n=3):
    """format ตัวเลขนัยสำคัญ; รองรับ None -> '' """
    try:
        if v is None or v == "":
            return ""
        x = float(v)
        n = int(n)
        return f"{x:.{n}g}"
    except Exception:
        return ""

def safe_fmt(value, fmt_pattern="%.2f"):
    """รูปแบบเดิมแบบ '% .2f'|safe_fmt; รองรับ None -> ใช้ 0"""
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

# ลงทะเบียนฟิลเตอร์
env.filters["nz"] = nz
env.filters["fmt"] = fmt         # {{ val|fmt(2) }}
env.filters["fmt2"] = lambda v: fmt(v, 2)
env.filters["fmt_int"] = fmt_int
env.filters["sig"] = sig         # {{ val|sig(3) }}
env.filters["safe_fmt"] = safe_fmt

# ลงทะเบียน globals
env.globals.update({
    "u": u,
    "url_for": static_url,          # ให้ template เดิมที่ใช้ url_for ใช้งานได้บน Pages
    "static_build": True,
    "resolve_endpoint": resolve_endpoint,
})

# ---------- Base context ----------
BASE_CTX = {
    "error": None,
    "content_extra": None,

    # วันที่แสดงบนหน้าเว็บ
    "UPDATE_DATE": "2025-11-15",
    "update_date": "2025-11-15",

    # jinja helpers
    "u": u,
    "static_build": True,

    # mock flask-ish objects
    "request": {"path": "/"},
    "session": {},
    "order": {},

    # compatibility index groups (จะถูกเติมจริงใน build_med_ctx() สำหรับบางหน้า)
    "groups": {},

    # defaults used in drug pages (ให้ None เพื่อไม่ให้โชว์ผลลัพธ์ตอน static build)
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
    "multiplication": None,
    "rate_ml_hr": None,
    "concentration_mg_ml": None,
    "target_conc": None,
    "stock_conc": None,
    "loading_dose_ml": None,
    "maintenance_dose_ml": None,
    "infusion_rate_ml_hr": None,
    "total_volume_ml": None,
    "dilution_volume_ml": None,

    # ค่าคงที่สำหรับหน้า dose result ที่ใช้ "%.2f"|format(...)
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
    "interval": "",
    "actual_dose": 0.0,
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

def build_med_ctx():
    """
    สร้าง groups A-Z สำหรับ:
    - Medication_administration.html
    - compatibility.html (หน้าเลือกยา A/B)
    """
    groups = defaultdict(list)
    for m in MEDS:
        groups[m["label"][0].upper()].append(m)

    for k in list(groups.keys()):
        groups[k].sort(key=lambda x: x["label"].lower())

    groups = dict(sorted(groups.items()))
    letters = list(groups.keys())
    return {"meds": MEDS, "groups": groups, "letters": letters}

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

            # เติม meds/groups ให้ 2 หน้าที่ต้องใช้
            if str(rel_path) in ("Medication_administration.html", "compatibility.html"):
                ctx.update(build_med_ctx())

            # ✅ ใส่ default เฉพาะหน้า vancomycin_dose.html (กัน format error + ให้หน้าแสดงได้สวยตอน static)
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

            # safety net: กัน path ซ้อน .html.html + href แปลก ๆ
            html = html.replace(".html.html", ".html")
            html = html.replace('href="././', 'href="./')
            html = html.replace('href=".//', 'href="./')
            html = html.replace('src="././', 'src="./')
            html = html.replace('src=".//', 'src="./')

            with open(out_path, "w", encoding="utf-8") as fp:
                fp.write(html)

            print("rendered ->", out_path)

if __name__ == "__main__":
    render_all()
