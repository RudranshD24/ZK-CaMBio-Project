# TRACEABILITY_REPORT.md
Fill this in during P9 from real files. Status: Not started / In progress / Done / Verified.

| Req | Code | Test | Result artifact | Status |
|---|---|---|---|---|
| FR-01 | src/data/ | tests/test_data.py | results/data_inspection.txt, data/processed/split_manifest.json | Verified |
| FR-02 | src/face/ | tests/test_face.py | results/face_eer.json, results/face_roc.png, results/face_cmc.png | Verified |
| FR-03 | src/finger/ | tests/test_finger.py | results/finger_val_experiments.json, results/finger_eer.json, results/finger_roc.png, results/finger_cmc.png, results/finger_score_dist.png, results/finger_preproc_check.png | Verified |


| FR-04 | src/fusion/ | tests/test_fusion.py | results/fused_unprotected.json, results/fusion_roc.png, results/fusion_cmc.png, results/fusion_score_dist.png, results/fusion_val_weight_tuning.png, results/fusion_test_weight_sensitivity.png, data/processed/fused_embeddings.npz | Verified |
| FR-05 | cpp/, src/chaos/ | tests/test_chaos.py | results/chaos_val_smoke.json, results/chaos_hd_vs_angle.png, results/chaos_val_hamming_hist.png | In progress (Phase 4 engine complete, smoke verified) |
| FR-06..08 | src/api/ | tests/test_api.py | demo | Not started |
| FR-09 | src/api/ | tests/test_revoke.py | results/revocability.png | Not started |
| FR-10 | src/db/ | tests/test_schema_no_biometrics.py | - | Not started |
| FR-11 | src/ui/ | manual demo script | screenshots | Not started |
| EV-01 | experiments/ | tests/test_fusion.py | results/fused_unprotected.json, results/fusion_roc.png, results/fusion_cmc.png (S1-S3 baselines complete) | In progress |
| EV-03 | experiments/ | - | results/unlinkability.png | Not started |
| EV-05 | experiments/ | - | results/inversion.json | Not started |
| NFR-01..04 | various | various | results/nfr.json | Not started |
| NFR-05 | cpp/, src/chaos/ | tests/test_chaos.py | results/chaos_val_smoke.json (5.22 ms/transform latency, KAT bit-exact determinism) | Verified |
