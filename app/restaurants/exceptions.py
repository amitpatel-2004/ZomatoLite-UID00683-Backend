from http import HTTPStatus

from app.exceptions import BaseHTTPException
from app.enums import ErrorMessage
from app.restaurants.enums import RestaurantErrorMessage


class RestaurantNotFoundError(BaseHTTPException):
    message = RestaurantErrorMessage.RESTAURANT_NOT_FOUND
    status_code = HTTPStatus.NOT_FOUND


class NotRestaurantOwnerError(BaseHTTPException):
    message = ErrorMessage.RESPONSE_MSG_FORBIDDEN
    status_code = HTTPStatus.FORBIDDEN


class DuplicateRestaurantNameError(BaseHTTPException):
    message = RestaurantErrorMessage.DUPLICATE_RESTAURANT_NAME
    status_code = HTTPStatus.CONFLICT


class RestaurantHasActiveOrdersError(BaseHTTPException):
    message = RestaurantErrorMessage.RESTAURANT_HAS_ACTIVE_ORDERS
    status_code = HTTPStatus.CONFLICT
