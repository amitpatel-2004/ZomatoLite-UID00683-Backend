from flask import Blueprint
from app.auth.views import LoginView, RegisterView

auth_bp = Blueprint("auth", __name__)

auth_bp.add_url_rule("/register", view_func=RegisterView.as_view("auth_register"))
auth_bp.add_url_rule("/login", view_func=LoginView.as_view("auth_login"))
