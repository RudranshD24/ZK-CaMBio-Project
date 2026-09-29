# REQUIREMENTS.md
IDs are used in TRACEABILITY_REPORT.md. Priority: M = must, S = should, C = could.

## Functional
- FR-01 (M) Load and preprocess face and fingerprint images.
- FR-02 (M) Face embedding via pretrained network (512-d).
- FR-03 (M) Fingerprint embedding (Gabor baseline and/or ResNet18 metric learning).
- FR-04 (M) L2-normalize each modality, feature-level fusion by weighted concatenation.
- FR-05 (M) C++ chaotic engine: logistic-map-driven key-dependent projection + binarization -> binary template.
- FR-06 (M) Enrollment with N=5 samples per user (mean embedding).
- FR-07 (M) Verification (1:1) via Hamming distance and threshold.
- FR-08 (M) Identification (1:N), ranked list.
- FR-09 (M) Revocation: new key version, new template, old template invalidated.
- FR-10 (M) SQL storage of templates + key metadata only.
- FR-11 (M) Streamlit UI for enroll / verify / identify / revoke.
- FR-12 (S) Multi-sample enrollment quality check (reject blurry/no-face).
- FR-13 (C) Challenge-response ZK-style authentication layer.

## Evaluation
- EV-01 (M) EER, ROC, CMC for: face-only, finger-only, fused-unprotected, fused-cancelable.
- EV-02 (M) Three scenarios: legit key, stolen-key, wrong-key impostor.
- EV-03 (M) Unlinkability analysis; EV-04 (M) revocability analysis; EV-05 (M) inversion attacks.
- EV-06 (S) Ablation over template length m and fusion weights.

## Non-functional
- NFR-01 No raw biometrics persisted. NFR-02 Full reproducibility from seed. NFR-03 Enroll < 3 s, verify < 1 s on CPU (excluding model load). NFR-04 One-command Docker start. NFR-05 Tests for chaos engine determinism.
