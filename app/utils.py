from flask import jsonify


def json_response(success: bool, message: str, data=None, status_code: int = 200):
    """Return a standard JSON response tuple for Flask routes.

    :param success: True for success, False for error.
    :param message: Description of the response status.
    :param data: Optional payload data.
    :param status_code: HTTP status code (default: 200).
    :return: Tuple of (Flask Response, int status code).
    """
    response_body = {"success": success, "message": message, "data": data}
    return jsonify(response_body), status_code
