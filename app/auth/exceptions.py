from http import HTTPStatus

from app.exceptions import BaseHTTPException
from app.auth.enums import AuthErrorMessage


class EmailAlreadyExistsError(BaseHTTPException):
    message = AuthErrorMessage.RESPONSE_MSG_REGISTRATION_FAILED
    status_code = HTTPStatus.CONFLICT


class InvalidCredentialsError(BaseHTTPException):
    message = AuthErrorMessage.RESPONSE_MSG_INVALID_CREDENTIALS
    status_code = HTTPStatus.UNAUTHORIZED
