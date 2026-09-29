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
Input: fused vector x in R^d, key (x0 in (0,1), r in [3.9, 4.0), salt), output length m < d.
1. Derive (x0, r) from key material using a keyed hash (SHA-256 / HMAC), so the user seed is never used directly.
2. Iterate x_{n+1} = r * x_n * (1 - x_n). Discard the first 1000 iterations (transient).
3. Post-process chaotic samples to near-uniform / Gaussian (the logistic map at r near 4 has an arcsine distribution, so apply the correction) and build a m x d **random projection matrix** R_K, plus a key-dependent **permutation** of x.
4. y = R_K * perm(x). Then **binarize** with sign(y - median-free zero threshold). Output m bits.
5. Non-invertibility: m < d (information loss) plus 1-bit quantization (many-to-one) plus secret key.
Determinism: use double precision with a fixed operation order, compile identical flags, and expose one function to Python via pybind11 so enroll and verify run the same code. Add a known-answer test (fixed key + fixed vector -> fixed bit string hash).

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

## Deployment
`docker compose`: `db` (postgres), `api` (FastAPI + built chaoshash), `ui` (Streamlit). Model weights mounted as a volume.

## Memory hygiene
Images -> embeddings -> fused vector -> template happen inside one request handler; only the template is persisted. Python cannot guarantee zeroing memory, so the docs claim "not persisted", not "cryptographically erased".
