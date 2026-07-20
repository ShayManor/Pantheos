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
