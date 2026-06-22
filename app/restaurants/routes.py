from flask import Blueprint

from app.restaurants.views import (
    MenuItemCreateView,
    MenuItemDeleteView,
    MenuItemDetailView,
    MenuItemListView,
    MenuItemUpdateView,
    MenuItemUploadUrlView,
    MyRestaurantsView,
    RestaurantCreateView,
    RestaurantDeleteView,
    RestaurantDetailView,
    RestaurantListView,
    RestaurantUpdateView,
)

restaurants_bp = Blueprint("restaurants", __name__)

restaurants_bp.add_url_rule(
    "/mine", view_func=MyRestaurantsView.as_view("restaurants_mine")
)

restaurants_bp.add_url_rule(
    "/",
    view_func=RestaurantListView.as_view("restaurants_list"),
    methods=["GET"],
)
restaurants_bp.add_url_rule(
    "/",
    view_func=RestaurantCreateView.as_view("restaurants_create"),
    methods=["POST"],
)

restaurants_bp.add_url_rule(
    "/<restaurant_id>",
    view_func=RestaurantDetailView.as_view("restaurants_detail"),
    methods=["GET"],
)
restaurants_bp.add_url_rule(
    "/<restaurant_id>",
    view_func=RestaurantUpdateView.as_view("restaurants_update"),
    methods=["PUT"],
)
restaurants_bp.add_url_rule(
    "/<restaurant_id>",
    view_func=RestaurantDeleteView.as_view("restaurants_delete"),
    methods=["DELETE"],
)

restaurants_bp.add_url_rule(
    "/<restaurant_id>/menu-items/upload-url",
    view_func=MenuItemUploadUrlView.as_view("menu_items_upload_url"),
)

restaurants_bp.add_url_rule(
    "/<restaurant_id>/menu-items",
    view_func=MenuItemListView.as_view("menu_items_list"),
    methods=["GET"],
)
restaurants_bp.add_url_rule(
    "/<restaurant_id>/menu-items",
    view_func=MenuItemCreateView.as_view("menu_items_create"),
    methods=["POST"],
)

restaurants_bp.add_url_rule(
    "/<restaurant_id>/menu-items/<item_id>",
    view_func=MenuItemDetailView.as_view("menu_items_detail"),
    methods=["GET"],
)
restaurants_bp.add_url_rule(
    "/<restaurant_id>/menu-items/<item_id>",
    view_func=MenuItemUpdateView.as_view("menu_items_update"),
    methods=["PUT"],
)
restaurants_bp.add_url_rule(
    "/<restaurant_id>/menu-items/<item_id>",
    view_func=MenuItemDeleteView.as_view("menu_items_delete"),
    methods=["DELETE"],
)
