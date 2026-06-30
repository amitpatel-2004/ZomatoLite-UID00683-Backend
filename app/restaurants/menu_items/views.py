from http import HTTPStatus

from flask import Response, request
from flask.views import MethodView
from pydantic import ValidationError

from app.auth.middleware import require_auth, require_role
from app.constants import (
    MAX_IMAGE_UPLOAD_SIZE_BYTES,
    RESPONSE_MSG_MISSING_FIELDS,
)
from app.dtos import UploadUrlRequestDTO
from app.enums import UserRole
from app.exceptions import CustomException
from app.restaurants.menu_items.dtos import (
    CreateMenuItemPayloadDTO,
    UpdateMenuItemPayloadDTO,
)
from app.restaurants.constants import (
    RESPONSE_MSG_MENU_ITEM_ADDED,
    RESPONSE_MSG_MENU_ITEM_DELETED,
    RESPONSE_MSG_MENU_ITEM_UPDATED,
    RESPONSE_MSG_MENU_ITEMS_FETCHED,
    RESPONSE_MSG_UPLOAD_URL_GENERATED,
)
from app.restaurants.exceptions import (
    DuplicateMenuItemNameError,
    MenuItemNotFoundError,
    RestaurantNotFoundError,
)
from app.restaurants.menu_items.service import MenuItemService
from app.restaurants.views import _check_restaurant_owner
from app.utils import extract_validation_errors, json_response, parse_pagination_params


class MenuItemCollectionView(MethodView):
    """
    Handles
        GET /restaurants/<restaurant_id>/menu-items — public menu listing.
        POST /restaurants/<restaurant_id>/menu-items — add menu item (owner only).
    """

    decorators = [require_auth]

    def get(self, restaurant_id: str) -> tuple[Response, HTTPStatus]:
        """Return paginated non-deleted menu items for a restaurant.

        Returns:
            200 with paginated menu items.
            404 if restaurant not found or deleted.
            500 on unexpected errors.
        """
        cursor, limit = parse_pagination_params(request)
        try:
            result = MenuItemService().list_menu_items(restaurant_id, cursor, limit)
        except RestaurantNotFoundError as e:
            return json_response(
                message=e.message, status_code=e.status_code, detail=e.detail
            )
        except Exception:
            return json_response(
                message=CustomException.message,
                status_code=CustomException.status_code,
            )

        return json_response(
            message=RESPONSE_MSG_MENU_ITEMS_FETCHED,
            data=result,
        )

    @require_role(UserRole.OWNER)
    def post(self, restaurant_id: str) -> tuple[Response, HTTPStatus]:
        """Add a new menu item to a restaurant the caller owns.

        Returns:
            201 with menu item data on success.
            400 if required fields are invalid.
            403 if caller doesn't own the restaurant.
            404 if restaurant not found or deleted.
            409 if a menu item with this name already exists.
            500 on unexpected errors.
        """
        body = request.get_json() or {}
        try:
            payload = CreateMenuItemPayloadDTO.model_validate(body)
        except ValidationError as err:
            return json_response(
                message=RESPONSE_MSG_MISSING_FIELDS,
                errors=extract_validation_errors(err),
                status_code=HTTPStatus.BAD_REQUEST,
            )

        err_resp = _check_restaurant_owner(restaurant_id)
        if err_resp:
            return err_resp

        try:
            result = MenuItemService().add_menu_item(restaurant_id, payload)
        except RestaurantNotFoundError as e:
            return json_response(
                message=e.message, status_code=e.status_code, detail=e.detail
            )
        except DuplicateMenuItemNameError as e:
            return json_response(
                message=e.message, status_code=e.status_code, detail=e.detail
            )
        except Exception:
            return json_response(
                message=CustomException.message,
                status_code=CustomException.status_code,
            )

        return json_response(
            message=RESPONSE_MSG_MENU_ITEM_ADDED,
            data=result.model_dump(by_alias=True),
            status_code=HTTPStatus.CREATED,
        )


class MenuItemEntityView(MethodView):
    """
    Handles
        GET /restaurants/<restaurant_id>/menu-items/<item_id> — public.
        PUT /restaurants/<restaurant_id>/menu-items/<item_id> — owner only.
        DELETE /restaurants/<restaurant_id>/menu-items/<item_id> — owner only.
    """

    decorators = [require_auth]

    def get(self, restaurant_id: str, item_id: str) -> tuple[Response, HTTPStatus]:
        """Return a single menu item.

        Returns:
            200 with menu item data on success.
            404 if restaurant or menu item not found or deleted.
            500 on unexpected errors.
        """
        try:
            result = MenuItemService().get_menu_item(restaurant_id, item_id)
        except (RestaurantNotFoundError, MenuItemNotFoundError) as e:
            return json_response(
                message=e.message,
                status_code=e.status_code,
                detail=e.detail,
            )
        except Exception:
            return json_response(
                message=CustomException.message,
                status_code=CustomException.status_code,
            )

        return json_response(
            message=RESPONSE_MSG_MENU_ITEMS_FETCHED,
            data=result.model_dump(by_alias=True),
        )

    @require_role(UserRole.OWNER)
    def put(self, restaurant_id: str, item_id: str) -> tuple[Response, HTTPStatus]:
        """Update a menu item on a restaurant the caller owns.

        Returns:
            200 with updated menu item data on success.
            400 if fields are invalid.
            403 if caller doesn't own the restaurant.
            404 if restaurant or menu item not found or deleted.
            409 if the new name conflicts with an existing menu item.
            500 on unexpected errors.
        """
        body = request.get_json() or {}
        try:
            payload = UpdateMenuItemPayloadDTO.model_validate(body)
        except ValidationError as err:
            return json_response(
                message=RESPONSE_MSG_MISSING_FIELDS,
                errors=extract_validation_errors(err),
                status_code=HTTPStatus.BAD_REQUEST,
            )

        err_resp = _check_restaurant_owner(restaurant_id)
        if err_resp:
            return err_resp

        try:
            result = MenuItemService().update_menu_item(restaurant_id, item_id, payload)
        except RestaurantNotFoundError as e:
            return json_response(
                message=e.message, status_code=e.status_code, detail=e.detail
            )
        except MenuItemNotFoundError as e:
            return json_response(
                message=e.message, status_code=e.status_code, detail=e.detail
            )
        except DuplicateMenuItemNameError as e:
            return json_response(
                message=e.message, status_code=e.status_code, detail=e.detail
            )
        except Exception:
            return json_response(
                message=CustomException.message,
                status_code=CustomException.status_code,
            )

        return json_response(
            message=RESPONSE_MSG_MENU_ITEM_UPDATED,
            data=result.model_dump(by_alias=True),
        )

    @require_role(UserRole.OWNER)
    def delete(self, restaurant_id: str, item_id: str) -> tuple[Response, HTTPStatus]:
        """Soft-delete a menu item from a restaurant the caller owns.

        Returns:
            200 on success.
            403 if caller doesn't own the restaurant.
            404 if restaurant or menu item not found or already deleted.
            500 on unexpected errors.
        """
        err_resp = _check_restaurant_owner(restaurant_id)
        if err_resp:
            return err_resp

        try:
            MenuItemService().delete_menu_item(restaurant_id, item_id)
        except RestaurantNotFoundError as e:
            return json_response(
                message=e.message, status_code=e.status_code, detail=e.detail
            )
        except MenuItemNotFoundError as e:
            return json_response(
                message=e.message, status_code=e.status_code, detail=e.detail
            )
        except Exception:
            return json_response(
                message=CustomException.message,
                status_code=CustomException.status_code,
            )

        return json_response(message=RESPONSE_MSG_MENU_ITEM_DELETED)


class MenuItemImageUploadView(MethodView):
    """Handles POST /restaurants/<restaurant_id>/menu-items/image-upload — owner only."""

    decorators = [require_role(UserRole.OWNER), require_auth]

    def post(self, restaurant_id: str) -> tuple[Response, HTTPStatus]:
        """Generate a signed URL for direct menu item image upload.

        Returns:
            200 with uploadUrl and imagePath on success.
            400 if fields are invalid or file size exceeds limit.
            403 if caller doesn't own the restaurant.
            404 if restaurant not found or deleted.
            500 on unexpected errors.
        """
        body = request.get_json() or {}
        try:
            payload = UploadUrlRequestDTO.model_validate(body)
        except ValidationError as err:
            return json_response(
                message=RESPONSE_MSG_MISSING_FIELDS,
                errors=extract_validation_errors(err),
                status_code=HTTPStatus.BAD_REQUEST,
            )

        if payload.file_size > MAX_IMAGE_UPLOAD_SIZE_BYTES:
            return json_response(
                message="File size exceeds the allowed limit.",
                status_code=HTTPStatus.BAD_REQUEST,
            )

        err_resp = _check_restaurant_owner(restaurant_id)
        if err_resp:
            return err_resp

        try:
            result = MenuItemService().generate_menu_item_upload_url(
                restaurant_id, payload.file_name, payload.content_type
            )
        except RestaurantNotFoundError as e:
            return json_response(
                message=e.message, status_code=e.status_code, detail=e.detail
            )
        except Exception:
            return json_response(
                message=CustomException.message,
                status_code=CustomException.status_code,
            )

        return json_response(
            message=RESPONSE_MSG_UPLOAD_URL_GENERATED,
            data=result.model_dump(by_alias=True),
        )
