from http import HTTPStatus

from app.exceptions import BaseHTTPException
from app.restaurants.orders.enums import OrderErrorMessage


class OrderNotFoundError(BaseHTTPException):
    message = OrderErrorMessage.ORDER_NOT_FOUND
    status_code = HTTPStatus.NOT_FOUND


class InsufficientBalanceError(BaseHTTPException):
    message = OrderErrorMessage.INSUFFICIENT_BALANCE
    status_code = HTTPStatus.PAYMENT_REQUIRED


class RestaurantClosedError(BaseHTTPException):
    message = OrderErrorMessage.RESTAURANT_CLOSED
    status_code = HTTPStatus.CONFLICT


class ItemUnavailableError(BaseHTTPException):
    message = OrderErrorMessage.ITEM_UNAVAILABLE
    status_code = HTTPStatus.CONFLICT


class PriceChangedError(BaseHTTPException):
    message = OrderErrorMessage.PRICE_CHANGED
    status_code = HTTPStatus.CONFLICT


class OwnRestaurantOrderError(BaseHTTPException):
    message = OrderErrorMessage.OWN_RESTAURANT_ORDER
    status_code = HTTPStatus.FORBIDDEN
