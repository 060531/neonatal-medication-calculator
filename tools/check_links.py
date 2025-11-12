# tools/check_links.py
# -*- coding: utf-8 -*-
import re, json, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
tpl = ROOT / "templates" / "index.html"
docs = ROOT / "docs"
tool = ROOT / "tools" / "jinja_render.py"

# 1) ดึง endpoint จาก index.html (safe_button(endpoint, ...))
pat = re.compile(r"safe_button\(\s*['\"]([^'\"]+)['\"]\s*,")
endpoints = pat.findall(tpl.read_text(encoding="utf-8"))

# 2) โหลด URL_MAP จาก jinja_render.py แบบง่าย ๆ (อ่านเป็นสตริงแล้ว regex)
text = (tool).read_text(encoding="utf-8")
m = re.search(r"URL_MAP\s*=\s*\{([\s\S]*?)\}", text)
url_map = {}
if m:
    body = m.group(1)
    # คีย์แบบ "key": "value",
    pair_pat = re.compile(r'"([^"]+)"\s*:\s*"([^"]+)"')
    for k, v in pair_pat.findall(body):
        url_map[k] = v

# 3) รายชื่อไฟล์ docs ที่มีจริง (ไม่รวมโฟลเดอร์)
docs_set = {p.name for p in docs.glob("*.html")}

missing_map = []
missing_file = []
ok = []

for ep in sorted(set(endpoints)):
    # กติกา resolve: ถ้าไม่มีใน URL_MAP → เดาเป็น ./<ep>.html
    target = url_map.get(ep, f"./{ep}.html")
    target_name = target.split("./", 1)[-1]
    if ep not in url_map:
        missing_map.append((ep, target))
    if target_name not in docs_set:
        missing_file.append((ep, target_name))
    else:
        ok.append((ep, target_name))

print("=== SUMMARY ===")
print(f"Endpoints found     : {len(set(endpoints))}")
print(f"OK                  : {len(ok)}")
print(f"Need URL_MAP entry  : {len(missing_map)}")
print(f"Missing docs file   : {len(missing_file)}")

if missing_map:
    print("\n-- Need URL_MAP entries --")
    for ep, tgt in missing_map:
        print(f'  "{ep}": "{tgt}",')

if missing_file:
    print("\n-- Missing docs files --")
    for ep, name in missing_file:
        print(f"  endpoint='{ep}' -> docs/{name} (ไม่พบ)")

# exit code > 0 ถ้ามีข้อผิดพลาด
if missing_file:
    sys.exit(2)
elif missing_map:
    sys.exit(1)
