from datetime import datetime
from zoneinfo import ZoneInfo

from app.enums import FirestoreCollections, RestaurantStatus
from app.utils import paginate_query
from app.restaurants.dtos import (
    CreateRestaurantPayloadDTO,
    RestaurantResponseDTO,
    UpdateRestaurantPayloadDTO,
)
from app.restaurants.exceptions import (
    DuplicateRestaurantNameError,
    RestaurantNotFoundError,
)
from app.settings import FS_CLIENT


def _now() -> datetime:
    return datetime.now(ZoneInfo("UTC"))


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
        self, name: str, exclude_id: str | None = None
    ) -> None:
        docs = (
            FS_CLIENT.collection(FirestoreCollections.RESTAURANTS)
            .where("name", "==", name)
            .limit(2)
            .get()
        )
        for doc in docs:
            data = doc.to_dict()
            if doc.id != exclude_id and data.get("status") != RestaurantStatus.DELETED:
                raise DuplicateRestaurantNameError(
                    detail=f"A restaurant named '{name}' already exists."
                )

    @staticmethod
    def _to_response(data: dict) -> dict:
        return RestaurantResponseDTO.model_validate(data).model_dump(by_alias=True)

    def create_restaurant(
        self, owner_uid: str, payload: CreateRestaurantPayloadDTO
    ) -> RestaurantResponseDTO:
        """Create a new restaurant owned by the user.

        Returns:
            RestaurantResponseDTO with the new restaurant data.
        """
        self._assert_restaurant_name_unique(payload.name)
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
        ref.set(data)
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
            .limit(limit + 1)
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
            .limit(limit + 1)
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
        self, restaurant_id: str, payload: UpdateRestaurantPayloadDTO
    ) -> RestaurantResponseDTO:
        """Update fields on a restaurant.

        Raises:
            RestaurantNotFoundError: If restaurant doesn't exist or is deleted.
            DuplicateRestaurantNameError: If another restaurant with the same name exists.
        """
        data = self._get_restaurant_or_raise(restaurant_id)
        if payload.name is not None:
            self._assert_restaurant_name_unique(payload.name, exclude_id=restaurant_id)
        updates = payload.model_dump(by_alias=True, exclude_none=True, mode="json")
        updates["_updatedAt"] = _now()
        FS_CLIENT.document(
            f"{FirestoreCollections.RESTAURANTS.value}/{restaurant_id}"
        ).set(updates, merge=True)
        data.update(updates)
        return RestaurantResponseDTO.model_validate(data)

    def delete_restaurant(self, restaurant_id: str) -> None:
        """Soft-delete a restaurant by marking its status as deleted.

        Raises:
            RestaurantNotFoundError: If restaurant doesn't exist or is already deleted.
        """
        # TODO: When orders feature is implemented, prevent deletion if restaurant has active orders.
        self._get_restaurant_or_raise(restaurant_id)
        FS_CLIENT.document(
            f"{FirestoreCollections.RESTAURANTS.value}/{restaurant_id}"
        ).update(
            {
                "status": RestaurantStatus.DELETED,
                "_updatedAt": _now(),
            }
        )
