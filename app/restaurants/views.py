from http import HTTPStatus

from flask import Response, g, request
from flask.views import MethodView
from pydantic import ValidationError

from app.auth.middleware import require_auth, require_role
from app.constants import (
    MAX_IMAGE_UPLOAD_SIZE_BYTES,
    RESPONSE_MSG_FORBIDDEN,
    RESPONSE_MSG_INTERNAL_ERROR,
    RESPONSE_MSG_MISSING_FIELDS,
)
from app.dtos import UploadUrlRequestDTO
from app.restaurants.dtos import (
    CreateMenuItemPayloadDTO,
    CreateRestaurantPayloadDTO,
    UpdateMenuItemPayloadDTO,
    UpdateRestaurantPayloadDTO,
)
from app.restaurants.constants import (
    RESPONSE_MSG_MENU_ITEM_ADDED,
    RESPONSE_MSG_MENU_ITEM_DELETED,
    RESPONSE_MSG_MENU_ITEM_NOT_FOUND,
    RESPONSE_MSG_MENU_ITEM_UPDATED,
    RESPONSE_MSG_MENU_ITEMS_FETCHED,
    RESPONSE_MSG_RESTAURANT_CREATED,
    RESPONSE_MSG_RESTAURANT_DELETED,
    RESPONSE_MSG_RESTAURANT_NOT_FOUND,
    RESPONSE_MSG_RESTAURANT_UPDATED,
    RESPONSE_MSG_RESTAURANTS_FETCHED,
    RESPONSE_MSG_UPLOAD_URL_GENERATED,
)
from app.restaurants.exceptions import (
    MenuItemNotFoundError,
    NotRestaurantOwnerError,
    RestaurantNotFoundError,
)
from app.restaurants.service import RestaurantService
from app.utils import extract_validation_errors, json_response, parse_pagination_params


class RestaurantListView(MethodView):
    """Handles GET /restaurants — browse all active restaurants."""

    decorators = [require_auth]

    def get(self) -> tuple[Response, HTTPStatus]:
        """Return paginated list of active restaurants.

        Returns:
            200 with paginated restaurant list.
        """
        after, limit = parse_pagination_params(request)
        result = RestaurantService().list_restaurants(after, limit)
        return json_response(
            message=RESPONSE_MSG_RESTAURANTS_FETCHED,
            data=result,
        )


class RestaurantCreateView(MethodView):
    """Handles POST /restaurants — create a restaurant (owner only)."""

    decorators = [require_role("owner"), require_auth]

    def post(self) -> tuple[Response, HTTPStatus]:
        """Create a new restaurant for the logged in owner.

        Returns:
            201 with restaurant data on success.
            400 if required fields are invalid.
            403 if caller is not an owner.
            500 on unexpected errors.
        """
        body = request.get_json() or {}
        try:
            payload = CreateRestaurantPayloadDTO.model_validate(body)
        except ValidationError as err:
            return json_response(
                message=RESPONSE_MSG_MISSING_FIELDS,
                errors=extract_validation_errors(err),
                status_code=HTTPStatus.BAD_REQUEST,
            )

        try:
            result = RestaurantService().create_restaurant(g.uid, payload)
        except Exception:
            return json_response(
                message=RESPONSE_MSG_INTERNAL_ERROR,
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return json_response(
            message=RESPONSE_MSG_RESTAURANT_CREATED,
            data=result.model_dump(by_alias=True),
            status_code=HTTPStatus.CREATED,
        )


class MyRestaurantsView(MethodView):
    """Handles GET /restaurants/mine — list the owner's own restaurants."""

    decorators = [require_role("owner"), require_auth]

    def get(self) -> tuple[Response, HTTPStatus]:
        """Return paginated list of active restaurants owned by the caller.

        Returns:
            200 with paginated restaurant list.
            403 if caller is not an owner.
        """
        after, limit = parse_pagination_params(request)
        result = RestaurantService().list_owner_restaurants(g.uid, after, limit)
        return json_response(
            message=RESPONSE_MSG_RESTAURANTS_FETCHED,
            data=result,
        )


class RestaurantDetailView(MethodView):
    """Handles GET /restaurants/<restaurant_id> — public restaurant detail."""

    decorators = [require_auth]

    def get(self, restaurant_id: str) -> tuple[Response, HTTPStatus]:
        """Return a single restaurant by ID.

        Returns:
            200 with restaurant data on success.
            404 if restaurant not found or deleted.
            500 on unexpected errors.
        """
        try:
            result = RestaurantService().get_restaurant(restaurant_id)
        except RestaurantNotFoundError:
            return json_response(
                message=RESPONSE_MSG_RESTAURANT_NOT_FOUND,
                status_code=HTTPStatus.NOT_FOUND,
            )
        except Exception:
            return json_response(
                message=RESPONSE_MSG_INTERNAL_ERROR,
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return json_response(
            message=RESPONSE_MSG_RESTAURANTS_FETCHED,
            data=result.model_dump(by_alias=True),
        )


class RestaurantUpdateView(MethodView):
    """Handles PUT /restaurants/<restaurant_id> — update a restaurant (owner only)."""

    decorators = [require_role("owner"), require_auth]

    def put(self, restaurant_id: str) -> tuple[Response, HTTPStatus]:
        """Update fields on a restaurant the caller owns.

        Returns:
            200 with updated restaurant data on success.
            400 if fields are invalid.
            403 if caller doesn't own the restaurant.
            404 if restaurant not found or deleted.
            500 on unexpected errors.
        """
        body = request.get_json() or {}
        try:
            payload = UpdateRestaurantPayloadDTO.model_validate(body)
        except ValidationError as err:
            return json_response(
                message=RESPONSE_MSG_MISSING_FIELDS,
                errors=extract_validation_errors(err),
                status_code=HTTPStatus.BAD_REQUEST,
            )

        try:
            result = RestaurantService().update_restaurant(
                g.uid, restaurant_id, payload
            )
        except RestaurantNotFoundError:
            return json_response(
                message=RESPONSE_MSG_RESTAURANT_NOT_FOUND,
                status_code=HTTPStatus.NOT_FOUND,
            )
        except NotRestaurantOwnerError:
            return json_response(
                message=RESPONSE_MSG_FORBIDDEN,
                status_code=HTTPStatus.FORBIDDEN,
            )
        except Exception:
            return json_response(
                message=RESPONSE_MSG_INTERNAL_ERROR,
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return json_response(
            message=RESPONSE_MSG_RESTAURANT_UPDATED,
            data=result.model_dump(by_alias=True),
        )


class RestaurantDeleteView(MethodView):
    """Handles DELETE /restaurants/<restaurant_id> — soft-delete a restaurant (owner only)."""

    decorators = [require_role("owner"), require_auth]

    def delete(self, restaurant_id: str) -> tuple[Response, HTTPStatus]:
        """Soft-delete a restaurant the caller owns.

        Returns:
            200 on success.
            403 if caller doesn't own the restaurant.
            404 if restaurant not found or already deleted.
            500 on unexpected errors.
        """
        try:
            RestaurantService().delete_restaurant(g.uid, restaurant_id)
        except RestaurantNotFoundError:
            return json_response(
                message=RESPONSE_MSG_RESTAURANT_NOT_FOUND,
                status_code=HTTPStatus.NOT_FOUND,
            )
        except NotRestaurantOwnerError:
            return json_response(
                message=RESPONSE_MSG_FORBIDDEN,
                status_code=HTTPStatus.FORBIDDEN,
            )
        except Exception:
            return json_response(
                message=RESPONSE_MSG_INTERNAL_ERROR,
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return json_response(message=RESPONSE_MSG_RESTAURANT_DELETED)


class MenuItemListView(MethodView):
    """Handles GET /restaurants/<restaurant_id>/menu-items — public menu listing."""

    decorators = [require_auth]

    def get(self, restaurant_id: str) -> tuple[Response, HTTPStatus]:
        """Return paginated non-deleted menu items for a restaurant.

        Returns:
            200 with paginated menu items.
            404 if restaurant not found or deleted.
            500 on unexpected errors.
        """
        after, limit = parse_pagination_params(request)
        try:
            result = RestaurantService().list_menu_items(restaurant_id, after, limit)
        except RestaurantNotFoundError:
            return json_response(
                message=RESPONSE_MSG_RESTAURANT_NOT_FOUND,
                status_code=HTTPStatus.NOT_FOUND,
            )
        except Exception:
            return json_response(
                message=RESPONSE_MSG_INTERNAL_ERROR,
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return json_response(
            message=RESPONSE_MSG_MENU_ITEMS_FETCHED,
            data=result,
        )


class MenuItemCreateView(MethodView):
    """Handles POST /restaurants/<restaurant_id>/menu-items — add menu item (owner only)."""

    decorators = [require_role("owner"), require_auth]

    def post(self, restaurant_id: str) -> tuple[Response, HTTPStatus]:
        """Add a new menu item to a restaurant the caller owns.

        Returns:
            201 with menu item data on success.
            400 if required fields are invalid.
            403 if caller doesn't own the restaurant.
            404 if restaurant not found or deleted.
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

        try:
            result = RestaurantService().add_menu_item(g.uid, restaurant_id, payload)
        except RestaurantNotFoundError:
            return json_response(
                message=RESPONSE_MSG_RESTAURANT_NOT_FOUND,
                status_code=HTTPStatus.NOT_FOUND,
            )
        except NotRestaurantOwnerError:
            return json_response(
                message=RESPONSE_MSG_FORBIDDEN,
                status_code=HTTPStatus.FORBIDDEN,
            )
        except Exception:
            return json_response(
                message=RESPONSE_MSG_INTERNAL_ERROR,
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return json_response(
            message=RESPONSE_MSG_MENU_ITEM_ADDED,
            data=result.model_dump(by_alias=True),
            status_code=HTTPStatus.CREATED,
        )


class MenuItemDetailView(MethodView):
    """Handles GET /restaurants/<restaurant_id>/menu-items/<item_id> — public."""

    decorators = [require_auth]

    def get(self, restaurant_id: str, item_id: str) -> tuple[Response, HTTPStatus]:
        """Return a single menu item.

        Returns:
            200 with menu item data on success.
            404 if restaurant or menu item not found or deleted.
            500 on unexpected errors.
        """
        try:
            result = RestaurantService().get_menu_item(restaurant_id, item_id)
        except (RestaurantNotFoundError, MenuItemNotFoundError):
            return json_response(
                message=RESPONSE_MSG_MENU_ITEM_NOT_FOUND,
                status_code=HTTPStatus.NOT_FOUND,
            )
        except Exception:
            return json_response(
                message=RESPONSE_MSG_INTERNAL_ERROR,
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return json_response(
            message=RESPONSE_MSG_MENU_ITEMS_FETCHED,
            data=result.model_dump(by_alias=True),
        )


class MenuItemUpdateView(MethodView):
    """Handles PUT /restaurants/<restaurant_id>/menu-items/<item_id> — owner only."""

    decorators = [require_role("owner"), require_auth]

    def put(self, restaurant_id: str, item_id: str) -> tuple[Response, HTTPStatus]:
        """Update a menu item on a restaurant the caller owns.

        Returns:
            200 with updated menu item data on success.
            400 if fields are invalid.
            403 if caller doesn't own the restaurant.
            404 if restaurant or menu item not found or deleted.
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

        try:
            result = RestaurantService().update_menu_item(
                g.uid, restaurant_id, item_id, payload
            )
        except RestaurantNotFoundError:
            return json_response(
                message=RESPONSE_MSG_RESTAURANT_NOT_FOUND,
                status_code=HTTPStatus.NOT_FOUND,
            )
        except NotRestaurantOwnerError:
            return json_response(
                message=RESPONSE_MSG_FORBIDDEN,
                status_code=HTTPStatus.FORBIDDEN,
            )
        except MenuItemNotFoundError:
            return json_response(
                message=RESPONSE_MSG_MENU_ITEM_NOT_FOUND,
                status_code=HTTPStatus.NOT_FOUND,
            )
        except Exception:
            return json_response(
                message=RESPONSE_MSG_INTERNAL_ERROR,
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return json_response(
            message=RESPONSE_MSG_MENU_ITEM_UPDATED,
            data=result.model_dump(by_alias=True),
        )


class MenuItemDeleteView(MethodView):
    """Handles DELETE /restaurants/<restaurant_id>/menu-items/<item_id> — owner only."""

    decorators = [require_role("owner"), require_auth]

    def delete(self, restaurant_id: str, item_id: str) -> tuple[Response, HTTPStatus]:
        """Soft-delete a menu item from a restaurant the caller owns.

        Returns:
            200 on success.
            403 if caller doesn't own the restaurant.
            404 if restaurant or menu item not found or already deleted.
            500 on unexpected errors.
        """
        try:
            RestaurantService().delete_menu_item(g.uid, restaurant_id, item_id)
        except RestaurantNotFoundError:
            return json_response(
                message=RESPONSE_MSG_RESTAURANT_NOT_FOUND,
                status_code=HTTPStatus.NOT_FOUND,
            )
        except NotRestaurantOwnerError:
            return json_response(
                message=RESPONSE_MSG_FORBIDDEN,
                status_code=HTTPStatus.FORBIDDEN,
            )
        except MenuItemNotFoundError:
            return json_response(
                message=RESPONSE_MSG_MENU_ITEM_NOT_FOUND,
                status_code=HTTPStatus.NOT_FOUND,
            )
        except Exception:
            return json_response(
                message=RESPONSE_MSG_INTERNAL_ERROR,
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return json_response(message=RESPONSE_MSG_MENU_ITEM_DELETED)


class MenuItemUploadUrlView(MethodView):
    """Handles POST /restaurants/<restaurant_id>/menu-items/upload-url — owner only."""

    decorators = [require_role("owner"), require_auth]

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

        try:
            result = RestaurantService().generate_menu_item_upload_url(
                g.uid, restaurant_id, payload.file_name, payload.content_type
            )
        except RestaurantNotFoundError:
            return json_response(
                message=RESPONSE_MSG_RESTAURANT_NOT_FOUND,
                status_code=HTTPStatus.NOT_FOUND,
            )
        except NotRestaurantOwnerError:
            return json_response(
                message=RESPONSE_MSG_FORBIDDEN,
                status_code=HTTPStatus.FORBIDDEN,
            )
        except Exception:
            return json_response(
                message=RESPONSE_MSG_INTERNAL_ERROR,
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return json_response(
            message=RESPONSE_MSG_UPLOAD_URL_GENERATED,
            data=result.model_dump(by_alias=True),
        )
