from enum import Enum


class RestaurantSuccessMessage(str, Enum):
    RESTAURANTS_FETCHED = "Restaurants fetched successfully."
    RESTAURANT_CREATED = "Restaurant created successfully."
    RESTAURANT_UPDATED = "Restaurant updated successfully."
    RESTAURANT_DELETED = "Restaurant deleted successfully."


class RestaurantErrorMessage(str, Enum):
    RESTAURANT_NOT_FOUND = "Restaurant not found."
    DUPLICATE_RESTAURANT_NAME = "A restaurant with this name already exists."


class RestaurantStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"


class CuisineType(str, Enum):
    INDIAN = "indian"
    CHINESE = "chinese"
    ITALIAN = "italian"
    OTHER = "other"
