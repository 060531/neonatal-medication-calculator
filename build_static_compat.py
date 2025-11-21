# build_static_compat.py
from pathlib import Path

from app import create_app
from flask import render_template

BASE_DIR = Path(__file__).resolve().parent
OUT_PATH = BASE_DIR / "docs" / "compatibility.html"


def build_compat_page():
    app = create_app()

    with app.app_context():
        # static_build=True -> base.html จะเซ็ต use_static = True
        html = render_template("compatibility.html", static_build=True)

    OUT_PATH.write_text(html, encoding="utf-8")
    print(f"✅ wrote {OUT_PATH}")


if __name__ == "__main__":
    build_compat_page()
