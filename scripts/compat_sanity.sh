#!/usr/bin/env bash
set -euo pipefail

APP="app.py"
DB="instance/app.db"

echo "== Alembic head =="
FLASK_APP="$APP" flask db current -v

echo "== Check unique index =="
sqlite3 "$DB" <<'SQL'
.headers on
.mode column
PRAGMA index_list('compatibility');
SELECT a,b,COUNT(*) AS cnt
FROM compatibility
GROUP BY a,b
HAVING COUNT(*) > 1;
SQL

echo "== Seed + Test UNIQUE =="
FLASK_APP="$APP" flask shell <<'PY'
from extensions import db
from models import Drug, Compatibility
from sqlalchemy.exc import IntegrityError

# prepare drugs
d1 = Drug.query.filter_by(name="Ampicillin").first() or Drug(name="Ampicillin")
d2 = Drug.query.filter_by(name="Gentamicin").first() or Drug(name="Gentamicin")
db.session.add_all([d1, d2]); db.session.commit()

# normalize a<=b
a,b = (d1.id,d2.id) if d1.id <= d2.id else (d2.id,d1.id)
pair = Compatibility.query.filter_by(a=a,b=b).first()
if not pair:
    db.session.add(Compatibility(a=a,b=b,status="Compatible"))
    db.session.commit()

# try duplicate -> should fail
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
sqlite3 "$DB" <<'SQL'
.headers on
.mode column
SELECT a,b,COUNT(*) AS cnt
FROM compatibility
GROUP BY a,b
HAVING COUNT(*) > 1;
SQL
