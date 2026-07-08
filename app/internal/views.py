import base64
import json
from http import HTTPStatus

from flask import Response, request

from app.internal.enums import CsvRowProcessingOutcome
from app.internal.middleware import require_pubsub_push
from app.internal.service import CsvRowProcessingService
from app.restaurants.menu_items.csv.enums import CsvUploadSuccessMessage
from app.utils import json_response


@require_pubsub_push
def process_csv_row() -> tuple[Response, HTTPStatus]:
    """Handles POST /internal/csv/process-item — Pub/Sub push target for single CSV row.

    Returns:
        200 once the row is recorded, whether it succeeded or failed.
    """
    body = request.get_json() or {}
    data = base64.b64decode(body["message"]["data"]).decode("utf-8")
    row = json.loads(data)

    outcome = CsvRowProcessingService().process_row(row)

    if outcome == CsvRowProcessingOutcome.PROCESSED:
        return json_response(message=CsvUploadSuccessMessage.ROW_ALREADY_PROCESSED)
    if outcome == CsvRowProcessingOutcome.FAILED:
        return json_response(message=CsvUploadSuccessMessage.ROW_RECORDED_AS_FAILED)

    return json_response(message=CsvUploadSuccessMessage.ROW_PROCESSED_SUCCESSFULLY)
