from typing import Annotated

from pydantic import Field, StringConstraints

from app.dtos import BaseDTO, CurrencyDTO
from app.enums import OrderStatus


class OrderItemInputDTO(BaseDTO):
    """A single item entry in the order request."""

    item_id: Annotated[str, StringConstraints(min_length=1)]
    quantity: int = Field(gt=0, le=50)
    unit_price: float = Field(gt=0, le=9999.99)


class CreateOrderPayloadDTO(BaseDTO):
    """Validation DTO for placing an order."""

    items: list[OrderItemInputDTO] = Field(min_length=1, max_length=20)


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
