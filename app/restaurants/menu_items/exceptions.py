from http import HTTPStatus

from app.exceptions import BaseHTTPException
from app.restaurants.menu_items.enums import MenuItemErrorMessage


class MenuItemNotFoundError(BaseHTTPException):
    message = MenuItemErrorMessage.MENU_ITEM_NOT_FOUND
    status_code = HTTPStatus.NOT_FOUND


class DuplicateMenuItemNameError(BaseHTTPException):
    message = MenuItemErrorMessage.DUPLICATE_MENU_ITEM_NAME
    status_code = HTTPStatus.CONFLICT


class MenuItemHasActiveOrdersError(BaseHTTPException):
    message = MenuItemErrorMessage.MENU_ITEM_HAS_ACTIVE_ORDERS
    status_code = HTTPStatus.CONFLICT
