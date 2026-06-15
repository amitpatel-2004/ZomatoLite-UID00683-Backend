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


def get_mock_service_result() -> dict:
    """Return a fresh copy of a successful auth service execution return value."""
    return {
        "customToken": "fake-custom-token",
        "user": {
            "_id": "uid-123",
            "email": "test@example.com",
            "displayName": "Test User",
            "role": "customer",
        },
    }
