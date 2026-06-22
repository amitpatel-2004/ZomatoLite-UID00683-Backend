from app.restaurants.dtos import MenuItemResponseDTO, RestaurantResponseDTO


def get_valid_create_restaurant_payload() -> dict:
    """Return a valid restaurant creation request body."""
    return {
        "name": "Test Restaurant",
        "cuisineTypes": ["indian"],
        "openingTime": "09:00",
        "closingTime": "22:00",
    }


def get_valid_update_restaurant_payload() -> dict:
    """Return a valid restaurant update body."""
    return {"name": "Updated Restaurant"}


def get_valid_create_menu_item_payload() -> dict:
    """Return a valid menu item creation request body."""
    return {
        "name": "Butter Chicken",
        "description": "Creamy tomato curry",
        "price": 299.0,
        "isVeg": False,
        "isAvailable": True,
    }


def get_mock_firestore_restaurant_doc(owner_uid: str = "owner-uid-123") -> dict:
    """Return a mock Firestore restaurant document."""
    return {
        "_id": "rest-123",
        "ownerId": owner_uid,
        "name": "Test Restaurant",
        "cuisineTypes": ["indian"],
        "openingTime": "09:00",
        "closingTime": "22:00",
        "rating": 0.0,
        "status": "active",
        "lastActivityAt": None,
        "metrics": {"totalItemsUploadedToday": 0, "lastUploadDate": ""},
    }


def get_mock_restaurant_response(owner_uid: str = "owner-uid-123") -> RestaurantResponseDTO:
    """Return a mock RestaurantResponseDTO."""
    return RestaurantResponseDTO(
        _id="rest-123",
        owner_id=owner_uid,
        name="Test Restaurant",
        cuisine_types=["indian"],
        rating=0.0,
        status="active",
        opening_time="09:00",
        closing_time="22:00",
    )


def get_mock_menu_item_response() -> MenuItemResponseDTO:
    """Return a mock MenuItemResponseDTO."""
    return MenuItemResponseDTO(
        _id="item-123",
        name="Butter Chicken",
        description="Creamy tomato curry",
        price=299.0,
        is_veg=False,
        is_available=True,
        image_path=None,
        rating=0.0,
        status="available",
    )
