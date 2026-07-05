from datetime import datetime
from zoneinfo import ZoneInfo

from google.cloud import firestore

from app.constants import TIMEZONE
from app.enums import FirestoreCollections
from app.utils import paginate_query
from app.restaurants.dtos import (
    CreateRestaurantPayloadDTO,
    RestaurantResponseDTO,
    UpdateRestaurantPayloadDTO,
)
from app.restaurants.enums import RestaurantStatus
from app.restaurants.exceptions import (
    DuplicateRestaurantNameError,
    RestaurantHasActiveOrdersError,
    RestaurantNotFoundError,
)
from app.restaurants.menu_items.enums import MenuItemStatus
from app.restaurants.orders.constants import ACTIVE_ORDER_STATUSES
from app.settings import FS_CLIENT


def _now() -> datetime:
    return datetime.now(ZoneInfo(TIMEZONE))


class RestaurantService:
    """Handles all restaurant operations."""

    def _get_restaurant_or_raise(self, restaurant_id: str) -> dict:
        """Fetch restaurant data or raise RestaurantNotFoundError."""
        snapshot = FS_CLIENT.document(
            f"{FirestoreCollections.RESTAURANTS.value}/{restaurant_id}"
        ).get()
        if not snapshot.exists:
            raise RestaurantNotFoundError(
                detail=f"No restaurant found with id: {restaurant_id}"
            )
        data = snapshot.to_dict()
        if data.get("status") == RestaurantStatus.DELETED:
            raise RestaurantNotFoundError(
                detail=f"No restaurant found with id: {restaurant_id}"
            )
        return data

    def _assert_restaurant_name_unique(
        self, name: str, exclude_id: str | None = None, transaction=None
    ) -> None:
        """Raise if an active restaurant with this name exists, other than exclude_id.

        Args:
            exclude_id: The restaurant being updated, excluded from the duplicate check.

        Raises:
            DuplicateRestaurantNameError: If an active restaurant with this name exists.
        """
        query = (
            FS_CLIENT.collection(FirestoreCollections.RESTAURANTS)
            .where("name", "==", name)
            .where("status", "==", RestaurantStatus.ACTIVE)
            .limit(1)
        )
        docs = query.get(transaction=transaction)
        for doc in docs:
            if doc.id != exclude_id:
                raise DuplicateRestaurantNameError(
                    detail=f"A restaurant named '{name}' already exists."
                )

    @staticmethod
    def _to_response(data: dict) -> dict:
        return RestaurantResponseDTO.model_validate(data).model_dump(by_alias=True)

    def _assert_no_active_orders(self, restaurant_id: str, transaction=None) -> None:
        """Raise if the restaurant has an order that hasn't reached a terminal status.

        Raises:
            RestaurantHasActiveOrdersError: If an active order exists for this restaurant.
        """
        query = (
            FS_CLIENT.collection(
                f"{FirestoreCollections.RESTAURANTS.value}/{restaurant_id}/{FirestoreCollections.ORDERS.value}"
            )
            .where("status", "in", ACTIVE_ORDER_STATUSES)
            .limit(1)
        )
        docs = query.get(transaction=transaction)
        if len(docs) > 0:
            raise RestaurantHasActiveOrdersError()

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
            "description": payload.description,
            "cuisineTypes": [c.value for c in payload.cuisine_types],
            "openingTime": payload.opening_time,
            "closingTime": payload.closing_time,
            "rating": 0.0,
            "status": RestaurantStatus.ACTIVE,
            "lastActivityAt": _now(),
            "metrics": {"totalItemsUploadedToday": 0, "lastUploadDate": ""},
            "_createdAt": _now(),
            "_updatedAt": _now(),
        }

        transaction = FS_CLIENT.transaction()

        @firestore.transactional
        def _create(transaction):
            self._assert_restaurant_name_unique(payload.name, transaction=transaction)
            transaction.set(ref, data)

        _create(transaction)
        return RestaurantResponseDTO.model_validate(data)

    def list_restaurants(self, cursor: str | None, limit: int) -> dict:
        """Get cursor-paginated list of all active restaurants.

        Returns:
            Dict with items, nextCursor, and hasMore.
        """
        query = (
            FS_CLIENT.collection(FirestoreCollections.RESTAURANTS)
            .where("status", "==", RestaurantStatus.ACTIVE)
            .order_by("_createdAt", direction="DESCENDING")
            .limit(limit)
        )
        cursor_ref = (
            FS_CLIENT.document(f"{FirestoreCollections.RESTAURANTS.value}/{cursor}")
            if cursor
            else None
        )
        return paginate_query(query, limit, self._to_response, cursor_ref)

    def list_owner_restaurants(
        self, owner_uid: str, cursor: str | None, limit: int
    ) -> dict:
        """Get cursor-paginated list of active restaurants belonging to the owner.

        Returns:
            Dict with items, nextCursor, and hasMore.
        """
        query = (
            FS_CLIENT.collection(FirestoreCollections.RESTAURANTS)
            .where("ownerId", "==", owner_uid)
            .where("status", "==", RestaurantStatus.ACTIVE)
            .order_by("_createdAt", direction="DESCENDING")
            .limit(limit)
        )
        cursor_ref = (
            FS_CLIENT.document(f"{FirestoreCollections.RESTAURANTS.value}/{cursor}")
            if cursor
            else None
        )
        return paginate_query(query, limit, self._to_response, cursor_ref)

    def get_restaurant(self, restaurant_id: str) -> RestaurantResponseDTO:
        """Fetch a single restaurant by ID.

        Raises:
            RestaurantNotFoundError: If restaurant doesn't exist or is deleted.
        """
        data = self._get_restaurant_or_raise(restaurant_id)
        return RestaurantResponseDTO.model_validate(data)

    def update_restaurant(
        self,
        restaurant_id: str,
        payload: UpdateRestaurantPayloadDTO,
        restaurant: RestaurantResponseDTO,
    ) -> RestaurantResponseDTO:
        """Update fields on a restaurant.

        Raises:
            DuplicateRestaurantNameError: If another restaurant with the same name exists.
        """
        updates = payload.model_dump(by_alias=True, exclude_none=True, mode="json")
        updates["_updatedAt"] = _now()
        ref = FS_CLIENT.document(
            f"{FirestoreCollections.RESTAURANTS.value}/{restaurant_id}"
        )

        transaction = FS_CLIENT.transaction()

        @firestore.transactional
        def _update(transaction):
            if payload.name is not None:
                self._assert_restaurant_name_unique(
                    payload.name, exclude_id=restaurant_id, transaction=transaction
                )
            transaction.set(ref, updates, merge=True)

        _update(transaction)

        data = restaurant.model_dump(by_alias=True)
        data.update(updates)
        return RestaurantResponseDTO.model_validate(data)

    def delete_restaurant(self, restaurant_id: str) -> None:
        """Soft-delete a restaurant, and cascade-delete its menu items.

        Raises:
            RestaurantHasActiveOrdersError: If the restaurant has an active order.
        """
        now = _now()
        restaurant_ref = FS_CLIENT.document(
            f"{FirestoreCollections.RESTAURANTS.value}/{restaurant_id}"
        )
        items_query = FS_CLIENT.collection(
            f"{FirestoreCollections.RESTAURANTS.value}/{restaurant_id}/{FirestoreCollections.MENU_ITEMS.value}"
        ).where("status", "==", MenuItemStatus.ACTIVE)

        transaction = FS_CLIENT.transaction()

        @firestore.transactional
        def _delete(transaction):
            self._assert_no_active_orders(restaurant_id, transaction=transaction)
            active_items = items_query.get(transaction=transaction)
            transaction.update(
                restaurant_ref, {"status": RestaurantStatus.DELETED, "_updatedAt": now}
            )
            for item in active_items:
                transaction.update(
                    item.reference,
                    {"status": MenuItemStatus.DELETED, "_updatedAt": now},
                )

        _delete(transaction)
