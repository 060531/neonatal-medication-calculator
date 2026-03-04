from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()   # ไม่ส่ง app เข้าไป
migrate = Migrate()
