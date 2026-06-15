from http import HTTPStatus

from flask import request, Response
from flask.views import MethodView
from pydantic import ValidationError

from app.auth.constants import (
    FIREBASE_ERROR_EMAIL_EXISTS,
    RESPONSE_MSG_EMAIL_EXISTS,
    RESPONSE_MSG_INVALID_CREDENTIALS,
    RESPONSE_MSG_LOGIN_SUCCESS,
    RESPONSE_MSG_REGISTER_SUCCESS,
    RESPONSE_MSG_INVALID_ROLE,
)
from app.auth.schemas import UserLoginSchema, UserRegisterSchema, AuthResponseSchema
from app.auth.service import login_user, register_user
from app.constants import (
    RESPONSE_MSG_INTERNAL_ERROR,
    RESPONSE_MSG_MISSING_FIELDS,
)
from app.utils import json_response


class RegisterView(MethodView):
    """
    Handles POST /auth/register — creates a new user account.
    """

    def post(self) -> tuple[Response, HTTPStatus]:
        """Create a new user account.

        Expects JSON body:
            email (str): User's email address.
            password (str): User's chosen password.
            displayName (str): Name to display for the user.
            role (str): "customer" or "owner".

        Returns:
            201 with customToken and user data on success.
            400 if required fields are missing or role is invalid.
            409 if the email is already registered.
            500 on unexpected errors.
        """
        body = request.get_json(silent=True) or {}

        try:
            input_data = UserRegisterSchema(**body)
        except ValidationError as err:
            error_details = {str(e["loc"][0]): e["msg"] for e in err.errors()}

            is_role_error = any(
                e["loc"] == ("role",) and "value_error" in e["type"]
                for e in err.errors()
            )

            msg = (
                RESPONSE_MSG_INVALID_ROLE
                if is_role_error
                else RESPONSE_MSG_MISSING_FIELDS
            )

            return json_response(
                message=msg,
                errors=error_details,
                status_code=HTTPStatus.BAD_REQUEST,
            )

        try:
            raw_result = register_user(
                email=input_data.email,
                password=input_data.password,
                display_name=input_data.displayName,
                role=input_data.role,
            )

            output_data = AuthResponseSchema(**raw_result)
        except ValueError as exc:
            if FIREBASE_ERROR_EMAIL_EXISTS in str(exc):
                return json_response(
                    message=RESPONSE_MSG_EMAIL_EXISTS,
                    status_code=HTTPStatus.CONFLICT,
                )
            return json_response(
                message=RESPONSE_MSG_INTERNAL_ERROR,
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )
        except Exception:
            return json_response(
                message=RESPONSE_MSG_INTERNAL_ERROR,
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return json_response(
            message=RESPONSE_MSG_REGISTER_SUCCESS,
            data=output_data.model_dump(by_alias=True),
            status_code=HTTPStatus.CREATED,
        )


class LoginView(MethodView):
    """
    Handles POST /auth/login — authenticates a user and returns a custom token.
    """

    def post(self) -> tuple[Response, HTTPStatus]:
        """Authenticate an existing user.

        Expects JSON body:
            email (str): User's registered email address.
            password (str): User's password.

        Returns:
            200 with customToken and user data on success.
            400 if required fields are missing.
            401 if credentials are wrong.
            500 on unexpected errors.
        """
        body = request.get_json(silent=True) or {}

        try:
            input_data = UserLoginSchema(**body)
        except ValidationError as err:
            error_details = {str(e["loc"][0]): e["msg"] for e in err.errors()}
            return json_response(
                message=RESPONSE_MSG_MISSING_FIELDS,
                errors=error_details,
                status_code=HTTPStatus.BAD_REQUEST,
            )

        try:
            raw_result = login_user(
                email=input_data.email, password=input_data.password
            )
            output_data = AuthResponseSchema(**raw_result)
        except ValueError:
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
            data=output_data.model_dump(by_alias=True),
            status_code=HTTPStatus.OK,
        )
