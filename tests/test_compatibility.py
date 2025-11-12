# tests/test_compatibility.py
import pytest
from sqlalchemy.exc import IntegrityError
from extensions import db
from models import Compatibility

def test_unique_and_symmetry(db_session):
    # insert ปกติ
    db_session.add(Compatibility(a=1, b=2, status="OK"))
    db_session.commit()

    # สลับลำดับ -> ต้องชน UNIQUE
    with pytest.raises(IntegrityError):
        db_session.add(Compatibility(a=2, b=1, status="OK"))
        db_session.commit()

def test_no_self_pair(db_session):
    with pytest.raises((IntegrityError, ValueError)):
        db_session.add(Compatibility(a=3, b=3, status="X"))
        db_session.commit()
