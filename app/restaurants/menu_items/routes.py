from flask import Blueprint

from app.restaurants.menu_items.views import (
    MenuItemImageUploadView,
    MenuItemCollectionView,
    MenuItemEntityView,
)

menu_items_bp = Blueprint("menu_items", __name__)

menu_items_bp.add_url_rule(
    "/image-upload",
    view_func=MenuItemImageUploadView.as_view("menu_items_image_upload"),
)
menu_items_bp.add_url_rule(
    "",
    view_func=MenuItemCollectionView.as_view("menu_items_collection"),
    methods=["GET", "POST"],
)
menu_items_bp.add_url_rule(
    "/<item_id>",
    view_func=MenuItemEntityView.as_view("menu_items_entity"),
    methods=["GET", "PATCH", "DELETE"],
)
