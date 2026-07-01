from http import HTTPStatus

from flask import Response, g, request
from flask.views import MethodView
from pydantic import ValidationError

from app.auth.middleware import require_auth, require_role
from app.constants import RESPONSE_MSG_MISSING_FIELDS
from app.enums import UserRole
from app.exceptions import CustomException
from app.restaurants.dtos import (
    CreateRestaurantPayloadDTO,
    UpdateRestaurantPayloadDTO,
)
from app.restaurants.constants import (
    RESPONSE_MSG_RESTAURANT_CREATED,
    RESPONSE_MSG_RESTAURANT_DELETED,
    RESPONSE_MSG_RESTAURANT_UPDATED,
    RESPONSE_MSG_RESTAURANTS_FETCHED,
)
from app.restaurants.exceptions import (
    DuplicateRestaurantNameError,
    NotRestaurantOwnerError,
    RestaurantNotFoundError,
)
from app.restaurants.service import RestaurantService
from app.utils import extract_validation_errors, json_response, parse_pagination_params


def _check_restaurant_owner(restaurant_id: str) -> tuple[Response, HTTPStatus] | None:
    """Return an error response if the caller doesn't own the restaurant, else None."""
    try:
        restaurant = RestaurantService().get_restaurant(restaurant_id)
    except RestaurantNotFoundError as e:
        return json_response(
            message=e.message, status_code=e.status_code, detail=e.detail
        )
    if restaurant.owner_id != g.uid:
        return json_response(
            message=NotRestaurantOwnerError.message,
            status_code=NotRestaurantOwnerError.status_code,
        )

    return None


class RestaurantCollectionView(MethodView):
    """
    Handles
        GET /restaurants — browse all active restaurants.
        POST /restaurants — create a restaurant (owner only).
    """

    decorators = [require_auth]

    def get(self) -> tuple[Response, HTTPStatus]:
        """Return paginated list of active restaurants.

        Returns:
            200 with paginated restaurant list.
        """
        cursor, limit = parse_pagination_params(request)
        result = RestaurantService().list_restaurants(cursor, limit)
        return json_response(
            message=RESPONSE_MSG_RESTAURANTS_FETCHED,
            data=result,
        )

    @require_role(UserRole.OWNER)
    def post(self) -> tuple[Response, HTTPStatus]:
        """Create a new restaurant for the logged in owner.

        Returns:
            201 with restaurant data on success.
            400 if required fields are invalid.
            403 if caller is not an owner.
            409 if a restaurant with this name already exists.
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
        except DuplicateRestaurantNameError as e:
            return json_response(
                message=e.message, status_code=e.status_code, detail=e.detail
            )
        except Exception:
            return json_response(
                message=CustomException.message,
                status_code=CustomException.status_code,
            )

        return json_response(
            message=RESPONSE_MSG_RESTAURANT_CREATED,
            data=result.model_dump(by_alias=True),
            status_code=HTTPStatus.CREATED,
        )


class MyRestaurantsView(MethodView):
    """Handles GET /restaurants/mine — list the owner's own restaurants."""

    decorators = [require_role(UserRole.OWNER), require_auth]

    def get(self) -> tuple[Response, HTTPStatus]:
        """Return paginated list of active restaurants owned by the caller.

        Returns:
            200 with paginated restaurant list.
            403 if caller is not an owner.
        """
        cursor, limit = parse_pagination_params(request)
        result = RestaurantService().list_owner_restaurants(g.uid, cursor, limit)
        return json_response(
            message=RESPONSE_MSG_RESTAURANTS_FETCHED,
            data=result,
        )


class RestaurantEntityView(MethodView):
    """
    Handles
        GET /restaurants/<restaurant_id> — public restaurant detail.
        PUT /restaurants/<restaurant_id> — update a restaurant (owner only).
        DELETE /restaurants/<restaurant_id> — soft-delete a restaurant (owner only).
    """

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
            message=RESPONSE_MSG_RESTAURANTS_FETCHED,
            data=result.model_dump(by_alias=True),
        )

    @require_role(UserRole.OWNER)
    def put(self, restaurant_id: str) -> tuple[Response, HTTPStatus]:
        """Update fields on a restaurant the caller owns.

        Returns:
            200 with updated restaurant data on success.
            400 if fields are invalid.
            403 if caller doesn't own the restaurant.
            404 if restaurant not found or deleted.
            409 if the new name conflicts with an existing restaurant.
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

        err_resp = _check_restaurant_owner(restaurant_id)
        if err_resp:
            return err_resp

        try:
            result = RestaurantService().update_restaurant(restaurant_id, payload)
        except (RestaurantNotFoundError, DuplicateRestaurantNameError) as e:
            return json_response(
                message=e.message, status_code=e.status_code, detail=e.detail
            )
        except Exception:
            return json_response(
                message=CustomException.message,
                status_code=CustomException.status_code,
            )

        return json_response(
            message=RESPONSE_MSG_RESTAURANT_UPDATED,
            data=result.model_dump(by_alias=True),
        )

    @require_role(UserRole.OWNER)
    def delete(self, restaurant_id: str) -> tuple[Response, HTTPStatus]:
        """Soft-delete a restaurant the caller owns.

        Returns:
            200 on success.
            403 if caller doesn't own the restaurant.
            404 if restaurant not found or already deleted.
            500 on unexpected errors.
        """
        err_resp = _check_restaurant_owner(restaurant_id)
        if err_resp:
            return err_resp

        try:
            RestaurantService().delete_restaurant(restaurant_id)
        except RestaurantNotFoundError as e:
            return json_response(
                message=e.message, status_code=e.status_code, detail=e.detail
            )
        except Exception:
            return json_response(
                message=CustomException.message,
                status_code=CustomException.status_code,
            )

        return json_response(message=RESPONSE_MSG_RESTAURANT_DELETED)
