import pytest
from app import create_app
from extensions import db

@pytest.fixture()
def app():
    app = create_app(testing=True)
    with app.app_context():
        yield app

@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def db_session(app):
    db.drop_all()
    db.create_all()
    try:
        yield db.session
    finally:
        db.session.remove()
        db.drop_all()
