import os

# Real server processes drain the Delphi chat queue in-process (see
# app.delphi_worker); unit tests leave it off. Set before create_app so Config
# picks it up.
os.environ.setdefault("PANTHEOS_RUN_DELPHI_WORKER", "1")

from app import create_app, hermes_connectors

app = create_app()
# Keep the connectors panel in step with Hermes' live config (no-op unless the
# SSH bridge is configured). Runs per gunicorn worker; the mirror is idempotent.
hermes_connectors.start_background_sync(app)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
