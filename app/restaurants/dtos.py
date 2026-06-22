from typing import Annotated, Optional

from pydantic import Field, StringConstraints

from app.dtos import BaseDTO
from app.enums import CuisineType, MenuItemStatus, RestaurantStatus


class CreateRestaurantPayloadDTO(BaseDTO):
    """Validation DTO for creating a new restaurant."""

    name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
    ]
    cuisine_types: list[CuisineType] = Field(min_length=1)
    opening_time: Annotated[str, StringConstraints(pattern=r"^\d{2}:\d{2}$")]
    closing_time: Annotated[str, StringConstraints(pattern=r"^\d{2}:\d{2}$")]


class UpdateRestaurantPayloadDTO(BaseDTO):
    """Validation DTO for updating an existing restaurant."""

    name: Optional[
        Annotated[
            str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
        ]
    ] = None
    cuisine_types: Optional[list[CuisineType]] = None
    opening_time: Optional[
        Annotated[str, StringConstraints(pattern=r"^\d{2}:\d{2}$")]
    ] = None
    closing_time: Optional[
        Annotated[str, StringConstraints(pattern=r"^\d{2}:\d{2}$")]
    ] = None
    status: Optional[RestaurantStatus] = None


class CreateMenuItemPayloadDTO(BaseDTO):
    """Validation DTO for adding a menu item."""

    name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
    ]
    description: str = ""
    price: float = Field(gt=0)
    is_veg: bool
    status: MenuItemStatus = MenuItemStatus.AVAILABLE
    image_path: Optional[str] = None


class UpdateMenuItemPayloadDTO(BaseDTO):
    """Validation DTO for updating a menu item."""

    name: Optional[
        Annotated[
            str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
        ]
    ] = None
    description: Optional[str] = None
    price: Optional[float] = Field(default=None, gt=0)
    is_veg: Optional[bool] = None
    status: Optional[MenuItemStatus] = None
    image_path: Optional[str] = None


class RestaurantResponseDTO(BaseDTO):
    """Output shape for a single restaurant."""

    id: str = Field(alias="_id")
    owner_id: str
    name: str
    cuisine_types: list[str]
    rating: float
    status: str
    opening_time: str
    closing_time: str


class MenuItemResponseDTO(BaseDTO):
    """Output shape for a single menu item."""

    id: str = Field(alias="_id")
    name: str
    description: str
    price: float
    is_veg: bool
    image_path: Optional[str]
    rating: float
    status: str


class UploadUrlResponseDTO(BaseDTO):
    """Output shape for a signed upload URL response."""

    upload_url: str
    image_path: str
