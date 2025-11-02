# verify_seed.py
import os
import csv
import json

# ปรับให้ตรงกับโครงสร้างโปรเจกต์ของคุณ
from app import app           # ใช้แอปหลักที่คุณรันอยู่
from extensions import db
from models import Drug

DATA_DIR = "data"
CSV_PATH = os.path.join(DATA_DIR, "drugs.csv")
JSON_PATH = "seed_drugs.json"

def norm(name: str) -> str:
    """normalize ชื่อยาให้เทียบกันได้แน่นอน"""
    return (name or "").strip().lower()

def load_expected_from_csv(path: str):
    items = set()
    if not os.path.exists(path):
        print(f"[WARN] CSV not found: {path} (ข้ามไฟล์นี้)")
        return items

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # รองรับทั้งหัวคอลัมน์ name / generic_name
        for row in reader:
            g = row.get("generic_name") or row.get("name")
            if g:
                items.add(g.strip())
    return items

def load_expected_from_json(path: str):
    items = set()
    if not os.path.exists(path):
        print(f"[WARN] JSON not found: {path} (ข้ามไฟล์นี้)")
        return items

    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"[ERROR] อ่าน JSON ไม่ได้: {e}")
            return items

    # รองรับทั้งโครงแบบ seed_drugs.json และ generic list
    for obj in data:
        if isinstance(obj, dict):
            g = obj.get("generic_name") or obj.get("name")
            if g:
                items.add(g.strip())
        elif isinstance(obj, str):
            items.add(obj.strip())
    return items

def main():
    # 1) โหลด expected จากไฟล์ seed
    expected_csv  = load_expected_from_csv(CSV_PATH)
    expected_json = load_expected_from_json(JSON_PATH)
    expected_all  = expected_csv | expected_json

    print("=== SEED SOURCES ===")
    print(f"- from CSV ({CSV_PATH}): {len(expected_csv)} รายการ")
    print(f"- from JSON ({JSON_PATH}): {len(expected_json)} รายการ")
    print(f"- รวม (unique): {len(expected_all)} รายการ")

    # 2) โหลดจาก DB
    db_names = [d.generic_name.strip() for d in Drug.query.all()]
    db_set   = set(db_names)

    # 3) เทียบความต่าง
    # สิ่งที่อยู่ใน seed แต่ยังไม่อยู่ใน DB
    missing_in_db = sorted([x for x in expected_all if norm(x) not in {norm(n) for n in db_set}])

    # สิ่งที่อยู่ใน DB แต่ไม่อยู่ใน seed (อาจจะเป็นรายการเก่าหรือ seed ยังไม่ใส่)
    extra_in_db = sorted([x for x in db_set if norm(x) not in {norm(n) for n in expected_all}])

    # 4) ตรวจ duplicates (ฝั่ง DB เอง)
    seen = set()
    duplicates = []
    for n in db_names:
        key = norm(n)
        if key in seen:
            duplicates.append(n)
        else:
            seen.add(key)

    print("\n=== DB SUMMARY ===")
    print(f"- จำนวนยาทั้งหมดใน DB: {len(db_set)}")
    if duplicates:
        print(f"- พบชื่อยาซ้ำใน DB: {len(duplicates)} รายการ")
        for n in duplicates:
            print(f"  • {n}")
    else:
        print("- ไม่พบชื่อยาซ้ำใน DB")

    print("\n=== DIFF ===")
    if missing_in_db:
        print(f"- ยังขาดใน DB (มีใน seed แต่ไม่มีใน DB): {len(missing_in_db)}")
        for n in missing_in_db:
            print(f"  • {n}")
    else:
        print("- ไม่พบรายการที่ขาดใน DB")

    if extra_in_db:
        print(f"- เกินใน DB (มีใน DB แต่ไม่อยู่ใน seed): {len(extra_in_db)}")
        for n in extra_in_db:
            print(f"  • {n}")
    else:
        print("- ไม่พบรายการที่เกินใน DB")

    print("\n[HINT]")
    if missing_in_db:
        print("- ถ้าต้องการเติมข้อมูลที่ขาด ให้รัน `python3 seed.py` อีกครั้ง (ตรวจว่า seed ดึงจากไฟล์ถูกต้อง)")
    print("- ถ้าเปลี่ยน/เพิ่มไฟล์ seed แล้ว แต่ยังไม่เข้า DB ให้เช็ค path: data/drugs.csv และ seed_drugs.json")

if __name__ == "__main__":
    with app.app_context():
        main()
