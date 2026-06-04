from flask import jsonify


def success_response(data=None, message="Success", status_code=200):
    """Return a standardized success JSON response."""
    return jsonify({"success": True, "message": message, "data": data}), status_code


def error_response(message="Something went wrong", status_code=500):
    """Return a standardized error JSON response."""
    return jsonify({"success": False, "message": message, "data": None}), status_code
