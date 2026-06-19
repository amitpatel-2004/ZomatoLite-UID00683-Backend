from flask import Flask
from flask_cors import CORS 

from app.enums import ApiVersionPrefix
from app.routes import api_bp
from app.settings import ALLOWED_ORIGINS


def create_app() -> Flask:
    """Create and return a configured application instance.

    Returns:
        Flask: An initialized and configured Flask application instance ready
        to handle routing contexts.
    """
    app = Flask(__name__)

    CORS(app, origins=ALLOWED_ORIGINS)


    app.register_blueprint(api_bp, url_prefix=ApiVersionPrefix.V1.value)

    return app
