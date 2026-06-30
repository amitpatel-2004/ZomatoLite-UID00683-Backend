from flask import Blueprint

from app.restaurants.views import (
    MyRestaurantsView,
    RestaurantCollectionView,
    RestaurantEntityView,
)
from app.restaurants.menu_items.views import (
    MenuItemCollectionView,
    MenuItemEntityView,
    MenuItemImageUploadView,
)

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
restaurants_bp.add_url_rule(
    "/<restaurant_id>/menu-items/image-upload",
    view_func=MenuItemImageUploadView.as_view("menu_items_image_upload"),
)
restaurants_bp.add_url_rule(
    "/<restaurant_id>/menu-items",
    view_func=MenuItemCollectionView.as_view("menu_items_collection"),
    methods=["GET", "POST"],
)
restaurants_bp.add_url_rule(
    "/<restaurant_id>/menu-items/<item_id>",
    view_func=MenuItemEntityView.as_view("menu_items_entity"),
    methods=["GET", "PUT", "DELETE"],
)
