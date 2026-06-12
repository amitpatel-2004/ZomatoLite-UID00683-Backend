import os

import firebase_admin
from firebase_admin import firestore


FIRESTORE_EMULATOR_HOST = os.getenv("FIRESTORE_EMULATOR_HOST")
FIREBASE_AUTH_EMULATOR_HOST = os.getenv("FIREBASE_AUTH_EMULATOR_HOST")
FIREBASE_WEB_API_KEY = os.getenv("FIREBASE_WEB_API_KEY")


def _init_firebase() -> firebase_admin.App:
    """Initializes Firebase using Application Default Credentials (ADC)."""
    if not firebase_admin._apps:
        return firebase_admin.initialize_app()
    return firebase_admin.get_app()


FIREBASE_APP = _init_firebase()
FS_CLIENT = firestore.client()
