#include "chaos.hpp"
#include <algorithm>
#include <stdexcept>

namespace zkcambio {

std::vector<uint8_t> transform_core(
    const int32_t* x_q,
    size_t d,
    uint64_t state,
    uint64_t r_param,
    int m
) {
    if (d == 0 || m <= 0) {
        throw std::invalid_argument("Input dimension d and output dimension m must be strictly positive");
    }

    // 1. Initialize chaotic generator
    ChaosGenerator gen(state, r_param);

    // 2. Discard 1000 transient iterations to enter the chaotic attractor
    for (int i = 0; i < TRANSIENT_STEPS; ++i) {
        gen.step();
    }

    // 3. Key-dependent permutation of the d input dimensions via Fisher-Yates
    std::vector<size_t> perm(d);
    for (size_t i = 0; i < d; ++i) {
        perm[i] = i;
    }

    for (size_t i = d - 1; i > 0; --i) {
        uint64_t s = gen.step();
        size_t j = static_cast<size_t>(s % (i + 1));
        std::swap(perm[i], perm[j]);
    }

    // Create permuted input vector
    std::vector<int32_t> x_perm(d);
    for (size_t i = 0; i < d; ++i) {
        x_perm[i] = x_q[perm[i]];
    }

    // 4. Random projection matrix R in {-1, +1}^{m x d} and 1-bit binarization
    size_t n_bytes = static_cast<size_t>((m + 7) / 8);
    std::vector<uint8_t> packed_output(n_bytes, 0);

    for (int k = 0; k < m; ++k) {
        int64_t sum = 0;
        for (size_t j = 0; j < d; ++j) {
            uint64_t s = gen.step();
            // Mid-order bit (bit 32) exhibits exact 50.0% balance and zero autocorrelation
            int64_t val = static_cast<int64_t>(x_perm[j]);
            if ((s >> 32) & 1ULL) {
                sum += val;
            } else {
                sum -= val;
            }
        }

        // Binarize: bit = 1 if sum >= 0, else 0
        if (sum >= 0) {
            size_t byte_idx = static_cast<size_t>(k / 8);
            int bit_pos = 7 - (k % 8);
            packed_output[byte_idx] |= static_cast<uint8_t>(1 << bit_pos);
        }
    }

    return packed_output;
}

double hamming_distance(
    const uint8_t* a,
    size_t len_a,
    const uint8_t* b,
    size_t len_b,
    int m
) {
    if (len_a != len_b) {
        throw std::invalid_argument("Input byte lengths must match for Hamming distance calculation");
    }

    if (len_a == 0) {
        return 0.0;
    }

    int total_bits = (m > 0) ? m : static_cast<int>(len_a * 8);
    int diff_bits = 0;

    for (size_t i = 0; i < len_a; ++i) {
        uint8_t diff = a[i] ^ b[i];

        // Mask trailing unused bits in the final byte if m is not a multiple of 8
        if (i == len_a - 1 && (total_bits % 8 != 0)) {
            int valid_bits = total_bits % 8;
            uint8_t mask = static_cast<uint8_t>(0xFF << (8 - valid_bits));
            diff &= mask;
        }

        diff_bits += popcount8(diff);
    }

    return static_cast<double>(diff_bits) / static_cast<double>(total_bits);
}

bool has_cycle_within(
    uint64_t state,
    uint64_t r_param,
    uint64_t max_steps
) {
    ChaosGenerator gen(state, r_param);

    // Discard transient
    for (int i = 0; i < TRANSIENT_STEPS; ++i) {
        gen.step();
    }

    // Brent's cycle detection algorithm on generator state
    uint64_t power = 1;
    uint64_t lam = 1;
    ChaosGenerator tortoise = gen;
    ChaosGenerator hare = gen;
    hare.step();
    uint64_t total_steps = 1;

    while (!(tortoise == hare) && total_steps < max_steps) {
        if (power == lam) {
            tortoise = hare;
            power *= 2;
            lam = 0;
        }
        hare.step();
        lam++;
        total_steps++;
    }

    return (tortoise == hare);
}

std::vector<uint8_t> stream_matrix_bits(
    uint64_t state,
    uint64_t r_param,
    size_t n_bits
) {
    ChaosGenerator gen(state, r_param);

    for (int i = 0; i < TRANSIENT_STEPS; ++i) {
        gen.step();
    }

    size_t n_bytes = (n_bits + 7) / 8;
    std::vector<uint8_t> out(n_bytes, 0);

    for (size_t k = 0; k < n_bits; ++k) {
        uint64_t s = gen.step();
        if ((s >> 32) & 1ULL) {
            out[k / 8] |= static_cast<uint8_t>(1 << (7 - (k % 8)));
        }
    }

    return out;
}

} // namespace zkcambio

