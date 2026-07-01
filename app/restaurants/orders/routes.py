from flask import Blueprint

from app.restaurants.orders.views import OrdersEntityView


orders_bp = Blueprint("orders", __name__)

orders_bp.add_url_rule(
    "", view_func=OrdersEntityView.as_view("orders_entity"), methods=["POST"]
)
