from http import HTTPStatus

from app.exceptions import CustomException
from app.restaurants.orders.constants import (
    RESPONSE_MSG_INSUFFICIENT_BALANCE,
    RESPONSE_MSG_ITEM_UNAVAILABLE,
    RESPONSE_MSG_ORDER_NOT_FOUND,
    RESPONSE_MSG_OWN_RESTAURANT_ORDER,
    RESPONSE_MSG_PRICE_CHANGED,
    RESPONSE_MSG_RESTAURANT_CLOSED,
)


class OrderNotFoundError(CustomException):
    message = RESPONSE_MSG_ORDER_NOT_FOUND
    status_code = HTTPStatus.NOT_FOUND


class InsufficientBalanceError(CustomException):
    message = RESPONSE_MSG_INSUFFICIENT_BALANCE
    status_code = HTTPStatus.PAYMENT_REQUIRED


class RestaurantClosedError(CustomException):
    message = RESPONSE_MSG_RESTAURANT_CLOSED
    status_code = HTTPStatus.CONFLICT


class ItemUnavailableError(CustomException):
    message = RESPONSE_MSG_ITEM_UNAVAILABLE
    status_code = HTTPStatus.CONFLICT


class PriceChangedError(CustomException):
    message = RESPONSE_MSG_PRICE_CHANGED
    status_code = HTTPStatus.CONFLICT


class OwnRestaurantOrderError(CustomException):
    message = RESPONSE_MSG_OWN_RESTAURANT_ORDER
    status_code = HTTPStatus.FORBIDDEN
