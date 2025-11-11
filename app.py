from flask import Flask
from extensions import db, migrate

def create_app(testing: bool = False):
    app = Flask(__name__)
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI="sqlite:///app.db",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        TESTING=testing,
        SECRET_KEY="dev",
    )

    db.init_app(app)
    migrate.init_app(app, db)

    try:
        from routes.core import bp as core_bp
        app.register_blueprint(core_bp)
    except Exception:
        pass

    from flask import current_app
    @app.template_global()
    def has_endpoint(name: str) -> bool:
        return name in current_app.view_functions

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
