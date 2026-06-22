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


class RestaurantStatus(str, Enum):
    """Possible states for a restaurant."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"


class MenuItemStatus(str, Enum):
    """Possible states for a menu item."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DELETED = "deleted"


class CuisineType(str, Enum):
    """Allowed cuisine categories for a restaurant."""

    INDIAN = "indian"
    CHINESE = "chinese"
    ITALIAN = "italian"
    OTHER = "other"
