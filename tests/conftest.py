import os
import sys
import types
import unittest.mock as mock

import pytest


sys.modules["firebase_admin"] = mock.MagicMock()
sys.modules["firebase_admin.auth"] = mock.MagicMock()
sys.modules["firebase_admin.firestore"] = mock.MagicMock()
sys.modules["firebase_admin.exceptions"] = mock.MagicMock()

fake_settings = types.ModuleType("app.settings")
setattr(fake_settings, "FS_CLIENT", mock.MagicMock())
setattr(fake_settings, "FIRESTORE_EMULATOR_HOST", "127.0.0.1:8080")
setattr(fake_settings, "FIREBASE_AUTH_EMULATOR_HOST", "127.0.0.1:9099")
setattr(fake_settings, "FIREBASE_WEB_API_KEY", "fake-key")
setattr(fake_settings, "ALLOWED_ORIGINS", ["http://localhost:8080"])
setattr(fake_settings, "FIREBASE_APP", mock.MagicMock())
sys.modules["app.settings"] = fake_settings


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Ensures test isolation by forcing emulator environments."""
    os.environ["ENV"] = "testing"
    os.environ["DEBUG"] = "1"
    
    os.environ["FIRESTORE_EMULATOR_HOST"] = "127.0.0.1:8080"
    os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = "127.0.0.1:9099"
    
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "fake-testing-key.json"
    
    yield
