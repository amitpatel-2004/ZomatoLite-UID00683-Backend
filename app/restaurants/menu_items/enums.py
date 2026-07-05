from enum import Enum


class MenuItemSuccessMessage(str, Enum):
    MENU_ITEMS_FETCHED = "Menu items fetched successfully."
    MENU_ITEM_ADDED = "Menu item added successfully."
    MENU_ITEM_UPDATED = "Menu item updated successfully."
    MENU_ITEM_DELETED = "Menu item deleted successfully."
    UPLOAD_URL_GENERATED = "Upload URL generated successfully."


class MenuItemErrorMessage(str, Enum):
    MENU_ITEM_NOT_FOUND = "Menu item not found."
    DUPLICATE_MENU_ITEM_NAME = (
        "A menu item with this name already exists in this restaurant."
    )


class MenuItemStatus(str, Enum):
    ACTIVE = "active"
    DELETED = "deleted"
