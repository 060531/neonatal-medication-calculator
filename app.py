from flask import Flask
from flask_migrate import Migrate
from extensions import db

def create_app():
    app = Flask(__name__)
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI="sqlite:///app.db",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    db.init_app(app)
    Migrate(app, db)

    # นำเข้า models หลัง init_app เพื่อให้ตารางถูกประกาศใน metadata
    import models  # noqa: F401

    @app.route("/healthz")
    def healthz():
        return "ok"

    return app

# สำหรับใช้งานกับ FLASK_APP=app:app
app = create_app()
