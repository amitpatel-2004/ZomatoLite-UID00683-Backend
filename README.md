# Zomato Lite — Backend

A Flask-based backend for Zomato Lite, the food ordering platform.

## Tech Stack

*   **Language:** Python 3.13
*   **Framework:** Flask 3.1
*   **Database & Auth:** Firebase Admin SDK (Authentication + Firestore)
*   **Package Manager:** Pipenv
*   **Testing:** Pytest

## Prerequisites

Ensure you have the following installed on your local machine:

*   **Python 3.13**
*   **Node.js & npm** (Required to run the Firebase CLI)
*   **Java Development Kit (JDK) 11+** (Required to run Firebase Emulators)
*   **Firebase CLI:** Install globally via npm:
    ```bash
    npm install -g firebase-tools
    ```

## Local Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd zomato-lite-backend
```

### 2. Install Dependencies
```bash
pipenv install
```

### 3. Configure Environment Variables
Copy the example environment file and fill in your local values:
```bash
cp .env.example .env
```

### 4. Add Firebase Credentials
Place your Firebase `serviceAccountKey.json` file directly into the project root directory.

### 5. Start Firebase Emulators
```bash
firebase emulators:start
```

### 6. Start the Flask Server
In a separate terminal window, launch the development server:
```bash
pipenv run python app.py
```

## Project Structure

```text
zomato-lite-backend/
├── app/
│   ├── __init__.py         # Application factory (create_app)
│   ├── config.py           # Configuration loader
│   ├── modules/            # Feature modules (auth, restaurants, orders, etc.)
│   └── shared/             # Utilities, Firebase initializer, middlewares
├── tests/                  # Pytest test suites
├── .env                    # Local environment variables (git-ignored)
├── .env.example            # Template for environment variables (committed)
├── app.py                  # Primary application entry point
├── firebase.json           # Firebase emulator configurations
└── Pipfile                 # Dependency tracking file
```

## Running Tests

Execute your test suite locally using `pytest` through Pipenv:
```bash
pipenv run pytest
```
