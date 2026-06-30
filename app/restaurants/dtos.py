from typing import Annotated

from pydantic import Field, StringConstraints

from app.dtos import BaseDTO
from app.enums import CuisineType, RestaurantStatus
from app.restaurants.constants import TIME_FORMAT_REGEX


class CreateRestaurantPayloadDTO(BaseDTO):
    """Validation DTO for creating a new restaurant."""

    name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
    ]
    description: Annotated[str, StringConstraints(max_length=500)] = ""
    cuisine_types: list[CuisineType] = Field(min_length=1)
    opening_time: Annotated[str, StringConstraints(pattern=TIME_FORMAT_REGEX)]
    closing_time: Annotated[str, StringConstraints(pattern=TIME_FORMAT_REGEX)]


class UpdateRestaurantPayloadDTO(BaseDTO):
    """Validation DTO for updating an existing restaurant."""

    name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
    ] | None = None
    description: Annotated[str, StringConstraints(max_length=500)] | None = None
    cuisine_types: list[CuisineType] | None = None
    opening_time: Annotated[str, StringConstraints(pattern=TIME_FORMAT_REGEX)] | None = None
    closing_time: Annotated[str, StringConstraints(pattern=TIME_FORMAT_REGEX)] | None = None
    status: RestaurantStatus | None = None


class RestaurantResponseDTO(BaseDTO):
    """Output shape for a single restaurant."""

    id: str = Field(alias="_id")
    owner_id: str
    name: str
    description: str = ""
    cuisine_types: list[str] = []
    rating: float = 0.0
    status: str = RestaurantStatus.ACTIVE
    opening_time: str
    closing_time: str
