# DEVELOPMENT_PLAN.md
Mark each phase `[ ]` -> `[x]` when acceptance is met.

- [ ] **P0 Setup**: repo layout, venv, requirements, pre-commit (ruff), pytest, CMake skeleton, Docker skeleton. *Accept*: `pytest` runs; `cmake --build` succeeds.
- [ ] **P1 Data**: `configs/paths.yaml`, inspect script, **face-source decision (D-005)**, loaders, pairing, split manifest. *Accept*: inspection report saved; identity labels confirmed (or agent stopped and asked); manifest exists; subject-disjoint test asserted; 300 VS = 180 train / 120 test, stratified by fingerprint DB.
- [ ] **P2 Encoders**: face embedding (pretrained), fingerprint embedding (Gabor baseline first, then ResNet18 metric learning on train split). *Accept*: embeddings cached for all subjects; per-modality EER computed on test.
- [ ] **P3 Fusion baseline (S1-S3)**: normalization, concat, weight tuning on train. *Accept*: fused EER < best single-modality EER (or explain why not).
- [ ] **P4 Chaos engine (C++)**: logistic map, projection, permutation, binarization, pybind11, known-answer + determinism tests, key derivation. *Accept*: tests green; same output across two builds/runs.
- [ ] **P5 Cancelable evaluation (S4-S6)**: EER/ROC/CMC, revocability, unlinkability, ablations. *Accept*: all plots in `results/`.
- [ ] **P6 Security experiments**: inversion + NN attacks. *Accept*: numbers + written interpretation.
- [ ] **P7 Backend + DB + Docker**: FastAPI, SQLAlchemy, Alembic, compose. *Accept*: `docker compose up`, API tests pass, DB has no biometric data (test asserts schema).
- [ ] **P8 Streamlit UI**: pages per UI_UX_SPEC. *Accept*: manual demo script works end to end.
- [ ] **P9 Paper + viva**: fill paper skeleton, TRACEABILITY_REPORT complete, slides.
- [ ] **P10 (Optional) ZK-style challenge-response layer**.

## Rough timeline (adjust to your deadline)
P0-P1: 2 days | P2-P3: 4 days | P4: 3 days | P5-P6: 4 days | P7-P8: 4 days | P9: 3 days.
