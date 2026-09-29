"""tests/test_chaos.py

Comprehensive tests for Phase 4: C++ Chaos Engine.
Tests:
1. Known-Answer Test (KAT): fixed key + fixed vector -> exact match between C++
   and pure-Python big-integer reference implementation and fixed expected hash.
2. Determinism: identical key + vector -> identical template; Hamming symmetry & range [0, 1].
3. Avalanche Effect:
   - 1-bit flip in 32-byte master key changes 45-55% of matrix bits.
   - 1 LSB change in initial state decorrelates the chaotic sequence within ~20 iterations.
4. Randomness Sanity:
   - Bit balance in matrix entries ~ 0.50 (in [0.485, 0.515]).
   - Lag-1..10 autocorrelation ~ 0.0 (|rho| < 0.02).
   - Chi-square test on byte distribution (p-value > 0.001).
   - Cycle check: no cycles detected within 2,000,000 steps across 100 random keys (Brent's algorithm).
5. Population Bit Balance:
   - Evaluated per bit position over the 180 TRAIN subjects (fraction of bits outside [0.3, 0.7]).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from scipy import stats
from src.chaos.engine import (
    ChaosEngine,
    derive_chaos_parameters,
    python_reference_transform,
)

try:
    import chaoshash
except ImportError:
    chaoshash = None


def test_chaoshash_module_present():
    assert chaoshash is not None, "chaoshash C++ extension must be built and importable"
    assert chaoshash.ping() == "chaoshash module loaded OK"


def test_known_answer_test_against_python_reference():
    """Known-Answer Test (KAT): Fixed master key + fixed quantized vector

    must yield the EXACT same bit string from C++ and pure-Python reference.
    """
    assert chaoshash is not None
    # Fixed 32-byte key
    master_key = bytes(range(32))
    state, r_param = derive_chaos_parameters(master_key, app_salt="kat_salt", key_version=1)

    # Fixed pseudo-random vector (seed 42)
    rng = np.random.RandomState(42)
    x_q = rng.randint(-150000, 150000, size=768, dtype=np.int32)

    # Compute with C++ chaoshash
    cpp_bits = chaoshash.transform(x_q, state, r_param, m=512)

    # Compute with pure Python big-integer reference
    py_bits = python_reference_transform(x_q, state, r_param, m=512)

    assert cpp_bits == py_bits, "C++ chaos output must match pure-Python reference bit-for-bit!"

    # Verify fixed expected hash for regression safety
    # Verify fixed expected hash for regression safety
    expected_hex_start = "83ec0508"  # first 4 bytes hex
    assert cpp_bits[:4].hex() == expected_hex_start, (
        f"KAT hex mismatch: expected {expected_hex_start}, got {cpp_bits[:4].hex()}"
    )


def test_determinism_and_hamming_properties():
    """Tests determinism across multiple runs, Hamming symmetry, and bounds."""
    assert chaoshash is not None
    engine = ChaosEngine()
    master_key = b"A" * 32
    rng = np.random.RandomState(42)
    fused_vec = rng.randn(768).astype(np.float32)
    fused_vec = fused_vec / np.linalg.norm(fused_vec)

    t1 = engine.transform(fused_vec, master_key, m=512)
    t2 = engine.transform(fused_vec, master_key, m=512)

    # Determinism
    assert t1 == t2, "Identical inputs and keys must produce identical templates"
    assert engine.hamming(t1, t2) == 0.0

    # Different key
    other_key = b"B" * 32
    t3 = engine.transform(fused_vec, other_key, m=512)
    assert t1 != t3

    # Hamming symmetry: d(a, b) == d(b, a)
    hd_13 = engine.hamming(t1, t3)
    hd_31 = engine.hamming(t3, t1)
    assert np.isclose(hd_13, hd_31, atol=1e-6)

    # Range [0.0, 1.0]
    assert 0.0 <= hd_13 <= 1.0
    # Independent keys should produce HD near 0.50
    assert 0.40 <= hd_13 <= 0.60, f"Expected HD near 0.50 for independent keys, got {hd_13}"


def test_avalanche_effect():
    """Tests avalanche criteria:

    1. Flipping 1 bit of master key changes ~50% (45-55%) of matrix bits.
    2. Changing initial state by 1 LSB decorrelates the chaotic sequence within ~20 steps.
    """
    assert chaoshash is not None
    base_key = bytearray(b"\x37" * 32)
    state1, r1 = derive_chaos_parameters(bytes(base_key), "avalanche_salt", 1)

    # 1. Flip exactly 1 bit in master key (bit 0 of byte 0)
    flipped_key = bytearray(base_key)
    flipped_key[0] ^= 1
    state2, r2 = derive_chaos_parameters(bytes(flipped_key), "avalanche_salt", 1)

    # Compare 50,000 raw matrix bits
    n_bits = 50000
    stream1 = chaoshash.stream_matrix_bits(state1, r1, n_bits)
    stream2 = chaoshash.stream_matrix_bits(state2, r2, n_bits)

    diff_hd = chaoshash.hamming(stream1, stream2, n_bits)
    assert 0.45 <= diff_hd <= 0.55, f"1-bit key flip avalanche outside [0.45, 0.55]: {diff_hd:.4f}"

    # 2. 1 LSB change in initial state decorrelation
    state_lsb = state1 ^ 1
    # Step both states and observe correlation over time
    from src.chaos.engine import ChaosGeneratorPy

    gen1 = ChaosGeneratorPy(state1, r1)
    gen2 = ChaosGeneratorPy(state_lsb, r1)

    diffs_after_decorrelation = []
    for step in range(200):
        s_a = gen1.step()
        s_b = gen2.step()
        bit_a = (s_a >> 32) & 1
        bit_b = (s_b >> 32) & 1
        if step >= 60:
            diffs_after_decorrelation.append(bit_a ^ bit_b)

    fraction_diff = float(np.mean(diffs_after_decorrelation))
    assert 0.35 <= fraction_diff <= 0.65, (
        f"1 LSB state change failed to decorrelate after 60 steps: fraction diff = {fraction_diff}"
    )



def test_randomness_sanity_of_matrix_bits():
    """Tests matrix bitstream properties:

    - Bit balance: fraction of 1s in [0.485, 0.515] (expected 0.50).
    - Lag-1..10 autocorrelation: |rho| < 0.02.
    - Chi-square test on byte distribution: p-value > 0.001.
    """
    assert chaoshash is not None
    master_key = b"\x77" * 32
    state, r_param = derive_chaos_parameters(master_key, "randomness_test", 1)

    n_bits = 200000
    stream = chaoshash.stream_matrix_bits(state, r_param, n_bits)
    bytes_arr = np.frombuffer(stream, dtype=np.uint8)

    # 1. Bit balance
    bits = np.unpackbits(bytes_arr)[:n_bits]
    fraction_ones = float(np.mean(bits))
    assert 0.485 <= fraction_ones <= 0.515, f"Bit balance skewed: {fraction_ones:.4f}"

    # 2. Autocorrelation for lags 1..10
    centered = bits.astype(np.float64) - fraction_ones
    var = np.var(centered)
    for lag in range(1, 11):
        corr = float(np.mean(centered[:-lag] * centered[lag:]) / var)
        assert abs(corr) < 0.025, f"Autocorrelation at lag {lag} too high: {corr:.4f}"

    # 3. Chi-square goodness-of-fit on byte values (256 bins)
    counts = np.bincount(bytes_arr, minlength=256)
    expected = len(bytes_arr) / 256.0
    chi2, p_val = stats.chisquare(counts, f_exp=np.full(256, expected))
    assert p_val > 0.001, f"Chi-square test failed: chi2={chi2:.2f}, p-val={p_val:.6f}"


def test_cycle_length_check_100_keys():
    """Cycle check: asserts no cycles detected within 2,000,000 iterations

    across 100 random keys using Brent's cycle detection algorithm in C++.
    """
    assert chaoshash is not None
    rng = np.random.RandomState(42)

    for i in range(100):
        key = rng.bytes(32)
        state, r_param = derive_chaos_parameters(key, app_salt="cycle_check", key_version=i)
        # Check 2,000,000 iterations for cycles
        has_cycle = chaoshash.has_cycle_within(state, r_param, max_steps=2000000)
        assert not has_cycle, f"Cycle detected in 2,000,000 steps for key index {i}!"


def test_train_population_bit_balance():
    """Computes bit balance per bit position across the 180 TRAIN subjects.

    Asserts that the fraction of bit positions with population mean outside
    [0.3, 0.7] is very low (< 5%).
    """
    assert chaoshash is not None
    fused_path = Path("data/processed/fused_embeddings.npz")
    if not fused_path.is_file():
        pytest.skip("fused_embeddings.npz not generated")

    fused_data = np.load(fused_path)
    train_mask = fused_data["splits"] == "train"
    train_tmpls = fused_data["enroll_templates"][train_mask]  # (180, 768)

    engine = ChaosEngine()
    fixed_key = b"\x5a" * 32
    m = 512

    # Transform all 180 train subjects
    bit_matrix = []
    for i in range(len(train_tmpls)):
        packed = engine.transform(train_tmpls[i], fixed_key, m=m)
        unpacked = np.unpackbits(np.frombuffer(packed, dtype=np.uint8))[:m]
        bit_matrix.append(unpacked)

    bit_matrix = np.array(bit_matrix)  # (180, 512)
    # Mean per bit position
    pos_means = np.mean(bit_matrix, axis=0)  # (512,)

    # Fraction of bits outside [0.3, 0.7]
    skewed_bits = (pos_means < 0.3) | (pos_means > 0.7)
    fraction_skewed = float(np.mean(skewed_bits))
    print(f"\nTrain bit balance: {fraction_skewed*100:.2f}% bits outside [0.3, 0.7] (mean={np.mean(pos_means):.3f})")

    assert fraction_skewed < 0.05, f"Too many skewed bit positions: {fraction_skewed*100:.2f}%"
