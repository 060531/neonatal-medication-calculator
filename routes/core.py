from flask import Blueprint, render_template, request

bp = Blueprint("core", __name__)

@bp.route("/")
def index():
    return render_template("index.html")

@bp.route("/calculate-pma", methods=["GET","POST"], endpoint="calculate_pma_route")
def calculate_pma_page():
    return render_template("pma_template.html")

@bp.route("/compatibility", endpoint="compatibility_page")
def compatibility_page():
    return render_template("compatibility.html")

@bp.route("/medication", endpoint="medication_administration")
def medication_administration():
    UPDATE_DATE = globals().get("UPDATE_DATE", "N/A")
    meds = [
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
    # group by first letter
    from collections import defaultdict
    groups = defaultdict(list)
    for m in meds:
        groups[m["label"][0].upper()].append(m)
    for k in groups:
        groups[k].sort(key=lambda x: x["label"].lower())
    groups = dict(sorted(groups.items()))
    letters = list(groups.keys())
    return render_template("Medication_administration.html",
                           groups=groups, letters=letters, meds=meds,
                           update_date=UPDATE_DATE)

@bp.route("/time-management", endpoint="time_management_route")
def time_management_route():
    return render_template("time_management.html")

@bp.get("/compatibility/check", endpoint="compatibility_check")
def compatibility_check():
    return "compatibility check (stub)"

@bp.get("/time-management/run", endpoint="run_time")
def run_time():
    return "time runner (stub)"

# --------- drug stubs: ให้กดจากรายการยาแล้วไม่ 404 ----------
def _register_drug_stub(bp, endpoint, title):
    def view():
        return f"{title} (stub page) — กำลังพัฒนา"
    view.__name__ = f"view_{endpoint}"
    bp.add_url_rule(f"/drug/{endpoint}", endpoint=endpoint, view_func=view)

for _lbl, _ep in [
    ("Acyclovir","acyclovir_route"),
    ("Amikacin","amikin_route"),
    ("Aminophylline","aminophylline_route"),
    ("Amoxicillin / Clavimoxy","amoxicillin_clavimoxy_route"),
    ("Amphotericin B","amphotericinB_route"),
    ("Ampicillin","ampicillin_route"),
    ("Benzathine penicillin G","benzathine_penicillin_g_route"),
    ("Cefazolin","cefazolin_route"),
    ("Cefotaxime","cefotaxime_route"),
    ("Ceftazidime","ceftazidime_route"),
    ("Ciprofloxacin","ciprofloxacin_route"),
    ("Clindamycin","clindamycin_route"),
    ("Cloxacillin","cloxacillin_route"),
    ("Colistin","colistin_route"),
    ("Dexamethasone","dexamethasone_route"),
    ("Dobutamine","dobutamine_route"),
    ("Dopamine","dopamine_route"),
    ("Fentanyl","fentanyl_route"),
    ("Furosemide","furosemide_route"),
    ("Gentamicin","gentamicin_route"),
    ("Hydrocortisone","hydrocortisone_route"),
    ("Insulin Human Regular","insulin_route"),
    ("Levofloxacin","levofloxacin_route"),
    ("Meropenem","meropenem_route"),
    ("Metronidazole (Flagyl)","metronidazole"),
    ("Midazolam","midazolam_route"),
    ("Midazolam + Fentanyl","midazolam_fentanyl_route"),
    ("Morphine","morphine_route"),
    ("Nimbex (Cisatracurium)","nimbex_route"),
    ("Omeprazole","omeprazole_route"),
    ("Penicillin G sodium","penicillin_g_sodium_route"),
    ("Phenobarbital","phenobarbital_route"),
    ("Phenytoin (Dilantin)","phenytoin_route"),
    ("Remdesivir","remdesivir_route"),
    ("Sul-am®","sul_am_route"),
    ("Sulbactam","sulbactam_route"),
    ("Sulperazone","sulperazone_route"),
    ("Tazocin","tazocin_route"),
    ("Unasyn","unasyn_route"),
    ("Vancomycin","vancomycin_route"),
]:
    _register_drug_stub(bp, _ep, _lbl)
