from http import HTTPStatus

from flask import Response, g, request
from pydantic import ValidationError

from app.auth.middleware import require_auth
from app.enums import ErrorMessage
from app.restaurants.orders.dtos import CreateOrderPayloadDTO
from app.restaurants.orders.enums import OrderSuccessMessage
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


@require_auth
def placeOrder(restaurant_id: str) -> tuple[Response, HTTPStatus]:
    """
    Handles POST /restaurants/<restaurant_id>/orders — place a new order.

    Returns:
        201 with order data on success.
        400 if required fields are invalid.
        402 if user's balance is insufficient.
        403 if the user owns current restaurant.
        404 if restaurant is not found.
        409 if restaurant is closed, an item is unavailable, or prices changed.
    """
    body = request.get_json() or {}
    try:
        payload = CreateOrderPayloadDTO.model_validate(body)
        result = OrderService().place_order(g.uid, restaurant_id, payload)
    except ValidationError as err:
        return json_response(
            message=ErrorMessage.RESPONSE_MSG_MISSING_FIELDS,
            errors=extract_validation_errors(err),
            status_code=HTTPStatus.BAD_REQUEST,
        )
    except (
        RestaurantNotFoundError,
        RestaurantClosedError,
        OwnRestaurantOrderError,
        ItemUnavailableError,
        PriceChangedError,
        InsufficientBalanceError,
    ) as err:
        return json_response(
            message=err.message, status_code=err.status_code, detail=err.detail
        )

    return json_response(
        message=OrderSuccessMessage.ORDER_PLACED,
        data=result.model_dump(by_alias=True),
        status_code=HTTPStatus.CREATED,
    )
