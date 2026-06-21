from http import HTTPStatus
from typing import Any
from flask import jsonify, Response
from pydantic import ValidationError


def extract_validation_errors(err: ValidationError) -> dict:
    return {str(e["loc"][0]): e["msg"] for e in err.errors()}


def json_response(
    message: str,
    data: Any = None,
    errors: dict[str, Any] | None = None,
    status_code: HTTPStatus = HTTPStatus.OK,
) -> tuple[Response, HTTPStatus]:
    """Return a standardized JSON response tuple for Flask routes.

    Args:
        message: Description of the response status.
        data: Optional payload data.
        errors: Optional dictionary containing structured validation or system errors.
        status_code: HTTP status code (default: 200).

    Returns:
        Tuple of (Flask Response, int status code).
    """
    response_body: dict[str, Any] = {"message": message}

    if data is not None:
        response_body["data"] = data

    if errors is not None:
        response_body["errors"] = errors

    return jsonify(response_body), status_code
