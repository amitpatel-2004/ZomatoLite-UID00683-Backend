import unittest
import unittest.mock as mock
from datetime import datetime
from http import HTTPStatus

from app import create_app
from app.auth.constants import (
    RESPONSE_MSG_INVALID_CREDENTIALS,
    RESPONSE_MSG_LOGIN_SUCCESS,
    RESPONSE_MSG_REGISTER_SUCCESS,
    RESPONSE_MSG_REGISTRATION_FAILED,
)
from app.constants import RESPONSE_MSG_INTERNAL_ERROR, RESPONSE_MSG_MISSING_FIELDS
from tests.auth.test_data import (
    get_mock_firestore_user_doc,
    get_valid_login_payload,
    get_valid_register_payload,
)

FAKE_UID = "uid-123"
FAKE_CUSTOM_TOKEN = b"fake-custom-token-bytes"

_FakeEmailAlreadyExistsError = type("EmailAlreadyExistsError", (Exception,), {})
_FakeFirebaseError = type("FirebaseError", (Exception,), {})


def _make_http_response(data: dict, ok: bool = True):
    response = mock.MagicMock()
    response.ok = ok
    response.json.return_value = data
    return response


def _make_firestore_snapshot(data: dict | None):
    snapshot = mock.MagicMock()
    snapshot.to_dict.return_value = data
    return snapshot


class TestRegisterView(unittest.TestCase):
    """
    Integration tests for POST /api/v1/auth/register.
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

    @mock.patch("app.auth.service.auth.create_custom_token")
    @mock.patch("app.auth.service.auth.create_user")
    def test_successful_registration_returns_201(self, mock_create_user, mock_token):
        """Valid payload must return 201 with the token and user data."""
        mock_create_user.return_value = mock.MagicMock(uid=FAKE_UID)
        mock_token.return_value = FAKE_CUSTOM_TOKEN

        status, body = self._post(get_valid_register_payload())

        self.assertEqual(status, HTTPStatus.CREATED)
        self.assertEqual(
            body,
            {
                "message": RESPONSE_MSG_REGISTER_SUCCESS,
                "data": {
                    "customToken": FAKE_CUSTOM_TOKEN.decode("utf-8"),
                    "user": {
                        "_id": FAKE_UID,
                        "email": "test@example.com",
                        "displayName": "Test User",
                        "role": "customer",
                    },
                },
            },
        )

    @mock.patch("app.auth.service.auth.create_custom_token")
    @mock.patch("app.auth.service.auth.create_user")
    def test_owner_role_is_accepted(self, mock_create_user, mock_token):
        """The 'owner' role value must be treated as valid and return 201."""
        mock_create_user.return_value = mock.MagicMock(uid=FAKE_UID)
        mock_token.return_value = FAKE_CUSTOM_TOKEN
        payload = get_valid_register_payload()
        payload["role"] = "owner"

        status, _ = self._post(payload)
        self.assertEqual(status, HTTPStatus.CREATED)

    def test_missing_required_field_returns_400(self):
        """Each required field, when omitted, must return 400."""
        required_fields = ["email", "password", "displayName", "role"]
        for field in required_fields:
            with self.subTest(missing_field=field):
                payload = get_valid_register_payload()
                payload.pop(field)
                status, body = self._post(payload)

                self.assertEqual(status, HTTPStatus.BAD_REQUEST)
                self.assertEqual(body["message"], RESPONSE_MSG_MISSING_FIELDS)

    def test_invalid_role_returns_400(self):
        """A role that is not 'customer' or 'owner' must return 400."""
        payload = get_valid_register_payload()
        payload["role"] = "admin"
        status, body = self._post(payload)

        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertEqual(body["message"], RESPONSE_MSG_MISSING_FIELDS)
        self.assertIn("role", body["errors"])

    @mock.patch(
        "app.auth.service.auth.EmailAlreadyExistsError", _FakeEmailAlreadyExistsError
    )
    @mock.patch("app.auth.service.auth.create_user")
    def test_duplicate_email_returns_409(self, mock_create_user):
        """Firebase EmailAlreadyExistsError must cause a 409 response."""
        mock_create_user.side_effect = _FakeEmailAlreadyExistsError("email taken")

        status, body = self._post(get_valid_register_payload())

        self.assertEqual(status, HTTPStatus.CONFLICT)
        self.assertEqual(body["message"], RESPONSE_MSG_REGISTRATION_FAILED)

    @mock.patch("app.auth.service.FirebaseError", _FakeFirebaseError)
    @mock.patch(
        "app.auth.service.auth.EmailAlreadyExistsError", _FakeEmailAlreadyExistsError
    )
    @mock.patch("app.auth.service.auth.create_user")
    def test_firebase_error_returns_500(self, mock_create_user):
        """Unexpected Firebase errors during registration must return 500."""
        mock_create_user.side_effect = _FakeFirebaseError("op not allowed")

        status, body = self._post(get_valid_register_payload())

        self.assertEqual(status, HTTPStatus.INTERNAL_SERVER_ERROR)
        self.assertEqual(body["message"], RESPONSE_MSG_INTERNAL_ERROR)

    @mock.patch("app.auth.service.auth.create_custom_token")
    @mock.patch("app.auth.service.FS_CLIENT")
    @mock.patch("app.auth.service.auth.create_user")
    def test_firestore_document_written_with_correct_fields(
        self, mock_create_user, mock_fs, mock_token
    ):
        """The Firestore user document must contain all required fields after registration."""
        mock_create_user.return_value = mock.MagicMock(uid=FAKE_UID)
        mock_token.return_value = FAKE_CUSTOM_TOKEN

        self._post(get_valid_register_payload())

        mock_doc = mock_fs.document.return_value
        mock_doc.set.assert_called_once()
        written = mock_doc.set.call_args[0][0]
        self.assertEqual(written["_id"], FAKE_UID)
        self.assertEqual(written["email"], "test@example.com")
        self.assertEqual(written["role"], "customer")
        self.assertIsInstance(written["_createdAt"], datetime)

    @mock.patch("app.auth.service.auth.create_custom_token")
    @mock.patch("app.auth.service.auth.create_user")
    def test_custom_token_minted_with_role_claim(self, mock_create_user, mock_token):
        """create_custom_token must be called with the correct uid and role claim."""
        mock_create_user.return_value = mock.MagicMock(uid=FAKE_UID)
        mock_token.return_value = FAKE_CUSTOM_TOKEN
        payload = get_valid_register_payload()
        payload["role"] = "owner"

        self._post(payload)

        mock_token.assert_called_once_with(FAKE_UID, developer_claims={"role": "owner"})


class TestLoginView(unittest.TestCase):
    """
    Integration tests for POST /api/v1/auth/login.
    """

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

    @mock.patch("app.auth.service.auth.create_custom_token")
    @mock.patch("app.auth.service.FS_CLIENT")
    @mock.patch("app.auth.service.requests.post")
    def test_successful_login_returns_200(self, mock_post, mock_fs, mock_token):
        """Correct credentials must return 200 with token and user data."""
        mock_post.return_value = _make_http_response(
            {"localId": FAKE_UID, "email": "test@example.com"}
        )
        mock_token.return_value = FAKE_CUSTOM_TOKEN
        mock_fs.document.return_value.get.return_value = _make_firestore_snapshot(
            get_mock_firestore_user_doc()
        )

        status, body = self._post(get_valid_login_payload())

        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(
            body,
            {
                "message": RESPONSE_MSG_LOGIN_SUCCESS,
                "data": {
                    "customToken": FAKE_CUSTOM_TOKEN.decode("utf-8"),
                    "user": {
                        "_id": FAKE_UID,
                        "email": "test@example.com",
                        "displayName": "Test User",
                        "role": "customer",
                    },
                },
            },
        )

    def test_missing_required_field_returns_400(self):
        """Each required field, when omitted, must return 400."""
        required_fields = ["email", "password"]
        for field in required_fields:
            with self.subTest(missing_field=field):
                payload = get_valid_login_payload()
                payload.pop(field)
                status, body = self._post(payload)

                self.assertEqual(status, HTTPStatus.BAD_REQUEST)
                self.assertEqual(body["message"], RESPONSE_MSG_MISSING_FIELDS)

    @mock.patch("app.auth.service.requests.post")
    def test_wrong_credentials_returns_401(self, mock_post):
        """Firebase INVALID_PASSWORD error must return 401."""
        mock_post.return_value = _make_http_response(
            {"error": {"message": "INVALID_PASSWORD"}}, ok=False
        )

        status, body = self._post(get_valid_login_payload())

        self.assertEqual(status, HTTPStatus.UNAUTHORIZED)
        self.assertEqual(body["message"], RESPONSE_MSG_INVALID_CREDENTIALS)

    @mock.patch("app.auth.service.requests.post")
    def test_email_not_found_returns_401(self, mock_post):
        """Firebase EMAIL_NOT_FOUND error must also return 401."""
        mock_post.return_value = _make_http_response(
            {"error": {"message": "EMAIL_NOT_FOUND"}}, ok=False
        )

        status, body = self._post(get_valid_login_payload())

        self.assertEqual(status, HTTPStatus.UNAUTHORIZED)
        self.assertEqual(body["message"], RESPONSE_MSG_INVALID_CREDENTIALS)

    @mock.patch("app.auth.service.requests.post")
    def test_firebase_error_returns_500(self, mock_post):
        """Unexpected Firebase errors during login must return 500."""
        mock_post.return_value = _make_http_response(
            {"error": {"message": "TOO_MANY_ATTEMPTS_TRY_LATER"}}, ok=False
        )

        status, body = self._post(get_valid_login_payload())

        self.assertEqual(status, HTTPStatus.INTERNAL_SERVER_ERROR)
        self.assertEqual(body["message"], RESPONSE_MSG_INTERNAL_ERROR)

    @mock.patch("app.auth.service.auth.create_custom_token")
    @mock.patch("app.auth.service.FS_CLIENT")
    @mock.patch("app.auth.service.requests.post")
    def test_role_is_read_from_firestore(self, mock_post, mock_fs, mock_token):
        """The role in the returned token must come from Firestore, not the request."""
        mock_post.return_value = _make_http_response(
            {"localId": FAKE_UID, "email": "test@example.com"}
        )
        mock_token.return_value = FAKE_CUSTOM_TOKEN
        user_doc = get_mock_firestore_user_doc()
        user_doc["role"] = "owner"
        mock_fs.document.return_value.get.return_value = _make_firestore_snapshot(
            user_doc
        )

        _, body = self._post(get_valid_login_payload())

        self.assertEqual(body["data"]["user"]["role"], "owner")
        mock_token.assert_called_once_with(FAKE_UID, developer_claims={"role": "owner"})

    @mock.patch("app.auth.service.auth.create_custom_token")
    @mock.patch("app.auth.service.FS_CLIENT")
    @mock.patch("app.auth.service.requests.post")
    def test_missing_firestore_doc_defaults_to_customer(
        self, mock_post, mock_fs, mock_token
    ):
        """If the Firestore document doesn't exist, role must default to 'customer'."""
        mock_post.return_value = _make_http_response(
            {"localId": FAKE_UID, "email": "test@example.com"}
        )
        mock_token.return_value = FAKE_CUSTOM_TOKEN
        mock_fs.document.return_value.get.return_value = _make_firestore_snapshot(None)

        _, body = self._post(get_valid_login_payload())

        self.assertEqual(body["data"]["user"]["role"], "customer")
