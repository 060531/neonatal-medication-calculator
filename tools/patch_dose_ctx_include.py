from pathlib import Path
import re

TEMPL_DIR = Path("templates")
files = sorted(TEMPL_DIR.glob("*_dose.html"))

include_line = '{% include "_dose_ctx_block.html" %}\n'

def inject(html: str) -> str:
    # idempotent: ถ้ามี include หรือมี id ที่ต้องใช้แล้ว ข้าม
    if '_dose_ctx_block.html' in html or 'id="pmaText"' in html:
        return html

    # ใส่หลัง </h1> ก่อน (มักอยู่หัวหน้า)
    m = re.search(r"</h1\s*>", html, flags=re.IGNORECASE)
    if m:
        i = m.end()
        return html[:i] + "\n" + include_line + html[i:]

    # fallback: ใส่หลัง <body>
    m = re.search(r"<body[^>]*>", html, flags=re.IGNORECASE)
    if m:
        i = m.end()
        return html[:i] + "\n" + include_line + html[i:]

    # fallback สุดท้าย: แปะหัวไฟล์
    return include_line + html

changed = 0
for f in files:
    s = f.read_text(encoding="utf-8")
    ns = inject(s)
    if ns != s:
        f.write_text(ns, encoding="utf-8")
        changed += 1

print(f"patched: {changed}/{len(files)}")
