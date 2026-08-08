"""Firebase ID-token gate.

Every ``/api/*`` request needs a Google sign-in from an allowlisted address, or
the shared service token that machine callers present. Tokens are verified
against Google's published signing certificates, so the app stores no
service-account credential and has no secret to rotate.
"""
import hmac
import json
import time
from urllib.request import urlopen

import jwt
from cryptography.x509 import load_pem_x509_certificate
from flask import Blueprint, current_app, g, jsonify, request

# Google's Firebase token signing certificates, as {kid: PEM}. Rotated roughly
# daily, so the cached copy is short-lived.
CERT_URL = ("https://www.googleapis.com/robot/v1/metadata/x509/"
            "securetoken@system.gserviceaccount.com")
CERT_TTL = 3600
CERT_MIN_REFRESH = 60  # seconds; an unknown kid may not force a re-fetch more often than this

# Endpoints reachable without a credential, by Flask endpoint name. This is the
# seam for a future public view: adding a name here opens that one route.
PUBLIC_ENDPOINTS = {"health", "auth.config"}

# Endpoints the shared service token may reach. It is the only credential that
# lives on disk, and it must be readable by a container that does not run as its
# owner, so it is scoped to exactly the machine-caller route rather than granting
# the API-wide access a Firebase token does.
SERVICE_ENDPOINTS = {"monitor.alerts_webhook"}

_certs = {"keys": {}, "at": 0.0}


class AuthError(Exception):
    """A rejected credential, carrying the HTTP status the caller should see."""

    def __init__(self, status, code):
        super().__init__(code)
        self.status = status
        self.code = code


def enabled(config):
    return bool(config["FIREBASE_PROJECT_ID"]) and not config["AUTH_DISABLED"]


def allowed_emails(config):
    return {e.strip().lower() for e in config["ALLOWED_EMAILS"].split(",") if e.strip()}


def _public_keys(force=False):
    """Google's signing keys by ``kid``, cached for CERT_TTL seconds."""
    age = time.time() - _certs["at"]
    if (force and age > CERT_MIN_REFRESH) or age > CERT_TTL:
        with urlopen(CERT_URL, timeout=10) as resp:
            raw = json.loads(resp.read().decode())
        _certs["keys"] = {
            kid: load_pem_x509_certificate(pem.encode()).public_key()
            for kid, pem in raw.items()
        }
        _certs["at"] = time.time()
    return _certs["keys"]


def verify_id_token(token, project_id):
    """Claims from a valid Firebase ID token. Raises AuthError on anything else."""
    try:
        kid = jwt.get_unverified_header(token).get("kid")
    except jwt.PyJWTError:
        raise AuthError(401, "malformed_token")
    try:
        key = _public_keys().get(kid)
        if key is None:  # unseen kid means a rotation, so refresh once before giving up
            key = _public_keys(force=True).get(kid)
    except (OSError, ValueError):
        raise AuthError(503, "certs_unavailable")
    if key is None:
        raise AuthError(401, "unknown_key")
    try:
        claims = jwt.decode(
            token, key, algorithms=["RS256"], audience=project_id,
            issuer=f"https://securetoken.google.com/{project_id}",
        )
    except jwt.PyJWTError:
        raise AuthError(401, "invalid_token")
    if not claims.get("sub"):
        raise AuthError(401, "invalid_token")
    if not claims.get("email_verified"):
        raise AuthError(401, "unverified_email")
    return claims


def _check():
    """before_request gate: a response short-circuits the request, None lets it through."""
    if not request.path.startswith("/api/"):
        return None  # the SPA shell and its assets, so the login screen can load
    config = current_app.config
    if not enabled(config):
        return None
    if request.endpoint in PUBLIC_ENDPOINTS:
        return None
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return jsonify({"error": "unauthorized", "code": "no_token"}), 401
    credential = header[7:].strip()
    service = config["SERVICE_TOKEN"]
    if service and hmac.compare_digest(credential.encode("utf-8"), service.encode("utf-8")):
        if request.endpoint not in SERVICE_ENDPOINTS:
            return jsonify({"error": "forbidden", "code": "service_scope"}), 403
        g.user = {"service": True}
        return None
    try:
        claims = verify_id_token(credential, config["FIREBASE_PROJECT_ID"])
    except AuthError as err:
        label = "unauthorized" if err.status == 401 else "unavailable"
        return jsonify({"error": label, "code": err.code}), err.status
    email = (claims.get("email") or "").lower()
    if email not in allowed_emails(config):
        # A real Google user who is not the owner. Distinct from 401 so the UI
        # says so instead of looping them back through sign-in forever.
        return jsonify({"error": "forbidden", "email": claims.get("email")}), 403
    g.user = claims
    return None


bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.get("/config")
def config():
    """Whether the gate is up, and what the frontend needs to talk to Firebase.
    Served at runtime so one built image works in every environment."""
    cfg = current_app.config
    if not enabled(cfg):
        return jsonify({"enabled": False})
    return jsonify({
        "enabled": True,
        "projectId": cfg["FIREBASE_PROJECT_ID"],
        "apiKey": cfg["FIREBASE_API_KEY"],
        "authDomain": cfg["FIREBASE_AUTH_DOMAIN"],
    })


@bp.get("/me")
def me():
    """The signed-in identity. Gated, so the frontend uses it to tell an
    allowlisted user from a stranger before it mounts the app."""
    return jsonify({"email": g.get("user", {}).get("email")})


def install(app):
    app.register_blueprint(bp)
    app.before_request(_check)
    if not enabled(app.config):
        app.logger.warning("Pantheos auth is off: every API route is open.")
