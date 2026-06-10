import unittest
from app import create_app
from app.constants import SuccessMessages


class TestHealthEndpoint(unittest.TestCase):
    """Test suite for the server health monitoring."""

    def setUp(self):
        """Set up the test client execution state."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_health_check_returns_success(self):
        """Verify that the health route returns standard structured data."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)

        json_data = response.get_json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["message"], SuccessMessages.SERVER_HEALTHY)
        self.assertIsNone(json_data["data"])


if __name__ == "__main__":
    unittest.main()
