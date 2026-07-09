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
from app.restaurants.dtos import RestaurantResponseDTO
from app.restaurants.menu_items.dtos import (
    CreateMenuItemPayloadDTO,
    UpdateMenuItemPayloadDTO,
)
from app.restaurants.menu_items.enums import MenuItemSuccessMessage
from app.restaurants.menu_items.exceptions import (
    DuplicateMenuItemNameError,
    MenuItemHasActiveOrdersError,
    MenuItemNotFoundError,
)
from app.restaurants.menu_items.service import MenuItemService
from app.restaurants.middleware import require_owner
from app.utils import extract_validation_errors, json_response, parse_pagination_params


@require_auth
def get_menu_items(restaurant_id: str) -> tuple[Response, HTTPStatus]:
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


class MenuItemView(MethodView):
    """
    Handles
        GET /restaurants/<restaurant_id>/menu-items/<item_id> — public.
        POST /restaurants/<restaurant_id>/menu-items — add menu item (owner only).
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
        except MenuItemNotFoundError as err:
            return json_response(
                message=err.message,
                status_code=err.status_code,
                detail=err.detail,
            )

        return json_response(
            message=MenuItemSuccessMessage.MENU_ITEMS_FETCHED,
            data=result.model_dump(by_alias=True),
        )

    @require_owner
    def post(
        self, restaurant_id: str, restaurant: RestaurantResponseDTO
    ) -> tuple[Response, HTTPStatus]:
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
            result = MenuItemService().add_menu_item(restaurant_id, payload)
        except ValidationError as err:
            return json_response(
                message=ErrorMessage.RESPONSE_MSG_MISSING_FIELDS,
                errors=extract_validation_errors(err),
                status_code=HTTPStatus.BAD_REQUEST,
            )
        except DuplicateMenuItemNameError as err:
            return json_response(
                message=err.message, status_code=err.status_code, detail=err.detail
            )

        return json_response(
            message=MenuItemSuccessMessage.MENU_ITEM_ADDED,
            data=result.model_dump(by_alias=True),
            status_code=HTTPStatus.CREATED,
        )

    @require_owner
    def patch(
        self,
        restaurant_id: str,
        item_id: str,
        restaurant: RestaurantResponseDTO,
    ) -> tuple[Response, HTTPStatus]:
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
            result = MenuItemService().update_menu_item(restaurant_id, item_id, payload)
        except ValidationError as err:
            return json_response(
                message=ErrorMessage.RESPONSE_MSG_MISSING_FIELDS,
                errors=extract_validation_errors(err),
                status_code=HTTPStatus.BAD_REQUEST,
            )
        except MenuItemNotFoundError as err:
            return json_response(
                message=err.message, status_code=err.status_code, detail=err.detail
            )
        except DuplicateMenuItemNameError as err:
            return json_response(
                message=err.message, status_code=err.status_code, detail=err.detail
            )

        return json_response(
            message=MenuItemSuccessMessage.MENU_ITEM_UPDATED,
            data=result.model_dump(by_alias=True),
        )

    @require_owner
    def delete(
        self, restaurant_id: str, item_id: str, restaurant: RestaurantResponseDTO
    ) -> tuple[Response, HTTPStatus]:
        """Soft-delete a menu item from a restaurant the caller owns.

        Returns:
            200 on success.
            403 if caller doesn't own the restaurant.
            404 if restaurant or menu item not found or already deleted.
            409 if the item is part of an active order.
        """
        try:
            MenuItemService().delete_menu_item(restaurant_id, item_id)
        except (MenuItemNotFoundError, MenuItemHasActiveOrdersError) as err:
            return json_response(
                message=err.message, status_code=err.status_code, detail=err.detail
            )

        return json_response(message=MenuItemSuccessMessage.MENU_ITEM_DELETED)


@require_auth
@require_owner
def upload_menu_item_image(
    restaurant_id: str, restaurant: RestaurantResponseDTO
) -> tuple[Response, HTTPStatus]:
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
