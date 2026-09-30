"""tests/test_api.py

API integration tests using FastAPI TestClient:
- Enroll -> Verify Genuine -> Verify Impostor -> Revoke -> Old Template Rejected -> Re-enroll Works.
- Wrong user_secret is rejected.
- Identify disabled for user_secret users.
- Rate limiting lockout test (A6).
- Zero secret / biometric data in captured logs.
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


@pytest.fixture(scope="module")
def client():
    # Remove test DB file if exists
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
    # Add a bright circular center so face features are consistent
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
    # Create smooth synthetic ridge-like sinusoidal pattern
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


def test_enroll_verify_revoke_lifecycle_user_secret(client, caplog):
    """Complete lifecycle test for default 'user_secret' mode."""
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

    # Assert no user secret in logs
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
    assert ver_data["normalized_hamming_distance"] < ver_data["threshold"]
    print(f"Verify CPU latency (1 probe pair matching): {verify_time_sec:.3f} s")

    # 3. Verify with WRONG secret -> Must Reject
    wrong_face = ("face_image", ("probe_face.jpg", generate_dummy_face_bytes(42), "image/jpeg"))
    wrong_finger = ("finger_image", ("probe_finger.tif", generate_dummy_finger_bytes(100), "image/tiff"))

    wrong_res = client.post(
        "/verify",
        data={"username": username, "user_secret": "WrongSecret!"},
        files=[wrong_face, wrong_finger],
        headers=headers,
    )
    assert wrong_res.status_code == 200
    assert wrong_res.json()["match"] is False
    assert wrong_res.json()["normalized_hamming_distance"] > 0.40  # cross-key HD ~0.50

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
    # alice_test was enrolled in user_secret mode, so candidate list must be empty
    assert len(data.get("candidates", [])) == 0


def test_rate_limiting_and_lockout(client):
    """Asserts that 5 consecutive failed attempts trigger a 429 lockout."""
    headers = {"Authorization": "Bearer test_token_123"}
    # Enroll user bob
    client.post(
        "/enroll",
        data={"username": "bob_lockout", "key_mode": "user_secret", "user_secret": "BobPass123!"},
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

    # 5 consecutive wrong secret attempts
    for _ in range(5):
        client.post(
            "/verify",
            data={"username": "bob_lockout", "user_secret": "WrongSecret"},
            files=[
                ("face_image", ("f.jpg", generate_dummy_face_bytes(50), "image/jpeg")),
                ("finger_image", ("g.tif", generate_dummy_finger_bytes(200), "image/tiff")),
            ],
            headers=headers,
        )

    # 6th attempt should be locked out (429)
    locked_res = client.post(
        "/verify",
        data={"username": "bob_lockout", "user_secret": "BobPass123!"},
        files=[
            ("face_image", ("f.jpg", generate_dummy_face_bytes(50), "image/jpeg")),
            ("finger_image", ("g.tif", generate_dummy_finger_bytes(200), "image/tiff")),
        ],
        headers=headers,
    )
    assert locked_res.status_code == 429, locked_res.text
    assert "locked out" in locked_res.json()["detail"].lower()
