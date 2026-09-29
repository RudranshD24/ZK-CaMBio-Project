# TRACEABILITY_REPORT.md
Fill this in during P9 from real files. Status: Not started / In progress / Done / Verified.

| Req | Code | Test | Result artifact | Status |
|---|---|---|---|---|
| FR-01 | src/data/ | tests/test_data.py | results/data_inspection.txt, data/processed/split_manifest.json | Verified |
| FR-02 | src/face/ | tests/test_face.py | results/face_eer.json, results/face_roc.png, results/face_cmc.png | Verified |
| FR-03 | src/finger/ | tests/test_finger.py | results/finger_eer.json, results/finger_roc.png, results/finger_cmc.png, results/finger_score_dist.png | Verified |

| FR-04 | src/fusion/ | tests/test_fusion.py | results/fused_unprotected.json | Not started |
| FR-05 | cpp/, src/chaos/ | cpp/tests, tests/test_chaos.py | results/cancelable_eer.json | Not started |
| FR-06..08 | src/api/ | tests/test_api.py | demo | Not started |
| FR-09 | src/api/ | tests/test_revoke.py | results/revocability.png | Not started |
| FR-10 | src/db/ | tests/test_schema_no_biometrics.py | - | Not started |
| FR-11 | src/ui/ | manual demo script | screenshots | Not started |
| EV-01 | experiments/ | - | results/roc.png, cmc.png, eer_table.md | Not started |
| EV-03 | experiments/ | - | results/unlinkability.png | Not started |
| EV-05 | experiments/ | - | results/inversion.json | Not started |
| NFR-01..05 | various | various | results/nfr.json | Not started |
