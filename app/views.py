from http import HTTPStatus

from flask import Response

from app.constants import RESPONSE_MSG_HEALTH_OK
from app.utils import json_response


def health_check_view() -> tuple[Response, HTTPStatus]:
    """Execute application monitoring health checks and return the server status.

    Endpoint:
        GET /api/v1/health

    Returns:
        tuple[Response, HTTPStatus]: A Flask response tuple containing a success message
        and an HTTPStatus.OK (200) status code payload.
    """

    return json_response(message=RESPONSE_MSG_HEALTH_OK, status_code=HTTPStatus.OK)
