import json
from pathlib import Path


def seed_compat_from_json(db, Drug, Compatibility, truncate: bool = False) -> None:
    """
    อ่านไฟล์ data/seed_compatibility.json แล้ว seed ลงตาราง Compatibility

    - รองรับได้ทั้ง key แบบ:
        - "drug_a" / "drug_b"
        - หรือ "drug" / "co_drug"
    - แปลงค่า status ให้เป็นโค้ดสั้น: C, I, U, ND
    - ถ้าไม่เจอยาใน Drug จะสร้าง Drug ใหม่ให้
    """
    path = Path("data") / "seed_compatibility.json"
    print(f"อ่านไฟล์: {path} | exists: {path.exists()}")

    if not path.exists():
        print("❌ ไม่พบไฟล์ seed_compatibility.json")
        return

    with path.open(encoding="utf-8") as f:
        rows = json.load(f)

    if truncate:
        print("⚠️ ลบข้อมูลเดิมใน Compatibility ทั้งหมด ...")
        db.session.query(Compatibility).delete()
        db.session.commit()

    created_drugs = 0
    created_pairs = 0
    updated_pairs = 0
    skipped_rows = 0

    def _get(row, *keys):
        """ดึงค่าตาม key แรกที่มีใน row"""
        for k in keys:
            if k in row and row[k]:
                return str(row[k]).strip()
        return None

    # map status เป็นโค้ดสั้น
    STATUS_MAP = {
        "C": "C",
        "I": "I",
        "U": "U",
        "ND": "ND",
        "COMPATIBLE": "C",
        "INCOMPATIBLE": "I",
        "UNCERTAIN": "U",
        "NO": "ND",        # สำหรับข้อความขึ้นต้นว่า "No data ..."
    }

    for idx, row in enumerate(rows, start=1):
        name_a = _get(row, "drug_a", "drug", "Drug", "A")
        name_b = _get(row, "drug_b", "co_drug", "Co_drug", "B")
        raw_status = _get(row, "status")
        source = _get(row, "source")
        note = _get(row, "note")

        if not name_a or not name_b or not raw_status:
            print(f"⏭️  skip แถวที่ {idx}: ข้อมูลไม่ครบ (drug/status missing) -> {row}")
            skipped_rows += 1
            continue

        # ปรับชื่อยาให้ตรง (ตัด space ซ้ายขวา)
        name_a = name_a.strip()
        name_b = name_b.strip()

        # normalize status เป็นตัวใหญ่
        s_up = raw_status.strip().upper()
        # ดึงคำตัวแรกกรณีเป็นประโยค เช่น "Compatible", "Incompatible drug"
        first_token = s_up.split()[0] if s_up else ""
        status = STATUS_MAP.get(s_up) or STATUS_MAP.get(first_token)

        if status is None:
            print(f"⏭️  skip แถวที่ {idx}: status ไม่รู้จัก -> {raw_status!r}")
            skipped_rows += 1
            continue

        # หา / สร้าง Drug A
        drug_a = Drug.query.filter_by(generic_name=name_a).first()
        if not drug_a:
            drug_a = Drug(generic_name=name_a)
            db.session.add(drug_a)
            db.session.flush()
            created_drugs += 1
            print(f"➕ สร้างยาใหม่: {name_a}")

        # หา / สร้าง Drug B
        drug_b = Drug.query.filter_by(generic_name=name_b).first()
        if not drug_b:
            drug_b = Drug(generic_name=name_b)
            db.session.add(drug_b)
            db.session.flush()
            created_drugs += 1
            print(f"➕ สร้างยาใหม่: {name_b}")

        # บังคับให้เก็บคู่แบบเรียง id เพื่อกันซ้ำ (1,10) กับ (10,1)
        if drug_a.id <= drug_b.id:
            d1, d2 = drug_a, drug_b
        else:
            d1, d2 = drug_b, drug_a

        compat = Compatibility.query.filter_by(
            drug_id=d1.id, co_drug_id=d2.id
        ).first()

        if compat is None:
            compat = Compatibility(
                drug_id=d1.id,
                co_drug_id=d2.id,
                status=status,
                source=source,
                note=note,
            )
            db.session.add(compat)
            created_pairs += 1
            print(f"✅ create pair: {d1.generic_name} + {d2.generic_name} -> {status}")
        else:
            compat.status = status
            compat.source = source
            compat.note = note
            updated_pairs += 1
            print(f"♻️ update pair: {d1.generic_name} + {d2.generic_name} -> {status}")

    db.session.commit()
    print("✅ Import summary:")
    print(f"  Drugs created : {created_drugs}")
    print(f"  Pairs created : {created_pairs}")
    print(f"  Pairs updated : {updated_pairs}")
    print(f"  Rows skipped  : {skipped_rows}")
