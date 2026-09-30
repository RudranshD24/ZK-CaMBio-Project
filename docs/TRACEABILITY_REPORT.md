# TRACEABILITY_REPORT.md
Fill this in during P9 from real files. Status: Not started / In progress / Done / Verified.

| Req | Code | Test | Result artifact | Status |
|---|---|---|---|---|
| FR-01 | src/data/ | tests/test_data.py | results/data_inspection.txt, data/processed/split_manifest.json | Verified |
| FR-02 | src/face/ | tests/test_face.py | results/face_eer.json, results/face_roc.png, results/face_cmc.png | Verified |
| FR-03 | src/finger/ | tests/test_finger.py | results/finger_val_experiments.json, results/finger_eer.json, results/finger_roc.png, results/finger_cmc.png, results/finger_score_dist.png, results/finger_preproc_check.png | Verified |


| FR-04 | src/fusion/ | tests/test_fusion.py | results/fused_unprotected.json, results/fusion_roc.png, results/fusion_cmc.png, results/fusion_score_dist.png, results/fusion_val_weight_tuning.png, results/fusion_test_weight_sensitivity.png, data/processed/fused_embeddings.npz | Verified |
| FR-05 | cpp/, src/chaos/ | tests/test_chaos.py | results/cancelable_summary.md, results/cancelable_eer.json, results/cancelable_roc.png, results/cancelable_cmc.png, results/cancelable_val_m_selection.png, results/cancelable_scenario_u_dist.png | Verified |
| FR-06..08 | src/api/ | tests/test_api.py | demo | Not started |
| FR-09 | src/api/, experiments/ | tests/test_chaos.py | results/cancelable_revocability_dist.png (100% rejection under revoked key; API endpoint in Phase 7) | Verified (partial/evaluation complete) |
| FR-10 | src/db/ | tests/test_schema_no_biometrics.py | - | Not started |
| FR-11 | src/ui/ | manual demo script | screenshots | Not started |
| EV-01 | experiments/ | tests/test_fusion.py, tests/test_chaos.py | results/fused_unprotected.json, results/cancelable_summary.md, results/cancelable_eer.json, results/cancelable_roc.png, results/cancelable_cmc.png | Verified |
| EV-02 | experiments/ | tests/test_chaos.py | results/cancelable_revocability_dist.png (FNMR=100.0% under revoked key, restored to 1.67%) | Verified |
| EV-03 | experiments/ | - | results/cancelable_unlinkability.png (D_sys = 0.0125 << 0.10) | Verified |
| EV-04 | experiments/ | - | results/cancelable_scenario_u_dist.png (EER = 0.0000%, cross-key imp mean HD = 0.5001) | Verified |
| EV-05 | experiments/ | - | results/inversion.json | Not started |
| NFR-01..04 | various | various | results/nfr.json | Not started |
| NFR-05 | cpp/, src/chaos/ | tests/test_chaos.py | results/chaos_val_smoke.json (5.22 ms/transform latency, KAT bit-exact determinism) | Verified |
