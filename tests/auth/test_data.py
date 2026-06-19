from app.auth.dtos import AuthResponseDTO, UserProfileResponseDTO


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
    }


def get_mock_auth_response() -> AuthResponseDTO:
    """Return a mock AuthResponseDTO for view-level service mocking."""
    return AuthResponseDTO(
        custom_token="fake-custom-token",
        user=UserProfileResponseDTO(
            _id="uid-123",
            email="test@example.com",
            display_name="Test User",
            role="customer",
        ),
    )
