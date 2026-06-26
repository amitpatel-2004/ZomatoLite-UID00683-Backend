from datetime import datetime, timezone


def get_valid_register_payload() -> dict:
    """Return a fresh copy of a valid registration request body."""
    return {
        "email": "test@example.com",
        "password": "secret123",
        "displayName": "Test User",
        "role": "customer",
    }


def get_valid_login_payload() -> dict:
    """Return a fresh copy of a valid login request body."""
    return {
        "email": "test@example.com",
        "password": "secret123",
    }


def get_mock_firestore_user_doc() -> dict:
    """Return a fresh copy of a Firestore user document."""
    return {
        "_id": "uid-123",
        "email": "test@example.com",
        "displayName": "Test User",
        "role": "customer",
        "balance": 1000,
        "currency": {"code": "INR", "symbol": "₹"},
        "_createdAt": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "_updatedAt": datetime(2026, 1, 1, tzinfo=timezone.utc),
    }
