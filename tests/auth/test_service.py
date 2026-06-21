import unittest
import unittest.mock as mock
from datetime import datetime

from app.auth.dtos import UserLoginPayloadDTO, UserRegisterPayloadDTO
from app.auth.exceptions import EmailAlreadyExistsError, InvalidCredentialsError
from app.auth.service import AuthService
from app.enums import UserRole
from tests.auth.test_data import get_mock_firestore_user_doc

FAKE_UID = "firebase-uid-abc123"
FAKE_CUSTOM_TOKEN = b"fake-custom-token-bytes"

_FakeEmailAlreadyExistsError = type("EmailAlreadyExistsError", (Exception,), {})
_FakeFirebaseError = type("FirebaseError", (Exception,), {})

auth_service = AuthService()


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
    """Unit tests for AuthService.register_user."""

    def _run_register(self, mock_token, mock_create_user, role="customer"):
        """Run register_user with happy-path mocks for Firebase Auth calls."""
        mock_create_user.return_value = mock.MagicMock(uid=FAKE_UID)
        mock_token.return_value = FAKE_CUSTOM_TOKEN

        payload = UserRegisterPayloadDTO(
            email="user@example.com",
            password="pass123",
            display_name="Test User",
            role=UserRole(role),
        )
        return auth_service.register_user(payload)

    @mock.patch("app.auth.service.auth.create_custom_token")
    @mock.patch("app.auth.service.auth.create_user")
    def test_returns_custom_token_and_user(self, mock_create_user, mock_token):
        """Successful registration must return a customToken and a user profile."""
        result = self._run_register(mock_token, mock_create_user)

        self.assertEqual(result.custom_token, FAKE_CUSTOM_TOKEN.decode("utf-8"))
        self.assertEqual(result.user.id, FAKE_UID)
        self.assertEqual(result.user.email, "user@example.com")
        self.assertEqual(result.user.role, "customer")

    @mock.patch("app.auth.service.auth.create_custom_token")
    @mock.patch("app.auth.service.FS_CLIENT")
    @mock.patch("app.auth.service.auth.create_user")
    def test_firestore_document_written_with_correct_fields(
        self, mock_create_user, mock_fs, mock_token
    ):
        """The user document saved to Firestore must contain all required fields."""
        mock_create_user.return_value = mock.MagicMock(uid=FAKE_UID)
        mock_token.return_value = FAKE_CUSTOM_TOKEN

        payload = UserRegisterPayloadDTO(
            email="user@example.com",
            password="pass123",
            display_name="Test User",
            role=UserRole("owner"),
        )
        auth_service.register_user(payload)

        mock_doc = mock_fs.document.return_value
        mock_doc.set.assert_called_once()

        written = mock_doc.set.call_args[0][0]
        self.assertEqual(written["_id"], FAKE_UID)
        self.assertEqual(written["email"], "user@example.com")
        self.assertEqual(written["role"], "owner")
        self.assertIsInstance(written["_createdAt"], datetime)

    @mock.patch("app.auth.service.auth.create_custom_token")
    @mock.patch("app.auth.service.auth.create_user")
    def test_custom_token_minted_with_role_claim(self, mock_create_user, mock_token):
        """create_custom_token must be called with the correct uid and role claim."""
        self._run_register(mock_token, mock_create_user, role="owner")

        mock_token.assert_called_once_with(
            FAKE_UID,
            developer_claims={"role": "owner"},
        )

    @mock.patch(
        "app.auth.service.auth.EmailAlreadyExistsError", _FakeEmailAlreadyExistsError
    )
    @mock.patch("app.auth.service.auth.create_user")
    def test_email_already_exists_raises_custom_error(self, mock_create_user):
        """Firebase EmailAlreadyExistsError must be re-raised as EmailAlreadyExistsError."""
        mock_create_user.side_effect = _FakeEmailAlreadyExistsError("email taken")

        payload = UserRegisterPayloadDTO(
            email="taken@example.com",
            password="pass12",
            display_name="Name",
            role=UserRole.CUSTOMER,
        )
        with self.assertRaises(EmailAlreadyExistsError):
            auth_service.register_user(payload)

    @mock.patch("app.auth.service.FirebaseError", _FakeFirebaseError)
    @mock.patch(
        "app.auth.service.auth.EmailAlreadyExistsError", _FakeEmailAlreadyExistsError
    )
    @mock.patch("app.auth.service.auth.create_user")
    def test_other_firebase_error_raises_runtime_error(self, mock_create_user):
        """Any Firebase error other than EmailAlreadyExistsError must raise RuntimeError."""
        mock_create_user.side_effect = _FakeFirebaseError("op not allowed")

        payload = UserRegisterPayloadDTO(
            email="user@example.com",
            password="pass12",
            display_name="Name",
            role=UserRole.CUSTOMER,
        )
        with self.assertRaises(RuntimeError):
            auth_service.register_user(payload)


class TestLoginUser(unittest.TestCase):
    """Unit tests for AuthService.login_user."""

    def _run_login(self, mock_post, mock_fs, mock_token, role="customer"):
        """Run login_user with all dependencies mocked to their happy-path values."""
        firebase_success = {
            "localId": FAKE_UID,
            "email": "user@example.com",
        }
        mock_post.return_value = _make_http_response(firebase_success)
        mock_token.return_value = FAKE_CUSTOM_TOKEN

        user_doc = get_mock_firestore_user_doc()
        user_doc["role"] = role

        mock_fs.document.return_value.get.return_value = _make_firestore_snapshot(
            user_doc
        )

        payload = UserLoginPayloadDTO(email="user@example.com", password="pass123")
        return auth_service.login_user(payload)

    @mock.patch("app.auth.service.auth.create_custom_token")
    @mock.patch("app.auth.service.FS_CLIENT")
    @mock.patch("app.auth.service.requests.post")
    def test_returns_custom_token_and_user(self, mock_post, mock_fs, mock_token):
        """Successful login must return a customToken and the user's profile."""
        result = self._run_login(mock_post, mock_fs, mock_token)

        self.assertEqual(result.custom_token, FAKE_CUSTOM_TOKEN.decode("utf-8"))
        self.assertEqual(result.user.id, FAKE_UID)
        self.assertEqual(result.user.display_name, "Test User")

    @mock.patch("app.auth.service.auth.create_custom_token")
    @mock.patch("app.auth.service.FS_CLIENT")
    @mock.patch("app.auth.service.requests.post")
    def test_role_is_read_from_firestore(self, mock_post, mock_fs, mock_token):
        """The role in the returned token must come from Firestore, not the request."""
        result = self._run_login(mock_post, mock_fs, mock_token, role="owner")

        self.assertEqual(result.user.role, "owner")
        mock_token.assert_called_once_with(FAKE_UID, developer_claims={"role": "owner"})

    @mock.patch("app.auth.service.auth.create_custom_token")
    @mock.patch("app.auth.service.FS_CLIENT")
    @mock.patch("app.auth.service.requests.post")
    def test_missing_firestore_doc_defaults_to_customer(
        self, mock_post, mock_fs, mock_token
    ):
        """If the Firestore document doesn't exist, role must default to 'customer'."""
        firebase_success = {
            "localId": FAKE_UID,
            "email": "user@example.com",
        }
        mock_post.return_value = _make_http_response(firebase_success)
        mock_token.return_value = FAKE_CUSTOM_TOKEN

        mock_fs.document.return_value.get.return_value = _make_firestore_snapshot(None)

        payload = UserLoginPayloadDTO(email="user@example.com", password="pass123")
        result = auth_service.login_user(payload)

        self.assertEqual(result.user.role, "customer")

    @mock.patch("app.auth.service.requests.post")
    def test_invalid_password_raises_custom_error(self, mock_post):
        """Firebase INVALID_PASSWORD error must raise InvalidCredentialsError."""
        mock_post.return_value = _make_http_response(
            {"error": {"message": "INVALID_PASSWORD"}},
            ok=False,
        )

        payload = UserLoginPayloadDTO(email="user@example.com", password="wrongpass")
        with self.assertRaises(InvalidCredentialsError):
            auth_service.login_user(payload)

    @mock.patch("app.auth.service.requests.post")
    def test_email_not_found_raises_custom_error(self, mock_post):
        """Firebase EMAIL_NOT_FOUND error must also raise InvalidCredentialsError."""
        mock_post.return_value = _make_http_response(
            {"error": {"message": "EMAIL_NOT_FOUND"}},
            ok=False,
        )

        payload = UserLoginPayloadDTO(email="ghost@example.com", password="pass123")
        with self.assertRaises(InvalidCredentialsError):
            auth_service.login_user(payload)

    @mock.patch("app.auth.service.requests.post")
    def test_other_firebase_error_raises_runtime_error(self, mock_post):
        """A Firebase error unrelated to credentials must raise RuntimeError."""
        mock_post.return_value = _make_http_response(
            {"error": {"message": "TOO_MANY_ATTEMPTS_TRY_LATER"}},
            ok=False,
        )

        payload = UserLoginPayloadDTO(email="user@example.com", password="pass123")
        with self.assertRaises(RuntimeError):
            auth_service.login_user(payload)
