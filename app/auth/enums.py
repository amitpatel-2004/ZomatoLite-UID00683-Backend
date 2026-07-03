from enum import Enum


class AuthSuccessMessage(str, Enum):
    RESPONSE_MSG_REGISTER_SUCCESS = "User registered successfully."
    RESPONSE_MSG_LOGIN_SUCCESS = "Logged in successfully."


class AuthErrorMessage(str, Enum):
    RESPONSE_MSG_INVALID_CREDENTIALS = "Invalid email or password."
    RESPONSE_MSG_REGISTRATION_FAILED = "Unable to complete registration."
    RESPONSE_MSG_TOKEN_MISSING = "Authorization token is missing."
    RESPONSE_MSG_TOKEN_INVALID = "Authorization token is invalid or expired."


class UserRole(str, Enum):
    CUSTOMER = "customer"
    OWNER = "owner"
