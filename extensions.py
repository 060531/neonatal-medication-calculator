from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

# --- Compatibility shim for legacy tests calling db.get_engine(app) ---
def _compat_get_engine(self, bind_key=None, **kwargs):
    try:
        from flask import Flask as _Flask
    except Exception:
        _Flask = object
    if isinstance(bind_key, _Flask) or bind_key is None:
        return self.engine
    return self.engines[bind_key]

SQLAlchemy.get_engine = _compat_get_engine
