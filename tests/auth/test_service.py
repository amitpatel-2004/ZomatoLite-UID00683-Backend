import unittest
import unittest.mock as mock
from datetime import datetime

from app.auth import service as auth_service
from app.auth.constants import FIREBASE_ERROR_EMAIL_EXISTS
from tests.auth.fixtures import (
    get_mock_service_result,
)

FAKE_UID = "firebase-uid-abc123"
FAKE_ID_TOKEN = "fake-id-token"
FAKE_CUSTOM_TOKEN = b"fake-custom-token-bytes"


def _make_http_response(data: dict, ok: bool = True):
    """Build a mock requests.Response with a .json() method and .ok property."""
    response = mock.MagicMock()
    response.ok = ok
    response.json.return_value = data
    return response


def _make_firestore_snapshot(data: dict | None):
    """Build a mock Firestore DocumentSnapshot with a .to_dict() method."""
    snapshot = mock.MagicMock()
    snapshot.to_dict.return_value = data
    return snapshot


class TestRegisterUser(unittest.TestCase):
    """Unit tests for auth_service.register_user."""

    def _run_register(
        self, mock_post, mock_verify, mock_fs, mock_create_token, role="customer"
    ):
        """Run register_user with all dependencies mocked to their happy-path values."""
        firebase_success = {
            "localId": FAKE_UID,
            "idToken": FAKE_ID_TOKEN,
            "email": "user@example.com",
        }
        mock_post.return_value = _make_http_response(firebase_success)
        mock_verify.return_value = {"uid": FAKE_UID}
        mock_create_token.return_value = FAKE_CUSTOM_TOKEN

        return auth_service.register_user(
            email="user@example.com",
            password="pass123",
            display_name="Test User",
            role=role,
        )

    @mock.patch("app.auth.service.auth.create_custom_token")
    @mock.patch("app.auth.service.FS_CLIENT")
    @mock.patch("app.auth.service.auth.verify_id_token")
    @mock.patch("app.auth.service.requests.post")
    def test_returns_custom_token_and_user(
        self, mock_post, mock_verify, mock_fs, mock_token
    ):
        """Successful registration must return a customToken and a user dict."""
        result = self._run_register(mock_post, mock_verify, mock_fs, mock_token)

        self.assertEqual(result["customToken"], FAKE_CUSTOM_TOKEN.decode("utf-8"))
        self.assertEqual(result["user"]["_id"], FAKE_UID)
        self.assertEqual(result["user"]["email"], "user@example.com")
        self.assertEqual(result["user"]["role"], "customer")

    @mock.patch("app.auth.service.auth.create_custom_token")
    @mock.patch("app.auth.service.FS_CLIENT")
    @mock.patch("app.auth.service.auth.verify_id_token")
    @mock.patch("app.auth.service.requests.post")
    def test_firestore_document_written_with_correct_fields(
        self, mock_post, mock_verify, mock_fs, mock_token
    ):
        """The user document saved to Firestore must contain all required fields."""
        self._run_register(mock_post, mock_verify, mock_fs, mock_token, role="owner")

        mock_doc = mock_fs.collection.return_value.document.return_value
        mock_doc.set.assert_called_once()

        written = mock_doc.set.call_args[0][0]
        self.assertEqual(written["_id"], FAKE_UID)
        self.assertEqual(written["email"], "user@example.com")
        self.assertEqual(written["role"], "owner")
        self.assertIsInstance(written["_createdAt"], datetime)

    @mock.patch("app.auth.service.auth.create_custom_token")
    @mock.patch("app.auth.service.FS_CLIENT")
    @mock.patch("app.auth.service.auth.verify_id_token")
    @mock.patch("app.auth.service.requests.post")
    def test_custom_token_minted_with_role_claim(
        self, mock_post, mock_verify, mock_fs, mock_token
    ):
        """create_custom_token must be called with the correct uid and role claim."""
        self._run_register(mock_post, mock_verify, mock_fs, mock_token, role="owner")

        mock_token.assert_called_once_with(
            FAKE_UID,
            developer_claims={"role": "owner"},
        )

    @mock.patch("app.auth.service.requests.post")
    def test_email_already_exists_raises_value_error(self, mock_post):
        """Firebase returning EMAIL_EXISTS must raise ValueError."""
        mock_post.return_value = _make_http_response(
            {"error": {"message": FIREBASE_ERROR_EMAIL_EXISTS}},
            ok=False,
        )

        with self.assertRaises(ValueError) as ctx:
            auth_service.register_user("taken@example.com", "pass", "Name", "customer")

        self.assertIn(FIREBASE_ERROR_EMAIL_EXISTS, str(ctx.exception))

    @mock.patch("app.auth.service.requests.post")
    def test_other_firebase_error_raises_runtime_error(self, mock_post):
        """Any Firebase error other than EMAIL_EXISTS must raise RuntimeError."""
        mock_post.return_value = _make_http_response(
            {"error": {"message": "OPERATION_NOT_ALLOWED"}},
            ok=False,
        )

        with self.assertRaises(RuntimeError):
            auth_service.register_user("user@example.com", "pass", "Name", "customer")


class TestLoginUser(unittest.TestCase):
    """Unit tests for auth_service.login_user."""

    def _run_login(self, mock_post, mock_verify, mock_fs, mock_token, role="customer"):
        """Run login_user with all dependencies mocked to their happy-path values."""
        firebase_success = {
            "localId": FAKE_UID,
            "idToken": FAKE_ID_TOKEN,
            "email": "user@example.com",
        }
        mock_post.return_value = _make_http_response(firebase_success)
        mock_verify.return_value = {"uid": FAKE_UID}
        mock_token.return_value = FAKE_CUSTOM_TOKEN

        service_result = get_mock_service_result()
        user_doc = service_result["user"]
        user_doc["role"] = role

        mock_fs.collection.return_value.document.return_value.get.return_value = (
            _make_firestore_snapshot(user_doc)
        )

        return auth_service.login_user(email="user@example.com", password="pass123")

    @mock.patch("app.auth.service.auth.create_custom_token")
    @mock.patch("app.auth.service.FS_CLIENT")
    @mock.patch("app.auth.service.auth.verify_id_token")
    @mock.patch("app.auth.service.requests.post")
    def test_returns_custom_token_and_user(
        self, mock_post, mock_verify, mock_fs, mock_token
    ):
        """Successful login must return a customToken and the user's profile."""
        result = self._run_login(mock_post, mock_verify, mock_fs, mock_token)

        self.assertEqual(result["customToken"], FAKE_CUSTOM_TOKEN.decode("utf-8"))
        self.assertEqual(result["user"]["_id"], FAKE_UID)
        self.assertEqual(result["user"]["displayName"], "Test User")

    @mock.patch("app.auth.service.auth.create_custom_token")
    @mock.patch("app.auth.service.FS_CLIENT")
    @mock.patch("app.auth.service.auth.verify_id_token")
    @mock.patch("app.auth.service.requests.post")
    def test_role_is_read_from_firestore(
        self, mock_post, mock_verify, mock_fs, mock_token
    ):
        """The role in the returned token must come from Firestore, not the request."""
        result = self._run_login(
            mock_post, mock_verify, mock_fs, mock_token, role="owner"
        )

        self.assertEqual(result["user"]["role"], "owner")
        mock_token.assert_called_once_with(FAKE_UID, developer_claims={"role": "owner"})

    @mock.patch("app.auth.service.auth.create_custom_token")
    @mock.patch("app.auth.service.FS_CLIENT")
    @mock.patch("app.auth.service.auth.verify_id_token")
    @mock.patch("app.auth.service.requests.post")
    def test_missing_firestore_doc_defaults_to_customer(
        self, mock_post, mock_verify, mock_fs, mock_token
    ):
        """If the Firestore document doesn't exist, role must default to 'customer'."""
        firebase_success = {
            "localId": FAKE_UID,
            "idToken": FAKE_ID_TOKEN,
            "email": "user@example.com",
        }
        mock_post.return_value = _make_http_response(firebase_success)
        mock_verify.return_value = {"uid": FAKE_UID}
        mock_token.return_value = FAKE_CUSTOM_TOKEN

        mock_fs.collection.return_value.document.return_value.get.return_value = (
            _make_firestore_snapshot(None)
        )

        result = auth_service.login_user(email="user@example.com", password="pass123")

        self.assertEqual(result["user"]["role"], "customer")

    @mock.patch("app.auth.service.requests.post")
    def test_invalid_password_raises_value_error(self, mock_post):
        """Firebase INVALID_PASSWORD error must raise ValueError."""
        mock_post.return_value = _make_http_response(
            {"error": {"message": "INVALID_PASSWORD"}},
            ok=False,
        )

        with self.assertRaises(ValueError):
            auth_service.login_user("user@example.com", "wrongpass")

    @mock.patch("app.auth.service.requests.post")
    def test_email_not_found_raises_value_error(self, mock_post):
        """Firebase EMAIL_NOT_FOUND error must also raise ValueError."""
        mock_post.return_value = _make_http_response(
            {"error": {"message": "EMAIL_NOT_FOUND"}},
            ok=False,
        )

        with self.assertRaises(ValueError):
            auth_service.login_user("ghost@example.com", "pass123")

    @mock.patch("app.auth.service.requests.post")
    def test_other_firebase_error_raises_runtime_error(self, mock_post):
        """A Firebase error unrelated to credentials must raise RuntimeError."""
        mock_post.return_value = _make_http_response(
            {"error": {"message": "TOO_MANY_ATTEMPTS_TRY_LATER"}},
            ok=False,
        )

        with self.assertRaises(RuntimeError):
            auth_service.login_user("user@example.com", "pass123")
