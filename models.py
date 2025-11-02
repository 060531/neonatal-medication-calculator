from extensions import db
from datetime import datetime

class AccessLog(db.Model):
    __tablename__ = "access_logs"
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    endpoint = db.Column(db.String(128), nullable=False)
    method = db.Column(db.String(8), nullable=False)
    remote_addr = db.Column(db.String(45))
    user_agent = db.Column(db.String(256))


class Drug(db.Model):
    __tablename__ = "drugs"
    id = db.Column(db.Integer, primary_key=True)
    generic_name = db.Column(db.String(128), unique=True, nullable=False)
    brand_name = db.Column(db.String(128))
    category = db.Column(db.String(64))

    compatibilities = db.relationship(
        "Compatibility", back_populates="drug", foreign_keys="Compatibility.drug_id"
    )
    co_compatibilities = db.relationship(
        "Compatibility", back_populates="co_drug", foreign_keys="Compatibility.co_drug_id"
    )

class Compatibility(db.Model):
    __tablename__ = "compatibility"
    id = db.Column(db.Integer, primary_key=True)
    drug_id = db.Column(db.Integer, db.ForeignKey("drugs.id"), nullable=False)
    co_drug_id = db.Column(db.Integer, db.ForeignKey("drugs.id"), nullable=False)
    status = db.Column(db.String(32), nullable=False)
    note = db.Column(db.Text)

    drug = db.relationship("Drug", foreign_keys=[drug_id], back_populates="compatibilities")
    co_drug = db.relationship("Drug", foreign_keys=[co_drug_id], back_populates="co_compatibilities")
