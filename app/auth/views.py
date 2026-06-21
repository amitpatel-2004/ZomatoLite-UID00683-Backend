from http import HTTPStatus

from flask import request, Response
from flask.views import MethodView
from pydantic import ValidationError

from app.auth.constants import (
    RESPONSE_MSG_INVALID_CREDENTIALS,
    RESPONSE_MSG_LOGIN_SUCCESS,
    RESPONSE_MSG_REGISTER_SUCCESS,
    RESPONSE_MSG_REGISTRATION_FAILED,
)
from app.auth.dtos import UserLoginPayloadDTO, UserRegisterPayloadDTO
from app.auth.exceptions import EmailAlreadyExistsError, InvalidCredentialsError
from app.auth.service import AuthService
from app.constants import (
    RESPONSE_MSG_INTERNAL_ERROR,
    RESPONSE_MSG_MISSING_FIELDS,
)
from app.utils import extract_validation_errors, json_response


auth_service = AuthService()


class RegisterView(MethodView):
    """
    Handles POST /auth/register — creates a new user account.
    """

    def post(self) -> tuple[Response, HTTPStatus]:
        """Create a new user account.

        Returns:
            201 with customToken and user data on success.
            400 if required fields are missing or invalid.
            409 if the email is already registered.
            500 on unexpected errors.
        """
        body = request.get_json() or {}

        try:
            input_data = UserRegisterPayloadDTO.model_validate(body)
        except ValidationError as err:
            return json_response(
                message=RESPONSE_MSG_MISSING_FIELDS,
                errors=extract_validation_errors(err),
                status_code=HTTPStatus.BAD_REQUEST,
            )

        try:
            result = auth_service.register_user(input_data)
        except EmailAlreadyExistsError:
            return json_response(
                message=RESPONSE_MSG_REGISTRATION_FAILED,
                status_code=HTTPStatus.CONFLICT,
            )
        except Exception:
            return json_response(
                message=RESPONSE_MSG_INTERNAL_ERROR,
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return json_response(
            message=RESPONSE_MSG_REGISTER_SUCCESS,
            data=result.model_dump(by_alias=True),
            status_code=HTTPStatus.CREATED,
        )


class LoginView(MethodView):
    """
    Handles POST /auth/login — authenticates a user and returns a custom token.
    """

    def post(self) -> tuple[Response, HTTPStatus]:
        """Authenticate an existing user.

        Returns:
            200 with customToken and user data on success.
            400 if required fields are missing.
            401 if credentials are wrong.
            500 on unexpected errors.
        """
        body = request.get_json() or {}

        try:
            input_data = UserLoginPayloadDTO.model_validate(body)
        except ValidationError as err:
            return json_response(
                message=RESPONSE_MSG_MISSING_FIELDS,
                errors=extract_validation_errors(err),
                status_code=HTTPStatus.BAD_REQUEST,
            )

        try:
            result = auth_service.login_user(input_data)
        except InvalidCredentialsError:
            return json_response(
                message=RESPONSE_MSG_INVALID_CREDENTIALS,
                status_code=HTTPStatus.UNAUTHORIZED,
            )
        except Exception:
            return json_response(
                message=RESPONSE_MSG_INTERNAL_ERROR,
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return json_response(
            message=RESPONSE_MSG_LOGIN_SUCCESS,
            data=result.model_dump(by_alias=True),
            status_code=HTTPStatus.OK,
        )
