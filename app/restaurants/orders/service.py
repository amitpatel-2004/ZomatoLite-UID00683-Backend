from datetime import datetime, time
from zoneinfo import ZoneInfo

from google.cloud import firestore

from app.constants import DEFAULT_CURRENCY, TIMEZONE
from app.enums import FirestoreCollections
from app.restaurants.enums import RestaurantStatus
from app.restaurants.menu_items.enums import MenuItemStatus
from app.restaurants.orders.constants import (
    BOOKING_FEE_FLAT,
    BOOKING_FEE_PERCENT,
    CURRENCY_DECIMAL_PLACES,
)
from app.restaurants.orders.dtos import CreateOrderPayloadDTO, OrderResponseDTO
from app.restaurants.orders.enums import OrderStatus
from app.restaurants.orders.exceptions import (
    InsufficientBalanceError,
    ItemUnavailableError,
    OwnRestaurantOrderError,
    PriceChangedError,
    RestaurantClosedError,
)
from app.restaurants.exceptions import RestaurantNotFoundError
from app.settings import FS_CLIENT


def _now() -> datetime:
    return datetime.now(ZoneInfo(TIMEZONE))


def _is_restaurant_open(opening_time: str, closing_time: str) -> bool:
    """Checks if the current time falls within the restaurants open hours."""
    now = _now().time().replace(second=0, microsecond=0)
    open_h, open_m = map(int, opening_time.split(":"))
    close_h, close_m = map(int, closing_time.split(":"))
    open_t = time(open_h, open_m)
    close_t = time(close_h, close_m)
    if open_t <= close_t:
        return open_t <= now < close_t
    return now >= open_t or now < close_t


def _calc_booking_fee(subtotal: float) -> float:
    return max(
        BOOKING_FEE_FLAT, round(subtotal * BOOKING_FEE_PERCENT, CURRENCY_DECIMAL_PLACES)
    )


class OrderService:
    """Handles all order operations."""

    def place_order(
        self, user_id: str, restaurant_id: str, payload: CreateOrderPayloadDTO
    ) -> OrderResponseDTO:
        """Place an order for the user, updating there balance.

        Validates restaurant availability, item availability, price match, and sufficient balance.

        Args:
            user_id: The UID of the authenticated user.
            restaurant_id: The ID of the restaurant being ordered from.
            payload: Validated order payload with items.

        Returns:
            OrderResponseDTO with the created order data.

        Raises:
            RestaurantNotFoundError: If the restaurant doesn't exist or is deleted.
            OwnRestaurantOrderError: If the user owns this restaurant.
            RestaurantClosedError: If the restaurant is not currently open.
            ItemUnavailableError: If any requested item is deleted or out of stock.
            PriceChangedError: If any item's price doesn't match what the client sent.
            InsufficientBalanceError: If the user's balance is too low.
        """
        restaurant_ref = FS_CLIENT.document(
            f"{FirestoreCollections.RESTAURANTS.value}/{restaurant_id}"
        )
        restaurant_snap = restaurant_ref.get()
        if not restaurant_snap.exists:
            raise RestaurantNotFoundError(
                detail=f"No restaurant found with id: {restaurant_id}"
            )
        restaurant_data = restaurant_snap.to_dict()
        if restaurant_data.get("status") == RestaurantStatus.DELETED:
            raise RestaurantNotFoundError(
                detail=f"No restaurant found with id: {restaurant_id}"
            )
        if restaurant_data.get("ownerId") == user_id:
            raise OwnRestaurantOrderError()
        if not _is_restaurant_open(
            restaurant_data["openingTime"], restaurant_data["closingTime"]
        ):
            raise RestaurantClosedError()

        item_refs = [
            FS_CLIENT.document(
                f"{FirestoreCollections.RESTAURANTS.value}/{restaurant_id}"
                f"/{FirestoreCollections.MENU_ITEMS.value}/{item.item_id}"
            )
            for item in payload.items
        ]

        user_ref = FS_CLIENT.document(f"{FirestoreCollections.USERS.value}/{user_id}")
        order_ref = FS_CLIENT.collection(
            f"{FirestoreCollections.RESTAURANTS.value}/{restaurant_id}"
            f"/{FirestoreCollections.ORDERS.value}"
        ).document()
        order_id = order_ref.id
        now = _now()

        transaction = FS_CLIENT.transaction()

        @firestore.transactional
        def _run(transaction):
            item_snaps = FS_CLIENT.get_all(item_refs, transaction=transaction)
            item_data_by_id: dict[str, dict] = {}
            for snap in item_snaps:
                if snap.exists:
                    item_data_by_id[snap.id] = snap.to_dict()

            order_items = []
            subtotal = 0.0
            for item_input in payload.items:
                item_data = item_data_by_id.get(item_input.item_id)
                if not item_data or item_data.get("status") == MenuItemStatus.DELETED:
                    raise ItemUnavailableError(
                        detail=f"Item '{item_input.item_id}' is not available."
                    )
                if (
                    item_data.get("quantity") is not None
                    and item_data["quantity"] < item_input.quantity
                ):
                    raise ItemUnavailableError(
                        detail=f"Not enough stock for item '{item_data['name']}'."
                    )
                actual_price = item_data["price"]
                if round(actual_price, CURRENCY_DECIMAL_PLACES) != round(
                    item_input.unit_price, CURRENCY_DECIMAL_PLACES
                ):
                    raise PriceChangedError(
                        detail=f"Price for '{item_data['name']}' has changed."
                    )
                subtotal += actual_price * item_input.quantity
                order_items.append(
                    {
                        "itemId": item_input.item_id,
                        "name": item_data["name"],
                        "quantity": item_input.quantity,
                        "unitPrice": actual_price,
                    }
                )

            subtotal = round(subtotal, CURRENCY_DECIMAL_PLACES)
            booking_fee = _calc_booking_fee(subtotal)
            total = round(subtotal + booking_fee, CURRENCY_DECIMAL_PLACES)

            user_snap = user_ref.get(transaction=transaction)
            user_data = user_snap.to_dict()
            balance = user_data.get("balance", 0)
            if balance < total:
                raise InsufficientBalanceError(
                    detail=f"Balance {balance} is less than required {total}."
                )
            currency = user_data.get("currency", DEFAULT_CURRENCY)
            pricing_summary = {
                "subtotal": subtotal,
                "bookingFee": booking_fee,
                "total": total,
            }
            order_doc = {
                "_id": order_id,
                "customerId": user_id,
                "status": OrderStatus.PENDING,
                "restaurant": {"name": restaurant_data["name"]},
                "currency": currency,
                "pricingSummary": pricing_summary,
                "items": order_items,
                "itemIds": [item.item_id for item in payload.items],
                "_createdAt": now,
                "_updatedAt": now,
            }
            transaction.update(
                user_ref, {"balance": balance - total, "_updatedAt": now}
            )
            transaction.update(restaurant_ref, {"lastActivityAt": now})
            transaction.set(order_ref, order_doc)
            for item_ref, item_input in zip(item_refs, payload.items):
                item_data = item_data_by_id[item_input.item_id]
                if item_data.get("quantity") is not None:
                    transaction.update(
                        item_ref,
                        {
                            "quantity": item_data["quantity"] - item_input.quantity,
                            "_updatedAt": now,
                        },
                    )
            return currency, pricing_summary, order_items

        currency, pricing_summary, order_items = _run(transaction)

        return OrderResponseDTO.model_validate(
            {
                "_id": order_id,
                "customerId": user_id,
                "status": OrderStatus.PENDING,
                "restaurant": {"name": restaurant_data["name"]},
                "currency": currency,
                "pricingSummary": pricing_summary,
                "items": order_items,
            }
        )
