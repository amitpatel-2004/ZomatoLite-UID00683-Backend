VALID_REGISTER_PAYLOAD = {
    "email": "test@example.com",
    "password": "secret123",
    "displayName": "Test User",
    "role": "customer",
}

VALID_LOGIN_PAYLOAD = {
    "email": "test@example.com",
    "password": "secret123",
}

MOCK_SERVICE_RESULT = {
    "customToken": "fake-custom-token",
    "user": {
        "_id": "uid-123",
        "email": "test@example.com",
        "displayName": "Test User",
        "role": "customer",
    },
}