import time
from datetime import datetime
from zoneinfo import ZoneInfo

from app.enums import FirestoreCollections, MenuItemStatus, RestaurantStatus
from app.utils import generate_signed_upload_url
from app.restaurants.dtos import (
    CreateMenuItemPayloadDTO,
    CreateRestaurantPayloadDTO,
    MenuItemResponseDTO,
    RestaurantResponseDTO,
    UpdateMenuItemPayloadDTO,
    UpdateRestaurantPayloadDTO,
    UploadUrlResponseDTO,
)
from app.restaurants.exceptions import (
    MenuItemNotFoundError,
    NotRestaurantOwnerError,
    RestaurantNotFoundError,
)
from app.settings import FS_CLIENT
from app.utils import build_paginated_response


def _now() -> datetime:
    return datetime.now(ZoneInfo("UTC"))


class RestaurantService:
    """Handles all restaurant and menu item operations."""

    def _restaurant_ref(self, restaurant_id: str):
        return FS_CLIENT.collection(FirestoreCollections.RESTAURANTS).document(
            restaurant_id
        )

    def _menu_item_ref(self, restaurant_id: str, item_id: str):
        return (
            self._restaurant_ref(restaurant_id)
            .collection(FirestoreCollections.MENU_ITEMS)
            .document(item_id)
        )

    def _get_restaurant_or_raise(self, restaurant_id: str) -> dict:
        """Fetch restaurant data or raise RestaurantNotFoundError."""
        snapshot = self._restaurant_ref(restaurant_id).get()
        if not snapshot.exists:
            raise RestaurantNotFoundError()
        data = snapshot.to_dict() or {}
        if data.get("status") == RestaurantStatus.DELETED.value:
            raise RestaurantNotFoundError()
        return data

    def _verify_owner(self, restaurant_data: dict, owner_uid: str) -> None:
        """Raise NotRestaurantOwnerError if owner doesn't match."""
        if restaurant_data.get("ownerId") != owner_uid:
            raise NotRestaurantOwnerError()

    def _to_restaurant_dto(self, data: dict) -> RestaurantResponseDTO:
        return RestaurantResponseDTO(
            _id=data["_id"],
            owner_id=data["ownerId"],
            name=data["name"],
            cuisine_types=data.get("cuisineTypes", []),
            rating=data.get("rating", 0.0),
            status=data.get("status", RestaurantStatus.ACTIVE.value),
            opening_time=data.get("openingTime", ""),
            closing_time=data.get("closingTime", ""),
        )

    def _to_menu_item_dto(self, data: dict) -> MenuItemResponseDTO:
        return MenuItemResponseDTO(
            _id=data["_id"],
            name=data["name"],
            description=data.get("description", ""),
            price=data["price"],
            is_veg=data.get("isVeg", False),
            is_available=data.get("isAvailable", True),
            image_path=data.get("imagePath"),
            rating=data.get("rating", 0.0),
            status=data.get("status", MenuItemStatus.AVAILABLE.value),
        )

    def create_restaurant(
        self, owner_uid: str, payload: CreateRestaurantPayloadDTO
    ) -> RestaurantResponseDTO:
        """Create a new restaurant owned by the user.

        Returns:
            RestaurantResponseDTO with the new restaurant data.
        """
        ref = FS_CLIENT.collection(FirestoreCollections.RESTAURANTS).document()
        restaurant_id = ref.id
        data = {
            "_id": restaurant_id,
            "ownerId": owner_uid,
            "name": payload.name,
            "cuisineTypes": [c.value for c in payload.cuisine_types],
            "openingTime": payload.opening_time,
            "closingTime": payload.closing_time,
            "rating": 0.0,
            "status": RestaurantStatus.ACTIVE.value,
            "lastActivityAt": _now(),
            "metrics": {"totalItemsUploadedToday": 0, "lastUploadDate": ""},
            "_createdAt": _now(),
            "_updatedAt": _now(),
        }
        ref.set(data)
        return self._to_restaurant_dto(data)

    def list_restaurants(self, page: int, limit: int) -> dict:
        """Get paginated list of all active restaurants.

        Returns:
            Dict with items, page, and hasMore.
        """
        offset = (page - 1) * limit
        query = (
            FS_CLIENT.collection(FirestoreCollections.RESTAURANTS)
            .where("status", "==", RestaurantStatus.ACTIVE.value)
            .order_by("_createdAt", direction="DESCENDING")
            .offset(offset)
            .limit(limit + 1)
        )
        docs = query.stream()
        items = [
            self._to_restaurant_dto(doc.to_dict()).model_dump(by_alias=True)
            for doc in docs
        ]
        return build_paginated_response(items, page, limit)

    def list_owner_restaurants(self, owner_uid: str, page: int, limit: int) -> dict:
        """Get paginated list of active restaurants belonging to the owner.

        Returns:
            Dict with items, page, and hasMore.
        """
        offset = (page - 1) * limit
        query = (
            FS_CLIENT.collection(FirestoreCollections.RESTAURANTS)
            .where("ownerId", "==", owner_uid)
            .where("status", "==", RestaurantStatus.ACTIVE.value)
            .order_by("_createdAt", direction="DESCENDING")
            .offset(offset)
            .limit(limit + 1)
        )
        docs = query.stream()
        items = [
            self._to_restaurant_dto(doc.to_dict()).model_dump(by_alias=True)
            for doc in docs
        ]
        return build_paginated_response(items, page, limit)

    def get_restaurant(self, restaurant_id: str) -> RestaurantResponseDTO:
        """Fetch a single restaurant by ID.

        Raises:
            RestaurantNotFoundError: If restaurant doesn't exist or is deleted.
        """
        data = self._get_restaurant_or_raise(restaurant_id)
        return self._to_restaurant_dto(data)

    def update_restaurant(
        self, owner_uid: str, restaurant_id: str, payload: UpdateRestaurantPayloadDTO
    ) -> RestaurantResponseDTO:
        """Update fields on a restaurant the owner owns.

        Raises:
            RestaurantNotFoundError: If restaurant doesn't exist or is deleted.
            NotRestaurantOwnerError: If caller doesn't own the restaurant.
        """
        data = self._get_restaurant_or_raise(restaurant_id)
        self._verify_owner(data, owner_uid)

        updates: dict = {"_updatedAt": _now()}
        if payload.name is not None:
            updates["name"] = payload.name
        if payload.cuisine_types is not None:
            updates["cuisineTypes"] = [c.value for c in payload.cuisine_types]
        if payload.opening_time is not None:
            updates["openingTime"] = payload.opening_time
        if payload.closing_time is not None:
            updates["closingTime"] = payload.closing_time
        if payload.status is not None:
            updates["status"] = payload.status.value

        self._restaurant_ref(restaurant_id).update(updates)
        data.update(updates)
        return self._to_restaurant_dto(data)

    def delete_restaurant(self, owner_uid: str, restaurant_id: str) -> None:
        """Soft-delete a restaurant the owner owns by marking status as deleted.

        Raises:
            RestaurantNotFoundError: If restaurant doesn't exist or is already deleted.
            NotRestaurantOwnerError: If caller doesn't own the restaurant.
        """
        data = self._get_restaurant_or_raise(restaurant_id)
        self._verify_owner(data, owner_uid)
        self._restaurant_ref(restaurant_id).update(
            {
                "status": RestaurantStatus.DELETED.value,
                "_updatedAt": _now(),
            }
        )

    def add_menu_item(
        self, owner_uid: str, restaurant_id: str, payload: CreateMenuItemPayloadDTO
    ) -> MenuItemResponseDTO:
        """Add a new menu item to restaurant.

        Raises:
            RestaurantNotFoundError: If restaurant doesn't exist or is deleted.
            NotRestaurantOwnerError: If caller doesn't own the restaurant.
        """
        restaurant_data = self._get_restaurant_or_raise(restaurant_id)
        self._verify_owner(restaurant_data, owner_uid)

        item_ref = (
            self._restaurant_ref(restaurant_id)
            .collection(FirestoreCollections.MENU_ITEMS)
            .document()
        )
        item_id = item_ref.id
        data = {
            "_id": item_id,
            "name": payload.name,
            "description": payload.description,
            "price": payload.price,
            "isVeg": payload.is_veg,
            "isAvailable": payload.is_available,
            "imagePath": payload.image_path,
            "rating": 0.0,
            "status": MenuItemStatus.AVAILABLE.value,
            "_createdAt": _now(),
            "_updatedAt": _now(),
        }
        item_ref.set(data)
        return self._to_menu_item_dto(data)

    def list_menu_items(self, restaurant_id: str, page: int, limit: int) -> dict:
        """Get paginated menu items for a restaurant, excluding deleted items.

        Raises:
            RestaurantNotFoundError: If restaurant doesn't exist or is deleted.
        """
        self._get_restaurant_or_raise(restaurant_id)
        docs = (
            self._restaurant_ref(restaurant_id)
            .collection(FirestoreCollections.MENU_ITEMS)
            .order_by("_createdAt", direction="DESCENDING")
            .stream()
        )
        all_items = []
        for doc in docs:
            data = doc.to_dict() or {}
            if data.get("status") != MenuItemStatus.DELETED.value:
                all_items.append(self._to_menu_item_dto(data).model_dump(by_alias=True))

        offset = (page - 1) * limit
        page_items = all_items[offset : offset + limit + 1]
        return build_paginated_response(page_items, page, limit)

    def get_menu_item(self, restaurant_id: str, item_id: str) -> MenuItemResponseDTO:
        """Fetch a single menu item.

        Raises:
            RestaurantNotFoundError: If restaurant doesn't exist or is deleted.
            MenuItemNotFoundError: If menu item doesn't exist or is deleted.
        """
        self._get_restaurant_or_raise(restaurant_id)
        snapshot = self._menu_item_ref(restaurant_id, item_id).get()
        if not snapshot.exists:
            raise MenuItemNotFoundError()
        data = snapshot.to_dict() or {}
        if data.get("status") == MenuItemStatus.DELETED.value:
            raise MenuItemNotFoundError()
        return self._to_menu_item_dto(data)

    def update_menu_item(
        self,
        owner_uid: str,
        restaurant_id: str,
        item_id: str,
        payload: UpdateMenuItemPayloadDTO,
    ) -> MenuItemResponseDTO:
        """Update a menu item on a restaurant the owner owns.

        Raises:
            RestaurantNotFoundError: If restaurant doesn't exist or is deleted.
            NotRestaurantOwnerError: If caller doesn't own the restaurant.
            MenuItemNotFoundError: If menu item doesn't exist or is deleted.
        """
        restaurant_data = self._get_restaurant_or_raise(restaurant_id)
        self._verify_owner(restaurant_data, owner_uid)

        snapshot = self._menu_item_ref(restaurant_id, item_id).get()
        if not snapshot.exists:
            raise MenuItemNotFoundError()
        data = snapshot.to_dict() or {}
        if data.get("status") == MenuItemStatus.DELETED.value:
            raise MenuItemNotFoundError()

        updates: dict = {"_updatedAt": _now()}
        if payload.name is not None:
            updates["name"] = payload.name
        if payload.description is not None:
            updates["description"] = payload.description
        if payload.price is not None:
            updates["price"] = payload.price
        if payload.is_veg is not None:
            updates["isVeg"] = payload.is_veg
        if payload.image_path is not None:
            updates["imagePath"] = payload.image_path
        if payload.is_available is not None:
            updates["isAvailable"] = payload.is_available

        self._menu_item_ref(restaurant_id, item_id).update(updates)
        data.update(updates)
        return self._to_menu_item_dto(data)

    def delete_menu_item(
        self, owner_uid: str, restaurant_id: str, item_id: str
    ) -> None:
        """Soft-delete a menu item by marking status as deleted.

        Raises:
            RestaurantNotFoundError: If restaurant doesn't exist or is deleted.
            NotRestaurantOwnerError: If caller doesn't own the restaurant.
            MenuItemNotFoundError: If menu item doesn't exist or is already deleted.
        """
        restaurant_data = self._get_restaurant_or_raise(restaurant_id)
        self._verify_owner(restaurant_data, owner_uid)

        snapshot = self._menu_item_ref(restaurant_id, item_id).get()
        if not snapshot.exists:
            raise MenuItemNotFoundError()
        data = snapshot.to_dict() or {}
        if data.get("status") == MenuItemStatus.DELETED.value:
            raise MenuItemNotFoundError()
        self._menu_item_ref(restaurant_id, item_id).update(
            {
                "status": MenuItemStatus.DELETED.value,
                "_updatedAt": _now(),
            }
        )

    def generate_menu_item_upload_url(
        self,
        owner_uid: str,
        restaurant_id: str,
        file_name: str,
        content_type: str,
    ) -> UploadUrlResponseDTO:
        """Generate a signed URL for direct menu item image upload.

        Raises:
            RestaurantNotFoundError: If restaurant doesn't exist or is deleted.
            NotRestaurantOwnerError: If caller doesn't own the restaurant.
        """
        restaurant_data = self._get_restaurant_or_raise(restaurant_id)
        self._verify_owner(restaurant_data, owner_uid)

        timestamp = int(time.time())
        object_path = f"restaurants/{restaurant_id}/menu-items/{timestamp}_{file_name}"
        upload_url = generate_signed_upload_url(object_path, content_type)

        return UploadUrlResponseDTO(upload_url=upload_url, image_path=object_path)
