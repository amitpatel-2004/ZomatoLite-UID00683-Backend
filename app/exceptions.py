from http import HTTPStatus

from app.constants import RESPONSE_MSG_INTERNAL_ERROR


class CustomException(Exception):
    status_code: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR
    message: str = RESPONSE_MSG_INTERNAL_ERROR
    detail: str = ""

    def __init__(self, detail: str = ""):
        super().__init__(detail)
        self.detail = detail
