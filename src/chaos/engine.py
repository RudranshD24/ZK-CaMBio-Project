"""src/chaos/engine.py

Python interface and reference implementation for the ZK-CaMBio C++ chaos engine.
Implements:
1. HMAC-SHA256 key derivation (master_key 32 bytes + context -> 64-bit state & r_param).
2. Public mean-centering and int32 fixed-point quantization (scale 2^20).
3. Pure Python bit-exact reference implementation for cross-verification.
4. Python wrapper calling the native C++ chaoshash extension.
"""

from __future__ import annotations

import hashlib
import hmac
from pathlib import Path

import numpy as np

try:
    import chaoshash
except ImportError:
    try:
        from src.chaos import chaoshash
    except ImportError:
        chaoshash = None

# Constants matching C++ chaos.hpp
GOLDEN_RATIO_64 = 0x9E3779B97F4A7C15
R_MIN_DIV4 = 0xF99999999999999A
R_MAX_DIV4 = 0xFFFFFFFFFFFFFFFF
R_SPAN_DIV4 = R_MAX_DIV4 - R_MIN_DIV4
TRANSIENT_STEPS = 1000
DEFAULT_QUANTIZATION_SCALE = 1 << 20  # 2^20 = 1,048,576


def derive_chaos_parameters(
    master_key: bytes,
    app_salt: str = "zkcambio_salt",
    key_version: int = 1,
) -> tuple[int, int]:
    """Derives a 64-bit initial chaotic state and map parameter r_param from

    a 32-byte master key using HMAC-SHA256.
    HMAC-SHA256(master_key, "zkcambio|" + app_salt + "|v" + key_version).
    """
    if len(master_key) != 32:
        raise ValueError(f"master_key must be exactly 32 bytes, got {len(master_key)} bytes")

    context = f"zkcambio|{app_salt}|v{key_version}".encode()
    derived_bytes = hmac.new(master_key, context, hashlib.sha256).digest()

    state = int.from_bytes(derived_bytes[0:8], byteorder="little")
    r_param = int.from_bytes(derived_bytes[8:16], byteorder="little")

    if state == 0:
        state = GOLDEN_RATIO_64

    return state, r_param


def quantize_vector(
    vector: np.ndarray,
    mean_vector: np.ndarray | None = None,
    scale: int = DEFAULT_QUANTIZATION_SCALE,
) -> np.ndarray:
    """Centers fused vector around the public train mean and quantizes to int32

    with fixed scale 2^20:
    x_q = round((x - mu) * 2^20)
    """
    vec = vector.astype(np.float64)
    if mean_vector is not None:
        vec = vec - mean_vector.astype(np.float64)

    scaled = np.round(vec * scale)
    # Clip to prevent int32 overflow in extreme cases
    clipped = np.clip(scaled, -2147483648, 2147483647)
    return clipped.astype(np.int32)


def mul64_high_py(a: int, b: int) -> int:
    """Portable 64x64 unsigned multiplication returning the upper 64 bits."""
    return (a * b) >> 64


class ChaosGeneratorPy:
    """Independent pure-Python reference chaotic generator matching C++ ChaosGenerator bit-for-bit."""

    CACHE_SIZE = 8192
    CACHE_MASK = CACHE_SIZE - 1

    def __init__(self, init_state: int, r_param: int):
        self.state = GOLDEN_RATIO_64 if init_state == 0 else (init_state & 0xFFFFFFFFFFFFFFFF)
        self.r_div4 = R_MIN_DIV4 + (r_param % R_SPAN_DIV4)
        self.cache = [0] * self.CACHE_SIZE
        self.reseed_count = 0

    def step(self) -> int:
        neg_x = (-self.state) & 0xFFFFFFFFFFFFFFFF
        hi = mul64_high_py(self.state, neg_x)
        lo = (self.state * neg_x) & 0xFFFFFFFFFFFFFFFF
        p = ((hi << 2) | (lo >> 62)) & 0xFFFFFFFFFFFFFFFF
        next_x = mul64_high_py(p, self.r_div4)

        # Guard against degenerate states: 0, fixed points, and recurrent cycles
        idx = (next_x ^ (next_x >> 13) ^ (next_x >> 27)) & self.CACHE_MASK
        if next_x == 0 or next_x == self.state or self.cache[idx] == next_x:
            self.reseed_count += 1
            next_x = (next_x ^ (GOLDEN_RATIO_64 + self.reseed_count * 0x517cc1b727220a95)) & 0xFFFFFFFFFFFFFFFF
            if next_x == 0:
                next_x = GOLDEN_RATIO_64

        self.cache[idx] = next_x
        self.state = next_x
        return next_x


def python_reference_transform(
    x_q: np.ndarray | list[int],
    state: int,
    r_param: int,
    m: int = 512,
) -> bytes:
    """Independent pure-Python big-integer reference implementation of the

    chaos engine transform, bit-for-bit identical to C++.
    """
    d = len(x_q)
    gen = ChaosGeneratorPy(state, r_param)

    # 1. 1000 transient steps
    for _ in range(TRANSIENT_STEPS):
        gen.step()

    # 2. Fisher-Yates coordinate permutation
    perm = list(range(d))
    for i in range(d - 1, 0, -1):
        s = gen.step()
        j = s % (i + 1)
        perm[i], perm[j] = perm[j], perm[i]

    x_perm = [int(x_q[perm[i]]) for i in range(d)]

    # 3. Projection and 1-bit binarization
    n_bytes = (m + 7) // 8
    out = bytearray(n_bytes)

    for k in range(m):
        acc = 0
        for j in range(d):
            s = gen.step()
            bit_sign = 1 if ((s >> 32) & 1) else -1
            acc += bit_sign * x_perm[j]
        if acc >= 0:
            out[k // 8] |= 1 << (7 - (k % 8))

    return bytes(out)



class ChaosEngine:
    """High-level Python wrapper for the native C++ chaoshash extension."""

    def __init__(
        self,
        mean_vector_path: str | Path | None = "data/processed/chaos_mean_vector.npy",
        scale: int = DEFAULT_QUANTIZATION_SCALE,
    ) -> None:
        self.scale = scale
        self.mean_vector: np.ndarray | None = None
        if mean_vector_path is not None:
            p = Path(mean_vector_path)
            if p.is_file():
                self.mean_vector = np.load(p).astype(np.float32)

    def transform(
        self,
        fused_vector: np.ndarray,
        master_key: bytes,
        app_salt: str = "zkcambio_salt",
        key_version: int = 1,
        m: int = 512,
    ) -> bytes:
        """Transforms an uncentered continuous fused vector into an m-bit

        cancelable biometric template.
        """
        state, r_param = derive_chaos_parameters(
            master_key=master_key,
            app_salt=app_salt,
            key_version=key_version,
        )
        x_q = quantize_vector(fused_vector, mean_vector=self.mean_vector, scale=self.scale)

        if chaoshash is not None:
            return chaoshash.transform(x_q, state, r_param, m)
        return python_reference_transform(x_q, state, r_param, m)

    @staticmethod
    def hamming(a: bytes, b: bytes, m: int = -1) -> float:
        """Computes normalized Hamming distance in [0.0, 1.0] between two templates."""
        if chaoshash is not None:
            return float(chaoshash.hamming(a, b, m))

        # Python fallback popcount
        if len(a) != len(b):
            raise ValueError("Templates must have matching lengths")
        total_bits = m if m > 0 else len(a) * 8
        diff_bits = 0
        for i in range(len(a)):
            diff = a[i] ^ b[i]
            if i == len(a) - 1 and (total_bits % 8 != 0):
                mask = 0xFF << (8 - (total_bits % 8))
                diff &= mask
            diff_bits += bin(diff).count("1")
        return float(diff_bits / total_bits)
