from flask import Blueprint

from app.restaurants.views import (
    MyRestaurantsView,
    RestaurantCollectionView,
    RestaurantEntityView,
)
from app.restaurants.menu_items.routes import menu_items_bp
from app.restaurants.orders.routes import orders_bp

restaurants_bp = Blueprint("restaurants", __name__)

restaurants_bp.add_url_rule(
    "/mine", view_func=MyRestaurantsView.as_view("restaurants_mine")
)
restaurants_bp.add_url_rule(
    "",
    view_func=RestaurantCollectionView.as_view("restaurants_collection"),
    methods=["GET", "POST"],
)
restaurants_bp.add_url_rule(
    "/<restaurant_id>",
    view_func=RestaurantEntityView.as_view("restaurants_entity"),
    methods=["GET", "PUT", "DELETE"],
)

restaurants_bp.register_blueprint(
    blueprint=menu_items_bp, url_prefix="/<restaurant_id>/menu-items"
)
restaurants_bp.register_blueprint(
    blueprint=orders_bp, url_prefix="/<restaurant_id>/orders"
)
