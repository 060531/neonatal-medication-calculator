# routes/compat.py
from flask import Blueprint

compat_bp = Blueprint("compat", __name__)

@compat_bp.route("/")
def compatibility_page():
    return "Compatibility page (stub) — implement me", 200
