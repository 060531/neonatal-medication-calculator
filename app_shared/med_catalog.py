# app_shared/med_catalog.py
from __future__ import annotations
import json
from pathlib import Path
from string import ascii_uppercase

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "meds_catalog.json"

def load_meds(path: Path = CATALOG) -> list[dict]:
    meds = json.loads(path.read_text(encoding="utf-8"))

    # ---- validation กันพังเงียบ ๆ ระยะยาว ----
    seen = set()
    for i, m in enumerate(meds, start=1):
        label = (m.get("label") or "").strip()
        ep = (m.get("endpoint") or "").strip()
        if not label or not ep:
            raise ValueError(f"[med_catalog] item#{i} ต้องมี label และ endpoint")
        if ep in seen:
            raise ValueError(f"[med_catalog] endpoint ซ้ำ: {ep}")
        seen.add(ep)

    return meds

def group_meds_by_letter(meds: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {ch: [] for ch in ascii_uppercase}
    for m in meds:
        label = (m.get("label") or "").strip()
        ch = (label[0].upper() if label else "#")
        if ch in groups:
            groups[ch].append(m)

    for ch in groups:
        groups[ch].sort(key=lambda x: (x.get("label") or "").lower())

    # เอาเฉพาะตัวอักษรที่มีข้อมูลจริง
    return {ch: groups[ch] for ch in ascii_uppercase if groups[ch]}

def build_ctx_for_admin_page() -> dict:
    meds = load_meds()
    groups = group_meds_by_letter(meds)
    letters = list(groups.keys())
    return {"meds": meds, "groups": groups, "letters": letters}
