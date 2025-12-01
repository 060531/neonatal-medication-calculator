# tools/build_compat_lookup.py
from __future__ import annotations
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "seed_compatibility.json"
OUT = ROOT / "static" / "compat_lookup.json"
OUT_MIN = ROOT / "static" / "compat_lookup.min.json"

def canon(s: str) -> str:
    s = (s or "").strip().lower()
    s = s.replace("&", " and ")
    s = re.sub(r"\s+", " ", s)
    return s

def pair_key(a: str, b: str) -> str:
    a2, b2 = canon(a), canon(b)
    return "||".join(sorted([a2, b2]))

def merge_pref(old: dict, new: dict) -> dict:
    # keep old but fill missing with new (or override if new has stronger note)
    merged = dict(old)
    for k, v in new.items():
        if merged.get(k) in (None, "", []):
            merged[k] = v
    # ถ้า new มี note_th ให้ override เพื่อให้ข้อความล่าสุดชนะ
    if new.get("note_th"):
        merged["note_th"] = new["note_th"]
    if new.get("note_en"):
        merged["note_en"] = new["note_en"]
    return merged

def main() -> None:
    rows = json.loads(DATA.read_text(encoding="utf-8"))

    lookup: dict[str, dict] = {}
    for r in rows:
        a = r.get("drug_a", "")
        b = r.get("drug_b", "")
        if not a or not b:
            continue

        payload = {
            "drug_a": a,
            "drug_b": b,
            "status": (r.get("status") or "ND").upper(),
            "reference": r.get("reference", ""),
            "summary_th": r.get("summary_th", ""),
            "summary_en": r.get("summary_en", ""),
            "note_th": r.get("note_th", "") or r.get("note", ""),  # เผื่อเคยใช้ note เดิม
            "note_en": r.get("note_en", ""),
        }

        k = pair_key(a, b)
        if k in lookup:
            lookup[k] = merge_pref(lookup[k], payload)
        else:
            lookup[k] = payload

    OUT.write_text(json.dumps(lookup, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MIN.write_text(json.dumps(lookup, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"✅ wrote: {OUT}  (keys={len(lookup)})")
    print(f"✅ wrote: {OUT_MIN}")

if __name__ == "__main__":
    main()
