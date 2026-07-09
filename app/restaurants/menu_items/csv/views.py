from http import HTTPStatus

from flask import Response, request
from pydantic import ValidationError

from app.auth.middleware import require_auth
from app.constants import MAX_CSV_UPLOAD_SIZE_BYTES
from app.enums import ErrorMessage
from app.restaurants.dtos import RestaurantResponseDTO
from app.restaurants.menu_items.csv.dtos import CsvUploadUrlRequestDTO
from app.restaurants.menu_items.csv.enums import (
    CsvUploadErrorMessage,
    CsvUploadSuccessMessage,
)
from app.restaurants.menu_items.csv.service import CsvUploadService
from app.restaurants.middleware import require_owner
from app.utils import extract_validation_errors, json_response


@require_auth
@require_owner
def request_csv_upload_url(
    restaurant_id: str, restaurant: RestaurantResponseDTO
) -> tuple[Response, HTTPStatus]:
    """Generate a signed URL for uploading a menu items CSV file.

    Returns:
        200 with uploadUrl and uploadId on success.
        400 if fields are invalid or file size exceeds limit.
        403 if caller don't own the restaurant.
        404 if restaurant not found or deleted.
    """
    body = request.get_json() or {}
    try:
        payload = CsvUploadUrlRequestDTO.model_validate(body)
    except ValidationError as err:
        return json_response(
            message=ErrorMessage.RESPONSE_MSG_MISSING_FIELDS,
            errors=extract_validation_errors(err),
            status_code=HTTPStatus.BAD_REQUEST,
        )

    if payload.file_size > MAX_CSV_UPLOAD_SIZE_BYTES:
        return json_response(
            message=CsvUploadErrorMessage.FILE_SIZE_EXCEEDS_LIMIT,
            status_code=HTTPStatus.BAD_REQUEST,
        )

    result = CsvUploadService().generate_upload_url(restaurant_id, payload.content_type)

    return json_response(
        message=CsvUploadSuccessMessage.UPLOAD_URL_GENERATED,
        data=result.model_dump(by_alias=True),
    )
