# seed_drugs_only.py
# ไม่ต้อง import app

from extensions import db
from models import Drug

DRUG_MASTER = [
    # A
    "Acyclovir", "Amikacin", "Aminophylline", "Amoxicillin / Clavimoxy",
    "Amphotericin B", "Ampicillin",
    # B
    "Benzathine_penicillin_g",
    # C
    "Cefazolin", "Cefotaxime", "Ceftazidime", "Clindamycin",
    "Cloxacillin", "Colistin",
    # D
    "Dexamethasone", "Dobutamine", "Dopamine",
    # F
    "Fentanyl", "Furosemide",
    # G
    "Gentamicin",
    # H
    "Hydrocortisone",
    # I
    "Insulin Human Regular",
    # L
    "Levofloxacin",
    # M
    "Meropenem", "Metronidazole (Flagyl)", "Midazolam",
    "Midazolam + Fentanyl", "Morphine",
    # N
    "Nimbex (Cisatracurium)",
    # O
    "Omeprazole",
    # P
    "Penicillin G sodium", "Phenobarbital", "Phenytoin (Dilantin)",
    # R
    "Remdesivir",
    # S
    "Sul-am®", "Sulbactam", "Sulperazone",
    # T
    "Tazocin",
    # U
    "Unasyn",
    # V
    "Vancomycin",
]


def seed_drugs_only():
    created = 0

    for raw in DRUG_MASTER:
        name = raw.strip()
        if not name:
            continue

        # กันไม่ให้ซ้ำ (เทียบ lowercase)
        existing = Drug.query.filter(
            db.func.lower(Drug.generic_name) == name.lower()
        ).first()

        if existing:
            continue

        db.session.add(Drug(generic_name=name))
        created += 1

    db.session.commit()
    print("✅ Done seeding Drug")
    print("  New created :", created)
    print("  Total drugs :", Drug.query.count())
