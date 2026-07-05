from flask import Blueprint

from app.auth.routes import auth_bp
from app.restaurants.routes import restaurants_bp
from app.views import health_check_view

api_bp = Blueprint("api", __name__)

api_bp.route("/health", methods=["GET"])(health_check_view)

api_bp.register_blueprint(auth_bp, url_prefix="/auth")
api_bp.register_blueprint(restaurants_bp, url_prefix="/restaurants")
