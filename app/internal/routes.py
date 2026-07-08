from flask import Blueprint

from app.internal.views import process_csv_row

internal_bp = Blueprint("internal", __name__)

internal_bp.add_url_rule(
    "/csv/process-item", view_func=process_csv_row, methods=["POST"]
)
