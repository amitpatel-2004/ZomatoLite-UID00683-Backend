from typing import Annotated
from pydantic import ConfigDict, EmailStr, Field, StringConstraints

from app.auth.constants import DISPLAY_NAME_REGEX, EMAIL_REGEX, PASSWORD_REGEX
from app.enums import UserRole
from app.dtos import BaseDTO, CurrencyDTO


class UserLoginPayloadDTO(BaseDTO):
    """Shared base DTO for authentication credentials."""

    email: Annotated[
        EmailStr, StringConstraints(max_length=255, pattern=EMAIL_REGEX)
    ]
    password: str = Field(min_length=6, max_length=128)


class UserRegisterPayloadDTO(UserLoginPayloadDTO):
    """Validation CamelCaseBaseDTO for incoming registration data."""

    model_config = ConfigDict(regex_engine="python-re")

    password: Annotated[
        str, StringConstraints(min_length=6, max_length=128, pattern=PASSWORD_REGEX)
    ]
    display_name: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True, min_length=1, max_length=100, pattern=DISPLAY_NAME_REGEX
        ),
    ]
    role: UserRole


class UserProfileResponseDTO(BaseDTO):
    """Defines what user profile details are allowed in output."""

    id: str = Field(alias="_id")
    email: EmailStr
    display_name: str
    role: str
    balance: float
    currency: CurrencyDTO


class AuthResponseDTO(BaseDTO):
    """The standardized output for successful authentication."""

    custom_token: str
    user: UserProfileResponseDTO
