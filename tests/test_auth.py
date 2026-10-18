"""
Automated Integration Tests for Role-Based Authentication, Password Security,
and Token RBAC Enforcement.
"""

from fastapi.testclient import TestClient

from src.auth.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from src.database.db import init_db
from src.serving.app import app

client = TestClient(app)


def setup_module():
    """Ensure database schema and seeded users exist."""
    init_db()


def test_password_hashing_and_verification():
    raw_pw = "SuperSecurePassword123!"
    pw_hash, pw_salt = hash_password(raw_pw)

    assert pw_hash != raw_pw
    assert len(pw_salt) == 32
    assert verify_password(raw_pw, pw_hash, pw_salt) is True
    assert verify_password("WrongPassword!", pw_hash, pw_salt) is False


def test_token_creation_and_decoding():
    token = create_access_token(
        user_id="usr_test_123",
        role="specialist_l3",
        department="DevOps",
        name="Test Devon",
    )
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "usr_test_123"
    assert payload["role"] == "specialist_l3"
    assert payload["department"] == "DevOps"
    assert payload["name"] == "Test Devon"

    # Tampered token check
    tampered_token = token[:-4] + "abcd"
    assert decode_access_token(tampered_token) is None


def test_demo_users_endpoint():
    resp = client.get("/api/v1/auth/demo-users")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 5
    roles = [u["role"] for u in data]
    assert "triager" in roles
    assert "resolver_lead" in roles
    assert "specialist_l3" in roles
    assert "manager" in roles
    assert "mlops_admin" in roles


def test_signup_and_duplicate_prevention():
    import uuid

    unique_email = f"jane_{uuid.uuid4().hex[:6]}@testcompany.org"
    signup_payload = {
        "name": "Jane Specialist",
        "email": unique_email,
        "password": "JanePassword2026!",
        "role": "specialist_l3",
        "department": "Project Engineering & DevOps",
    }
    resp = client.post("/api/v1/auth/signup", json=signup_payload)
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == unique_email
    assert data["user"]["role"] == "specialist_l3"

    # Duplicate email attempt
    dup_resp = client.post("/api/v1/auth/signup", json=signup_payload)
    assert dup_resp.status_code == 400
    assert "already registered" in dup_resp.json()["detail"]


def test_login_flow():
    # 1. Valid login using seeded demo user
    login_payload = {
        "email": "alex@enterprise.local",
        "password": "ServiceDesk2026!",
    }
    resp = client.post("/api/v1/auth/login", json=login_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["role"] == "triager"
    token = data["access_token"]

    # 2. Check /me with token
    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "alex@enterprise.local"

    # 3. Invalid password
    bad_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "alex@enterprise.local", "password": "WrongPassword!"},
    )
    assert bad_resp.status_code == 401

    # 4. Non-existent email
    unknown_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "ghost@nowhere.local", "password": "any"},
    )
    assert unknown_resp.status_code == 401


def test_quick_demo_login():
    resp = client.post("/api/v1/auth/quick-login", json={"role": "specialist_l3"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]["role"] == "specialist_l3"
    token = data["access_token"]

    # Verify token access to L3 restricted backlog
    l3_resp = client.get("/api/v1/escalations/l3-backlog", headers={"Authorization": f"Bearer {token}"})
    assert l3_resp.status_code == 200


def test_rbac_with_bearer_token():
    # Triager token
    triage_token_resp = client.post("/api/v1/auth/quick-login", json={"role": "triager"})
    triager_token = triage_token_resp.json()["access_token"]

    # Triager attempting to access L3 backlog -> Forbidden 403
    forbidden_resp = client.get(
        "/api/v1/escalations/l3-backlog",
        headers={"Authorization": f"Bearer {triager_token}"},
    )
    assert forbidden_resp.status_code == 403

    # Triager attempting to access Manager Oversight -> Forbidden 403
    forbidden_mgr = client.get(
        "/api/v1/escalations/manager-oversight",
        headers={"Authorization": f"Bearer {triager_token}"},
    )
    assert forbidden_mgr.status_code == 403

    # Manager token accessing Manager Oversight -> Allowed 200
    mgr_token_resp = client.post("/api/v1/auth/quick-login", json={"role": "manager"})
    mgr_token = mgr_token_resp.json()["access_token"]
    ok_mgr = client.get(
        "/api/v1/escalations/manager-oversight",
        headers={"Authorization": f"Bearer {mgr_token}"},
    )
    assert ok_mgr.status_code == 200
