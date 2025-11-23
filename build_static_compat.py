# build_static_compat.py
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "data" / "seed_compatibility.json"
DST = ROOT / "docs" / "static" / "compat_lookup.json"

def canonical(name: str) -> str:
    """ปรับชื่อยาให้เป็นมาตรฐาน: ตัดช่องว่างหัว–ท้าย, เว้นวรรคเดียว, พิมพ์เล็กทั้งหมด"""
    return " ".join(name.strip().lower().split())

def main():
    raw = json.loads(SRC.read_text(encoding="utf-8"))
    lookup = {}

    for item in raw:
        a = (item.get("drug_a") or "").strip()
        b = (item.get("drug_b") or "").strip()
        if not a or not b:
            continue

        key = f"{canonical(a)}|{canonical(b)}"

        status_raw = (item.get("status") or "").strip().upper()
        if status_raw.startswith("C"):
            status = "C"
        elif status_raw.startswith("I"):
            status = "I"
        elif status_raw.startswith("U"):
            status = "U"
        elif status_raw.startswith("ND") or status_raw.startswith("N"):
            status = "ND"
        else:
            status = "ND"

        lookup[key] = {
            "drug_a": a,
            "drug_b": b,
            "status": status,
            "summary_th": item.get("summary_th") or item.get("note_th") or "",
            "summary_en": item.get("summary_en") or item.get("note_en") or "",
            "reference": item.get("reference") or item.get("source") or "",
        }

    DST.parent.mkdir(parents=True, exist_ok=True)
    DST.write_text(json.dumps(lookup, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ Wrote {len(lookup)} pairs → {DST}")

if __name__ == "__main__":
    main()
