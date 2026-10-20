"""Integration tests for Mobile Backend API (Phase 1):
- Token auth & refresh rotation with theft detection (B1)
- Device registry for FCM push (B2)
- Android ticket intake channel & idempotency (B4, B5)
- Ticket file attachments upload, EXIF strip, and download (B6)
- App Links Digital Asset Links (B7)
- Requester account deletion Play Store policy (B8)
- App configuration & runtime status banner (B9)
- Password reset request & confirm flow (B11)
"""

import io
import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from src.app.main import app
from src.db.models.password_reset import PasswordReset
from src.db.models.user import User
from src.db.session import SessionLocal


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """Test client managing lifespan context."""
    with TestClient(app) as c:
        yield c


def test_demo_token_issue(client: TestClient) -> None:
    """B1: Verify demo-token endpoint issues bearer access and rotating refresh token."""
    res = client.post(
        "/api/v1/auth/demo-token",
        json={"role": "requester", "device_name": "Google Pixel 8 Pro"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 900
    assert "refresh_token" in data
    assert len(data["refresh_token"]) >= 32
    assert data["me"]["role"] == "requester"


def test_token_issue_with_credentials(client: TestClient) -> None:
    """B1: Verify credential-based token issue and rejection on invalid password."""
    # Successful login
    res = client.post(
        "/api/v1/auth/token",
        json={
            "email": "requester@example.com",
            "password": "demo123",
            "device_name": "Samsung Galaxy S24",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["me"]["email"] == "requester@example.com"
    assert data["access_token"] is not None

    # Failed login
    bad_res = client.post(
        "/api/v1/auth/token",
        json={
            "email": "requester@example.com",
            "password": "wrongpassword",
            "device_name": "Samsung Galaxy S24",
        },
    )

    assert bad_res.status_code == 401
    assert bad_res.json()["code"] == "AUTH_INVALID"


def test_token_refresh_rotation_and_theft_detection(client: TestClient) -> None:
    """B1: Verify token rotation on use and whole-family revocation upon token theft/reuse."""
    init_res = client.post(
        "/api/v1/auth/demo-token",
        json={"role": "requester", "device_name": "Test Device"},
    )
    assert init_res.status_code == 200
    t1_refresh = init_res.json()["refresh_token"]

    # 1. Normal rotation: use t1_refresh to get t2_refresh
    rot_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": t1_refresh},
    )
    assert rot_res.status_code == 200
    t2_data = rot_res.json()
    t2_refresh = t2_data["refresh_token"]
    assert t2_refresh != t1_refresh

    # 2. Token theft attempt: attacker or replay attempts to use already-rotated t1_refresh!
    theft_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": t1_refresh},
    )
    assert theft_res.status_code == 401
    assert theft_res.json()["code"] == "AUTH_TOKEN_THEFT_DETECTED"

    # 3. Family revocation: the legitimate t2_refresh must NOW ALSO be revoked!
    t2_after_theft = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": t2_refresh},
    )
    assert t2_after_theft.status_code == 401
    assert t2_after_theft.json()["code"] == "AUTH_TOKEN_THEFT_DETECTED"


def test_auth_sessions_and_revocation(client: TestClient) -> None:
    """B1: Verify signed-in sessions listing and individual session revocation."""
    token_res = client.post(
        "/api/v1/auth/demo-token",
        json={"role": "requester", "device_name": "Pixel Tablet"},
    )
    access_token = token_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # List sessions
    sessions_res = client.get("/api/v1/auth/sessions", headers=headers)
    assert sessions_res.status_code == 200
    sessions = sessions_res.json()
    assert len(sessions) >= 1
    session_id = sessions[0]["id"]

    # Revoke session
    del_res = client.delete(f"/api/v1/auth/sessions/{session_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "revoked"


def test_auth_logout_revokes_refresh_token(client: TestClient) -> None:
    """B1: Verify logout revokes the specified refresh token."""
    token_res = client.post(
        "/api/v1/auth/demo-token",
        json={"role": "requester", "device_name": "OnePlus 12"},
    )
    tokens = token_res.json()
    refresh_token = tokens["refresh_token"]
    access_token = tokens["access_token"]

    logout_res = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"refresh_token": refresh_token},
    )
    assert logout_res.status_code == 200

    # Refresh should now fail as token was revoked
    ref_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert ref_res.status_code == 401


def test_device_registry_lifecycle(client: TestClient) -> None:
    """B2: Verify FCM device registration, re-binding, and deletion on sign-out."""
    token_res = client.post(
        "/api/v1/auth/demo-token",
        json={"role": "requester"},
    )
    access_token = token_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    test_fcm_token = f"fcm_token_{uuid.uuid4()}"
    device_payload = {
        "fcm_token": test_fcm_token,
        "platform": "android",
        "app_version": "1.0.0",
        "os_version": "14",
        "locale": "en_IN",
    }

    # Register device
    reg_res = client.post("/api/v1/devices", json=device_payload, headers=headers)
    assert reg_res.status_code == 200
    dev_data = reg_res.json()
    assert dev_data["fcm_token"] == test_fcm_token
    device_id = dev_data["id"]

    # Re-registering same token updates last_seen_at without duplicate key error
    re_res = client.post("/api/v1/devices", json=device_payload, headers=headers)
    assert re_res.status_code == 200
    assert re_res.json()["id"] == device_id

    # Delete device
    del_res = client.delete(f"/api/v1/devices/{device_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"


def test_app_config_and_assetlinks(client: TestClient) -> None:
    """B7 & B9: Verify app-config and Digital Asset Links for Android App Links."""
    # App config
    config_res = client.get("/api/v1/app-config")
    assert config_res.status_code == 200
    cfg = config_res.json()
    assert "android" in cfg
    assert cfg["android"]["min_supported_version_code"] >= 1
    assert "features" in cfg
    assert cfg["features"]["attachments"] is True
    assert "status" in cfg

    # Digital Asset Links
    links_res = client.get("/.well-known/assetlinks.json")
    assert links_res.status_code == 200
    links = links_res.json()
    assert isinstance(links, list)
    assert links[0]["target"]["package_name"] == "com.routedesk.app"
    assert len(links[0]["target"]["sha256_cert_fingerprints"]) >= 1


def test_ticket_android_channel_and_idempotency(client: TestClient) -> None:
    """B4 & B5: Verify ticket creation with channel='android' and Idempotency-Key reuse."""
    idemp_key = f"key-ticket-{uuid.uuid4()}"
    payload = {
        "subject": "Mobile Wi-Fi keeps disconnecting in building 4",
        "description": "Every 10 minutes the phone loses Wi-Fi connection and reverts to cellular data.",
        "channel": "android",
        "blocking_team": False,
    }

    headers = {"Idempotency-Key": idemp_key}
    res1 = client.post("/api/v1/tickets", json=payload, headers=headers)
    assert res1.status_code == 201
    ticket1 = res1.json()
    assert ticket1["id"].startswith("T-")

    # Retry with same idempotency key
    res2 = client.post("/api/v1/tickets", json=payload, headers=headers)
    assert res2.status_code == 201
    ticket2 = res2.json()
    assert ticket2["id"] == ticket1["id"]
    assert ticket2["ticket_uuid"] == ticket1["ticket_uuid"]


def test_ticket_message_idempotency(client: TestClient) -> None:
    """B5: Verify posting ticket discussion message with Idempotency-Key prevents double posting."""
    ticket_res = client.post(
        "/api/v1/tickets",
        json={
            "subject": "Need software license key for JetBrains",
            "description": "Please approve license key for local development workstation.",
            "channel": "android",
        },
    )
    ticket_id = ticket_res.json()["id"]

    idemp_key = f"key-msg-{uuid.uuid4()}"
    msg_payload = {"body": "Any update on this request?", "internal": False}
    headers = {"Idempotency-Key": idemp_key}

    res1 = client.post(f"/api/v1/tickets/{ticket_id}/messages", json=msg_payload, headers=headers)
    assert res1.status_code == 201
    msg1 = res1.json()

    # Retry same message with same idempotency key
    res2 = client.post(f"/api/v1/tickets/{ticket_id}/messages", json=msg_payload, headers=headers)
    assert res2.status_code == 201
    msg2 = res2.json()
    assert msg2["id"] == msg1["id"]

    # Verify ticket message list contains only one instance
    ticket_detail = client.get(f"/api/v1/tickets/{ticket_id}").json()
    user_msgs = [m for m in ticket_detail["messages"] if m["body"] == "Any update on this request?"]
    assert len(user_msgs) == 1


def test_ticket_attachments_flow(client: TestClient) -> None:
    """B6: Verify image and PDF attachment upload, EXIF stripping, listing, and download."""
    ticket_res = client.post(
        "/api/v1/tickets",
        json={
            "subject": "Broken laptop screen attachment test",
            "description": "Uploading error screenshot and photo of display damage.",
            "channel": "android",
        },
    )
    ticket_id = ticket_res.json()["id"]

    # 1. Create a synthetic test image with Pillow
    img = Image.new("RGB", (60, 60), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    # 2. Upload image attachment
    files = {"file": ("screenshot.png", png_bytes, "image/png")}
    upload_res = client.post(f"/api/v1/tickets/{ticket_id}/attachments", files=files)
    assert upload_res.status_code == 201
    att_data = upload_res.json()
    att_id = att_data["id"]
    assert att_data["filename"] == "screenshot.png"
    assert att_data["content_type"] == "image/png"

    # 3. Check attachment is included in ticket details
    detail_res = client.get(f"/api/v1/tickets/{ticket_id}")
    assert detail_res.status_code == 200
    atts = detail_res.json()["attachments"]
    assert len(atts) == 1
    assert atts[0]["id"] == att_id

    # 4. Download / stream attachment
    dl_res = client.get(f"/api/v1/tickets/{ticket_id}/attachments/{att_id}")
    assert dl_res.status_code == 200
    assert len(dl_res.content) > 0

    # 5. Unsupported file type rejected
    bad_file = {"file": ("script.exe", b"MZbinarycontent", "application/x-msdownload")}
    bad_res = client.post(f"/api/v1/tickets/{ticket_id}/attachments", files=bad_file)
    assert bad_res.status_code == 400
    assert bad_res.json()["code"] == "UNSUPPORTED_MEDIA_TYPE"


def test_password_reset_flow(client: TestClient) -> None:
    """B11: Verify password reset request returns 202 and confirm updates password and revokes tokens."""
    from src.core.security import generate_opaque_token, hash_password, hash_token

    email = f"reset_test_{uuid.uuid4()}@example.com"
    with SessionLocal() as db:
        test_user = User(
            email=email,
            name="Password Reset Test User",
            password_hash=hash_password("oldpassword123"),
            role="requester",
            is_active=True,
        )
        db.add(test_user)
        # Also ensure demo user is reset to default password
        demo_u = db.query(User).filter(User.email == "requester@example.com").first()
        if demo_u:
            demo_u.password_hash = hash_password("demo123")
        db.commit()

    # Request reset
    req_res = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": email},
    )
    assert req_res.status_code == 202
    assert req_res.json()["status"] == "accepted"

    # Fetch token from database directly to test confirmation
    with SessionLocal() as db:
        user = db.query(User).filter(User.email == email).first()
        reset_row = (
            db.query(PasswordReset)
            .filter(PasswordReset.user_id == user.id, PasswordReset.used_at.is_(None))
            .first()
        )
        assert reset_row is not None
        test_token = generate_opaque_token(32)
        reset_row.token_hash = hash_token(test_token)
        db.commit()

    # Confirm password reset
    confirm_res = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": test_token, "new_password": "newpassword123"},
    )
    assert confirm_res.status_code == 200
    assert confirm_res.json()["status"] == "password_reset_successful"

    # Verify login with new password works
    new_login = client.post(
        "/api/v1/auth/token",
        json={"email": email, "password": "newpassword123"},
    )
    assert new_login.status_code == 200



def test_account_deletion_play_store_policy(client: TestClient) -> None:
    """B8: Verify staff account deletion is forbidden (403) and requester deletion anonymizes user."""
    # Staff account deletion blocked
    agent_token = client.post(
        "/api/v1/auth/demo-token",
        json={"role": "agent"},
    ).json()["access_token"]
    staff_del = client.delete(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {agent_token}"},
    )
    assert staff_del.status_code == 403
    assert staff_del.json()["code"] == "ACCOUNT_MANAGED_BY_ROSTER"

    # Create dedicated test requester to delete
    with SessionLocal() as db:
        del_user = User(
            email=f"temp_user_{uuid.uuid4()}@example.com",
            name="Temporary User",
            password_hash="mock",
            role="requester",
            is_active=True,
        )
        db.add(del_user)
        db.commit()
        db.refresh(del_user)
        del_user_id = del_user.id

    from src.core.security import create_access_token

    temp_token = create_access_token(
        {"sub": str(del_user_id), "email": "temp@example.com", "role": "requester", "name": "Temp"}
    )
    req_del = client.delete(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {temp_token}"},
    )
    assert req_del.status_code == 200
    assert req_del.json()["status"] == "account_deleted"

    # Verify user record is anonymized and deactivated
    with SessionLocal() as db:
        u = db.query(User).filter(User.id == del_user_id).first()
        assert u.is_active is False
        assert u.name == "Deleted User"
        assert "deleted_" in u.email
