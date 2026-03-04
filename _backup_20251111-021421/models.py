# models.py
from app import db
from sqlalchemy import UniqueConstraint

class Compatibility(db.Model):
    __tablename__ = 'compatibility'

    id = db.Column(db.Integer, primary_key=True)
    a  = db.Column(db.Integer, nullable=False)
    b  = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(10), nullable=False)

    __table_args__ = (
        UniqueConstraint('a', 'b', name='uq_compatibility_ab'),
    )
