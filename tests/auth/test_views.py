import unittest
import unittest.mock as mock
from http import HTTPStatus

from app import create_app
from app.auth.constants import (
    RESPONSE_MSG_INVALID_CREDENTIALS,
    RESPONSE_MSG_LOGIN_SUCCESS,
    RESPONSE_MSG_REGISTER_SUCCESS,
    RESPONSE_MSG_REGISTRATION_FAILED,
)
from app.auth.exceptions import EmailAlreadyExistsError, InvalidCredentialsError
from app.constants import RESPONSE_MSG_INTERNAL_ERROR, RESPONSE_MSG_MISSING_FIELDS
from tests.auth.test_data import (
    get_mock_auth_response,
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

    @mock.patch("app.auth.views.auth_service.register_user")
    def test_successful_registration_returns_201(self, mock_register):
        """Valid payload must return 201 with the token and user data."""
        mock_register.return_value = get_mock_auth_response()
        status, body = self._post(get_valid_register_payload())

        self.assertEqual(status, HTTPStatus.CREATED)
        self.assertEqual(body, {"message": RESPONSE_MSG_REGISTER_SUCCESS, "data": get_mock_auth_response().model_dump(by_alias=True)})

    @mock.patch("app.auth.views.auth_service.register_user")
    def test_owner_role_is_accepted(self, mock_register):
        """The 'owner' role value must be treated as valid and return 201."""
        mock_register.return_value = get_mock_auth_response()
        payload = get_valid_register_payload()
        payload["role"] = "owner"

        status, _ = self._post(payload)
        self.assertEqual(status, HTTPStatus.CREATED)

    @mock.patch("app.auth.views.auth_service.register_user")
    def test_missing_required_field_returns_400(self, _mock):
        """Each required field, when omitted, must return 400."""
        required_fields = ["email", "password", "displayName", "role"]
        for field in required_fields:
            with self.subTest(missing_field=field):
                payload = get_valid_register_payload()
                payload.pop(field)
                status, body = self._post(payload)

                self.assertEqual(status, HTTPStatus.BAD_REQUEST)
                self.assertEqual(body["message"], RESPONSE_MSG_MISSING_FIELDS)

    @mock.patch("app.auth.views.auth_service.register_user")
    def test_invalid_role_returns_400(self, _mock):
        """A role that is not 'customer' or 'owner' must return 400."""
        payload = get_valid_register_payload()
        payload["role"] = "admin"
        status, body = self._post(payload)

        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(body["message"], RESPONSE_MSG_MISSING_FIELDS)
        self.assertIn("role", body["errors"])

    @mock.patch("app.auth.views.auth_service.register_user")
    def test_duplicate_email_returns_409(self, mock_register):
        """When the service raises EmailAlreadyExistsError, view must return 409."""
        mock_register.side_effect = EmailAlreadyExistsError()
        status, body = self._post(get_valid_register_payload())

        self.assertEqual(status, HTTPStatus.CONFLICT)
        self.assertEqual(body["message"], RESPONSE_MSG_REGISTRATION_FAILED)

    @mock.patch("app.auth.views.auth_service.register_user")
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

    @mock.patch("app.auth.views.auth_service.login_user")
    def test_successful_login_returns_200(self, mock_login):
        """Correct credentials must return 200 with token and user data."""
        mock_login.return_value = get_mock_auth_response()
        status, body = self._post(get_valid_login_payload())

        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(body, {"message": RESPONSE_MSG_LOGIN_SUCCESS, "data": get_mock_auth_response().model_dump(by_alias=True)})

    @mock.patch("app.auth.views.auth_service.login_user")
    def test_missing_required_field_returns_400(self, _mock):
        """Each required field, when omitted, must return 400."""
        required_fields = ["email", "password"]
        for field in required_fields:
            with self.subTest(missing_field=field):
                payload = get_valid_login_payload()
                payload.pop(field)
                status, body = self._post(payload)

                self.assertEqual(status, HTTPStatus.BAD_REQUEST)
                self.assertEqual(body["message"], RESPONSE_MSG_MISSING_FIELDS)

    @mock.patch("app.auth.views.auth_service.login_user")
    def test_wrong_credentials_returns_401(self, mock_login):
        """When the service raises InvalidCredentialsError, view must return 401."""
        mock_login.side_effect = InvalidCredentialsError()
        status, body = self._post(get_valid_login_payload())

        self.assertEqual(status, HTTPStatus.UNAUTHORIZED)
        self.assertEqual(body["message"], RESPONSE_MSG_INVALID_CREDENTIALS)

    @mock.patch("app.auth.views.auth_service.login_user")
    def test_service_runtime_error_returns_500(self, mock_login):
        """When the service raises RuntimeError, view must return 500."""
        mock_login.side_effect = RuntimeError("Firebase timeout")
        status, body = self._post(get_valid_login_payload())

        self.assertEqual(status, HTTPStatus.INTERNAL_SERVER_ERROR)
        self.assertEqual(body["message"], RESPONSE_MSG_INTERNAL_ERROR)
