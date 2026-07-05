from flask import Blueprint

from app.restaurants.orders.views import placeOrder


orders_bp = Blueprint("orders", __name__)

orders_bp.add_url_rule("", view_func=placeOrder, methods=["POST"])
