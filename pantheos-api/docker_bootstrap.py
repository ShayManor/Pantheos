"""Container startup: wait for the DB, create tables, seed if empty.

Idempotent — safe to run on every start. Seeds only when the DB is empty, so
mutations persist across restarts. Lives outside the `app` package on purpose
(it is container glue, not application code under the 100% coverage gate).
"""
import time

import sqlalchemy

from app import create_app
from app.models import Area, Base
from app.seed import seed, sync_models

app = create_app()

for attempt in range(60):
    try:
        with app.db_engine.connect() as conn:
            conn.execute(sqlalchemy.text("SELECT 1"))
        break
    except Exception as exc:  # DB not up yet
        print(f"waiting for database ({attempt + 1}/60): {exc}", flush=True)
        time.sleep(1)
else:
    raise SystemExit("database never became reachable")

Base.metadata.create_all(app.db_engine)
session = app.db_session
if session.query(Area).count() == 0:
    seed(session)
    print("database seeded", flush=True)
else:
    print("database already populated; skipping seed", flush=True)
# Model catalog is code-defined config, not user data — refresh it every boot
# so an existing DB doesn't keep offering stale/unservable models.
sync_models(session)
print("model catalog synced", flush=True)
session.remove()
