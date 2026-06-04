import firebase_admin
from firebase_admin import credentials, firestore
from src.config import Config


def init_firebase():
    """Initialize Firebase Admin SDK using service account credentials."""
    if firebase_admin._apps:
        return firebase_admin.get_app()

    service_account_path = Config.FIREBASE_SERVICE_ACCOUNT_PATH
    
    if not service_account_path:
        # TODO: Add this error to constants file
        raise ValueError("FIREBASE_SERVICE_ACCOUNT_PATH is not set in the environment configuration.")

    cred = credentials.Certificate(service_account_path)
    
    return firebase_admin.initialize_app(cred)


def get_firestore_client():
    """Return an initialized Firestore client instance."""
    return firestore.client()
