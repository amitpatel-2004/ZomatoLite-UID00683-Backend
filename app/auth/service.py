from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from firebase_admin import auth
from firebase_admin.exceptions import FirebaseError

from app.auth.constants import (
    FIREBASE_AUTH_REST_SIGN_IN,
    FIREBASE_ERROR_EMAIL_NOT_FOUND,
    FIREBASE_ERROR_INVALID_LOGIN,
    FIREBASE_ERROR_INVALID_PASSWORD,
)
from app.auth.dtos import (
    AuthResponseDTO,
    UserLoginPayloadDTO,
    UserProfileResponseDTO,
    UserRegisterPayloadDTO,
)
from app.dtos import CurrencyDTO
from app.auth.exceptions import EmailAlreadyExistsError, InvalidCredentialsError
from app.constants import (
    TOKEN_CLAIM_ROLE,
    DEFAULT_BALANCE,
    DEFAULT_CURRENCY,
    FIREBASE_TIMEOUT_SECONDS,
)
from app.enums import FirestoreCollections
from app.settings import FS_CLIENT, FIREBASE_AUTH_EMULATOR_HOST, FIREBASE_WEB_API_KEY


class AuthService:
    """Handles all authentication operations against Firebase and Firestore."""

    def _get_login_endpoint(self) -> str:
        """Return the correct Firebase Auth REST endpoint.

        Switches between emulator and production URLs based on the
        FIREBASE_AUTH_EMULATOR_HOST environment variable.

        Returns:
            The full URL string for the sign-in endpoint.
        """
        if FIREBASE_AUTH_EMULATOR_HOST:
            base_url = f"http://{FIREBASE_AUTH_EMULATOR_HOST}/identitytoolkit.googleapis.com/v1/accounts"
            return f"{base_url}:signInWithPassword"
        return FIREBASE_AUTH_REST_SIGN_IN

    def register_user(self, payload: UserRegisterPayloadDTO) -> AuthResponseDTO:
        """Create a new user in Firebase Auth and save their profile to Firestore.

        Args:
            payload: Validated registration data from the request.

        Returns:
            An AuthResponseDTO with "customToken" and "user" fields for the client.

        Raises:
            EmailAlreadyExistsError: If the email is already registered.
            RuntimeError: If Firebase returns any other unexpected error.
        """
        try:
            user_record = auth.create_user(
                email=payload.email,
                password=payload.password,
                display_name=payload.display_name,
            )
            uid = user_record.uid
        except auth.EmailAlreadyExistsError:
            raise EmailAlreadyExistsError()
        except FirebaseError as e:
            raise RuntimeError(f"Firebase sign-up error: {str(e)}")

        now = datetime.now(ZoneInfo("UTC"))
        FS_CLIENT.document(f"{FirestoreCollections.USERS}/{uid}").set(
            {
                "_id": uid,
                "email": payload.email,
                "displayName": payload.display_name,
                "role": payload.role,
                "balance": DEFAULT_BALANCE,
                "currency": DEFAULT_CURRENCY,
                "_createdAt": now,
                "_updatedAt": now,
            }
        )

        custom_token: bytes = auth.create_custom_token(
            uid,
            developer_claims={TOKEN_CLAIM_ROLE: payload.role},
        )

        return AuthResponseDTO(
            custom_token=custom_token.decode("utf-8"),
            user=UserProfileResponseDTO(
                _id=uid,
                email=payload.email,
                display_name=payload.display_name,
                role=payload.role,
                balance=DEFAULT_BALANCE,
                currency=CurrencyDTO(**DEFAULT_CURRENCY),
            ),
        )

    def login_user(self, payload: UserLoginPayloadDTO) -> AuthResponseDTO:
        """Sign in an existing user and return a custom token with their role claim.

        Args:
            payload: Validated login data from the request.

        Returns:
            An AuthResponseDTO with "customToken" and "user" fields for the client.

        Raises:
            InvalidCredentialsError: If the credentials are wrong.
            RuntimeError: If Firebase returns any other unexpected error.
        """
        response = requests.post(
            self._get_login_endpoint(),
            params={"key": FIREBASE_WEB_API_KEY},
            json={
                "email": payload.email,
                "password": payload.password,
                "returnSecureToken": True,
            },
            timeout=FIREBASE_TIMEOUT_SECONDS,
        )
        response_data = response.json()

        if not response.ok:
            firebase_error = response_data.get("error", {}).get("message", "")
            invalid_cred_errors = (
                FIREBASE_ERROR_INVALID_PASSWORD,
                FIREBASE_ERROR_EMAIL_NOT_FOUND,
                FIREBASE_ERROR_INVALID_LOGIN,
            )
            if firebase_error in invalid_cred_errors:
                raise InvalidCredentialsError()
            raise RuntimeError(f"Firebase sign-in error: {firebase_error}")

        uid: str = response_data["localId"]

        user_snapshot = FS_CLIENT.document(f"{FirestoreCollections.USERS}/{uid}").get()
        user_data = user_snapshot.to_dict() or {}
        role: str = user_data.get("role", "customer")
        display_name: str = user_data.get("displayName", "")
        balance: float = user_data.get("balance", DEFAULT_BALANCE)
        currency: CurrencyDTO = CurrencyDTO(
            **user_data.get("currency", DEFAULT_CURRENCY)
        )

        custom_token: bytes = auth.create_custom_token(
            uid,
            developer_claims={TOKEN_CLAIM_ROLE: role},
        )

        return AuthResponseDTO(
            custom_token=custom_token.decode("utf-8"),
            user=UserProfileResponseDTO(
                _id=uid,
                email=payload.email,
                display_name=display_name,
                role=role,
                balance=balance,
                currency=currency,
            ),
        )
