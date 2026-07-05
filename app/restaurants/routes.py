from flask import Blueprint

from app.restaurants.views import (
    RestaurantView,
    get_owner_restaurants,
    get_all_restaurants,
)
from app.restaurants.menu_items.routes import menu_items_bp
from app.restaurants.orders.routes import orders_bp

restaurants_bp = Blueprint("restaurants", __name__)

restaurants_bp.add_url_rule("/mine", view_func=get_owner_restaurants, methods=["GET"])
restaurants_bp.add_url_rule(
    "",
    view_func=get_all_restaurants,
    methods=["GET"],
)
restaurants_bp.add_url_rule(
    "",
    view_func=RestaurantView.as_view("restaurants_create"),
    methods=["POST"],
)
restaurants_bp.add_url_rule(
    "/<restaurant_id>",
    view_func=RestaurantView.as_view("restaurants_entity"),
    methods=["GET", "PATCH", "DELETE"],
)

restaurants_bp.register_blueprint(
    blueprint=menu_items_bp, url_prefix="/<restaurant_id>/menu-items"
)
restaurants_bp.register_blueprint(
    blueprint=orders_bp, url_prefix="/<restaurant_id>/orders"
)
