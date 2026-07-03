from http import HTTPStatus

from flask import Response, g, request
from flask.views import MethodView
from pydantic import ValidationError

from app.auth.middleware import require_auth, require_role
from app.enums import ErrorMessage
from app.auth.enums import UserRole
from app.restaurants.dtos import (
    CreateRestaurantPayloadDTO,
    RestaurantResponseDTO,
    UpdateRestaurantPayloadDTO,
)
from app.restaurants.enums import RestaurantSuccessMessage
from app.restaurants.exceptions import (
    DuplicateRestaurantNameError,
    RestaurantNotFoundError,
)
from app.restaurants.middleware import require_owner
from app.restaurants.service import RestaurantService
from app.utils import extract_validation_errors, json_response, parse_pagination_params


@require_auth
@require_role(UserRole.OWNER)
def get_owner_restaurants() -> tuple[Response, HTTPStatus]:
    """Return paginated list of active restaurants owned by the caller.

    Returns:
        200 with paginated restaurant list.
        403 if caller is not an owner.
    """
    cursor, limit = parse_pagination_params(request)
    result = RestaurantService().list_owner_restaurants(g.uid, cursor, limit)

    return json_response(
        message=RestaurantSuccessMessage.RESTAURANTS_FETCHED,
        data=result,
    )


@require_auth
def get_all_restaurants() -> tuple[Response, HTTPStatus]:
    """Return paginated list of active restaurants.

    Returns:
        200 with paginated restaurant list.
    """
    cursor, limit = parse_pagination_params(request)
    result = RestaurantService().list_restaurants(cursor, limit)

    return json_response(
        message=RestaurantSuccessMessage.RESTAURANTS_FETCHED,
        data=result,
    )


class RestaurantView(MethodView):
    """
    Handles
        GET /restaurants/<restaurant_id> — public restaurant detail.
        POST /restaurants — create a restaurant (owner only).
        PATCH /restaurants/<restaurant_id> — update a restaurant (owner only).
        DELETE /restaurants/<restaurant_id> — soft-delete a restaurant (owner only).
    """

    decorators = [require_auth]

    def get(self, restaurant_id: str) -> tuple[Response, HTTPStatus]:
        """Return a single restaurant by ID.

        Returns:
            200 with restaurant data on success.
            404 if restaurant not found or deleted.
        """
        try:
            result = RestaurantService().get_restaurant(restaurant_id)
        except RestaurantNotFoundError as e:
            return json_response(
                message=e.message, status_code=e.status_code, detail=e.detail
            )

        return json_response(
            message=RestaurantSuccessMessage.RESTAURANTS_FETCHED,
            data=result.model_dump(by_alias=True),
        )

    @require_role(UserRole.OWNER)
    def post(self) -> tuple[Response, HTTPStatus]:
        """Create a new restaurant for the logged in owner.

        Returns:
            201 with restaurant data on success.
            400 if required fields are invalid.
            403 if caller is not an owner.
            409 if a restaurant with this name already exists.
        """
        body = request.get_json() or {}
        try:
            payload = CreateRestaurantPayloadDTO.model_validate(body)
        except ValidationError as err:
            return json_response(
                message=ErrorMessage.RESPONSE_MSG_MISSING_FIELDS,
                errors=extract_validation_errors(err),
                status_code=HTTPStatus.BAD_REQUEST,
            )

        try:
            result = RestaurantService().create_restaurant(g.uid, payload)
        except DuplicateRestaurantNameError as e:
            return json_response(
                message=e.message, status_code=e.status_code, detail=e.detail
            )

        return json_response(
            message=RestaurantSuccessMessage.RESTAURANT_CREATED,
            data=result.model_dump(by_alias=True),
            status_code=HTTPStatus.CREATED,
        )

    @require_owner
    def patch(
        self, restaurant_id: str, restaurant: RestaurantResponseDTO
    ) -> tuple[Response, HTTPStatus]:
        """Update fields on a restaurant the caller owns.

        Returns:
            200 with updated restaurant data on success.
            400 if fields are invalid.
            403 if caller doesn't own the restaurant.
            404 if restaurant not found or deleted.
            409 if the new name conflicts with an existing restaurant.
        """
        body = request.get_json() or {}
        try:
            payload = UpdateRestaurantPayloadDTO.model_validate(body)
        except ValidationError as err:
            return json_response(
                message=ErrorMessage.RESPONSE_MSG_MISSING_FIELDS,
                errors=extract_validation_errors(err),
                status_code=HTTPStatus.BAD_REQUEST,
            )

        try:
            result = RestaurantService().update_restaurant(
                restaurant_id, payload, restaurant
            )
        except DuplicateRestaurantNameError as e:
            return json_response(
                message=e.message, status_code=e.status_code, detail=e.detail
            )

        return json_response(
            message=RestaurantSuccessMessage.RESTAURANT_UPDATED,
            data=result.model_dump(by_alias=True),
        )

    @require_owner
    def delete(self, restaurant_id: str) -> tuple[Response, HTTPStatus]:
        """Soft-delete a restaurant the caller owns.

        Returns:
            200 on success.
            403 if caller doesn't own the restaurant.
            404 if restaurant not found or already deleted.
        """
        RestaurantService().delete_restaurant(restaurant_id)
        return json_response(message=RestaurantSuccessMessage.RESTAURANT_DELETED)
