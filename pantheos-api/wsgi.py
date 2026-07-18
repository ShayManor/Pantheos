from app import create_app, hermes_connectors

app = create_app()
# Keep the connectors panel in step with Hermes' live config (no-op unless the
# SSH bridge is configured). Runs per gunicorn worker; the mirror is idempotent.
hermes_connectors.start_background_sync(app)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
