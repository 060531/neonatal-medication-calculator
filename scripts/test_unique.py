import pytest
from sqlalchemy.exc import IntegrityError

from models import Drug, Compatibility

def test_unique_and_symmetry(db_session):
    d1 = Drug(generic_name="Ampicillin")
    d2 = Drug(generic_name="Gentamicin")
    db_session.add_all([d1, d2])
    db_session.commit()

    # ใส่กลับลำดับให้ event จัด normalize เป็น a<b
    pair = Compatibility(drug_id=d2.id, co_drug_id=d1.id, status="Compatible")
    db_session.add(pair)
    db_session.commit()

    # สลับซ้ำ => ต้องชน UNIQUE
    with pytest.raises(IntegrityError):
        db_session.add(Compatibility(drug_id=d1.id, co_drug_id=d2.id, status="Compatible"))
        db_session.commit()

def test_self_pair_rejected(db_session):
    d = Drug(generic_name="Vancomycin")
    db_session.add(d)
    db_session.commit()

    # ORM event ควร raise ValueError ก่อนถึง DB
    with pytest.raises(ValueError):
        db_session.add(Compatibility(drug_id=d.id, co_drug_id=d.id, status="N/A"))
        db_session.flush()
