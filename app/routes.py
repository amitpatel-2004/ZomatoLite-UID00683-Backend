from flask import Blueprint

from app.views import health_check_view

api_bp = Blueprint("api", __name__)

api_bp.route("/health", methods=["GET"])(health_check_view)
