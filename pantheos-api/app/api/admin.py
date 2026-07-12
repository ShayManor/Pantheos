from flask import Blueprint, current_app, jsonify

from . import db
from ..seed import reset_db, seed

bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@bp.post("/reseed")
def reseed():
    """Wipe + reseed the DB. Gated by ALLOW_RESEED (dev/test only).

    Used by the E2E suite's beforeEach to isolate each test.
    """
    if not current_app.config.get("ALLOW_RESEED"):
        return jsonify({"error": "forbidden"}), 403
    reset_db(current_app.db_engine)
    seed(db())
    return jsonify({"status": "reseeded"})
