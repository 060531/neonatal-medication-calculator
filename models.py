# models.py
from sqlalchemy import event
from app import db   # หรือจากที่โปรเจกต์ใช้จริง

class Drug(db.Model):
    __tablename__ = "drug"
    id = db.Column(db.Integer, primary_key=True)
    generic_name = db.Column(db.String(128), unique=True, nullable=False)
    # ...

class Compatibility(db.Model):
    __tablename__ = "compatibility"

    id = db.Column(db.Integer, primary_key=True)
    drug_id = db.Column(db.Integer, db.ForeignKey("drug.id"), nullable=False)
    co_drug_id = db.Column(db.Integer, db.ForeignKey("drug.id"), nullable=False)

    status = db.Column(db.String(4), nullable=False, default="ND")

    # 👇 อันนี้ต้องมี
    source = db.Column(db.String(255), nullable=True)
    note = db.Column(db.Text, nullable=True)

    drug = db.relationship("Drug", foreign_keys=[drug_id])
    co_drug = db.relationship("Drug", foreign_keys=[co_drug_id])

    __table_args__ = (
        db.UniqueConstraint("drug_id", "co_drug_id", name="uq_compat_pair"),
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


    @property
    def a(self):
        return self.drug_id

    @a.setter
    def a(self, value):
        self.drug_id = value

    @property
    def b(self):
        return self.co_drug_id

    @b.setter
    def b(self, value):
        self.co_drug_id = value

    def __repr__(self):
        return f"<Compat {self.drug_id} x {self.co_drug_id} = {self.status}>"

@event.listens_for(Compatibility, "before_insert")
@event.listens_for(Compatibility, "before_update")
def normalize_compatibility(mapper, connection, target: Compatibility):
    """บังคับลำดับคู่ยา + กันไม่ให้เป็น pair ตัวเอง"""
    if target.drug_id is None or target.co_drug_id is None:
        return

    # ไม่ให้ยาเดียวกันมา pair กัน
    if target.drug_id == target.co_drug_id:
        raise ValueError("Self-pair (drug with itself) is not allowed")

    # บังคับให้น้อยกว่าอยู่ด้านซ้ายเสมอ → (a,b) และ (b,a) จะ normalize เป็นคู่เดียวกัน
    if target.drug_id > target.co_drug_id:
        target.drug_id, target.co_drug_id = target.co_drug_id, target.drug_id
