from flask import Flask
from app import settings
from app.routes import main_bp

def create_app() -> Flask:
    """Create and return a configured application instance."""
    app = Flask(__name__)
    app.config.from_object(settings)

    app.register_blueprint(main_bp)

    return app
