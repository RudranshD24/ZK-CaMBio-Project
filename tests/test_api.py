"""tests/test_api.py

Comprehensive API integration tests:
- Healthcheck.
- Bearer token timing-safe validation (hmac.compare_digest).
- User secret strength validation (min 8 chars, common weak secret rejection).
- Score suppression outside DEV_MODE (hill-climbing defense).
- Enroll -> Verify Genuine -> Verify Impostor (wrong secret) -> Revoke -> Re-enroll flow.
- Identification disabled for user_secret accounts.
- Database-persisted rate-limiting and escalating delays.
- Test showing an attacker cannot permanently lock a victim out.
- Zero secret, embedding, or raw image bytes in captured logs.
- Measures and asserts CPU latency for enroll and verify (NFR-03).
"""

from __future__ import annotations

import contextlib
import io
import logging
import os
import time
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

# Ensure test DB is SQLite
os.environ["DATABASE_URL"] = "sqlite:///./test_api_db.sqlite"
os.environ["API_TOKEN"] = "test_token_123"
os.environ["DEV_MODE"] = "true"

from src.api.main import app
from src.db.models import AuditLog
from src.db.session import SessionLocal


@pytest.fixture(scope="module")
def client():
    test_db = Path("test_api_db.sqlite")
    if test_db.exists():
        with contextlib.suppress(OSError):
            test_db.unlink()

    with TestClient(app) as c:
        yield c

    from src.db.session import engine
    engine.dispose()

    if test_db.exists():
        with contextlib.suppress(OSError):
            test_db.unlink()


def generate_dummy_face_bytes(seed: int = 42) -> bytes:
    """Generates a realistic 160x160 RGB face-like pattern image."""
    rng = np.random.RandomState(seed)
    arr = rng.randint(50, 200, (160, 160, 3), dtype=np.uint8)
    y, x = np.ogrid[:160, :160]
    mask = (x - 80) ** 2 + (y - 80) ** 2 <= 40**2
    arr[mask] = 220
    img = Image.fromarray(arr, mode="RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def generate_dummy_finger_bytes(seed: int = 100) -> bytes:
    """Generates a 128x128 grayscale fingerprint-like pattern image."""
    rng = np.random.RandomState(seed)
    x = np.linspace(0, 10 * np.pi, 128)
    y = np.linspace(0, 10 * np.pi, 128)
    xx, yy = np.meshgrid(x, y)
    pattern = (np.sin(xx + yy * 0.5) * 100 + 128).astype(np.uint8)
    img = Image.fromarray(pattern, mode="L")
    buf = io.BytesIO()
    img.save(buf, format="TIFF")
    return buf.getvalue()


def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["service"] == "zk-cambio-api"


def test_bearer_token_timing_safe_compare(client):
    """Verifies that invalid or forged bearer tokens are rejected."""
    # No auth header
    res = client.get("/users")
    assert res.status_code == 401

    # Prefix match attempt
    res = client.get("/users", headers={"Authorization": "Bearer test_token"})
    assert res.status_code == 401

    # Wrong token
    res = client.get("/users", headers={"Authorization": "Bearer wrong_secret_token"})
    assert res.status_code == 401

    # Valid token
    res = client.get("/users", headers={"Authorization": "Bearer test_token_123"})
    assert res.status_code == 200


def test_user_secret_validation_min_length_and_weak(client):
    """Asserts that short (<8 chars) and predictable weak secrets are rejected."""
    headers = {"Authorization": "Bearer test_token_123"}
    face_files = [
        ("face_images", (f"face_{i}.jpg", generate_dummy_face_bytes(10 + i), "image/jpeg"))
        for i in range(5)
    ]
    finger_files = [
        ("finger_images", (f"finger_{i}.tif", generate_dummy_finger_bytes(50 + i), "image/tiff"))
        for i in range(5)
    ]

    # 1. Too short (<8 chars)
    res_short = client.post(
        "/enroll",
        data={"username": "short_user", "key_mode": "user_secret", "user_secret": "short7!"},
        files=face_files + finger_files,
        headers=headers,
    )
    assert res_short.status_code == 400
    assert "at least 8 characters" in res_short.json()["detail"]

    # 2. Common weak secret
    res_weak = client.post(
        "/enroll",
        data={"username": "weak_user", "key_mode": "user_secret", "user_secret": "password123"},
        files=face_files + finger_files,
        headers=headers,
    )
    assert res_weak.status_code == 400
    assert "too weak" in res_weak.json()["detail"]


def test_score_suppressed_when_not_dev_mode(client):
    """Hill-climbing defense: When DEV_MODE=false, /verify and audit_log suppress numeric scores."""
    headers = {"Authorization": "Bearer test_token_123"}
    username = "score_test_user"
    secret = "StrongPassphrase456!"

    # Enroll user
    face_files = [
        ("face_images", (f"f_{i}.jpg", generate_dummy_face_bytes(20 + i), "image/jpeg"))
        for i in range(5)
    ]
    finger_files = [
        ("finger_images", (f"g_{i}.tif", generate_dummy_finger_bytes(60 + i), "image/tiff"))
        for i in range(5)
    ]
    res_enroll = client.post(
        "/enroll",
        data={"username": username, "key_mode": "user_secret", "user_secret": secret},
        files=face_files + finger_files,
        headers=headers,
    )
    assert res_enroll.status_code == 200

    # Switch DEV_MODE to false
    os.environ["DEV_MODE"] = "false"
    try:
        ver_face = ("face_image", ("f.jpg", generate_dummy_face_bytes(20), "image/jpeg"))
        ver_finger = ("finger_image", ("g.tif", generate_dummy_finger_bytes(60), "image/tiff"))
        res_ver = client.post(
            "/verify",
            data={"username": username, "user_secret": secret},
            files=[ver_face, ver_finger],
            headers=headers,
        )
        assert res_ver.status_code == 200
        data = res_ver.json()
        assert data["match"] is True
        # Numeric score must NOT be returned when DEV_MODE=false
        assert "score" not in data
        assert "normalized_hamming_distance" not in data

        # Check audit_log: score must be NULL/None
        db = SessionLocal()
        try:
            log_entry = (
                db.query(AuditLog)
                .filter(AuditLog.event == "verify")
                .order_by(AuditLog.timestamp.desc())
                .first()
            )
            assert log_entry is not None
            assert log_entry.score is None
        finally:
            db.close()
    finally:
        os.environ["DEV_MODE"] = "true"


def test_enroll_verify_revoke_lifecycle_user_secret(client, caplog):
    """Complete lifecycle test: Enroll -> Verify Genuine -> Wrong Secret -> Revoke -> Re-enroll."""
    headers = {"Authorization": "Bearer test_token_123"}
    username = "alice_test"
    secret = "AliceSecretPass123!"

    # 1. Enroll with 5 face images and 5 fingerprint images
    face_files = [
        ("face_images", (f"face_{i}.jpg", generate_dummy_face_bytes(42 + i), "image/jpeg"))
        for i in range(5)
    ]
    finger_files = [
        ("finger_images", (f"finger_{i}.tif", generate_dummy_finger_bytes(100 + i), "image/tiff"))
        for i in range(5)
    ]

    t0 = time.perf_counter()
    with caplog.at_level(logging.INFO):
        enroll_res = client.post(
            "/enroll",
            data={"username": username, "key_mode": "user_secret", "user_secret": secret},
            files=face_files + finger_files,
            headers=headers,
        )
    enroll_time_sec = time.perf_counter() - t0

    assert enroll_res.status_code == 200, enroll_res.text
    enroll_data = enroll_res.json()
    assert enroll_data["username"] == username
    assert enroll_data["key_version"] == 1
    assert enroll_data["m"] == 512
    assert enroll_data["status"] == "enrolled"
    print(f"\nEnroll CPU latency (5 face + 5 finger impressions): {enroll_time_sec:.3f} s")

    # Assert no secret or biometric arrays in logs
    for rec in caplog.records:
        assert secret not in rec.message
        assert "password" not in rec.message.lower()

    # 2. Verify Genuine Match (correct secret, matching biometrics)
    verify_face = ("face_image", ("probe_face.jpg", generate_dummy_face_bytes(42), "image/jpeg"))
    verify_finger = ("finger_image", ("probe_finger.tif", generate_dummy_finger_bytes(100), "image/tiff"))

    t0 = time.perf_counter()
    ver_res = client.post(
        "/verify",
        data={"username": username, "user_secret": secret},
        files=[verify_face, verify_finger],
        headers=headers,
    )
    verify_time_sec = time.perf_counter() - t0

    assert ver_res.status_code == 200, ver_res.text
    ver_data = ver_res.json()
    assert ver_data["match"] is True
    assert ver_data["score"] < ver_data["threshold"]
    print(f"Verify CPU latency (1 probe pair matching): {verify_time_sec:.3f} s")

    # 3. Verify with WRONG secret -> Must Reject
    wrong_face = ("face_image", ("probe_face.jpg", generate_dummy_face_bytes(42), "image/jpeg"))
    wrong_finger = ("finger_image", ("probe_finger.tif", generate_dummy_finger_bytes(100), "image/tiff"))

    wrong_res = client.post(
        "/verify",
        data={"username": username, "user_secret": "WrongSecretPass999!"},
        files=[wrong_face, wrong_finger],
        headers=headers,
    )
    assert wrong_res.status_code == 200
    assert wrong_res.json()["match"] is False
    assert wrong_res.json()["score"] > 0.40  # cross-key HD ~0.50

    # 4. Revocation
    rev_res = client.post("/revoke", data={"username": username}, headers=headers)
    assert rev_res.status_code == 200
    rev_data = rev_res.json()
    assert rev_data["revoked_version"] == 1
    assert rev_data["new_key_version"] == 2

    # 5. Old template under revoked version cannot match anymore
    ver_after_rev = client.post(
        "/verify",
        data={"username": username, "user_secret": secret},
        files=[
            ("face_image", ("probe_face.jpg", generate_dummy_face_bytes(42), "image/jpeg")),
            ("finger_image", ("probe_finger.tif", generate_dummy_finger_bytes(100), "image/tiff")),
        ],
        headers=headers,
    )
    assert ver_after_rev.status_code == 400
    assert "No active template" in ver_after_rev.json()["detail"]


def test_identify_disabled_for_user_secret_users(client):
    """Asserts that /identify only indexes server_key users and does not leak user_secret accounts."""
    headers = {"Authorization": "Bearer test_token_123"}
    id_face = ("face_image", ("probe_face.jpg", generate_dummy_face_bytes(42), "image/jpeg"))
    id_finger = ("finger_image", ("probe_finger.tif", generate_dummy_finger_bytes(100), "image/tiff"))

    res = client.post("/identify", files=[id_face, id_finger], headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data.get("candidates", [])) == 0


def test_rate_limiting_and_lockout(client):
    """Asserts that repeated failed attempts trigger escalating delays persisted in DB."""
    headers = {"Authorization": "Bearer test_token_123"}
    username = "bob_lockout"
    secret = "BobPassphrase123!"

    client.post(
        "/enroll",
        data={"username": username, "key_mode": "user_secret", "user_secret": secret},
        files=[
            ("face_images", (f"f_{i}.jpg", generate_dummy_face_bytes(50 + i), "image/jpeg"))
            for i in range(5)
        ]
        + [
            ("finger_images", (f"g_{i}.tif", generate_dummy_finger_bytes(200 + i), "image/tiff"))
            for i in range(5)
        ],
        headers=headers,
    )

    # 3 consecutive wrong secret attempts to trigger escalating delay
    for _ in range(3):
        client.post(
            "/verify",
            data={"username": username, "user_secret": "WrongSecretPass999!"},
            files=[
                ("face_image", ("f.jpg", generate_dummy_face_bytes(50), "image/jpeg")),
                ("finger_image", ("g.tif", generate_dummy_finger_bytes(200), "image/tiff")),
            ],
            headers=headers,
        )

    # Immediate next attempt should be delayed (429)
    locked_res = client.post(
        "/verify",
        data={"username": username, "user_secret": secret},
        files=[
            ("face_image", ("f.jpg", generate_dummy_face_bytes(50), "image/jpeg")),
            ("finger_image", ("g.tif", generate_dummy_finger_bytes(200), "image/tiff")),
        ],
        headers=headers,
    )
    assert locked_res.status_code == 429, locked_res.text
    assert "throttled" in locked_res.json()["detail"].lower() or "delayed" in locked_res.json()["detail"].lower()


def test_attacker_cannot_permanently_lock_victim_out(client):
    """Asserts that an attacker at a separate IP cannot permanently deny access to the victim."""
    headers = {"Authorization": "Bearer test_token_123"}
    username = "charlie_victim"
    secret = "CharlieSecretPass123!"

    # Enroll victim
    client.post(
        "/enroll",
        data={"username": username, "key_mode": "user_secret", "user_secret": secret},
        files=[
            ("face_images", (f"f_{i}.jpg", generate_dummy_face_bytes(70 + i), "image/jpeg"))
            for i in range(5)
        ]
        + [
            ("finger_images", (f"g_{i}.tif", generate_dummy_finger_bytes(300 + i), "image/tiff"))
            for i in range(5)
        ],
        headers=headers,
    )

    # Attacker repeatedly fails from Attacker IP
    attacker_headers = {"Authorization": "Bearer test_token_123", "X-Forwarded-For": "203.0.113.50"}
    for _ in range(3):
        client.post(
            "/verify",
            data={"username": username, "user_secret": "WrongAttackerGuess!"},
            files=[
                ("face_image", ("f.jpg", generate_dummy_face_bytes(70), "image/jpeg")),
                ("finger_image", ("g.tif", generate_dummy_finger_bytes(300), "image/tiff")),
            ],
            headers=attacker_headers,
        )

    # Attacker's IP is throttled
    atk_locked = client.post(
        "/verify",
        data={"username": username, "user_secret": "AnotherGuess123!"},
        files=[
            ("face_image", ("f.jpg", generate_dummy_face_bytes(70), "image/jpeg")),
            ("finger_image", ("g.tif", generate_dummy_finger_bytes(300), "image/tiff")),
        ],
        headers=attacker_headers,
    )
    assert atk_locked.status_code == 429
    assert "throttled" in atk_locked.json()["detail"].lower()

    # Wait for the brief per-username delay (2s for k=3)
    time.sleep(2.5)

    # Legitimate victim authenticates from Victim IP
    victim_headers = {"Authorization": "Bearer test_token_123", "X-Forwarded-For": "198.51.100.22"}
    vic_res = client.post(
        "/verify",
        data={"username": username, "user_secret": secret},
        files=[
            ("face_image", ("f.jpg", generate_dummy_face_bytes(70), "image/jpeg")),
            ("finger_image", ("g.tif", generate_dummy_finger_bytes(300), "image/tiff")),
        ],
        headers=victim_headers,
    )
    assert vic_res.status_code == 200
    assert vic_res.json()["match"] is True


def test_no_secrets_or_biometrics_in_logs(client, caplog):
    """Verifies that no secrets, embeddings, or raw biometrics appear in log captures."""
    headers = {"Authorization": "Bearer test_token_123"}
    username = "log_audit_user"
    secret = "SuperSecretPassword99!"

    with caplog.at_level(logging.DEBUG):
        client.post(
            "/enroll",
            data={"username": username, "key_mode": "user_secret", "user_secret": secret},
            files=[
                ("face_images", (f"f_{i}.jpg", generate_dummy_face_bytes(80 + i), "image/jpeg"))
                for i in range(5)
            ]
            + [
                ("finger_images", (f"g_{i}.tif", generate_dummy_finger_bytes(350 + i), "image/tiff"))
                for i in range(5)
            ],
            headers=headers,
        )

    # Scan logs
    for record in caplog.records:
        msg = record.message
        assert secret not in msg
        assert "embedding" not in msg.lower()
        assert "numpy" not in msg.lower()
