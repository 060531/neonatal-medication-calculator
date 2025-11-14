# compat_cli.py
import json
import click
from flask.cli import with_appcontext
from extensions import db
from models import Drug, Compatibility  # ปรับให้ตรงกับ path ที่ใช้จริง

@click.group()
def compat():
    """คำสั่งจัดการข้อมูล Drug Compatibility"""
    pass


@compat.command("import-compat")
@click.argument("json_path", type=click.Path(exists=True))
@click.option("--truncate", is_flag=True, help="ลบข้อมูลเดิมทั้งหมดก่อน import")
@with_appcontext
def import_compat(json_path, truncate):
    """
    นำเข้าข้อมูลยาและ compatibility จากไฟล์ JSON
    โครงไฟล์ seed_compatibility.json ที่เราออกแบบไว้ก่อนหน้า เช่น:

    {
      "drugs": [
        {"code": "amikacin", "name": "Amikacin"},
        {"code": "ampicillin", "name": "Ampicillin"}
      ],
      "pairs": [
        {
          "drug_a": "amikacin",
          "drug_b": "ampicillin",
          "status": "compatible",
          "note": "ใช้ร่วมกันใน Y-site ได้"
        }
      ]
    }
    """
    click.echo(f"อ่านไฟล์: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    drugs_data = payload.get("drugs", [])
    pairs_data = payload.get("pairs", [])

    if truncate:
        click.echo("ลบข้อมูลเดิมในตาราง compatibility และ drug ...")
        Compatibility.query.delete()
        Drug.query.delete()
        db.session.commit()

    # --- import drugs ---
    code_to_obj = {}
    for d in drugs_data:
        code = d["code"]
        name = d.get("name", code)
        existing = Drug.query.filter_by(code=code).first()
        if existing:
            existing.name = name
            obj = existing
        else:
            obj = Drug(code=code, name=name)
            db.session.add(obj)
        code_to_obj[code] = obj

    db.session.flush()  # ให้ได้ id ของ Drug

    # --- import pairs ---
    for p in pairs_data:
        a_code = p["drug_a"]
        b_code = p["drug_b"]
        status = p.get("status", "unknown")
        note = p.get("note", "")

        drug_a = code_to_obj.get(a_code) or Drug.query.filter_by(code=a_code).first()
        drug_b = code_to_obj.get(b_code) or Drug.query.filter_by(code=b_code).first()

        if not drug_a or not drug_b:
            click.echo(f"ข้าม pair เพราะหา drug ไม่เจอ: {a_code} - {b_code}")
            continue

        # บังคับให้ a_id < b_id เพื่อเก็บแบบ unique
        a_id, b_id = sorted([drug_a.id, drug_b.id])

        compat = Compatibility.query.filter_by(drug_a_id=a_id, drug_b_id=b_id).first()
        if compat:
            compat.status = status
            compat.note = note
        else:
            compat = Compatibility(
                drug_a_id=a_id,
                drug_b_id=b_id,
                status=status,
                note=note,
            )
            db.session.add(compat)

    db.session.commit()
    click.echo("นำเข้าข้อมูลเรียบร้อย ✅")
