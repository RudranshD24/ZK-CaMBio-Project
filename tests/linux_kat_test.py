import hashlib
import hmac

import chaoshash
import numpy as np


def derive_chaos_parameters(master_key, app_salt="kat_salt", key_version=1):
    context = f"zkcambio|{app_salt}|v{key_version}".encode()
    derived = hmac.new(master_key, context, hashlib.sha256).digest()
    state = int.from_bytes(derived[0:8], byteorder="little")
    r_param = int.from_bytes(derived[8:16], byteorder="little")
    return (state if state != 0 else 0x9E3779B97F4A7C15), r_param

master_key = bytes(range(32))
state, r_param = derive_chaos_parameters(master_key, app_salt="kat_salt", key_version=1)
rng = np.random.RandomState(42)
x_q = rng.randint(-150000, 150000, size=768, dtype=np.int32)
cpp_bits = chaoshash.transform(x_q, state, r_param, 512)
first_4_hex = cpp_bits[:4].hex()
print(f"Linux Container C++ KAT First 4 Bytes: {first_4_hex}")
assert first_4_hex == "83ec0508", f"Mismatch in Linux container: {first_4_hex} vs 83ec0508"
print("SUCCESS: Bit-exact determinism verified in Linux container!")
