# ARCHITECTURE.md

## Pipeline
```
face img --> detect/align --> ArcFace/FaceNet emb (512) --\
                                                           L2 norm each -> weight -> concat (d) --> [PCA optional]
fingerprint img --> enhance/crop --> emb (256-512) -------/                                           |
                                                                                                       v
                                  user key K_v (secret seed) --> C++ chaos engine --> binary template B (m bits)
                                                                                                       |
                               enroll: store B + key metadata     verify: Hamming(B_probe, B_stored) < tau
```

## Chaos engine (C++17, `chaoshash`)
Fully integer fixed-point pipeline for cross-platform determinism across Windows (MSVC) and Linux (g++):

1. **Key Derivation (Python)**:
   - Key derivation is performed in Python using HMAC-SHA256:
     `HMAC-SHA256(master_key [32 bytes], "zkcambio|" + app_salt + "|v" + key_version)`
   - The 32-byte digest is split into two 64-bit unsigned integers:
     - `state`: 64-bit initial state $x_0 \in (0, 1)$ represented as Q64 fixed-point ($x_0 = \text{state} / 2^{64}$).
     - `r_param`: mapped to map parameter $r \in [3.9, 4.0)$ via $r/4 = R_{MIN} + (r_{param} \pmod{R_{SPAN}})$ where $R_{MIN} = 0.975 \times 2^{64}$.
   - No cryptographic libraries exist in the C++ layer.

2. **Fixed-Point Q64 Logistic Map & Cycle Guard (C++)**:
   - Iteration: $x_{n+1} = 4 \cdot (r/4) \cdot x_n \cdot (1 - x_n)$ implemented using portable 64x64 unsigned multiplication (`mul64_high`) using four 32-bit half multiplications (MSVC/GCC compatible, no `__int128` requirement).
   - Degenerate state & cycle protection: An 8192-entry direct-mapped cache tracks recently visited states. If $x_{n+1} = 0$, $x_{n+1} = x_n$, or $x_{n+1} = \text{cache}[\text{hash}(x_{n+1})]$, a degenerate state or periodic cycle is detected and reseeded deterministically:
     `next_x ^= (GOLDEN_RATIO_64 + reseed_count * 0x517cc1b727220a95ULL)`.
   - The first 1,000 iterations are discarded (transient warmup into the chaotic attractor).

3. **Key-Dependent Permutation & Projection**:
   - **Permutation**: Coordinate index shuffle of $d=768$ dimensions via Fisher-Yates shuffle where swap index $j = \text{step}() \pmod{i+1}$.
   - **Rademacher Projection Matrix**: Entries $R_{k, j} \in \{+1, -1\}$ sampled from bit 32 of the chaotic state:
     - Bit choice rationale: While the MSB (bit 63) is slightly asymmetric due to $r < 4.0$, intermediate fractional bits (specifically bit 32) undergo rapid Bernoulli-shift mixing, exhibiting exact 50.0% bit balance, zero lag-1..10 autocorrelation ($|\rho| < 0.003$), and passing chi-square uniformity ($p > 0.05$).

4. **Quantization & Template Generation**:
   - **Centering**: Public train mean $\mu$ (computed strictly on 180 train subjects, stored in `data/processed/chaos_mean_vector.npy`) is subtracted: $\tilde{x} = x - \mu$.
   - **Quantization**: $\tilde{x}$ is scaled by fixed factor $S = 2^{20} = 1,048,576$ and rounded to `int32_t`. (Rationale: Preserves 6 decimal digits of unit vectors, guarantees $\max |x_q| \approx 2^{21}$, and accumulated dot products over $d=768$ bounded by $\approx 1.6 \times 10^9$, never overflowing `int64_t`).
   - **Accumulation & Binarization**: $y_k = \sum_{j=0}^{d-1} R_{k, j} \tilde{x}_{\pi(j)}$ accumulated in `int64_t`.
   - Output bit $b_k = 1$ if $y_k \ge 0$, else $0$. Bits are packed MSB-first into $\lceil m / 8 \rceil$ uint8 bytes.

5. **Compiler Flags**:
   - MSVC: `/fp:strict` (strict floating-point model).
   - GCC/Clang: `-ffp-contract=off`.

6. **Engine Limitations & Disclosures**:
   - **Key Space Bound**: The effective chaotic parameter space is bounded by the derived 64-bit state and 64-bit parameter size ($2^{128}$ theoretical states), though the master key is 256 bits.
   - **Not a Proven CSPRNG**: The logistic map is a deterministic dynamical system, not a cryptographically proven pseudorandom generator (such as ChaCha20 or AES-CTR). It is used here specifically for cancelable biometric projection with angle-preserving metric properties.
   - **Non-Invertibility Argument**: Non-invertibility is argued through information loss via dimension reduction ($m < d$, e.g., $512 < 768$), non-linear 1-bit quantization (infinite-to-one sign mapping), and a secret key. This is an information-theoretic argument; empirical pre-image resistance and inversion attacks will be tested empirically in Phase 6 (no mathematical proof is claimed).

### Build commands (Windows native)
Ensure `.venv` is created and dependencies are installed (`pip install -e .`):
```powershell
# Configure CMake with active Python venv and pybind11
cmake -B cpp/build -S cpp -A x64 -DPYTHON_EXECUTABLE=".venv/Scripts/python.exe" -Dpybind11_DIR=".venv/Lib/site-packages/pybind11/share/cmake/pybind11"

# Compile and link Release extension (.pyd placed in src/chaos/ and copied to src/)
cmake --build cpp/build --config Release
```


## Services / modules
| Module | Path | Responsibility |
|---|---|---|
| data | `src/data/` | UMDFaces + FVC loaders, pairing, split manifest |
| face | `src/face/` | detection, alignment, embedding |
| finger | `src/finger/` | enhancement, embedding (Gabor / ResNet18) |
| fusion | `src/fusion/` | normalization, weighting, concat |
| chaos | `cpp/` + `src/chaos/` | C++ engine + Python wrapper |
| api | `src/api/` | FastAPI: enroll, verify, identify, revoke |
| db | `src/db/` | SQLAlchemy models, migrations |
| ui | `src/ui/` | Streamlit app (calls API only) |
| experiments | `experiments/` | evaluation scripts, write `results/` |

## Repo layout
```
Biometric Project/   (project root)
  configs/paths.yaml  dataset/ (git-ignored)  data/processed/ (git-ignored)
  cpp/ (CMakeLists.txt, chaos.cpp, chaos.hpp, bindings.cpp, tests/)
  src/  experiments/  tests/  results/  docs/  data/
  docker/ (Dockerfile.api, Dockerfile.ui)  docker-compose.yml
```

## Deployment & Multi-Stage Docker Architecture
- **Docker Compose**: Orchestrates `db` (PostgreSQL 16 Alpine with healthchecks), `api` (FastAPI backend with native Linux-compiled `chaoshash`), and `ui` (Streamlit dashboard communicating over internal network).
- **Multi-Stage Build (`docker/Dockerfile.api`)**:
  - *Stage 1 (`builder`)*: Uses `python:3.13-slim` + `g++` to compile `cpp/chaos.cpp` and `cpp/bindings.cpp` into `chaoshash.so` using `-O3 -Wall -shared -std=c++17 -fPIC -ffp-contract=off`.
  - *Stage 2 (`runtime`)*: Minimal `python:3.13-slim` runtime image copying the compiled `.so` library, application code, cached model weights (`models/`), versioned public parameters (`configs/biometric_parameters.json`), and Alembic migrations.
- **Cross-Platform Known-Answer Parity**:
  - The Linux container build was validated against the reference MSVC output using `tests/run_linux_kat.sh`.
  - Both MSVC (Windows x86_64) and GCC 12+ (Linux x86_64) produce the identical 64-bit KAT template hash: `83ec0508`.

## Backend Model Service & Public Parameters
- Encoders (VGGFace2 ResNet-50 and Fingerprint ResNet-18 V2) are initialized once at application startup into the singleton `BiometricService`.
- Model weights are pre-cached in `models/` to ensure offline, air-gapped Docker startup without external network downloads.
- Public parameters ($d=768, m=512, w=0.60, \mu \in \mathbb{R}^{768}$) are loaded from `configs/biometric_parameters.json` and validated at startup against an integrity SHA-256 checksum (`ded6e0b1163b7615a2c1895203fa73ba322d720e18c4858fd82413910671acaf`).

## Key Derivation & Mode Isolation (ADR D-016)
- **`user_secret` Mode (Default)**:
  - User presents PIN/secret on every request; server computes HMAC-SHA256 in volatile RAM and immediately discards it.
  - Zero key material is stored on the server.
  - Verification only; 1:N `/identify` is rejected by design to prevent unkeyed database scans.
- **`server_key` Mode (Opt-in)**:
  - System derives and encrypts a 256-bit key using AES-256-GCM under `SERVER_MASTER_KEY`.
  - Enables 1:N identification across enrolled active templates.

## Memory Hygiene & Anti-Leakage
- Images -> tensors -> embeddings -> fused vectors -> binary template occur entirely in-memory within the scope of a single request.
- Every endpoint wraps processing in `try ... finally` blocks triggering `gc.collect()`.
- Database schema whitelist tests ([test_schema_whitelist_no_raw_biometrics](file:///D:/Biometric%20Project/tests/test_schema_no_biometrics.py)) statically inspect all tables to assert zero columns can store raw image bytes, floating-point vectors, or plaintext credentials.
- The documentation explicitly notes that Python memory management does not guarantee cryptographic zeroization of RAM, but guarantees zero disk persistence.

