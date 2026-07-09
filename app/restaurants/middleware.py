from functools import wraps
from flask import g, request
from http import HTTPStatus
from typing import Callable

from app.auth.enums import UserRole
from app.restaurants.service import RestaurantService
from app.restaurants.exceptions import RestaurantNotFoundError, NotRestaurantOwnerError
from app.utils import json_response
from app.enums import ErrorMessage


def require_owner(f: Callable) -> Callable:
    """Restrict a restaurant routes to their owners.

    Args:
        f: The view function to protect.

    Returns:
        A decorator that wraps the view function with ownership enforcement.

    Raises:
        HTTP 403 Forbidden: If the user is not the owner for the restaurant.
        HTTP 404 Not found: If restaurant not found or already deleted.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        view_args = request.view_args
        if g.get("role") != UserRole.OWNER:
            return json_response(
                message=ErrorMessage.RESPONSE_MSG_FORBIDDEN,
                status_code=HTTPStatus.FORBIDDEN,
            )
        if view_args and "restaurant_id" in view_args:
            restaurant_id: str = str(view_args["restaurant_id"])
            try:
                restaurant = RestaurantService().get_restaurant(restaurant_id)
            except RestaurantNotFoundError as err:
                return json_response(
                    message=err.message, status_code=err.status_code, detail=err.detail
                )
            if restaurant.owner_id != g.uid:
                return json_response(
                    message=NotRestaurantOwnerError.message,
                    status_code=NotRestaurantOwnerError.status_code,
                )
            kwargs["restaurant"] = restaurant
        return f(*args, **kwargs)

    return decorated
