# config.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'app.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
    UPDATE_DATE = os.getenv("UPDATE_DATE", "2025-11-09")
    APP_DATA_DIR = os.getenv("APP_DATA_DIR", str(BASE_DIR / "data"))
