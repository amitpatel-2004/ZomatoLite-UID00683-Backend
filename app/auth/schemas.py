from pydantic import BaseModel, EmailStr, Field, field_validator
from app.enums import UserRole


class UserRegisterSchema(BaseModel):
    """Validation schema for incoming registration data."""

    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=6, max_length=128)
    displayName: str = Field(min_length=1, max_length=100)
    role: str

    @field_validator("role")
    @classmethod
    def check_role(cls, value: str) -> str:
        valid_roles = {r.value for r in UserRole}
        if value not in valid_roles:
            raise ValueError(f"Must be one of: {', '.join(sorted(valid_roles))}.")
        return value


class UserLoginSchema(BaseModel):
    """Validation schema for incoming login data."""

    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=1, max_length=128)


class UserProfileResponse(BaseModel):
    """Defines what user profile details are allowed in output."""

    id: str = Field(alias="_id")
    email: EmailStr
    displayName: str
    role: str


class AuthResponseSchema(BaseModel):
    """The standardized output for successful authentication."""

    customToken: str
    user: UserProfileResponse
