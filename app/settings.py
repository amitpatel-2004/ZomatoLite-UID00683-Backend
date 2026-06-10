import os
import firebase_admin
from firebase_admin import firestore
from app.constants import AppConstants

SECRET_KEY = os.getenv("SECRET_KEY")
ENV = os.getenv("ENV", AppConstants.ENV_DEVELOPMENT)
DEBUG = os.getenv("DEBUG", "0") == "1"

FIRESTORE_EMULATOR_HOST = os.getenv("FIRESTORE_EMULATOR_HOST")
FIREBASE_AUTH_EMULATOR_HOST = os.getenv("FIREBASE_AUTH_EMULATOR_HOST")


def _init_firebase():
    """Initializes Firebase using Application Default Credentials (ADC)."""
    if not firebase_admin._apps:
        return firebase_admin.initialize_app()
    return firebase_admin.get_app()


FIREBASE_APP = _init_firebase()
FS_CLIENT = firestore.client()
