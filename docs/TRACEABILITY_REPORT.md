# TRACEABILITY_REPORT.md

| Req | Code | Test | Result artifact | Status |
|---|---|---|---|---|
| FR-01 | src/data/ | tests/test_data.py | results/data_inspection.txt, data/processed/split_manifest.json | Verified |
| FR-02 | src/face/ | tests/test_face.py | results/face_eer.json, results/face_roc.png, results/face_cmc.png | Verified |
| FR-03 | src/finger/ | tests/test_finger.py | results/finger_val_experiments.json, results/finger_eer.json, results/finger_roc.png, results/finger_cmc.png, results/finger_score_dist.png, results/finger_preproc_check.png | Verified |
| FR-04 | src/fusion/ | tests/test_fusion.py | results/fused_unprotected.json, results/fusion_roc.png, results/fusion_cmc.png, results/fusion_score_dist.png, results/fusion_val_weight_tuning.png, results/fusion_test_weight_sensitivity.png, data/processed/fused_embeddings.npz | Verified |
| FR-05 | cpp/, src/chaos/ | tests/test_chaos.py | results/cancelable_summary.md, results/cancelable_eer.json, results/cancelable_roc.png, results/cancelable_cmc.png, results/cancelable_val_m_selection.png, results/cancelable_scenario_u_dist.png | Verified |
| FR-06 | src/api/ | tests/test_api.py | FastAPI /enroll (5-face + 5-finger multipart, scrypt key stretching >=8 chars, template bit-packing) | Verified |
| FR-07 | src/api/ | tests/test_api.py | FastAPI /verify (1:1 matching, score suppression hill-climbing defense, DB-backed escalating delay lockout) | Verified |
| FR-08 | src/api/ | tests/test_api.py | FastAPI /identify (1:N matching restricted to server_key accounts, score suppression, rank-only reporting) | Verified |
| FR-09 | src/api/, experiments/ | tests/test_api.py, tests/test_chaos.py | FastAPI /revoke (key rotation, active template timestamping; FNMR=100.0% under revoked key) | Verified |
| FR-10 | src/db/ | tests/test_schema_no_biometrics.py | SQLAlchemy 2 + Alembic schema whitelist (users, templates, user_keys, audit_log, auth_rate_limits): zero raw biometrics, embeddings, or secrets | Verified |
| FR-11 | src/ui/ | tests/test_ui.py (AppTest) | Streamlit dashboard (Enroll, Verify, Identify, Revoke, Results, Threat demo; zero model imports), docs/DEMO_SCRIPT.md, docs/screenshots/ | Verified |
| FR-12 | src/api/service.py | tests/test_api.py | Recalibrated on 30 validation subjects (tau_face=0.45, tau_finger=0.60, >=3 consistent samples rule); 0.00% test FRR across all 120 test subjects | Verified |
| EV-01 | experiments/ | tests/test_fusion.py, tests/test_chaos.py | results/fused_unprotected.json, results/cancelable_summary.md, results/cancelable_eer.json, results/cancelable_roc.png, results/cancelable_cmc.png | Verified |
| EV-02 | experiments/ | tests/test_chaos.py | results/cancelable_revocability_dist.png (FNMR=100.0% under revoked key, restored to 1.67%) | Verified |
| EV-03 | experiments/ | tests/test_security.py | results/cancelable_unlinkability.png (D_sys = 0.0245 << 0.10 score-only without keys; D_sys = 0.9649 under A3 with keys known) | Verified |
| EV-04 | experiments/ | - | results/cancelable_scenario_u_dist.png (EER = 0.0000%, cross-key imp mean HD = 0.5001) | Verified |
| EV-05 | experiments/ | tests/test_security.py | results/security_summary.md, results/security_eval.json, results/privacy_utility_tradeoff.png (Atk-2 Ridge cos=0.9335, 100% replay @ m=512) | Verified |
| EV-06 | scripts/benchmark_latency.py, experiments/ | tests/test_chaos.py, tests/test_api.py | results/chaos_val_smoke.json (transform time 3.95 ms/op), scripts/benchmark_latency.py (Docker verify latency 0.3698 s) | Verified |
| FR-13 | - | - | Zero-Knowledge cryptographic proof (zk-SNARK/STARK circuit verification for template matching). **NOT IMPLEMENTED**: The system achieves template protection through cancelable randomized projection and zero server-side secret/biometric storage, but does not construct a zero-knowledge cryptographic proof circuit. | Not Implemented |
| NFR-01 | src/db/, src/api/ | tests/test_schema_no_biometrics.py, tests/test_api.py | No raw biometrics, float embeddings, or secrets stored on server or in logs; timing-safe bearer auth | Verified |
| NFR-02 | src/db/, src/api/ | tests/test_api.py | DB-backed per-username and per-IP escalating delay lockout; victim cannot be permanently locked out | Verified |
| NFR-03 | src/api/ | tests/test_api.py, scripts/benchmark_latency.py | CPU latency with scrypt on live Docker container: verify mean = 0.3698 s (< 1.0 s threshold, PASS), enroll mean = 0.6095 s | Verified |
| NFR-04 | docker/ | tests/run_linux_kat.sh, tests/linux_kat_test.py | Multi-stage Docker build with Linux container KAT parity matching Windows hashes (server_key: 2d8998aa, user_secret: 9ed1a9ad) | Verified |
| NFR-05 | cpp/, src/chaos/ | tests/test_chaos.py | results/chaos_val_smoke.json (3.95 ms/transform latency, KAT bit-exact determinism) | Verified |

