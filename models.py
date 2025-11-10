from extensions import db
from sqlalchemy import UniqueConstraint

class Drug(db.Model):
    __tablename__ = "drug"
    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)

class Compatibility(db.Model):
    __tablename__ = "compatibility"
    id     = db.Column(db.Integer, primary_key=True)
    a      = db.Column(db.Integer, nullable=False)
    b      = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(10), nullable=False)
    __table_args__ = (
        UniqueConstraint('a', 'b', name='uq_compatibility_ab'),
    )

class AccessLog(db.Model):
    __tablename__ = "access_log"
    id     = db.Column(db.Integer, primary_key=True)
    path   = db.Column(db.String(255), nullable=False)
    method = db.Column(db.String(10), nullable=False)

# --- normalize Compatibility(a,b) so that a <= b on insert/update ---
from sqlalchemy import event

@event.listens_for(Compatibility, "before_insert")
def _compat_before_insert(mapper, connection, target):
    # ทำให้ a,b เรียงลำดับเสมอ ป้องกัน (b,a) ชนกับ (a,b)
    if target.a is not None and target.b is not None and str(target.a) > str(target.b):
        target.a, target.b = target.b, target.a

@event.listens_for(Compatibility, "before_update")
def _compat_before_update(mapper, connection, target):
    if target.a is not None and target.b is not None and str(target.a) > str(target.b):
        target.a, target.b = target.b, target.a
