# ZK-CaMBio: Zero-Knowledge Cancelable Multimodal Biometrics

ZK-CaMBio is a cancelable multimodal biometric authentication system integrating deep facial recognition and convolutional fingerprint embeddings with an integer-quantized chaotic projection engine. 

> **Definition of Zero-Knowledge in ZK-CaMBio:**  
> The term "zero-knowledge" in this work denotes an architectural data-at-rest privacy guarantee: **zero raw biometric images, zero unquantized floating-point embeddings, and (in default `user_secret` mode) zero key material or passphrases are stored on the server**.  
> *Note on Cryptographic Scope:* No cryptographic zero-knowledge proof circuit (e.g., zk-SNARK / zk-STARK) is implemented.

---

## 1. System Requirements & Environment

- **Operating System:** Windows 10/11 x64, Linux (Ubuntu 22.04+), or macOS (ARM/x64).
- **Python Version:** Python 3.13 (or 3.11+).
- **C++ Compiler:** C++17 compliant compiler (MSVC 2019+ on Windows; GCC 11+ or Clang 14+ on Linux).
- **Container Runtime:** Docker Desktop / Docker Engine 24+ with Docker Compose v2.

---

## 2. Quickstart Installation

### 2.1 Clone and Set Up Virtual Environment

```bash
git clone https://github.com/organization/biometric-project.git
cd biometric-project

python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

### 2.2 Compile the Native C++ Chaos Engine

The chaotic projection engine requires `-ffp-contract=off` (or `/fp:precise` on MSVC) to eliminate non-deterministic fused multiply-add operations across CPU microarchitectures:

```bash
# Build native C++ pybind11 extension in-place:
python setup.py build_ext --inplace
```

To verify compilation:
```bash
python -c "import chaoshash; print('chaoshash loaded successfully!')"
```

---

## 3. Dataset Setup & Manifest Generation

Place the raw datasets into the `dataset/` directory according to the following layout:

```
dataset/
├── UMDFaces/
│   └── (subject directories containing .jpg face crops)
└── FVC2004/
    ├── DB1_A/ (101_1.tif ... 180_8.tif)
    ├── DB2_A/ (101_1.tif ... 180_8.tif)
    └── DB3_A/ (101_1.tif ... 180_8.tif)
```

### Dataset Citations and Licenses:
- **UMDFaces:** Bansal et al., *"UMDFaces: An Annotated Face Dataset for Facial Analysis,"* IEEE CVPR Workshops, 2017. Used strictly under academic research license.
- **FVC2004:** Maio, Maltoni, Cappelli, Wayman, Jain, *"FVC2004: Third Fingerprint Verification Competition,"* ICBA 2004. Standard benchmark fingerprint databases for research.

### Regenerate Manifest and Caches:
To rebuild the 300 virtual chimeric subjects split manifest and precompute embeddings caches:
```bash
# 1. Assemble chimeric manifest (180 train, 30 validation, 120 test subjects):
python src/data/build_manifest.py

# 2. Extract and cache face embeddings (InceptionResnetV1):
python src/face/extractor.py

# 3. Extract and cache fingerprint embeddings (FingerResNet18):
python src/finger/extractor.py

# 4. Extract and cache fused multimodal embeddings (w=0.60):
python src/fusion/extractor.py
```

---

## 4. Master Reproducibility Pipeline

All experiments and result artifacts (ROC curves, CMC curves, score distributions, and JSON metrics) can be reproduced sequentially from cached embeddings with a single command:

```bash
python scripts/reproduce_all.py
```

This master script runs:
1. `experiments/01_face_baseline.py` (Face recognition baseline)
2. `experiments/02_finger_baseline.py` (Fingerprint Gabor vs. ResNet18 baseline)
3. `experiments/03_fusion_baseline.py` (Multimodal feature & score fusion)
4. `experiments/04_chaos_smoke_eval.py` (Chaos engine property verification)
5. `experiments/05_cancelable_eval.py` (Cancelable evaluation: Scenario K/U, revocability, unlinkability)
6. `experiments/06_security_eval.py` (Security & non-invertibility evaluation under Threats A1, A2, A3)

Result checksums are tracked in `results/MANIFEST.md`.

---

## 5. Running Tests

Execute the comprehensive test suite (unit tests, security tests, schema whitelist checks, and UI smoke tests):

```bash
pytest tests/ -v
```

To run the Linux Known-Answer Test (KAT) inside Docker verifying cross-platform MSVC vs. GCC bit determinism:
```bash
docker compose exec -T api python tests/linux_kat_test.py
```

---

## 6. Docker Compose Deployment

ZK-CaMBio provides an isolated multi-service Docker deployment with three containers:
- `db`: PostgreSQL 16 Alpine (with Alembic migrations applied).
- `api`: FastAPI backend running Uvicorn with native C++ chaos engine.
- `ui`: Streamlit dashboard with strict architectural boundary isolation (no ML models or keys).

### Start Services:

```bash
# Copy example environment file:
cp .env.example .env

# Build and launch containers:
docker compose up -d --build
```

### Accessing the Applications:
- **Streamlit Web UI:** `http://localhost:8501`
- **FastAPI Documentation:** `http://localhost:8000/docs`
- **Database Port:** `localhost:5432`

### Check Service Health:
```bash
docker compose ps
```

---

## 7. Security Architecture & Threat Model

ZK-CaMBio is designed with defense in depth:
1. **Zero Raw Biometric Storage:** The SQL schema (`users`, `templates`, `user_keys`, `audit_log`) contains only 512-bit packed binary bitstrings and non-secret salts. Raw images and continuous embeddings are discarded immediately after feature extraction.
2. **Per-User Key Separation:** In `user_secret` mode, secrets are stretched with memory-hard `scrypt` ($N=16384, r=8, p=1, dklen=32$) and mixed with a per-user random 16-byte salt (`users.kdf_salt`) and `user_id` context. Two users with the same passphrase produce mutually orthogonal keys.
3. **Timing-Safe Authentication:** Authentication bearer tokens are compared using constant-time `hmac.compare_digest`.
4. **Score Suppression:** Numeric similarity scores and Hamming distances are returned only when `DEV_MODE=true` to prevent gradient-based hill-climbing attacks against the decision boundary.
5. **Database-Persisted Escalating Lockout:** Failed authentication attempts trigger exponentially increasing delays tracked per-username and per-IP in PostgreSQL. An attacker cannot permanently lock out a victim.
6. **Honest Inversion Disclosure:** Random projection binarization is **not** a one-way cryptographic hash. If the chaotic projection key leaks, linear decoders can invert templates with $0.9335$ cosine similarity. System security relies on key secrecy.
