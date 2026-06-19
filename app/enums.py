from enum import Enum


class ApiVersionPrefix(Enum):
    """Centralized API routing version prefixes."""

    V1 = "/api/v1"


class UserRole(str, Enum):
    """Enum for user role types."""

    CUSTOMER = "customer"
    OWNER = "owner"


class FirestoreCollections(str, Enum):
    """Firestore collection name constants."""

    USERS = "users"
    RESTAURANTS = "restaurants"
    ORDERS = "orders"
    MENU_ITEMS = "menuItems"
