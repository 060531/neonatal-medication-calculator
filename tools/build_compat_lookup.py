#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SRC = ROOT / "data" / "seed_compatibility.json"
OUT_DIR = ROOT / "static"
OUT_JSON = OUT_DIR / "compat_lookup.json"
OUT_MIN = OUT_DIR / "compat_lookup.min.json"

def norm(s):
    return (s or "").strip()

def get(d, *keys, default=""):
    for k in keys:
        if isinstance(d, dict) and k in d and d[k] is not None:
            return d[k]
    return default

def main():
    if not SRC.exists():
        raise SystemExit(f"❌ Missing source: {SRC}")

    raw = json.loads(SRC.read_text(encoding="utf-8"))

    # รองรับทั้ง: list / dict{pairs:[...]} / dict mapping
    if isinstance(raw, list):
        pairs = raw
    elif isinstance(raw, dict):
        # ถ้าเป็น dict mapping อยู่แล้ว
        if all(isinstance(k, str) for k in raw.keys()) and not any(k in raw for k in ("pairs","items","data","records","compatibilities")):
            OUT_DIR.mkdir(parents=True, exist_ok=True)
            out_obj = {str(k).strip().lower(): v for k, v in raw.items()}
            OUT_JSON.write_text(json.dumps(out_obj, ensure_ascii=False, indent=2), encoding="utf-8")
            OUT_MIN.write_text(json.dumps(out_obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
            print(f"✅ wrote: {OUT_JSON}")
            print(f"✅ wrote: {OUT_MIN}")
            return

        for key in ("pairs", "compatibilities", "items", "data", "records"):
            if key in raw and isinstance(raw[key], list):
                pairs = raw[key]
                break
        else:
            # fallback: ถ้า dict แต่ไม่เจอ list ให้ถือเป็นว่าง
            pairs = []
    else:
        raise SystemExit("❌ Unsupported JSON format")

    out_obj = {}

    for r in pairs:
        a = norm(get(r, "drug_a", "a", "drugA", "DrugA"))
        b = norm(get(r, "drug_b", "b", "drugB", "DrugB"))
        if not a or not b:
            continue

        status = get(r, "status", "code", "result", default="ND")
        note_th = get(r, "note_th", "noteTH", "note_thai", default="")
        note_en = get(r, "note_en", "noteEN", "note_english", default="")
        detail  = get(r, "detail", "details", default="")

        rec = {
            "drug_a": a,
            "drug_b": b,
            "status": status,
            "note_th": note_th,
            "note_en": note_en,
            "detail": detail,
        }

        k1 = f"{a}||{b}".lower()
        k2 = f"{b}||{a}".lower()
        out_obj[k1] = rec
        out_obj[k2] = rec

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out_obj, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MIN.write_text(json.dumps(out_obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    print(f"✅ wrote: {OUT_JSON}  (keys={len(out_obj)})")
    print(f"✅ wrote: {OUT_MIN}")

if __name__ == "__main__":
    main()
