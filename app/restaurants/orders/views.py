from http import HTTPStatus

from flask import Response, g, request
from flask.views import MethodView
from pydantic import ValidationError

from app.auth.middleware import require_auth
from app.constants import RESPONSE_MSG_MISSING_FIELDS
from app.exceptions import CustomException
from app.restaurants.orders.constants import RESPONSE_MSG_ORDER_PLACED
from app.restaurants.orders.dtos import CreateOrderPayloadDTO
from app.restaurants.orders.exceptions import (
    InsufficientBalanceError,
    ItemUnavailableError,
    OwnRestaurantOrderError,
    PriceChangedError,
    RestaurantClosedError,
)
from app.restaurants.orders.service import OrderService
from app.restaurants.exceptions import RestaurantNotFoundError
from app.utils import extract_validation_errors, json_response


class OrdersEntityView(MethodView):
    """Handles POST /restaurants/<restaurant_id>/orders — place a new order."""

    decorators = [require_auth]

    def post(self, restaurant_id: str) -> tuple[Response, HTTPStatus]:
        """Place order at given restaurant for a user.

        Returns:
            201 with order data on success.
            400 if required fields are invalid.
            402 if user's balance is insufficient.
            403 if the user owns current restaurant.
            404 if restaurant is not found.
            409 if restaurant is closed, an item is unavailable, or prices changed.
            500 on unexpected errors.
        """
        body = request.get_json() or {}
        try:
            payload = CreateOrderPayloadDTO.model_validate(body)
        except ValidationError as err:
            return json_response(
                message=RESPONSE_MSG_MISSING_FIELDS,
                errors=extract_validation_errors(err),
                status_code=HTTPStatus.BAD_REQUEST,
            )

        try:
            result = OrderService().place_order(g.uid, restaurant_id, payload)
        except (
            RestaurantNotFoundError,
            RestaurantClosedError,
            OwnRestaurantOrderError,
            ItemUnavailableError,
            PriceChangedError,
            InsufficientBalanceError,
        ) as e:
            return json_response(
                message=e.message, status_code=e.status_code, detail=e.detail
            )
        except Exception:
            return json_response(
                message=CustomException.message,
                status_code=CustomException.status_code,
            )

        return json_response(
            message=RESPONSE_MSG_ORDER_PLACED,
            data=result.model_dump(by_alias=True),
            status_code=HTTPStatus.CREATED,
        )
