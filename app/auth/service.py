import os
from datetime import datetime, timezone
from typing import Any

import requests
from firebase_admin import auth

from app.auth.constants import (
    FIREBASE_AUTH_REST_SIGN_IN,
    FIREBASE_AUTH_REST_SIGN_UP,
    FIREBASE_ERROR_EMAIL_EXISTS,
    FIREBASE_ERROR_EMAIL_NOT_FOUND,
    FIREBASE_ERROR_INVALID_LOGIN,
    FIREBASE_ERROR_INVALID_PASSWORD,
)
from app.constants import (
    FIRESTORE_COLLECTION_USERS,
    TOKEN_CLAIM_ROLE,
    FIREBASE_TIMEOUT_SECONDS,
)
from app.settings import FS_CLIENT, FIREBASE_AUTH_EMULATOR_HOST


def _get_auth_endpoint(action: str) -> str:
    """Return the correct Firebase Auth REST endpoint for the given action.

    Switches between emulator and production URLs based on the
    FIREBASE_AUTH_EMULATOR_HOST environment variable.

    Args:
        action: Either "sign_in" or "sign_up".

    Returns:
        The full URL string for the requested auth action.
    """

    if FIREBASE_AUTH_EMULATOR_HOST:
        base_url = f"http://{FIREBASE_AUTH_EMULATOR_HOST}/identitytoolkit.googleapis.com/v1/accounts"
        return (
            f"{base_url}:signUp"
            if action == "sign_up"
            else f"{base_url}:signInWithPassword"
        )

    return (
        FIREBASE_AUTH_REST_SIGN_UP
        if action == "sign_up"
        else FIREBASE_AUTH_REST_SIGN_IN
    )


def _get_api_key() -> str:
    """Return the Firebase Web API key from environment.

    Returns:
        The API key string.
    """
    return os.getenv("FIREBASE_WEB_API_KEY", "emulator-fake-api-key")


def register_user(
    email: str,
    password: str,
    display_name: str,
    role: str,
) -> dict[str, Any]:
    """Create a new user in Firebase Auth and save their profile to Firestore.

    Args:
        email: The user's email address.
        password: The user's password.
        display_name: The user's name to display.
        role: Either "customer" or "owner".

    Returns:
        A dict with "customToken" and "user" fields for the client.

    Raises:
        ValueError: If the email is already registered ("EMAIL_EXISTS").
        RuntimeError: If Firebase returns any other unexpected error.
    """
    response = requests.post(
        _get_auth_endpoint("sign_up"),
        params={"key": _get_api_key()},
        json={
            "email": email,
            "password": password,
            "displayName": display_name,
            "returnSecureToken": True,
        },
        timeout=FIREBASE_TIMEOUT_SECONDS,
    )
    response_data = response.json()

    if not response.ok:
        firebase_error = response_data.get("error", {}).get("message", "")
        if firebase_error == FIREBASE_ERROR_EMAIL_EXISTS:
            raise ValueError(FIREBASE_ERROR_EMAIL_EXISTS)
        raise RuntimeError(f"Firebase sign-up error: {firebase_error}")

    id_token: str = response_data["idToken"]
    decoded = auth.verify_id_token(id_token)
    uid: str = decoded["uid"]

    FS_CLIENT.collection(FIRESTORE_COLLECTION_USERS).document(uid).set(
        {
            "_id": uid,
            "email": email,
            "displayName": display_name,
            "role": role,
            "_createdAt": datetime.now(timezone.utc),
        }
    )

    custom_token: bytes = auth.create_custom_token(
        uid,
        developer_claims={TOKEN_CLAIM_ROLE: role},
    )

    return {
        "customToken": custom_token.decode("utf-8"),
        "user": {
            "_id": uid,
            "email": email,
            "displayName": display_name,
            "role": role,
        },
    }


def login_user(email: str, password: str) -> dict[str, Any]:
    """Sign in an existing user and return a custom token with their role claim.

    Args:
        email: The user's registered email address.
        password: The user's password.

    Returns:
        A dict with "customToken" and "user" fields for the client.

    Raises:
        ValueError: If the credentials are wrong ("INVALID_CREDENTIALS").
        RuntimeError: If Firebase returns any other unexpected error.
    """
    response = requests.post(
        _get_auth_endpoint("sign_in"),
        params={"key": _get_api_key()},
        json={
            "email": email,
            "password": password,
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
            raise ValueError("INVALID_CREDENTIALS")
        raise RuntimeError(f"Firebase sign-in error: {firebase_error}")

    id_token: str = response_data["idToken"]
    decoded = auth.verify_id_token(id_token)
    uid: str = decoded["uid"]

    user_snapshot = FS_CLIENT.collection(FIRESTORE_COLLECTION_USERS).document(uid).get()
    user_data = user_snapshot.to_dict() or {}
    role: str = user_data.get("role", "customer")
    display_name: str = user_data.get("displayName", "")

    custom_token: bytes = auth.create_custom_token(
        uid,
        developer_claims={TOKEN_CLAIM_ROLE: role},
    )

    return {
        "customToken": custom_token.decode("utf-8"),
        "user": {
            "_id": uid,
            "email": email,
            "displayName": display_name,
            "role": role,
        },
    }
