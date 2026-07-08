from flask import Blueprint

from app.restaurants.menu_items.csv.routes import csv_bp
from app.restaurants.menu_items.views import (
    MenuItemView,
    get_menu_items,
    upload_menu_item_image,
)

menu_items_bp = Blueprint("menu_items", __name__)

menu_items_bp.add_url_rule(
    "/image-upload", view_func=upload_menu_item_image, methods=["POST"]
)
menu_items_bp.add_url_rule("", view_func=get_menu_items, methods=["GET"])
menu_items_bp.add_url_rule(
    "",
    view_func=MenuItemView.as_view("menu_items_create"),
    methods=["POST"],
)
menu_items_bp.add_url_rule(
    "/<item_id>",
    view_func=MenuItemView.as_view("menu_items_entity"),
    methods=["GET", "PATCH", "DELETE"],
)
menu_items_bp.register_blueprint(blueprint=csv_bp, url_prefix="/csv")
