import unittest
import unittest.mock as mock
from http import HTTPStatus

from app import create_app
from app.auth.constants import (
    FIREBASE_ERROR_EMAIL_EXISTS,
    RESPONSE_MSG_EMAIL_EXISTS,
    RESPONSE_MSG_INVALID_CREDENTIALS,
    RESPONSE_MSG_INVALID_ROLE,
    RESPONSE_MSG_LOGIN_SUCCESS,
    RESPONSE_MSG_REGISTER_SUCCESS,
)
from app.constants import RESPONSE_MSG_INTERNAL_ERROR, RESPONSE_MSG_MISSING_FIELDS
from tests.auth.fixtures import (
    get_mock_service_result,
    get_valid_login_payload,
    get_valid_register_payload,
)


class TestRegisterView(unittest.TestCase):
    """
    Tests for POST /api/v1/auth/register.
    """

    def setUp(self):
        """Create a fresh Flask test client before each test."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.url = "/api/v1/auth/register"

    def _post(self, payload):
        """Send a POST request with JSON body and return (status_code, body)."""
        response = self.client.post(self.url, json=payload)
        return response.status_code, response.get_json()

    @mock.patch("app.auth.views.register_user")
    def test_successful_registration_returns_201(self, mock_register):
        """Valid payload must return 201 with the token and user data."""
        mock_register.return_value = get_mock_service_result()
        status, body = self._post(get_valid_register_payload())

        self.assertEqual(status, HTTPStatus.CREATED)
        self.assertEqual(body["message"], RESPONSE_MSG_REGISTER_SUCCESS)
        self.assertEqual(body["data"]["customToken"], "fake-custom-token")
        self.assertEqual(body["data"]["user"]["email"], "test@example.com")

    @mock.patch("app.auth.views.register_user")
    def test_owner_role_is_accepted(self, mock_register):
        """The 'owner' role value must be treated as valid and return 201."""
        mock_register.return_value = get_mock_service_result()
        payload = get_valid_register_payload()
        payload["role"] = "owner"

        status, _ = self._post(payload)
        self.assertEqual(status, HTTPStatus.CREATED)

    @mock.patch("app.auth.views.register_user")
    def test_service_called_with_correct_arguments(self, mock_register):
        """The view must forward exactly the right fields to the service."""
        mock_register.return_value = get_mock_service_result()
        self._post(get_valid_register_payload())

        mock_register.assert_called_once_with(
            email="test@example.com",
            password="secret123",
            display_name="Test User",
            role="customer",
        )

    @mock.patch("app.auth.views.register_user")
    def test_missing_email_returns_400(self, _mock):
        """Omitting email must return 400."""
        payload = get_valid_register_payload()
        payload.pop("email")
        status, body = self._post(payload)

        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(body["message"], RESPONSE_MSG_MISSING_FIELDS)

    @mock.patch("app.auth.views.register_user")
    def test_missing_password_returns_400(self, _mock):
        """Omitting password must return 400."""
        payload = get_valid_register_payload()
        payload.pop("password")
        status, body = self._post(payload)

        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(body["message"], RESPONSE_MSG_MISSING_FIELDS)

    @mock.patch("app.auth.views.register_user")
    def test_missing_display_name_returns_400(self, _mock):
        """Omitting displayName must return 400."""
        payload = get_valid_register_payload()
        payload.pop("displayName")
        status, body = self._post(payload)

        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(body["message"], RESPONSE_MSG_MISSING_FIELDS)

    @mock.patch("app.auth.views.register_user")
    def test_missing_role_returns_400(self, _mock):
        """Omitting role must return 400."""
        payload = get_valid_register_payload()
        payload.pop("role")
        status, body = self._post(payload)

        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(body["message"], RESPONSE_MSG_MISSING_FIELDS)

    @mock.patch("app.auth.views.register_user")
    def test_invalid_role_returns_400(self, _mock):
        """A role that is not 'customer' or 'owner' must return 400."""
        payload = get_valid_register_payload()
        payload["role"] = "admin"
        status, body = self._post(payload)

        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(body["message"], RESPONSE_MSG_INVALID_ROLE)
        self.assertIn("role", body["errors"])

    @mock.patch("app.auth.views.register_user")
    def test_duplicate_email_returns_409(self, mock_register):
        """When the service raises ValueError(EMAIL_EXISTS), view must return 409."""
        mock_register.side_effect = ValueError(FIREBASE_ERROR_EMAIL_EXISTS)
        status, body = self._post(get_valid_register_payload())

        self.assertEqual(status, HTTPStatus.CONFLICT)
        self.assertEqual(body["message"], RESPONSE_MSG_EMAIL_EXISTS)

    @mock.patch("app.auth.views.register_user")
    def test_service_runtime_error_returns_500(self, mock_register):
        """When the service raises RuntimeError, view must return 500."""
        mock_register.side_effect = RuntimeError("unexpected")
        status, body = self._post(get_valid_register_payload())

        self.assertEqual(status, HTTPStatus.INTERNAL_SERVER_ERROR)
        self.assertEqual(body["message"], RESPONSE_MSG_INTERNAL_ERROR)


class TestLoginView(unittest.TestCase):
    """Tests for POST /api/v1/auth/login."""

    def setUp(self):
        """Create a fresh Flask test client before each test."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.url = "/api/v1/auth/login"

    def _post(self, payload):
        """Send a POST request with JSON body and return (status_code, body)."""
        response = self.client.post(self.url, json=payload)
        return response.status_code, response.get_json()

    @mock.patch("app.auth.views.login_user")
    def test_successful_login_returns_200(self, mock_login):
        """Correct credentials must return 200 with token and user data."""
        mock_login.return_value = get_mock_service_result()
        status, body = self._post(get_valid_login_payload())

        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(body["message"], RESPONSE_MSG_LOGIN_SUCCESS)
        self.assertEqual(body["data"]["customToken"], "fake-custom-token")

    @mock.patch("app.auth.views.login_user")
    def test_service_called_with_correct_arguments(self, mock_login):
        """The view must forward email and password to the service unchanged."""
        mock_login.return_value = get_mock_service_result()
        self._post(get_valid_login_payload())

        mock_login.assert_called_once_with(
            email="test@example.com",
            password="secret123",
        )

    @mock.patch("app.auth.views.login_user")
    def test_missing_email_returns_400(self, _mock):
        """Omitting email must return 400."""
        status, body = self._post({"password": "secret123"})

        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(body["message"], RESPONSE_MSG_MISSING_FIELDS)

    @mock.patch("app.auth.views.login_user")
    def test_missing_password_returns_400(self, _mock):
        """Omitting password must return 400."""
        status, body = self._post({"email": "test@example.com"})

        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(body["message"], RESPONSE_MSG_MISSING_FIELDS)

    @mock.patch("app.auth.views.login_user")
    def test_wrong_credentials_returns_401(self, mock_login):
        """When the service raises ValueError, view must return 401."""
        mock_login.side_effect = ValueError("INVALID_CREDENTIALS")
        status, body = self._post(get_valid_login_payload())

        self.assertEqual(status, HTTPStatus.UNAUTHORIZED)
        self.assertEqual(body["message"], RESPONSE_MSG_INVALID_CREDENTIALS)

    @mock.patch("app.auth.views.login_user")
    def test_service_runtime_error_returns_500(self, mock_login):
        """When the service raises RuntimeError, view must return 500."""
        mock_login.side_effect = RuntimeError("Firebase timeout")
        status, body = self._post(get_valid_login_payload())

        self.assertEqual(status, HTTPStatus.INTERNAL_SERVER_ERROR)
        self.assertEqual(body["message"], RESPONSE_MSG_INTERNAL_ERROR)
