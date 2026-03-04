cat > tools/check_links.py <<'PY'
#!/usr/bin/env python3
import os
import sys
from html.parser import HTMLParser
from urllib.parse import urlsplit

IGNORE_SCHEMES = {"http", "https", "mailto", "tel", "data", "javascript"}

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []  # (tag, attr, value, lineno)

    def handle_starttag(self, tag, attrs):
        # tags ที่มักมีลิงก์ไฟล์
        want = {
            "a": "href",
            "link": "href",
            "script": "src",
            "img": "src",
            "source": "src",
        }
        if tag not in want:
            return
        attr_name = want[tag]
        for k, v in attrs:
            if k == attr_name and v:
                self.links.append((tag, attr_name, v.strip(), self.getpos()[0]))

def iter_html_files(target_path: str):
    if os.path.isfile(target_path):
        yield os.path.abspath(target_path)
        return
    for root, _, files in os.walk(target_path):
        for fn in files:
            if fn.lower().endswith((".html", ".htm")):
                yield os.path.abspath(os.path.join(root, fn))

def is_ignored(url: str) -> bool:
    u = url.strip()
    if not u:
        return True
    if u.startswith("#"):
        return True
    parts = urlsplit(u)
    if parts.scheme and parts.scheme.lower() in IGNORE_SCHEMES:
        return True
    return False

def clean_target(url: str) -> str:
    # ตัด query/fragment ออก เหลือเฉพาะ path
    parts = urlsplit(url.strip())
    path = parts.path or ""
    return path

def resolve_to_fs(source_file: str, href: str, root_dir: str) -> str | None:
    if is_ignored(href):
        return None

    path = clean_target(href)
    if not path or path == "/":
        return None

    # absolute path แบบ "/xxx" ใน GH Pages = อิง root_dir
    if path.startswith("/"):
        fs = os.path.join(root_dir, path.lstrip("/"))
    else:
        fs = os.path.join(os.path.dirname(source_file), path)

    fs = os.path.normpath(fs)

    # ถ้าลิงก์ลงท้ายด้วย "/" ให้ตีความเป็น index.html
    if fs.endswith(os.sep):
        fs = os.path.join(fs, "index.html")

    return fs

def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/check_links.py <docs_or_file_path>")
        sys.exit(2)

    target = sys.argv[1]
    target_abs = os.path.abspath(target)

    # root_dir: ถ้าส่งไฟล์มา ให้ใช้โฟลเดอร์เดียวกับไฟล์เป็น root; ถ้าส่งโฟลเดอร์มา ใช้โฟลเดอร์นั้น
    root_dir = os.path.dirname(target_abs) if os.path.isfile(target_abs) else target_abs

    html_files = sorted(set(iter_html_files(target_abs)))
    internal_links = 0
    missing = []  # (src, lineno, href, resolved_fs)

    for f in html_files:
        try:
            with open(f, "r", encoding="utf-8", errors="replace") as fp:
                content = fp.read()
        except Exception as e:
            missing.append((f, 0, f"[READ_ERROR] {e}", ""))
            continue

        p = LinkParser()
        p.feed(content)

        for tag, attr, href, lineno in p.links:
            fs = resolve_to_fs(f, href, root_dir)
            if fs is None:
                continue

            internal_links += 1

            # ถ้าลิงก์ชี้ไปโฟลเดอร์ที่มี index.html หรือไฟล์จริง
            if os.path.isdir(fs):
                fs2 = os.path.join(fs, "index.html")
                if not os.path.exists(fs2):
                    missing.append((f, lineno, href, fs2))
            else:
                if not os.path.exists(fs):
                    missing.append((f, lineno, href, fs))

    # Summary
    print("\n=== SUMMARY ===")
    print(f"HTML files scanned    : {len(html_files)}")
    print(f"Internal links found  : {internal_links}")
    print(f"Missing targets       : {len(missing)}")

    if missing:
        print("\n=== MISSING (first 60) ===")
        for i, (src, lineno, href, fs) in enumerate(missing[:60], 1):
            rel_src = os.path.relpath(src, root_dir)
            rel_fs = os.path.relpath(fs, root_dir) if fs else fs
            print(f"{i:02d}. {rel_src}:{lineno} -> {href}  [expected: {rel_fs}]")

        if len(missing) > 60:
            print(f"... and {len(missing) - 60} more")

    # exit code: มี missing ให้เป็น 1 (เหมาะกับ CI)
    sys.exit(1 if missing else 0)

if __name__ == "__main__":
    main()
PY

chmod +x tools/check_links.py
