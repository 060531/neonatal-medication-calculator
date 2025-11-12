from flask import Blueprint, render_template, request
meds_bp = Blueprint("meds", __name__)

@meds_bp.get("/medication_administration")
def medication_administration():
    meds = [
        {"label": "Acyclovir", "endpoint": "meds.acyclovir_route"},
        {"label": "Amikacin", "endpoint": "meds.amikin_route"},
        {"label": "Cefazolin", "endpoint": "meds.cefazolin_route"},
    ]
    return render_template("medication_administration.html", meds=meds)

@meds_bp.route("/acyclovir", methods=["GET","POST"])
def acyclovir_route():
    # ... คำนวณ dose/result ...
    return render_template("acyclovir.html")  # ตัวอย่าง
