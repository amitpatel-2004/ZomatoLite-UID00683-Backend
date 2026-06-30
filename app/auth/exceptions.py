from http import HTTPStatus

from app.exceptions import CustomException
from app.auth.constants import (
    RESPONSE_MSG_REGISTRATION_FAILED,
    RESPONSE_MSG_INVALID_CREDENTIALS,
)


class EmailAlreadyExistsError(CustomException):
    message = RESPONSE_MSG_REGISTRATION_FAILED
    status_code = HTTPStatus.CONFLICT


class InvalidCredentialsError(CustomException):
    message = RESPONSE_MSG_INVALID_CREDENTIALS
    status_code = HTTPStatus.UNAUTHORIZED
