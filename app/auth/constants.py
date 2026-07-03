FIREBASE_AUTH_REST_SIGN_IN = (
    "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
)

EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
DISPLAY_NAME_REGEX = r"^[A-Za-z ]+$"
PASSWORD_REGEX = r"^(?=.*[A-Za-z])(?=.*\d).+$"

RESPONSE_MSG_REGISTER_SUCCESS = "User registered successfully."
RESPONSE_MSG_LOGIN_SUCCESS = "Logged in successfully."
RESPONSE_MSG_INVALID_CREDENTIALS = "Invalid email or password."
RESPONSE_MSG_REGISTRATION_FAILED = "Unable to complete registration."
RESPONSE_MSG_TOKEN_MISSING = "Authorization token is missing."
RESPONSE_MSG_TOKEN_INVALID = "Authorization token is invalid or expired."

FIREBASE_ERROR_EMAIL_EXISTS = "EMAIL_EXISTS"
FIREBASE_ERROR_INVALID_PASSWORD = "INVALID_PASSWORD"
FIREBASE_ERROR_EMAIL_NOT_FOUND = "EMAIL_NOT_FOUND"
FIREBASE_ERROR_INVALID_LOGIN = "INVALID_LOGIN_CREDENTIALS"
