from http import HTTPStatus

from app.exceptions import CustomException
from app.constants import RESPONSE_MSG_FORBIDDEN
from app.restaurants.constants import (
    RESPONSE_MSG_DUPLICATE_MENU_ITEM_NAME,
    RESPONSE_MSG_DUPLICATE_RESTAURANT_NAME,
    RESPONSE_MSG_MENU_ITEM_NOT_FOUND,
    RESPONSE_MSG_RESTAURANT_NOT_FOUND,
)


class RestaurantNotFoundError(CustomException):
    message = RESPONSE_MSG_RESTAURANT_NOT_FOUND
    status_code = HTTPStatus.NOT_FOUND


class MenuItemNotFoundError(CustomException):
    message = RESPONSE_MSG_MENU_ITEM_NOT_FOUND
    status_code = HTTPStatus.NOT_FOUND


class NotRestaurantOwnerError(CustomException):
    message = RESPONSE_MSG_FORBIDDEN
    status_code = HTTPStatus.FORBIDDEN


class DuplicateRestaurantNameError(CustomException):
    message = RESPONSE_MSG_DUPLICATE_RESTAURANT_NAME
    status_code = HTTPStatus.CONFLICT


class DuplicateMenuItemNameError(CustomException):
    message = RESPONSE_MSG_DUPLICATE_MENU_ITEM_NAME
    status_code = HTTPStatus.CONFLICT
