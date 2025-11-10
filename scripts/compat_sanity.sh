#!/usr/bin/env bash
set -euo pipefail

echo "== Alembic head =="
flask db current -v

echo "== Check unique index =="
sqlite3 instance/app.db <<'SQL'
.headers on
.mode column
PRAGMA index_list('compatibility');
SQL

echo "== Seed + Test UNIQUE =="
flask shell <<'PY'
from extensions import db
from models import Drug, Compatibility
from sqlalchemy.exc import IntegrityError

d1 = Drug.query.filter_by(name="Ampicillin").first() or Drug(name="Ampicillin")
d2 = Drug.query.filter_by(name="Gentamicin").first() or Drug(name="Gentamicin")
db.session.add_all([d1,d2]); db.session.commit()

a,b = (d1.id,d2.id) if d1.id <= d2.id else (d2.id,d1.id)
if not Compatibility.query.filter_by(a=a,b=b).first():
    db.session.add(Compatibility(a=a,b=b,status="Compatible")); db.session.commit()

dup = Compatibility(a=b,b=a,status="Compatible")
db.session.add(dup)
try:
    db.session.commit()
    print("ERROR: UNIQUE not enforced")
except IntegrityError:
    db.session.rollback()
    print("OK: UNIQUE enforced")

print("Rows:", [(r.id,r.a,r.b,r.status) for r in Compatibility.query.order_by(Compatibility.id).all()])
PY

echo "== Scan duplicates by SQL =="
sqlite3 instance/app.db <<'SQL'
.headers on
.mode column
SELECT a,b,COUNT(*) AS cnt
FROM compatibility
GROUP BY a,b
HAVING COUNT(*) > 1;
SQL
