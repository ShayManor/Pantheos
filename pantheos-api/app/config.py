import os


class Config:
    DATABASE_URL = os.environ.get(
        "PANTHEOS_DATABASE_URL",
        "postgresql+psycopg://shay@localhost:5432/pantheos",
    )
    # Guards the destructive reseed endpoint; enabled in dev/test only.
    ALLOW_RESEED = os.environ.get("PANTHEOS_ALLOW_RESEED", "0") == "1"
    # Absolute path to the built frontend (Vite dist). When set, Flask serves
    # it at "/" (assets + SPA fallback). Unset in dev/test — Vite serves it.
    FRONTEND_DIST = os.environ.get("PANTHEOS_FRONTEND_DIST")
    # Start the Delphi queue-draining worker in this process. On for real server
    # processes (wsgi, dev, E2E); off in unit tests so no background thread
    # mutates the DB mid-test.
    RUN_DELPHI_WORKER = os.environ.get("PANTHEOS_RUN_DELPHI_WORKER", "0") == "1"
    # Firebase auth. The gate is on when FIREBASE_PROJECT_ID is set and
    # AUTH_DISABLED is not; local dev and pytest leave the project id unset, so
    # they run open. The API key and auth domain are public values handed to the
    # frontend at runtime by GET /api/auth/config.
    FIREBASE_PROJECT_ID = os.environ.get("FIREBASE_PROJECT_ID", "")
    FIREBASE_API_KEY = os.environ.get("FIREBASE_API_KEY", "")
    FIREBASE_AUTH_DOMAIN = os.environ.get("FIREBASE_AUTH_DOMAIN", "")
    ALLOWED_EMAILS = os.environ.get("PANTHEOS_ALLOWED_EMAILS", "shay.manor@gmail.com")
    # Shared secret for machine callers (Alertmanager) that cannot hold a
    # Firebase token. Empty disables the bypass entirely.
    SERVICE_TOKEN = os.environ.get("PANTHEOS_SERVICE_TOKEN", "")
    AUTH_DISABLED = os.environ.get("PANTHEOS_AUTH_DISABLED", "0") == "1"
