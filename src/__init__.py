from flask import Flask, jsonify
from src.config import Config
from src.shared.firebase import init_firebase


def create_app(config_class=Config):
    """Create and return a configured application instance."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    init_firebase()

    @app.route('/health', methods=['GET'])
    def health_check():
        """Verify the server status."""
        return jsonify({
            "status": "healthy",
            "message": "Server is running!"
        }), 200

    return app
