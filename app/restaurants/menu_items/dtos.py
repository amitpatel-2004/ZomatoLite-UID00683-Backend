from typing import Annotated

from pydantic import Field, StringConstraints

from app.dtos import BaseDTO
from app.restaurants.constants import (
    MENU_ITEM_DESCRIPTION_MAX_LENGTH,
    MENU_ITEM_MAX_PRICE,
    MENU_ITEM_MAX_QUANTITY,
    MENU_ITEM_NAME_MAX_LENGTH,
)
from app.restaurants.menu_items.enums import MenuItemStatus


class CreateMenuItemPayloadDTO(BaseDTO):
    """Validation DTO for adding a menu item."""

    name: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True, min_length=1, max_length=MENU_ITEM_NAME_MAX_LENGTH
        ),
    ]
    description: Annotated[
        str, StringConstraints(max_length=MENU_ITEM_DESCRIPTION_MAX_LENGTH)
    ] = ""
    price: float = Field(gt=0, le=MENU_ITEM_MAX_PRICE)
    is_veg: bool
    quantity: int | None = Field(default=None, ge=0, le=MENU_ITEM_MAX_QUANTITY)
    image_path: str | None = None


class UpdateMenuItemPayloadDTO(BaseDTO):
    """Validation DTO for updating a menu item."""

    name: (
        Annotated[
            str,
            StringConstraints(
                strip_whitespace=True,
                min_length=1,
                max_length=MENU_ITEM_NAME_MAX_LENGTH,
            ),
        ]
        | None
    ) = None
    description: (
        Annotated[str, StringConstraints(max_length=MENU_ITEM_DESCRIPTION_MAX_LENGTH)]
        | None
    ) = None
    price: float | None = Field(default=None, gt=0, le=MENU_ITEM_MAX_PRICE)
    is_veg: bool | None = None
    quantity: int | None = Field(default=None, ge=0, le=MENU_ITEM_MAX_QUANTITY)
    image_path: str | None = None


class MenuItemResponseDTO(BaseDTO):
    """Output shape for a single menu item."""

    id: str = Field(alias="_id")
    name: str
    description: str = ""
    price: float
    is_veg: bool = False
    image_path: str | None = None
    rating: float = 0.0
    quantity: int | None = None
    status: str = MenuItemStatus.ACTIVE


class UploadUrlResponseDTO(BaseDTO):
    """Output shape for a signed upload URL response."""

    upload_url: str
    image_path: str
