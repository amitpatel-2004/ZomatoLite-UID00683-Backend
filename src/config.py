import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration class"""

    SECRET_KEY = os.getenv("SECRET_KEY")
    ENV = os.getenv("ENV", "development")
    DEBUG = os.getenv("DEBUG", "0") == "1"
    FIREBASE_SERVICE_ACCOUNT_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
    FIRESTORE_EMULATOR_HOST = os.getenv("FIRESTORE_EMULATOR_HOST")
    FIREBASE_AUTH_EMULATOR_HOST = os.getenv("FIREBASE_AUTH_EMULATOR_HOST")
