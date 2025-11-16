# routes/routes_compatibility.py
import json
import re
import string
from collections import OrderedDict
from pathlib import Path

from flask import (
    Blueprint,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask.cli import with_appcontext
import click

from extensions import db
from models import Drug, Compatibility, AccessLog

compat_bp = Blueprint("compat", __name__)

# ===== Utility: path / normalize / status mapping =====


def _base_dir() -> Path:
    # โฟลเดอร์ root ของโปรเจกต์ (ที่มี app.py)
    return Path(current_app.root_path).resolve()


def _data_dir() -> Path:
    return _base_dir() / "data"


def _norm_txt(s: str) -> str:
    return " ".join((s or "").strip().lower().split())


def canonicalize_name(s: str) -> str:
    """
    แปลงชื่อยาให้ standardized:
    - ตัด space เกิน
    - lower-case
    - แก้สะกดผิดยอดฮิต
    - ลบคำต่อท้ายอย่าง ' small dose', ' continuous'
    """
    if not s:
        return ""
    low = re.sub(r"\s+", " ", s.strip().lower())
    low = low.replace("meropenam", "meropenem")
    for bad in (" small dose", " continuous"):
        if low.endswith(bad):
            low = low[: -len(bad)]
    return low


def status_to_code(s: str) -> str:
    """
    Map text → code:
      C  = compatible
      I  = incompatible
      U  = uncertain
      ND = no data
    """
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


# ===== meta loader จาก data/seed_compatibility.json =====
_pair_meta_cache = None


def load_pair_meta():
    global _pair_meta_cache
    if _pair_meta_cache is not None:
        return _pair_meta_cache

    meta_map = {}
    p = _data_dir() / "seed_compatibility.json"
    if not p.exists():
        _pair_meta_cache = meta_map
        return meta_map

    try:
        items = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        _pair_meta_cache = meta_map
        return meta_map

    for it in items:
        a = _norm_txt(it.get("drug", ""))
        b = _norm_txt(it.get("co_drug", ""))
        if not a or not b or a == b:
            continue
        payload = {
            "en": it.get("en"),
            "th": it.get("th"),
            "detail": it.get("detail"),
            "note": it.get("note"),
        }
        k = (min(a, b), max(a, b))
        meta_map[k] = payload

    _pair_meta_cache = meta_map
    return meta_map


def get_pair_meta(name_a: str, name_b: str):
    a, b = _norm_txt(name_a), _norm_txt(name_b)
    if not a or not b or a == b:
        return None
    return load_pair_meta().get((min(a, b), max(a, b)))


def get_all_drugs_for_select():
    q = Drug.query.filter(Drug.generic_name.isnot(None)).order_by(
        db.func.lower(Drug.generic_name)
    )
    return [{"id": d.id, "generic_name": d.generic_name} for d in q.all()]


def get_drug_name(drug_id: int):
    row = Drug.query.get(drug_id)
    return row.generic_name if row else None


def group_meds_by_letter(
    meds, key_preference=("label", "generic_name", "name", "drug", "title")
) -> OrderedDict:
    if not meds:
        return OrderedDict()

    groups = {ch: [] for ch in string.ascii_uppercase}
    groups["#"] = []

    for item in meds:
        name = None
        if isinstance(item, dict):
            for k in key_preference:
                if item.get(k):
                    name = str(item[k]).strip()
                    break
        else:
            for k in key_preference:
                v = getattr(item, k, None)
                if v:
                    name = str(v).strip()
                    break

        if not name:
            groups["#"].append(item)
            continue

        first = name[0].upper()
        if first in groups:
            groups[first].append(item)
        else:
            groups["#"].append(item)

    ordered = OrderedDict()
    for ch in string.ascii_uppercase:
        if groups[ch]:
            ordered[ch] = groups[ch]
    if groups["#"]:
        ordered["#"] = groups["#"]
    return ordered


# ===== Logging =====
@compat_bp.before_app_request
def log_request():
    # log เฉพาะ request ที่วิ่งเข้า blueprint นี้
    if request.blueprint != compat_bp.name:
        return

    log = AccessLog(
        endpoint=request.path,
        method=request.method,
        remote_addr=request.remote_addr,
        user_agent=request.user_agent.string,
    )
    db.session.add(log)
    db.session.commit()


# ===== Views: UI =====
@compat_bp.route("/compatibility", methods=["GET", "POST"], endpoint="compat_index")
def compat_index():
    """
    หน้าเลือกยาสองตัว (ใช้ UI ใหม่จาก compatibility.html)
    """
    drugs = get_all_drugs_for_select()
    groups = group_meds_by_letter(drugs, key_preference=("generic_name",))
    error = None

    selected_drug_id = None
    selected_co_drug_id = None

    if request.method == "POST":
        selected_drug_id = request.form.get("drug_a")
        selected_co_drug_id = request.form.get("drug_b")

        if not selected_drug_id or not selected_co_drug_id:
            error = "กรุณาเลือกยาทั้งสองตัว"
        elif selected_drug_id == selected_co_drug_id:
            error = "กรุณาเลือกยาคนละชนิดกัน"
        else:
            return redirect(
                url_for(
                    "compat.compat_result",
                    drug_a_id=selected_drug_id,
                    drug_b_id=selected_co_drug_id,
                )
            )

    return render_template(
        "compatibility.html",      # ใช้หน้าใหม่
        drugs=drugs,
        groups=groups,
        error=error,
        selected_drug_id=selected_drug_id,
        selected_co_drug_id=selected_co_drug_id,
    )

@compat_bp.route("/compatibility/result", methods=["GET"], endpoint="compat_result")
def compat_result():
    """
    แสดงผล compatibility ของคู่ยา ด้วย UI ใหม่ (compatibility_result.html)
    """
    drug_a_id = request.args.get("drug_a_id", type=int)
    drug_b_id = request.args.get("drug_b_id", type=int)

    if not drug_a_id or not drug_b_id:
        return redirect(url_for("compat.compat_index"))

    a_id, b_id = sorted([drug_a_id, drug_b_id])
    compat = Compatibility.query.filter_by(drug_id=a_id, co_drug_id=b_id).first()

    drug_a_name = get_drug_name(drug_a_id) or f"ID {drug_a_id}"
    drug_b_name = get_drug_name(drug_b_id) or f"ID {drug_b_id}"

    meta = get_pair_meta(drug_a_name, drug_b_name)

    raw_status = compat.status if compat else "ND"
    code = status_to_code(raw_status)  # ใช้ helper ด้านบนไฟล์

    note = compat.note if compat and compat.note else ""

    return render_template(
        "compatibility_result.html",
        code=code,
        status=raw_status,
        status_code=code,
        drug1_name=drug_a_name,
        drug2_name=drug_b_name,
        meta=meta,
        note=note,
    )

# ===== JSON API =====
@compat_bp.get("/api/compatibility")
def api_compatibility():
    """
    GET /api/compatibility?drug_a=1&drug_b=2
    """
    drug_a_id = request.args.get("drug_a", type=int)
    drug_b_id = request.args.get("drug_b", type=int)

    if not drug_a_id or not drug_b_id:
        return jsonify({"error": "missing drug_a or drug_b"}), 400

    a_id, b_id = sorted([drug_a_id, drug_b_id])
    compat = Compatibility.query.filter_by(drug_id=a_id, co_drug_id=b_id).first()

    drug_a_name = get_drug_name(drug_a_id)
    drug_b_name = get_drug_name(drug_b_id)

    meta = get_pair_meta(drug_a_name or "", drug_b_name or "")

    return jsonify(
        {
            "drug_a": {"id": drug_a_id, "name": drug_a_name},
            "drug_b": {"id": drug_b_id, "name": drug_b_name},
            "status": compat.status if compat else "ND",
            "source": compat.source if compat else None,
            "note": compat.note if compat else None,
            "meta": meta,
        }
    )


@compat_bp.get("/api/drugs")
def api_drugs():
    """
    GET /api/drugs?q=mero → สำหรับ auto-complete
    """
    q = request.args.get("q", "", type=str).strip()
    query = Drug.query
    if q:
        like = f"%{q.lower()}%"
        query = query.filter(db.func.lower(Drug.generic_name).like(like))

    rows = query.order_by(db.func.lower(Drug.generic_name)).limit(50).all()
    return jsonify(
        [
            {
                "id": d.id,
                "generic_name": d.generic_name,
                "brand_name": d.brand_name,
            }
            for d in rows
        ]
    )

# ===== CLI command: import-compat =====
@compat_bp.cli.command("import-compat-json")
@click.argument("json_file")
@click.option(
    "--truncate",
    is_flag=True,
    default=False,
    help="ลบข้อมูล Compatibility เดิมทั้งหมดก่อน import",
)
@with_appcontext
def import_compat_json(json_file: str, truncate: bool):
    """
    ใช้งาน: flask --app app compat import-compat-json data/seed_compatibility.json --truncate

    นำเข้าข้อมูลจากไฟล์ JSON ที่เป็น list:
      [
        {"drug": "...", "co_drug": "...", "status": "...", "source": "...", "note": "..."},
        ...
      ]
    """
    path = Path(json_file)
    if not path.exists():
        click.echo(f"[ERROR] ไม่พบไฟล์: {path}")
        return

    click.echo(f"อ่านไฟล์: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(data, list):
        click.echo("[ERROR] ไฟล์ JSON ต้องเป็น list ของ objects (rows)")
        return

    if truncate:
        click.echo("ลบ Compatibility เดิมทั้งหมด...")
        Compatibility.query.delete()
        db.session.commit()

    created_drugs = 0
    updated_drugs = 0
    created_pairs = 0
    updated_pairs = 0
    skipped_rows = 0

    def _status_to_code(s: str) -> str:
        return status_to_code(s)

    for row in data:
        name_a = canonicalize_name(row.get("drug"))
        name_b = canonicalize_name(row.get("co_drug"))
        if not name_a or not name_b or name_a == name_b:
            skipped_rows += 1
            continue

        # หา / สร้าง Drug A
        drug_a = Drug.query.filter(
            db.func.lower(Drug.generic_name) == name_a
        ).first()
        if not drug_a:
            drug_a = Drug(generic_name=name_a)
            db.session.add(drug_a)
            created_drugs += 1

        # หา / สร้าง Drug B
        drug_b = Drug.query.filter(
            db.func.lower(Drug.generic_name) == name_b
        ).first()
        if not drug_b:
            drug_b = Drug(generic_name=name_b)
            db.session.add(drug_b)
            created_drugs += 1

        # ให้ได้ id ก่อน
        db.session.flush()
        a_id, b_id = sorted([drug_a.id, drug_b.id])

        code = _status_to_code(row.get("status"))
        source = row.get("source")
        note = row.get("note")

        compat = Compatibility.query.filter_by(drug_id=a_id, co_drug_id=b_id).first()
        if compat:
            old_state = (compat.status, compat.source, compat.note)
            compat.status = code
            compat.source = source
            compat.note = note
            if old_state != (compat.status, compat.source, compat.note):
                updated_pairs += 1
        else:
            compat = Compatibility(
                drug_id=a_id,
                co_drug_id=b_id,
                status=code,
                source=source,
                note=note,
            )
            db.session.add(compat)
            created_pairs += 1

    db.session.commit()
    click.echo("✅ Import summary:")
    click.echo(f"  Drugs created : {created_drugs}")
    click.echo(f"  Pairs created : {created_pairs}")
    click.echo(f"  Pairs updated : {updated_pairs}")
    click.echo(f"  Rows skipped  : {skipped_rows}")
