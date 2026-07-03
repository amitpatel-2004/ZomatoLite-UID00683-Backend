from http import HTTPStatus

from flask import Response, request
from flask.views import MethodView
from pydantic import ValidationError

from app.auth.middleware import require_auth
from app.constants import (
    MAX_IMAGE_UPLOAD_SIZE_BYTES,
)
from app.enums import ErrorMessage
from app.dtos import UploadUrlRequestDTO
from app.restaurants.menu_items.dtos import (
    CreateMenuItemPayloadDTO,
    UpdateMenuItemPayloadDTO,
)
from app.restaurants.menu_items.enums import MenuItemSuccessMessage
from app.restaurants.menu_items.exceptions import (
    DuplicateMenuItemNameError,
    MenuItemNotFoundError,
)
from app.restaurants.menu_items.service import MenuItemService
from app.restaurants.middleware import require_owner
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
        """
        cursor, limit = parse_pagination_params(request)
        result = MenuItemService().list_menu_items(restaurant_id, cursor, limit)

        return json_response(
            message=MenuItemSuccessMessage.MENU_ITEMS_FETCHED,
            data=result,
        )

    @require_owner
    def post(self, restaurant_id: str) -> tuple[Response, HTTPStatus]:
        """Add a new menu item to a restaurant the caller owns.

        Returns:
            201 with menu item data on success.
            400 if required fields are invalid.
            403 if caller doesn't own the restaurant.
            404 if restaurant not found or deleted.
            409 if a menu item with this name already exists.
        """
        body = request.get_json() or {}
        try:
            payload = CreateMenuItemPayloadDTO.model_validate(body)
        except ValidationError as err:
            return json_response(
                message=ErrorMessage.RESPONSE_MSG_MISSING_FIELDS,
                errors=extract_validation_errors(err),
                status_code=HTTPStatus.BAD_REQUEST,
            )

        try:
            result = MenuItemService().add_menu_item(restaurant_id, payload)
        except DuplicateMenuItemNameError as e:
            return json_response(
                message=e.message, status_code=e.status_code, detail=e.detail
            )

        return json_response(
            message=MenuItemSuccessMessage.MENU_ITEM_ADDED,
            data=result.model_dump(by_alias=True),
            status_code=HTTPStatus.CREATED,
        )


class MenuItemEntityView(MethodView):
    """
    Handles
        GET /restaurants/<restaurant_id>/menu-items/<item_id> — public.
        PATCH /restaurants/<restaurant_id>/menu-items/<item_id> — owner only.
        DELETE /restaurants/<restaurant_id>/menu-items/<item_id> — owner only.
    """

    decorators = [require_auth]

    def get(self, restaurant_id: str, item_id: str) -> tuple[Response, HTTPStatus]:
        """Return a single menu item.

        Returns:
            200 with menu item data on success.
            404 if menu item not found or deleted.
        """
        try:
            result = MenuItemService().get_menu_item(restaurant_id, item_id)
        except MenuItemNotFoundError as e:
            return json_response(
                message=e.message,
                status_code=e.status_code,
                detail=e.detail,
            )

        return json_response(
            message=MenuItemSuccessMessage.MENU_ITEMS_FETCHED,
            data=result.model_dump(by_alias=True),
        )

    @require_owner
    def patch(self, restaurant_id: str, item_id: str) -> tuple[Response, HTTPStatus]:
        """Update a menu item on a restaurant the caller owns.

        Returns:
            200 with updated menu item data on success.
            400 if fields are invalid.
            403 if caller doesn't own the restaurant.
            404 if restaurant or menu item not found or deleted.
            409 if the new name conflicts with an existing menu item.
        """
        body = request.get_json() or {}
        try:
            payload = UpdateMenuItemPayloadDTO.model_validate(body)
        except ValidationError as err:
            return json_response(
                message=ErrorMessage.RESPONSE_MSG_MISSING_FIELDS,
                errors=extract_validation_errors(err),
                status_code=HTTPStatus.BAD_REQUEST,
            )

        try:
            result = MenuItemService().update_menu_item(restaurant_id, item_id, payload)
        except MenuItemNotFoundError as e:
            return json_response(
                message=e.message, status_code=e.status_code, detail=e.detail
            )
        except DuplicateMenuItemNameError as e:
            return json_response(
                message=e.message, status_code=e.status_code, detail=e.detail
            )

        return json_response(
            message=MenuItemSuccessMessage.MENU_ITEM_UPDATED,
            data=result.model_dump(by_alias=True),
        )

    @require_owner
    def delete(self, restaurant_id: str, item_id: str) -> tuple[Response, HTTPStatus]:
        """Soft-delete a menu item from a restaurant the caller owns.

        Returns:
            200 on success.
            403 if caller doesn't own the restaurant.
            404 if restaurant or menu item not found or already deleted.
        """
        try:
            MenuItemService().delete_menu_item(restaurant_id, item_id)
        except MenuItemNotFoundError as e:
            return json_response(
                message=e.message, status_code=e.status_code, detail=e.detail
            )

        return json_response(message=MenuItemSuccessMessage.MENU_ITEM_DELETED)


class MenuItemImageUploadView(MethodView):
    """Handles POST /restaurants/<restaurant_id>/menu-items/image-upload — owner only."""

    decorators = [require_owner, require_auth]

    def post(self, restaurant_id: str) -> tuple[Response, HTTPStatus]:
        """Generate a signed URL for direct menu item image upload.

        Returns:
            200 with uploadUrl and imagePath on success.
            400 if fields are invalid or file size exceeds limit.
            403 if caller doesn't own the restaurant.
            404 if restaurant not found or deleted.
        """
        body = request.get_json() or {}
        try:
            payload = UploadUrlRequestDTO.model_validate(body)
        except ValidationError as err:
            return json_response(
                message=ErrorMessage.RESPONSE_MSG_MISSING_FIELDS,
                errors=extract_validation_errors(err),
                status_code=HTTPStatus.BAD_REQUEST,
            )

        if payload.file_size > MAX_IMAGE_UPLOAD_SIZE_BYTES:
            return json_response(
                message="File size exceeds the allowed limit.",
                status_code=HTTPStatus.BAD_REQUEST,
            )

        result = MenuItemService().generate_menu_item_upload_url(
            restaurant_id, payload.file_name, payload.content_type
        )

        return json_response(
            message=MenuItemSuccessMessage.UPLOAD_URL_GENERATED,
            data=result.model_dump(by_alias=True),
        )
