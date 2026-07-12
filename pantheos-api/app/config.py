import os


class Config:
    DATABASE_URL = os.environ.get(
        "PANTHEOS_DATABASE_URL",
        "postgresql+psycopg://shay@localhost:5432/pantheos",
    )
    # Guards the destructive reseed endpoint; enabled in dev/test only.
    ALLOW_RESEED = os.environ.get("PANTHEOS_ALLOW_RESEED", "0") == "1"
