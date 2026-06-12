from enum import Enum


class ApiVersionPrefix(Enum):
    """Centralized API routing version prefixes."""

    V1 = "/api/v1"


class UserRole(Enum):
    """Enum for user role types."""

    CUSTOMER = "customer"
    OWNER = "owner"
