#pragma once

#include <cstdint>
#include <vector>
#include <string>

namespace zkcambio {

// Golden ratio fractional constant 2^64 / phi for degenerate state perturbation
constexpr uint64_t GOLDEN_RATIO_64 = 0x9E3779B97F4A7C15ULL;

// Minimum R_div4 representing r=3.90 in Q64 (0.975 * 2^64)
constexpr uint64_t R_MIN_DIV4 = 0xF99999999999999AULL;
constexpr uint64_t R_MAX_DIV4 = 0xFFFFFFFFFFFFFFFFULL;
constexpr uint64_t R_SPAN_DIV4 = R_MAX_DIV4 - R_MIN_DIV4;

constexpr int TRANSIENT_STEPS = 1000;

/**
 * Portable 64x64 unsigned multiplication returning the upper 64 bits.
 * Uses 32-bit halves for bit-exact cross-platform determinism (MSVC / GCC / Clang).
 */
inline uint64_t mul64_high(uint64_t a, uint64_t b) {
    uint64_t a_hi = a >> 32;
    uint64_t a_lo = a & 0xFFFFFFFFULL;
    uint64_t b_hi = b >> 32;
    uint64_t b_lo = b & 0xFFFFFFFFULL;

    uint64_t p0 = a_lo * b_lo;
    uint64_t p1 = a_lo * b_hi;
    uint64_t p2 = a_hi * b_lo;
    uint64_t p3 = a_hi * b_hi;

    uint64_t cy = (p0 >> 32) + (p1 & 0xFFFFFFFFULL) + (p2 & 0xFFFFFFFFULL);
    return p3 + (p1 >> 32) + (p2 >> 32) + (cy >> 32);
}

/**
 * Fixed-point chaotic generator (Q64 logistic map).
 * x_{n+1} = 4 * (r/4) * x_n * (1 - x_n)
 * Guards against degenerate states (0, fixed points, short cycles)
 * by detecting repeats within an 8192-entry direct-mapped cache and reseeding deterministically
 * using a golden-ratio Weyl sequence increment.
 */
class ChaosGenerator {
public:
    static constexpr size_t CACHE_SIZE = 8192;
    static constexpr size_t CACHE_MASK = CACHE_SIZE - 1;

    uint64_t state;
    uint64_t r_div4;
    std::vector<uint64_t> cache;
    uint64_t reseed_count;

    ChaosGenerator(uint64_t init_state, uint64_t r_param)
        : cache(CACHE_SIZE, 0ULL), reseed_count(0ULL) {
        state = (init_state == 0ULL) ? GOLDEN_RATIO_64 : init_state;
        r_div4 = R_MIN_DIV4 + (r_param % R_SPAN_DIV4);
    }

    inline uint64_t step() {
        uint64_t neg_x = (uint64_t)(0ULL - state);
        uint64_t hi = mul64_high(state, neg_x);
        uint64_t lo = state * neg_x;
        // 4 * x * (1 - x) in Q64
        uint64_t p = (hi << 2) | (lo >> 62);
        uint64_t next_x = mul64_high(p, r_div4);

        // Guard against degenerate states: 0, fixed points, and recurrent cycles
        size_t idx = static_cast<size_t>((next_x ^ (next_x >> 13) ^ (next_x >> 27)) & CACHE_MASK);
        if (next_x == 0ULL || next_x == state || cache[idx] == next_x) {
            reseed_count++;
            next_x ^= (GOLDEN_RATIO_64 + reseed_count * 0x517cc1b727220a95ULL);
            if (next_x == 0ULL) {
                next_x = GOLDEN_RATIO_64;
            }
        }

        cache[idx] = next_x;
        state = next_x;
        return next_x;
    }

    bool operator==(const ChaosGenerator& other) const {
        return (state == other.state && r_div4 == other.r_div4);
    }
};

/**
 * Counts set bits in a single byte (portable popcount).
 */
inline int popcount8(uint8_t x) {
    x = x - ((x >> 1) & 0x55);
    x = (x & 0x33) + ((x >> 2) & 0x33);
    return (x + (x >> 4)) & 0x0F;
}

/**
 * Applies chaotic random projection and 1-bit binarization:
 * 1. Discards 1000 transient iterations.
 * 2. Key-dependent permutation of the d input dimensions via Fisher-Yates.
 * 3. Random projection matrix R in {-1, +1}^{m x d} taken from top bit of chaotic state.
 * 4. Binarizes output bit = (accumulated_sum >= 0) and packs into uint8 bytes.
 */
std::vector<uint8_t> transform_core(
    const int32_t* x_q,
    size_t d,
    uint64_t state,
    uint64_t r_param,
    int m
);

/**
 * Computes normalized Hamming distance between two packed bit strings.
 */
double hamming_distance(
    const uint8_t* a,
    size_t len_a,
    const uint8_t* b,
    size_t len_b,
    int m = -1
);

/**
 * Checks for chaotic cycle of length <= max_steps using Brent's cycle detection algorithm.
 */
bool has_cycle_within(
    uint64_t state,
    uint64_t r_param,
    uint64_t max_steps
);

/**
 * Generates a packed bitstream directly from the chaotic matrix generator
 * for randomness and statistical testing (bit balance, autocorrelation, chi-square).
 */
std::vector<uint8_t> stream_matrix_bits(
    uint64_t state,
    uint64_t r_param,
    size_t n_bits
);

} // namespace zkcambio

