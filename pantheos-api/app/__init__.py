"""Flask application factory."""
import os

from flask import Flask, abort, jsonify, send_from_directory
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from .api import register_blueprints
from .config import Config


def create_app(overrides=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if overrides:
        app.config.update(overrides)
    app.json.sort_keys = False  # preserve position-ordered insertion order

    engine = create_engine(app.config["DATABASE_URL"], future=True)
    db_session = scoped_session(sessionmaker(bind=engine, autoflush=False, future=True))
    app.db_engine = engine
    app.db_session = db_session

    @app.teardown_appcontext
    def remove_session(exc=None):
        db_session.remove()

    @app.errorhandler(404)
    def not_found(err):
        return jsonify({"error": "not found"}), 404

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    register_blueprints(app)

    # Serve the built frontend at "/" when a dist path is configured (container
    # deploy). The API keeps priority: registered /api/* rules match first, and
    # unmatched /api/* paths 404 as JSON rather than falling through to index.
    dist = app.config.get("FRONTEND_DIST")
    if dist:
        @app.get("/")
        def index():
            return send_from_directory(dist, "index.html")

        @app.get("/<path:filename>")
        def spa(filename):
            if filename.startswith("api/"):
                abort(404)
            if os.path.isfile(os.path.join(dist, filename)):
                return send_from_directory(dist, filename)
            return send_from_directory(dist, "index.html")

    return app
