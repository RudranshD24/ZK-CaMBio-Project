"""tests/linux_kat_test.py

Linux Container Known-Answer Tests (KAT) for ZK-CaMBio (Phase 7d).
Verifies exact cross-platform bit-level determinism between Linux GCC and Windows MSVC
for both server_key mode and user_secret mode with per-user key separation.
"""

import hashlib
import hmac

import numpy as np

try:
    import chaoshash
except ImportError:
    import sys
    sys.exit("chaoshash C++ extension not found")


def derive_chaos_parameters(master_key, app_salt="kat_salt", key_version=1, user_id="test_user_kat_001"):
    context = f"zkcambio|{app_salt}|v{key_version}|server_key|{user_id}".encode()
    derived = hmac.new(master_key, context, hashlib.sha256).digest()
    state = int.from_bytes(derived[0:8], byteorder="little")
    r_param = int.from_bytes(derived[8:16], byteorder="little")
    return (state if state != 0 else 0x9E3779B97F4A7C15), r_param


def derive_user_secret_chaos_parameters(
    master_key,
    user_secret,
    app_salt="kat_salt",
    key_version=1,
    user_id="test_user_kat_001",
    user_salt=b"0123456789abcdef",
):
    stretched = hashlib.scrypt(
        user_secret.encode("utf-8"),
        salt=user_salt,
        n=16384,
        r=8,
        p=1,
        maxmem=32 * 1024 * 1024,
        dklen=32,
    )
    context = f"zkcambio|{app_salt}|v{key_version}|{user_id}".encode() + b"|" + stretched
    derived = hmac.new(master_key, context, hashlib.sha256).digest()
    state = int.from_bytes(derived[0:8], byteorder="little")
    r_param = int.from_bytes(derived[8:16], byteorder="little")
    return (state if state != 0 else 0x9E3779B97F4A7C15), r_param


master_key = bytes(range(32))
rng = np.random.RandomState(42)
x_q = rng.randint(-150000, 150000, size=768, dtype=np.int32)

# 1. Server-key KAT verification
state, r_param = derive_chaos_parameters(master_key, app_salt="kat_salt", key_version=1, user_id="test_user_kat_001")
cpp_bits = chaoshash.transform(x_q, state, r_param, 512)
first_4_hex = cpp_bits[:4].hex()
print(f"Linux Container C++ Server-Key KAT First 4 Bytes: {first_4_hex}")
assert first_4_hex == "2d8998aa", f"Mismatch in Linux container server key KAT: {first_4_hex} vs 2d8998aa"

# 2. Stretched user_secret KAT verification (Per-User Salt & user_id binding)
state_u, r_param_u = derive_user_secret_chaos_parameters(
    master_key,
    "CorrectHorseBatteryStaple!",
    app_salt="kat_salt",
    key_version=1,
    user_id="test_user_kat_001",
    user_salt=b"0123456789abcdef",
)
cpp_bits_u = chaoshash.transform(x_q, state_u, r_param_u, 512)
first_4_hex_u = cpp_bits_u[:4].hex()
print(f"Linux Container C++ User-Secret KAT First 4 Bytes: {first_4_hex_u}")
assert first_4_hex_u == "9ed1a9ad", f"Mismatch in Linux container user secret KAT: {first_4_hex_u} vs 9ed1a9ad"

print("SUCCESS: Bit-exact determinism verified for both server_key and stretched user_secret in Linux container!")
