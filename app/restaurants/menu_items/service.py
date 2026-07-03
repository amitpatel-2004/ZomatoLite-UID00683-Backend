from uuid import uuid4
from datetime import datetime
from zoneinfo import ZoneInfo

from app.constants import DUPLICATE_NAME_CHECK_LIMIT
from app.enums import FirestoreCollections, MenuItemStatus
from app.utils import generate_signed_upload_url, paginate_query
from app.restaurants.menu_items.dtos import (
    CreateMenuItemPayloadDTO,
    MenuItemResponseDTO,
    UpdateMenuItemPayloadDTO,
    UploadUrlResponseDTO,
)
from app.restaurants.exceptions import (
    DuplicateMenuItemNameError,
    MenuItemNotFoundError,
)
from app.restaurants.service import RestaurantService
from app.settings import FS_CLIENT


def _now() -> datetime:
    return datetime.now(ZoneInfo("UTC"))


class MenuItemService:
    """Handles all menu item operations."""

    def _assert_menu_item_name_unique(
        self, restaurant_id: str, name: str, exclude_id: str | None = None
    ) -> None:
        """Raise if an active menu item with this name exists, other than exclude_id.

        Args:
            exclude_id: The menu item being updated, excluded from the duplicate check.

        Raises:
            DuplicateMenuItemNameError: If an active menu item with this name exists.
        """
        docs = (
            FS_CLIENT.collection(
                f"{FirestoreCollections.RESTAURANTS.value}/{restaurant_id}/{FirestoreCollections.MENU_ITEMS.value}"
            )
            .where("name", "==", name)
            .where("status", "==", MenuItemStatus.ACTIVE)
            .limit(DUPLICATE_NAME_CHECK_LIMIT)
            .get()
        )
        for doc in docs:
            if doc.id != exclude_id:
                raise DuplicateMenuItemNameError(
                    detail=f"A menu item named '{name}' already exists in this restaurant."
                )

    @staticmethod
    def _to_response(data: dict) -> dict:
        return MenuItemResponseDTO.model_validate(data).model_dump(by_alias=True)

    def add_menu_item(
        self, restaurant_id: str, payload: CreateMenuItemPayloadDTO
    ) -> MenuItemResponseDTO:
        """Add a new menu item to restaurant.

        Raises:
            RestaurantNotFoundError: If restaurant doesn't exist or is deleted.
            DuplicateMenuItemNameError: If a menu item with the same name exists.
        """
        RestaurantService().get_restaurant(restaurant_id)
        self._assert_menu_item_name_unique(restaurant_id, payload.name)

        item_ref = FS_CLIENT.collection(
            f"{FirestoreCollections.RESTAURANTS.value}/{restaurant_id}/{FirestoreCollections.MENU_ITEMS.value}"
        ).document()
        item_id = item_ref.id
        data = {
            "_id": item_id,
            "name": payload.name,
            "description": payload.description,
            "price": payload.price,
            "isVeg": payload.is_veg,
            "imagePath": payload.image_path,
            "rating": 0.0,
            "quantity": payload.quantity,
            "status": MenuItemStatus.ACTIVE,
            "_createdAt": _now(),
            "_updatedAt": _now(),
        }
        item_ref.set(data)
        return MenuItemResponseDTO.model_validate(data)

    def list_menu_items(
        self, restaurant_id: str, cursor: str | None, limit: int
    ) -> dict:
        """Get cursor-paginated menu items for a restaurant, excluding deleted items.

        Raises:
            RestaurantNotFoundError: If restaurant doesn't exist or is deleted.
        """
        RestaurantService().get_restaurant(restaurant_id)
        query = (
            FS_CLIENT.collection(
                f"{FirestoreCollections.RESTAURANTS.value}/{restaurant_id}/{FirestoreCollections.MENU_ITEMS.value}"
            )
            .where("status", "==", MenuItemStatus.ACTIVE)
            .order_by("_createdAt", direction="DESCENDING")
            .limit(limit + 1)
        )
        return paginate_query(query, limit, self._to_response, cursor)

    def get_menu_item(self, restaurant_id: str, item_id: str) -> MenuItemResponseDTO:
        """Fetch a single menu item.

        Raises:
            RestaurantNotFoundError: If restaurant doesn't exist or is deleted.
            MenuItemNotFoundError: If menu item doesn't exist or is deleted.
        """
        RestaurantService().get_restaurant(restaurant_id)
        snapshot = FS_CLIENT.document(
            f"{FirestoreCollections.RESTAURANTS.value}/{restaurant_id}/{FirestoreCollections.MENU_ITEMS.value}/{item_id}"
        ).get()
        if not snapshot.exists:
            raise MenuItemNotFoundError(
                detail=f"No menu item found with id: {item_id} in restaurant: {restaurant_id}"
            )
        data = snapshot.to_dict()
        if data.get("status") == MenuItemStatus.DELETED:
            raise MenuItemNotFoundError(
                detail=f"No menu item found with id: {item_id} in restaurant: {restaurant_id}"
            )
        return MenuItemResponseDTO.model_validate(data)

    def update_menu_item(
        self,
        restaurant_id: str,
        item_id: str,
        payload: UpdateMenuItemPayloadDTO,
    ) -> MenuItemResponseDTO:
        """Update a menu item on a restaurant.

        Raises:
            RestaurantNotFoundError: If restaurant doesn't exist or is deleted.
            MenuItemNotFoundError: If menu item doesn't exist or is deleted.
            DuplicateMenuItemNameError: If another menu item with the same name exists.
        """
        RestaurantService().get_restaurant(restaurant_id)

        snapshot = FS_CLIENT.document(
            f"{FirestoreCollections.RESTAURANTS.value}/{restaurant_id}/{FirestoreCollections.MENU_ITEMS.value}/{item_id}"
        ).get()
        if not snapshot.exists:
            raise MenuItemNotFoundError(
                detail=f"No menu item found with id: {item_id} in restaurant: {restaurant_id}"
            )
        data = snapshot.to_dict()
        if data.get("status") == MenuItemStatus.DELETED:
            raise MenuItemNotFoundError(
                detail=f"No menu item found with id: {item_id} in restaurant: {restaurant_id}"
            )

        if payload.name is not None:
            self._assert_menu_item_name_unique(
                restaurant_id, payload.name, exclude_id=item_id
            )

        updates = payload.model_dump(by_alias=True, exclude_none=True, mode="json")
        updates["_updatedAt"] = _now()
        FS_CLIENT.document(
            f"{FirestoreCollections.RESTAURANTS.value}/{restaurant_id}/{FirestoreCollections.MENU_ITEMS.value}/{item_id}"
        ).set(updates, merge=True)
        data.update(updates)
        return MenuItemResponseDTO.model_validate(data)

    def delete_menu_item(self, restaurant_id: str, item_id: str) -> None:
        """Soft-delete a menu item by setting its status to deleted.

        Raises:
            RestaurantNotFoundError: If restaurant doesn't exist or is deleted.
            MenuItemNotFoundError: If menu item doesn't exist or is already deleted.
        """
        # TODO: Once orders feature is implemented, prevent deletion if the item is part of an active order.
        RestaurantService().get_restaurant(restaurant_id)

        snapshot = FS_CLIENT.document(
            f"{FirestoreCollections.RESTAURANTS.value}/{restaurant_id}/{FirestoreCollections.MENU_ITEMS.value}/{item_id}"
        ).get()
        if not snapshot.exists:
            raise MenuItemNotFoundError(
                detail=f"No menu item found with id: {item_id} in restaurant: {restaurant_id}"
            )
        data = snapshot.to_dict()
        if data.get("status") == MenuItemStatus.DELETED:
            raise MenuItemNotFoundError(
                detail=f"No menu item found with id: {item_id} in restaurant: {restaurant_id}"
            )
        FS_CLIENT.document(
            f"{FirestoreCollections.RESTAURANTS.value}/{restaurant_id}/{FirestoreCollections.MENU_ITEMS.value}/{item_id}"
        ).update(
            {
                "status": MenuItemStatus.DELETED,
                "_updatedAt": _now(),
            }
        )

    def generate_menu_item_upload_url(
        self,
        restaurant_id: str,
        file_name: str,
        content_type: str,
    ) -> UploadUrlResponseDTO:
        """Generate a signed URL for direct menu item image upload.

        Raises:
            RestaurantNotFoundError: If restaurant doesn't exist or is deleted.
        """
        RestaurantService().get_restaurant(restaurant_id)

        object_path = (
            f"restaurants/{restaurant_id}/menu-items/{uuid4().hex}_{file_name}"
        )
        upload_url = generate_signed_upload_url(object_path, content_type)
        return UploadUrlResponseDTO(upload_url=upload_url, image_path=object_path)
