from functools import wraps
from http import HTTPStatus
from typing import Callable

from firebase_admin import auth
from flask import g, request

from app.auth.enums import AuthErrorMessage
from app.auth.enums import UserRole
from app.constants import TOKEN_CLAIM_ROLE
from app.enums import ErrorMessage
from app.utils import json_response


def require_auth(f: Callable) -> Callable:
    """Protect a route by validating the Bearer token in the Authorization header.

    Args:
        f: The view function to protect.

    Returns:
        The wrapped function.

    Raises:
        HTTP 401 Unauthorized: If the Authorization header is missing, malformed,
            or contains an invalid/expired token.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header: str | None = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return json_response(
                message=AuthErrorMessage.RESPONSE_MSG_TOKEN_MISSING,
                status_code=HTTPStatus.UNAUTHORIZED,
            )

        id_token = auth_header.split("Bearer ")[1].strip()

        try:
            decoded_token = auth.verify_id_token(id_token)
        except (
            auth.InvalidIdTokenError,
            auth.ExpiredIdTokenError,
            auth.RevokedIdTokenError,
        ):
            return json_response(
                message=AuthErrorMessage.RESPONSE_MSG_TOKEN_INVALID,
                status_code=HTTPStatus.UNAUTHORIZED,
            )

        g.uid = decoded_token["uid"]
        g.role = decoded_token.get(TOKEN_CLAIM_ROLE, "customer")
        g.decoded_token = decoded_token

        return f(*args, **kwargs)

    return decorated


def require_role(*roles: UserRole) -> Callable:
    """Restrict a route to users whose role matches one of the given roles.

    Must be used together with @require_auth, and applied after it,
    so that g.role is already set when this decorator runs.

    Args:
        *roles: The UserRole values allowed to access this route.

    Returns:
        A decorator that wraps the view function with role enforcement.

    Raises:
        HTTP 403 Forbidden: If the authenticated user's role is not in *roles*.
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated(*args, **kwargs):
            if g.get("role") not in roles:
                return json_response(
                    message=ErrorMessage.RESPONSE_MSG_FORBIDDEN,
                    status_code=HTTPStatus.FORBIDDEN,
                )
            return f(*args, **kwargs)

        return decorated

    return decorator
