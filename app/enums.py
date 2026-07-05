from enum import Enum


class SuccessMessage(str, Enum):
    RESPONSE_MSG_HEALTH_OK = "OK"


class ErrorMessage(str, Enum):
    RESPONSE_MSG_MISSING_FIELDS = "Required fields are missing."
    RESPONSE_MSG_FORBIDDEN = "You do not have permission to access this resource."
    RESPONSE_MSG_INTERNAL_ERROR = "An unexpected error occurred."


class ApiVersionPrefix(Enum):
    """Centralized API routing version prefixes."""

    V1 = "/api/v1"


class FirestoreCollections(str, Enum):
    """Firestore collection name constants."""

    USERS = "users"
    RESTAURANTS = "restaurants"
    ORDERS = "orders"
    MENU_ITEMS = "menuItems"
