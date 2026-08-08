import datetime
import json
import os
import time

import jwt
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from app import auth, create_app

PROJECT = "pantheos-8d962"
KID = "kid-1"
OWNER = "shay.manor@gmail.com"

TEST_DB = os.environ.get(
    "PANTHEOS_TEST_DATABASE_URL",
    "postgresql+psycopg://shay@localhost:5432/pantheos_test",
)


def _keypair():
    """A private key plus a self-signed PEM cert, the shape Google publishes."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime(2020, 1, 1))
        .not_valid_after(datetime.datetime(2040, 1, 1))
        .sign(key, hashes.SHA256())
    )
    pem = cert.public_bytes(serialization.Encoding.PEM).decode()
    return key, pem


KEY, PEM = _keypair()
OTHER_KEY, OTHER_PEM = _keypair()


class _FakeResp:
    def __init__(self, payload):
        self._payload = payload

    def read(self):
        return json.dumps(self._payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


@pytest.fixture()
def certs(monkeypatch):
    """Serve a fixed cert set in place of Google's, counting fetches."""
    calls = {"n": 0}

    def fake_urlopen(url, timeout=None):
        calls["n"] += 1
        return _FakeResp({KID: PEM})

    monkeypatch.setattr(auth, "urlopen", fake_urlopen)
    auth._certs["keys"] = {}
    auth._certs["at"] = 0.0
    yield calls
    auth._certs["keys"] = {}
    auth._certs["at"] = 0.0


def token(key=KEY, kid=KID, **claims):
    now = int(time.time())
    payload = {
        "iss": f"https://securetoken.google.com/{PROJECT}",
        "aud": PROJECT,
        "sub": "uid-123",
        "email": OWNER,
        "email_verified": True,
        "iat": now - 10,
        "exp": now + 3600,
    }
    payload.update(claims)
    return jwt.encode(payload, key, algorithm="RS256", headers={"kid": kid})


def test_valid_token_returns_claims(certs):
    claims = auth.verify_id_token(token(), PROJECT)
    assert claims["email"] == OWNER
    assert claims["sub"] == "uid-123"


def test_certs_cached_across_verifications(certs):
    auth.verify_id_token(token(), PROJECT)
    auth.verify_id_token(token(), PROJECT)
    assert certs["n"] == 1


def test_certs_refetched_after_ttl(certs):
    auth.verify_id_token(token(), PROJECT)
    auth._certs["at"] -= auth.CERT_TTL + 1
    auth.verify_id_token(token(), PROJECT)
    assert certs["n"] == 2


def test_unknown_kid_does_not_refetch_within_the_floor(certs):
    with pytest.raises(auth.AuthError) as err:
        auth.verify_id_token(token(kid="nope"), PROJECT)
    assert err.value.status == 401
    assert err.value.code == "unknown_key"
    # A junk kid moments after a fetch must not force another one, or an
    # anonymous caller could drive one outbound request per request.
    assert certs["n"] == 1


def test_unknown_kid_refetches_once_past_the_floor(certs):
    auth.verify_id_token(token(), PROJECT)
    auth._certs["at"] -= auth.CERT_MIN_REFRESH + 1
    with pytest.raises(auth.AuthError) as err:
        auth.verify_id_token(token(kid="nope"), PROJECT)
    assert err.value.code == "unknown_key"
    assert certs["n"] == 2


def test_cert_fetch_failure_is_503(monkeypatch):
    def boom(url, timeout=None):
        raise OSError("no route to host")

    monkeypatch.setattr(auth, "urlopen", boom)
    auth._certs["keys"] = {}
    auth._certs["at"] = 0.0
    try:
        with pytest.raises(auth.AuthError) as err:
            auth.verify_id_token(token(), PROJECT)
        assert err.value.status == 503
        assert err.value.code == "certs_unavailable"
    finally:
        auth._certs["keys"] = {}
        auth._certs["at"] = 0.0


def test_unverified_email_rejected(certs):
    with pytest.raises(auth.AuthError) as err:
        auth.verify_id_token(token(email_verified=False), PROJECT)
    assert err.value.status == 401
    assert err.value.code == "unverified_email"


def test_malformed_token(certs):
    with pytest.raises(auth.AuthError) as err:
        auth.verify_id_token("not-a-jwt", PROJECT)
    assert err.value.code == "malformed_token"


@pytest.mark.parametrize("claims", [
    {"exp": int(time.time()) - 10, "iat": int(time.time()) - 3600},
    {"aud": "some-other-project"},
    {"iss": "https://evil.example.com/pantheos-8d962"},
    {"sub": ""},
])
def test_rejected_claims(certs, claims):
    with pytest.raises(auth.AuthError) as err:
        auth.verify_id_token(token(**claims), PROJECT)
    assert err.value.status == 401
    assert err.value.code == "invalid_token"


def test_wrong_signing_key(certs):
    with pytest.raises(auth.AuthError) as err:
        auth.verify_id_token(token(key=OTHER_KEY), PROJECT)
    assert err.value.code == "invalid_token"


def test_allowed_emails_parsing():
    cfg = {"ALLOWED_EMAILS": " Shay.Manor@Gmail.com , other@x.com ,"}
    assert auth.allowed_emails(cfg) == {"shay.manor@gmail.com", "other@x.com"}


def test_enabled_flag():
    assert auth.enabled({"FIREBASE_PROJECT_ID": PROJECT, "AUTH_DISABLED": False})
    assert not auth.enabled({"FIREBASE_PROJECT_ID": "", "AUTH_DISABLED": False})
    assert not auth.enabled({"FIREBASE_PROJECT_ID": PROJECT, "AUTH_DISABLED": True})


# ------------------------------------------------------------------ the gate

def bearer(tok):
    return {"Authorization": f"Bearer {tok}"}


def test_gate_allows_owner(auth_app, certs):
    r = auth_app.test_client().get("/api/tickets", headers=bearer(token()))
    assert r.status_code == 200


def test_gate_rejects_missing_token(auth_app, certs):
    r = auth_app.test_client().get("/api/tickets")
    assert r.status_code == 401
    assert r.get_json() == {"error": "unauthorized", "code": "no_token"}


def test_gate_rejects_non_bearer_header(auth_app, certs):
    r = auth_app.test_client().get("/api/tickets", headers={"Authorization": "Basic abc"})
    assert r.status_code == 401


def test_gate_rejects_bad_token(auth_app, certs):
    r = auth_app.test_client().get("/api/tickets", headers=bearer(token(key=OTHER_KEY)))
    assert r.status_code == 401
    assert r.get_json()["code"] == "invalid_token"


def test_gate_rejects_non_ascii_credential(auth_app, certs):
    """Werkzeug hands headers over as latin-1 str, which compare_digest refuses."""
    r = auth_app.test_client().get("/api/tickets", headers={"Authorization": "Bearer é"})
    assert r.status_code == 401


def test_gate_reports_certs_unavailable(auth_app, monkeypatch):
    def boom(url, timeout=None):
        raise OSError("no route to host")

    monkeypatch.setattr(auth, "urlopen", boom)
    auth._certs["keys"] = {}
    auth._certs["at"] = 0.0
    try:
        r = auth_app.test_client().get("/api/tickets", headers=bearer(token()))
        assert r.status_code == 503
        assert r.get_json() == {"error": "unavailable", "code": "certs_unavailable"}
    finally:
        auth._certs["keys"] = {}
        auth._certs["at"] = 0.0


def test_gate_forbids_stranger(auth_app, certs):
    r = auth_app.test_client().get("/api/tickets", headers=bearer(token(email="nope@x.com")))
    assert r.status_code == 403
    assert r.get_json() == {"error": "forbidden", "email": "nope@x.com"}


def test_gate_accepts_service_token(auth_app, certs):
    r = auth_app.test_client().post(
        "/api/monitor/alerts", json={"alerts": []}, headers=bearer("svc-secret"))
    assert r.status_code == 200


def test_gate_rejects_wrong_service_token(auth_app, certs):
    r = auth_app.test_client().get("/api/tickets", headers=bearer("svc-wrong"))
    assert r.status_code == 401


def test_service_bypass_off_when_unset(certs):
    application = create_app({
        "DATABASE_URL": TEST_DB, "FIREBASE_PROJECT_ID": PROJECT,
        "ALLOWED_EMAILS": OWNER, "SERVICE_TOKEN": "", "AUTH_DISABLED": False,
    })
    try:
        assert application.test_client().get("/api/tickets", headers=bearer("")).status_code == 401
    finally:
        application.db_engine.dispose()


def test_public_endpoints_open_while_gated(auth_app, certs):
    client = auth_app.test_client()
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/auth/config").status_code == 200


def test_me_requires_a_token(auth_app, certs):
    client = auth_app.test_client()
    assert client.get("/api/auth/me").status_code == 401
    r = client.get("/api/auth/me", headers=bearer(token()))
    assert r.status_code == 200
    assert r.get_json() == {"email": OWNER}


def test_service_token_is_scoped_to_the_webhook(auth_app, certs):
    r = auth_app.test_client().get("/api/auth/me", headers=bearer("svc-secret"))
    assert r.status_code == 403
    assert r.get_json()["code"] == "service_scope"


def test_service_token_rejected_on_data_routes(auth_app, certs):
    r = auth_app.test_client().get("/api/tickets", headers=bearer("svc-secret"))
    assert r.status_code == 403
    assert r.get_json()["code"] == "service_scope"


def test_non_api_paths_bypass_the_gate(auth_app, certs, tmp_path):
    """The SPA shell must load so the login screen can render."""
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<!doctype html><title>Pantheos</title>")
    application = create_app({
        "DATABASE_URL": TEST_DB, "FIREBASE_PROJECT_ID": PROJECT,
        "ALLOWED_EMAILS": OWNER, "AUTH_DISABLED": False,
        "FRONTEND_DIST": str(dist),
    })
    try:
        assert application.test_client().get("/").status_code == 200
    finally:
        application.db_engine.dispose()


def test_config_shape_when_enabled(auth_app):
    body = auth_app.test_client().get("/api/auth/config").get_json()
    assert body == {
        "enabled": True,
        "projectId": "pantheos-8d962",
        "apiKey": "test-api-key",
        "authDomain": "pantheos-8d962.firebaseapp.com",
    }


def test_config_shape_when_disabled(client):
    assert client.get("/api/auth/config").get_json() == {"enabled": False}


def test_disabled_flag_beats_project_id(certs):
    application = create_app({
        "DATABASE_URL": TEST_DB, "FIREBASE_PROJECT_ID": PROJECT, "AUTH_DISABLED": True,
    })
    try:
        assert application.test_client().get("/api/tickets").status_code == 200
    finally:
        application.db_engine.dispose()
