from typing import Annotated
from pydantic import EmailStr, Field, StringConstraints

from app.enums import UserRole
from app.dtos import CamelCaseBaseDTO


class UserLoginPayloadDTO(CamelCaseBaseDTO):
    """Shared base DTO for authentication credentials."""

    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=6, max_length=128)


class UserRegisterPayloadDTO(UserLoginPayloadDTO):
    """Validation CamelCaseBaseDTO for incoming registration data."""

    display_name: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True, min_length=1, max_length=100, pattern=r"^[\w '.,-]+$"
        ),
    ]
    role: UserRole


class UserProfileResponseDTO(CamelCaseBaseDTO):
    """Defines what user profile details are allowed in output."""

    id: str = Field(alias="_id")
    email: EmailStr
    display_name: str
    role: str


class AuthResponseDTO(CamelCaseBaseDTO):
    """The standardized output for successful authentication."""

    custom_token: str
    user: UserProfileResponseDTO
