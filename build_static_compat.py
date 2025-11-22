from pathlib import Path
import json

from flask import render_template
from app import create_app  # ใช้ฟังก์ชันสร้าง Flask app

ROOT_DIR = Path(__file__).resolve().parent
DATA_FILE = ROOT_DIR / "data" / "seed_compatibility.json"
DOCS_DIR = ROOT_DIR / "docs"


def status_to_code(s: str) -> str:
    if not s:
        return "ND"
    t = str(s).strip().lower()

    if t.startswith("comp") or t in {"c", "yes", "true", "1", "เข้ากันได้"}:
        return "C"
    if t.startswith("incomp") or t in {
        "i",
        "no",
        "false",
        "0",
        "ห้ามผสม",
        "ไม่เข้ากัน",
        "ควรหลีกเลี่ยง",
    }:
        return "I"
    if t.startswith("uncer") or t in {"u", "ไม่แน่ชัด"}:
        return "U"
    if t in {"nd", "unknown", "no data", "ไม่มีข้อมูล"}:
        return "ND"
    return "ND"


def load_compat_pairs():
    """อ่านข้อมูลจาก data/seed_compatibility.json ให้เป็น list ของคู่ยา + รวบรวมชื่อยา"""
    raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    pairs = []
    drug_names = set()

    for row in raw:
        a = row.get("drug_a") or row.get("drug") or ""
        b = row.get("drug_b") or row.get("co_drug") or ""
        a = a.strip()
        b = b.strip()
        if not a or not b or a == b:
            continue

        code = status_to_code(row.get("status"))
        source = row.get("source") or ""
        note = row.get("note") or ""

        pairs.append(
            {
                "drug_a": a,
                "drug_b": b,
                "status": code,
                "source": source,
                "note": note,
            }
        )

        drug_names.add(a)
        drug_names.add(b)

    fallback = sorted(drug_names, key=lambda x: x.lower())
    return pairs, fallback


def build_compat_page():
    app = create_app()

    compat_pairs, fallback = load_compat_pairs()

    DOCS_DIR.mkdir(exist_ok=True)

    # ✨ จุดสำคัญ: ต้องมีทั้ง app_context และ test_request_context
    with app.app_context():
        with app.test_request_context("/compatibility"):
            html = render_template(
                "compatibility.html",
                use_static=True,
                drugs=None,
                compat_pairs=compat_pairs,
                fallback_names=fallback,
                status_code=None,
                status_text=None,
                compat=None,
                drug_a_name=None,
                drug_b_name=None,
            )

    out_file = DOCS_DIR / "compatibility.html"
    out_file.write_text(html, encoding="utf-8")
    print(f"✅ wrote {out_file}")


if __name__ == "__main__":
    build_compat_page()
