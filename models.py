from extensions import db
from sqlalchemy import UniqueConstraint, CheckConstraint, ForeignKey

class Drug(db.Model):
    __tablename__ = "drug"

    id = db.Column(db.Integer, primary_key=True)
    generic_name = db.Column(db.String(128), nullable=False, unique=True)

    @property
    def name(self):
        return self.generic_name

    def __repr__(self):
        return f"<Drug id={self.id} generic_name={self.generic_name!r}>"

class Compatibility(db.Model):
    __tablename__ = "compatibility"

    id = db.Column(db.Integer, primary_key=True)

    # ใช้คอลัมน์ตามสคีมาหลัก (อิง scripts/test_unique.py)
    drug_id = db.Column(db.Integer, ForeignKey("drug.id"), nullable=False)
    co_drug_id = db.Column(db.Integer, ForeignKey("drug.id"), nullable=False)

    status = db.Column(db.String(32), nullable=False)

    __table_args__ = (
        UniqueConstraint("drug_id", "co_drug_id", name="uq_compat_pair"),
        CheckConstraint("drug_id < co_drug_id", name="ck_drug_id_lt_co_drug_id"),
    )

    # รองรับทั้งแบบ a,b และ drug_id, co_drug_id
    def __init__(self, *, a=None, b=None, drug_id=None, co_drug_id=None, status: str):
        if status is None:
            raise ValueError("status is required")

        # map พารามิเตอร์
        if a is not None or b is not None:
            if a is None or b is None:
                raise ValueError("both a and b must be provided together")
            drug_id, co_drug_id = a, b
        else:
            if drug_id is None or co_drug_id is None:
                raise ValueError("drug_id and co_drug_id are required")

        # validation
        if drug_id == co_drug_id:
            raise ValueError("drug_id and co_drug_id must be different")

        # normalize ลำดับ: เล็กก่อนใหญ่
        if drug_id > co_drug_id:
            drug_id, co_drug_id = co_drug_id, drug_id

        self.drug_id = drug_id
        self.co_drug_id = co_drug_id
        self.status = status

    # properties เพื่อความเข้ากันได้หากโค้ด/เทสอ้าง a,b ภายหลัง
    @property
    def a(self):
        return self.drug_id

    @property
    def b(self):
        return self.co_drug_id

    def __repr__(self):
        return f"<Compatibility ({self.drug_id},{self.co_drug_id}) status={self.status}>"
