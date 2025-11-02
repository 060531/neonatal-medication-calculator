import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(basedir, 'app.db')  # ใช้ SQLite local
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # ✅ เพิ่มเติม
    SECRET_KEY = os.getenv('SECRET_KEY', 'my-secret-key')  # สำหรับ session/CSRF
