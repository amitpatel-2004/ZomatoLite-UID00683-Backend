from typing import Annotated

from pydantic import Field, StringConstraints

from app.dtos import BaseDTO, CurrencyDTO
from app.restaurants.constants import MENU_ITEM_MAX_PRICE
from app.restaurants.orders.constants import ORDER_ITEM_MAX_QUANTITY, ORDER_MAX_ITEMS
from app.restaurants.orders.enums import OrderStatus


class OrderItemInputDTO(BaseDTO):
    """A single item entry in the order request."""

    item_id: Annotated[str, StringConstraints(min_length=1)]
    quantity: int = Field(gt=0, le=ORDER_ITEM_MAX_QUANTITY)
    unit_price: float = Field(gt=0, le=MENU_ITEM_MAX_PRICE)


class CreateOrderPayloadDTO(BaseDTO):
    """Validation DTO for placing an order."""

    items: list[OrderItemInputDTO] = Field(min_length=1, max_length=ORDER_MAX_ITEMS)


class OrderItemResponseDTO(BaseDTO):
    """Output for a single item in a order."""

    name: str
    quantity: int
    unit_price: float


class PricingSummaryDTO(BaseDTO):
    """Breakdown of the order cost."""

    subtotal: float
    booking_fee: float
    total: float


class OrderRestaurantDTO(BaseDTO):
    """Name of the restaurant added in the order."""

    name: str


class OrderResponseDTO(BaseDTO):
    """Output shape for a placed order."""

    id: str = Field(alias="_id")
    customer_id: str
    status: str = OrderStatus.PENDING
    restaurant: OrderRestaurantDTO
    currency: CurrencyDTO
    pricing_summary: PricingSummaryDTO
    items: list[OrderItemResponseDTO]
