import os
import pytest

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Ensures test isolation by forcing emulator environments."""
    os.environ["ENV"] = "testing"
    os.environ["DEBUG"] = "1"
    
    os.environ["FIRESTORE_EMULATOR_HOST"] = "127.0.0.1:8080"
    os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = "127.0.0.1:9099"
    
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "fake-testing-key.json"
    
    yield
