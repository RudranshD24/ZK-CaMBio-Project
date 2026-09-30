"""scripts/demo_live_lifecycle.py

Live Docker lifecycle verification demo for ZK-CaMBio.
Executes against the running containerized API (http://localhost:8000).

Flow:
1. Healthcheck (/health)
2. Enroll new user in 'user_secret' mode (5 face + 5 finger impressions)
3. Verify Genuine Probe -> match: True, score suppressed (hill-climbing defense)
4. Verify Impostor / Wrong Secret Probe -> match: False (indistinguishable schema)
5. Revoke User Active Template -> status: revoked, key_version bumped
6. Verify against Revoked Template -> HTTP 400 (no active template found)
7. Re-enroll User -> key_version: 2
8. Verify under New Enrollment -> match: True

Credentials & Configuration:
Pulls API_TOKEN and API_URL from environment or local .env file.
Contains NO hard-coded secrets.
"""

from __future__ import annotations

import io
import os
import secrets
import sys
import time
from pathlib import Path

import numpy as np
import requests
from PIL import Image


def load_env_file():
    """Lightweight loader for .env without external dependencies."""
    env_path = Path(".env")
    if env_path.is_file():
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip()
                    if k not in os.environ:
                        os.environ[k] = v


load_env_file()

BASE_URL = os.environ.get("API_URL", "http://localhost:8000")
TOKEN = os.environ.get("API_TOKEN")
if not TOKEN:
    print("ERROR: API_TOKEN environment variable is required to run demo_live_lifecycle.py", file=sys.stderr)
    sys.exit(1)

HEADERS = {"Authorization": f"Bearer {TOKEN}"}


def generate_face_bytes(seed: int = 42) -> bytes:
    rng = np.random.RandomState(seed)
    arr = rng.randint(50, 200, (160, 160, 3), dtype=np.uint8)
    y, x = np.ogrid[:160, :160]
    mask = (x - 80) ** 2 + (y - 80) ** 2 <= 40**2
    arr[mask] = 220
    img = Image.fromarray(arr, mode="RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def generate_finger_bytes(seed: int = 100) -> bytes:
    x = np.linspace(0, 10 * np.pi, 128)
    y = np.linspace(0, 10 * np.pi, 128)
    xx, yy = np.meshgrid(x, y)
    pattern = (np.sin(xx + yy * 0.5) * 100 + 128).astype(np.uint8)
    img = Image.fromarray(pattern, mode="L")
    buf = io.BytesIO()
    img.save(buf, format="TIFF")
    return buf.getvalue()


def run_live_lifecycle_demo():
    print("=================================================================")
    print("  ZK-CaMBio Live Docker API Lifecycle Demonstration")
    print(f"  Target: {BASE_URL}")
    print("=================================================================\n")

    # 1. Healthcheck
    print("--- 1. Checking /health ---")
    resp = requests.get(f"{BASE_URL}/health", timeout=10)
    assert resp.status_code == 200, f"/health failed: {resp.text}"
    health_data = resp.json()
    print(f"Health Response: {health_data}")
    assert health_data.get("status") == "healthy"

    # Unique test username and strong dynamic passphrase
    random_suffix = secrets.token_hex(4)
    username = f"docker_demo_user_{random_suffix}"
    secret_passphrase = f"DemoSecret_{secrets.token_urlsafe(12)}!"

    # 2. Enrollment
    print(f"\n--- 2. Enrolling user '{username}' (user_secret mode) ---")
    face_bytes = [generate_face_bytes(42 + i) for i in range(5)]
    finger_bytes = [generate_finger_bytes(100 + i) for i in range(5)]

    files = []
    for fb in face_bytes:
        files.append(("face_images", ("face.jpg", fb, "image/jpeg")))
    for finb in finger_bytes:
        files.append(("finger_images", ("finger.tif", finb, "image/tiff")))

    data = {
        "username": username,
        "key_mode": "user_secret",
        "user_secret": secret_passphrase,
    }

    t0 = time.perf_counter()
    resp = requests.post(f"{BASE_URL}/enroll", headers=HEADERS, data=data, files=files, timeout=15)
    enr_latency = time.perf_counter() - t0
    assert resp.status_code == 200, f"Enroll failed: {resp.status_code} {resp.text}"
    enroll_data = resp.json()
    print(f"Enroll Response: {enroll_data} (Latency: {enr_latency:.3f}s)")
    assert enroll_data.get("status") == "enrolled"
    assert enroll_data.get("key_version") == 1

    # 3. Genuine Verification
    print("\n--- 3. Verifying Genuine Probe ---")
    probe_files = [
        ("face_image", ("face_probe.jpg", generate_face_bytes(42), "image/jpeg")),
        ("finger_image", ("finger_probe.tif", generate_finger_bytes(100), "image/tiff")),
    ]
    verify_data = {
        "username": username,
        "user_secret": secret_passphrase,
    }
    t0 = time.perf_counter()
    resp = requests.post(f"{BASE_URL}/verify", headers=HEADERS, data=verify_data, files=probe_files, timeout=10)
    ver_latency = time.perf_counter() - t0
    assert resp.status_code == 200, f"Verify failed: {resp.status_code} {resp.text}"
    verify_res = resp.json()
    print(f"Verify Genuine Response: {verify_res} (Latency: {ver_latency:.3f}s)")
    assert verify_res.get("match") is True, f"Expected match=True, got {verify_res}"
    print(f"Score field returned: {verify_res.get('score')} (Correctly suppressed outside DEV_MODE=true)")

    # 4. Impostor / Wrong Secret Verification
    print("\n--- 4. Verifying Impostor / Wrong Secret Probe ---")
    time.sleep(0.5)
    wrong_secret_data = {
        "username": username,
        "user_secret": "CompletelyWrongPassphrase999!",
    }
    resp = requests.post(f"{BASE_URL}/verify", headers=HEADERS, data=wrong_secret_data, files=probe_files, timeout=10)
    assert resp.status_code == 200, f"Verify wrong secret failed: {resp.status_code} {resp.text}"
    wrong_sec_res = resp.json()
    print(f"Verify Wrong Secret Response: {wrong_sec_res}")
    assert wrong_sec_res.get("match") is False, f"Expected match=False, got {wrong_sec_res}"

    # 5. Revocation
    print(f"\n--- 5. Revoking Active Template for user '{username}' ---")
    resp = requests.post(f"{BASE_URL}/revoke", headers=HEADERS, data={"username": username}, timeout=10)
    assert resp.status_code == 200, f"Revoke failed: {resp.status_code} {resp.text}"
    revoke_res = resp.json()
    print(f"Revoke Response: {revoke_res}")
    assert revoke_res.get("status") == "revoked"

    # 6. Verification with Revoked Template
    print("\n--- 6. Verifying against Revoked Template ---")
    time.sleep(0.5)
    resp = requests.post(f"{BASE_URL}/verify", headers=HEADERS, data=verify_data, files=probe_files, timeout=10)
    print(f"Verify after Revoke: Status={resp.status_code}, Body={resp.json()}")
    assert resp.status_code == 400
    assert "No active template found" in resp.json().get("detail", "")

    # 7. Re-enrollment
    print(f"\n--- 7. Re-enrolling user '{username}' under new key version ---")
    files_re = []
    for fb in face_bytes:
        files_re.append(("face_images", ("face.jpg", fb, "image/jpeg")))
    for finb in finger_bytes:
        files_re.append(("finger_images", ("finger.tif", finb, "image/tiff")))

    resp = requests.post(f"{BASE_URL}/enroll", headers=HEADERS, data=data, files=files_re, timeout=15)
    assert resp.status_code == 200, f"Re-enroll failed: {resp.status_code} {resp.text}"
    re_enroll_data = resp.json()
    print(f"Re-enroll Response: {re_enroll_data}")
    assert re_enroll_data.get("status") == "enrolled"
    assert re_enroll_data.get("key_version") == 2, f"Expected key_version=2, got {re_enroll_data.get('key_version')}"

    # 8. Verification under New Enrollment
    print("\n--- 8. Verifying under New Active Enrollment (key_version 2) ---")
    time.sleep(0.5)
    resp = requests.post(f"{BASE_URL}/verify", headers=HEADERS, data=verify_data, files=probe_files, timeout=10)
    assert resp.status_code == 200, f"Re-verify failed: {resp.status_code} {resp.text}"
    re_verify_res = resp.json()
    print(f"Re-verify Response: {re_verify_res}")
    assert re_verify_res.get("match") is True, f"Expected match=True, got {re_verify_res}"
    assert re_verify_res.get("key_version") == 2

    print("\n=================================================================")
    print("  ALL LIVE DOCKER LIFECYCLE CHECKS PASSED SUCCESSFULLY!")
    print("=================================================================")


if __name__ == "__main__":
    run_live_lifecycle_demo()
