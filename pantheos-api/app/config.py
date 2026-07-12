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
