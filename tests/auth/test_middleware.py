import unittest
import unittest.mock as mock
from http import HTTPStatus

from flask import g

from app import create_app
from app.auth.constants import (
    RESPONSE_MSG_TOKEN_INVALID,
    RESPONSE_MSG_TOKEN_MISSING,
)
from app.constants import RESPONSE_MSG_FORBIDDEN
from app.auth.middleware import require_auth, require_role


class TestRequireAuth(unittest.TestCase):
    """
    Tests for the @require_auth decorator.
    """

    def setUp(self):
        """Create a fresh app with a protected test route before each test."""
        self.app = create_app()
        self.app.config["TESTING"] = True

        @self.app.route("/test-protected")
        @require_auth
        def protected_view():
            return {"uid": g.uid, "role": g.role}, 200

        self.client = self.app.test_client()
        self.url = "/test-protected"

    def _get(self, headers=None):
        """Send a GET to the protected route and return (status_code, body)."""
        response = self.client.get(self.url, headers=headers or {})
        return response.status_code, response.get_json()

    def test_no_authorization_header_returns_401(self):
        """A request with no Authorization header must be rejected with 401."""
        status, body = self._get()

        self.assertEqual(status, HTTPStatus.UNAUTHORIZED)
        self.assertEqual(body["message"], RESPONSE_MSG_TOKEN_MISSING)

    def test_non_bearer_scheme_returns_401(self):
        """Authorization header without 'Bearer' prefix must return 401."""
        status, body = self._get(headers={"Authorization": "Basic sometoken"})

        self.assertEqual(status, HTTPStatus.UNAUTHORIZED)
        self.assertEqual(body["message"], RESPONSE_MSG_TOKEN_MISSING)

    @mock.patch("app.auth.middleware.auth.verify_id_token")
    def test_invalid_token_returns_401(self, mock_verify):
        """A token that Firebase rejects must return 401."""
        mock_verify.side_effect = Exception("Token expired")

        status, body = self._get(headers={"Authorization": "Bearer bad-token"})

        self.assertEqual(status, HTTPStatus.UNAUTHORIZED)
        self.assertEqual(body["message"], RESPONSE_MSG_TOKEN_INVALID)

    @mock.patch("app.auth.middleware.auth.verify_id_token")
    def test_valid_token_allows_request(self, mock_verify):
        """A valid Bearer token must let the request reach the view (200)."""
        mock_verify.return_value = {"uid": "user-123", "role": "customer"}

        status, _ = self._get(headers={"Authorization": "Bearer good-token"})

        self.assertEqual(status, HTTPStatus.OK)

    @mock.patch("app.auth.middleware.auth.verify_id_token")
    def test_uid_and_role_are_set_on_g(self, mock_verify):
        """After a valid token, g.uid and g.role must hold the decoded values."""
        mock_verify.return_value = {"uid": "user-abc", "role": "owner"}

        _, body = self._get(headers={"Authorization": "Bearer good-token"})

        self.assertEqual(body["uid"], "user-abc")
        self.assertEqual(body["role"], "owner")

    @mock.patch("app.auth.middleware.auth.verify_id_token")
    def test_token_without_role_claim_defaults_to_customer(self, mock_verify):
        """A decoded token with no 'role' key must default g.role to 'customer'."""
        mock_verify.return_value = {"uid": "user-xyz"}

        _, body = self._get(headers={"Authorization": "Bearer good-token"})

        self.assertEqual(body["role"], "customer")


class TestRequireRole(unittest.TestCase):
    """
    Tests for the @require_role decorator.
    """

    def setUp(self):
        """Create a fresh app with an owner-only test route before each test."""
        self.app = create_app()
        self.app.config["TESTING"] = True

        @self.app.route("/test-owner-only")
        @require_auth
        @require_role("owner")
        def owner_only_view():
            return {"uid": g.uid, "role": g.role}, 200

        self.client = self.app.test_client()
        self.url = "/test-owner-only"

    def _get(self, headers=None):
        """Send a GET to the owner-only route."""
        response = self.client.get(self.url, headers=headers or {})
        return response.status_code, response.get_json()

    @mock.patch("app.auth.middleware.auth.verify_id_token")
    def test_owner_role_is_allowed(self, mock_verify):
        """A user with 'owner' role must be granted access (200)."""
        mock_verify.return_value = {"uid": "owner-1", "role": "owner"}

        status, _ = self._get(headers={"Authorization": "Bearer good-token"})

        self.assertEqual(status, HTTPStatus.OK)

    @mock.patch("app.auth.middleware.auth.verify_id_token")
    def test_customer_role_is_forbidden(self, mock_verify):
        """A user with 'customer' role must be denied with 403."""
        mock_verify.return_value = {"uid": "cust-1", "role": "customer"}

        status, body = self._get(headers={"Authorization": "Bearer good-token"})

        self.assertEqual(status, HTTPStatus.FORBIDDEN)
        self.assertEqual(body["message"], RESPONSE_MSG_FORBIDDEN)
