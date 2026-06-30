import unittest
from http import HTTPStatus

from app import create_app
from app.constants import RESPONSE_MSG_HEALTH_OK


class TestHealthEndpoint(unittest.TestCase):
    """Test suite for the server health monitoring."""

    def setUp(self) -> None:
        """Set up the test client execution state."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["DEBUG"] = True
        self.client = self.app.test_client()

    def test_health_check_returns_success(self) -> None:
        """Verify that the health route returns standard structured data."""
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, HTTPStatus.OK.value)

        json_data = response.get_json()
        self.assertEqual(json_data["message"], RESPONSE_MSG_HEALTH_OK)
        self.assertNotIn("errors", json_data)
