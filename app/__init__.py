from flask import Flask

from app.enums import ApiVersionPrefix
from app.routes import api_bp


def create_app() -> Flask:
    """Create and return a configured application instance.

    Returns:
        Flask: An initialized and configured Flask application instance ready
        to handle routing contexts.
    """
    app = Flask(__name__)

    app.register_blueprint(api_bp, url_prefix=ApiVersionPrefix.V1.value)

    return app
