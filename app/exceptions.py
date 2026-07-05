from http import HTTPStatus

from app.enums import ErrorMessage


class BaseHTTPException(Exception):
    status_code: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR
    message: str = ErrorMessage.RESPONSE_MSG_INTERNAL_ERROR
    detail: str = ""

    def __init__(self, detail: str = ""):
        super().__init__(detail)
        self.detail = detail
