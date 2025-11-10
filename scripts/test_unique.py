from extensions import db
from models import Drug, Compatibility
from sqlalchemy.exc import IntegrityError

# seed drugs
d1 = Drug.query.filter_by(name="Ampicillin").first() or Drug(name="Ampicillin")
d2 = Drug.query.filter_by(name="Gentamicin").first() or Drug(name="Gentamicin")
db.session.add_all([d1, d2]); db.session.commit()

# normalize pair (a<=b)
a, b = (d1.id, d2.id) if d1.id <= d2.id else (d2.id, d1.id)

# ensure base pair exists once
if not Compatibility.query.filter_by(a=a, b=b).first():
    db.session.add(Compatibility(a=a, b=b, status="Compatible"))
    db.session.commit()

# try reversed dup -> should violate UNIQUE(a,b)
dup = Compatibility(a=b, b=a, status="Compatible")
db.session.add(dup)
try:
    db.session.commit()
    print("ERROR: UNIQUE not enforced")
except IntegrityError:
    db.session.rollback()
    print("OK: UNIQUE enforced")

print("Rows:", [(r.id, r.a, r.b, r.status) for r in Compatibility.query.order_by(Compatibility.id).all()])
