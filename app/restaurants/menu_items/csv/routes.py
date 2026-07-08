from flask import Blueprint

from app.restaurants.menu_items.csv.views import request_csv_upload_url

csv_bp = Blueprint("menu_items_csv", __name__)

csv_bp.add_url_rule("/upload-url", view_func=request_csv_upload_url, methods=["POST"])
