"""scripts/benchmark_latency.py

Measures enroll and verify latency on the live API with scrypt enabled (N=16384, r=8, p=1).
Evaluates compliance against NFR-03 (< 1.0 s).
"""

import io
import os
import time
import numpy as np
import requests
from PIL import Image


def generate_face_bytes(seed: int = 42) -> bytes:
    rng = np.random.RandomState(seed)
    arr = rng.randint(50, 200, (160, 160, 3), dtype=np.uint8)
    y, x = np.ogrid[:160, :160]
    arr[(x - 80) ** 2 + (y - 80) ** 2 <= 40**2] = 220
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


def main():
    token = os.environ.get("API_TOKEN", "prod_token_sec_a1b2c3d4e5f60718293a4b5c6d7e8f90")
    headers = {"Authorization": f"Bearer {token}"}
    base_url = os.environ.get("API_URL", "http://localhost:8000")

    print("Measuring Enroll Latency (5 iterations of 5 face + 5 finger impressions)...")
    enroll_times = []
    for i in range(5):
        u = f"lat_user_{int(time.time() * 1000)}_{i}"
        files = [("face_images", ("f.jpg", generate_face_bytes(42 + j), "image/jpeg")) for j in range(5)]
        files += [("finger_images", ("g.tif", generate_finger_bytes(100 + j), "image/tiff")) for j in range(5)]
        data = {"username": u, "key_mode": "user_secret", "user_secret": "PassphraseBenchmark123!"}
        t0 = time.perf_counter()
        r = requests.post(f"{base_url}/enroll", headers=headers, data=data, files=files)
        dt = time.perf_counter() - t0
        assert r.status_code == 200, r.text
        enroll_times.append(dt)

    print("Measuring Verify Latency (10 iterations of 1 probe pair + scrypt key stretching)...")
    verify_times = []
    u_ver = f"lat_user_verify_{int(time.time() * 1000)}"
    files = [("face_images", ("f.jpg", generate_face_bytes(42 + j), "image/jpeg")) for j in range(5)]
    files += [("finger_images", ("g.tif", generate_finger_bytes(100 + j), "image/tiff")) for j in range(5)]
    requests.post(
        f"{base_url}/enroll",
        headers=headers,
        data={"username": u_ver, "key_mode": "user_secret", "user_secret": "PassphraseBenchmark123!"},
        files=files,
    )

    for i in range(10):
        time.sleep(0.1)
        p_files = [
            ("face_image", ("f.jpg", generate_face_bytes(42), "image/jpeg")),
            ("finger_image", ("g.tif", generate_finger_bytes(100), "image/tiff")),
        ]
        p_data = {"username": u_ver, "user_secret": "PassphraseBenchmark123!"}
        t0 = time.perf_counter()
        r = requests.post(f"{base_url}/verify", headers=headers, data=p_data, files=p_files)
        dt = time.perf_counter() - t0
        assert r.status_code == 200, r.text
        verify_times.append(dt)

    mean_enr = float(np.mean(enroll_times))
    std_enr = float(np.std(enroll_times))
    mean_ver = float(np.mean(verify_times))
    std_ver = float(np.std(verify_times))

    print("\n=== Latency Benchmark (scrypt N=16384, r=8, p=1 on live Docker API) ===")
    print(f"Enroll (5 face + 5 finger impressions): mean={mean_enr:.4f}s, std={std_enr:.4f}s")
    print(f"Verify (1 probe pair + scrypt KDF):     mean={mean_ver:.4f}s, std={std_ver:.4f}s")
    print(f"NFR-03 Target: < 1.0 s for verification")
    status_str = "PASS (NFR-03 met)" if mean_ver < 1.0 else "FAIL"
    print(f"Compliance: {status_str}")


if __name__ == "__main__":
    main()
