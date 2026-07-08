from functools import wraps
from http import HTTPStatus
from typing import Callable

from flask import request
from google.auth.transport import requests
from google.oauth2 import id_token

from app.internal.enums import InternalErrorMessage
from app.settings import PUBSUB_PUSH_AUDIENCE
from app.utils import json_response

_google_auth_request = requests.Request()


def require_pubsub_push(f: Callable) -> Callable:
    """Protect a route by validating the Pub/Sub push subscription's OIDC token.

    Args:
        f: The view function to protect.

    Returns:
        The wrapped function.

    Raises:
        HTTP 401 Unauthorized: If the Authorization header is missing or the token is invalid.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header: str | None = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return json_response(
                message=InternalErrorMessage.RESPONSE_MSG_PUSH_TOKEN_MISSING,
                status_code=HTTPStatus.UNAUTHORIZED,
            )

        token = auth_header.split("Bearer ")[1].strip()

        try:
            id_token.verify_oauth2_token(
                token, _google_auth_request, audience=PUBSUB_PUSH_AUDIENCE
            )
        except ValueError:
            return json_response(
                message=InternalErrorMessage.RESPONSE_MSG_PUSH_TOKEN_INVALID,
                status_code=HTTPStatus.UNAUTHORIZED,
            )

        return f(*args, **kwargs)

    return decorated
