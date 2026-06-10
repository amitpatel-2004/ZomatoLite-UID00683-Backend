from flask import Blueprint
from app.constants import SuccessMessages
from app.utils import json_response

main_bp = Blueprint('main', __name__)

@main_bp.route('/health', methods=['GET'])
def health_check():
    """
    Verify server health and return status.
    :return: JSON response indicating server is running.
    """
    return json_response(
        success=True, 
        message=SuccessMessages.SERVER_HEALTHY, 
        status_code=200
    )
