from pathlib import Path

targets = []
for root in ["templates", "docs"]:
    d = Path(root)
    if d.exists():
        targets += sorted(d.glob("*_dose*.html"))

need = {
    "patient_ctx": 'patient_ctx.js',
    "dose_page": 'dose_page.js',
    "dose_run": 'DosePage.run',
}

missing = []
for f in targets:
    s = f.read_text(encoding="utf-8", errors="ignore")
    miss = [k for k,v in need.items() if v not in s]
    if miss:
        missing.append((str(f), miss))

print(f"Found {len(targets)} dose pages.")
print(f"Missing in {len(missing)} files.\n")
for path, miss in missing:
    print(f"- {path}: missing {', '.join(miss)}")
