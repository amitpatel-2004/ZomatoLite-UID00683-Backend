from http import HTTPStatus

from flask.typing import ResponseReturnValue

from app.constants import SERVER_HEALTHY_MESSAGE
from app.utils import json_response


def health_check_view() -> ResponseReturnValue:
    """Execute application monitoring health checks and return the server status.

    Endpoint:
        GET /api/v1/health

    Returns:
        ResponseReturnValue: A Flask response tuple containing a success message
        and an HTTPStatus.OK (200) status code payload.
    """

    return json_response(message=SERVER_HEALTHY_MESSAGE, status_code=HTTPStatus.OK)
