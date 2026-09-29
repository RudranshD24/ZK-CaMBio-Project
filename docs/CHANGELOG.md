# CHANGELOG.md
Format: `## [phase-N] YYYY-MM-DD` then bullets Added / Changed / Fixed.

## [phase-3] 2026-09-30
- Implemented feature-level and score-level multimodal biometric fusion (src/fusion/fuse.py, src/fusion/extractor.py):
  - Feature-level fusion concatenates $[\sqrt{w} f_{face}, \sqrt{1-w} f_{finger}]$ into 768-d unit-norm vectors, preserving inner-product linearity $\cos(fused) = w \cos_{face} + (1-w) \cos_{finger}$.
  - Grid search over $w \in [0.10, 0.90]$ strictly on the 30 validation subjects (Protocol D-009) identified a flat near-optimal plateau $w \in [0.50, 0.70]$ ($0.00\% - 0.18\%$ EER); selected $w=0.60$ (D-011).
  - Saved validation weight curve results/fusion_val_weight_tuning.png and test sensitivity plot results/fusion_test_weight_sensitivity.png (analysis only).
  - Score-level fusion (S3b) implemented with z-score normalization parameters fit on validation subjects.
  - Cached 768-d fused representations for all 300 virtual subjects in data/processed/fused_embeddings.npz.
- Evaluated systems S1, S2, S3, S3b on 120 test subjects under Protocol D-009 (same-DB impostors: 40 subjects/DB, 14,040 impostor comparisons pooled, 360 genuine trials):
  - S1 (Face): Pooled EER = 2.00% (95% CI [1.11%, 3.60%]), FNMR@1% = 3.33%, FNMR@0.1% = 9.44%, d' = 4.78, Rank-1 (G40) = 97.22%.
  - S2 (Finger): Pooled EER = 5.81% (95% CI [4.72%, 7.15%]), FNMR@1% = 26.67%, FNMR@0.1% = 68.06%, d' = 3.42, Rank-1 (G40) = 78.89%.
  - S3 (Fused Feature-Level): Pooled EER = 1.11% (95% CI [0.29%, 1.66%]), FNMR@1% = 1.11%, FNMR@0.1% = 1.94%, d' = 5.91, Rank-1 (G40) = 99.44%.
  - S3b (Fused Score-Level): Pooled EER = 1.10% (95% CI [0.28%, 1.67%]), FNMR@1% = 1.39%, FNMR@0.1% = 1.94%, d' = 5.92, Rank-1 (G40) = 99.17%.
  - Fused EER is 0.89 percentage points below the best single modality (Face 2.00%), representing a 44.5% relative error reduction. Rank-1 accuracy reached 99.44% (358/360 correct).
- Generated evaluation artifacts: results/fused_unprotected.json, results/fusion_roc.png, results/fusion_cmc.png, results/fusion_score_dist.png, and raw score arrays (.npy).
- Added comprehensive unit and integration tests in tests/test_fusion.py (all 24 tests passing).
- Updated TRACEABILITY_REPORT.md (FR-04 Verified, EV-01 partial) and DECISIONS.md (D-011).

## [phase-2b] 2026-09-30

- Implemented fingerprint preprocessing variant V2 (src/finger/preprocess.py) resolving scale inconsistency and sensor platen border artifacts:
  - Fixed physical scale factor per DB (DB1: scale 0.333, DB2: scale 0.50, DB3: scale 0.333) preserving spatial ridge frequency across impressions.
  - Centering on foreground centroid $(c_y, c_x)$ and fixed-window extraction.
  - DB2 tighter horizontal window ($42\le x\le 286$) centered at $x=164$ strictly eliminating slanted trapezoid borders and padding bars.
  - Constant pad value of 255 (background white) matching normalized background.
  - Retained V1 as fallback/comparison baseline.
  - Regenerated results/finger_preproc_check.png with 6 diverse impressions per DB (faint, standard, dark/contrast).
- Executed validation suite across the 30 validation fingers (experiments/02_run_val_experiments.py, results/finger_val_experiments.json):
  - Gabor V1: Val Sep = 0.0089, Val EER = 47.65%.
  - Gabor V2: Val Sep = 0.0129, Val EER = 44.01% (+44.4% separation improvement).
  - ResNet18 V1 (150 fit fingers): Val Sep = 0.6282, Val EER = 6.48%.
  - ResNet18 V2 (150 fit fingers): Val Sep = 0.6322, Val EER = 6.79%.
  - ResNet18 V2 + Extra Data (290 fingers: 150 fit + 100 DB4_A + 40 DB*_B, verified zero manifest overlap): Val Sep = 0.6414, Val EER = 5.49% (WINNER).
- Selected ResNet18 V2 + Extra Data as primary encoder strictly based on validation separation (D-010).
- Single test evaluation on the 120 test virtual subjects under Protocol D-009 (same-DB impostors: 40 subjects/DB, 14,040 impostors pooled):
  - Baseline A (Gabor V2): Pooled EER = 41.10% (95% CI [38.89%, 43.11%]), Rank-1 (gallery 40) = 26.67%.
  - Baseline B (ResNet18 V2 + Extra Data): Pooled EER = 5.81% (95% CI [4.72%, 7.15%]), Rank-1 (gallery 40) = 78.89%.
  - Per-DB ResNet18: DB1_A EER = 5.06% (Rank-1 75.83%), DB2_A EER = 8.50% (Rank-1 75.00%), DB3_A EER = 3.35% (Rank-1 85.83%).
- Generated evaluation artifacts: results/finger_eer.json, results/finger_roc.png, results/finger_cmc.png, results/finger_score_dist.png, and raw score arrays (.npy).
- Added unit tests in tests/test_finger.py (18 total tests passing across test suite).
- Updated TRACEABILITY_REPORT.md (FR-03 Verified), DECISIONS.md (D-009, D-010), and EVALUATION_PLAN.md.


## [phase-2a] 2026-09-30
- Evaluated face encoder candidates in throwaway venv on Python 3.13 / torch 2.14; resolved D-007 by adopting InceptionResnetV1 (VGGFace2 pretrained, 512-d).
- Implemented FaceEncoder (src/face/encoder.py) and batch feature extractor (src/face/extractor.py).
- Extracted and cached 512-d embeddings for all 300 virtual subjects in data/processed/face_embeddings.npz.
- Evaluated face recognition baseline on 120 test subjects (experiments/01_face_baseline.py); achieved 1.99% EER (95% CI [1.11%, 3.89%]) and 94.72% Rank-1 accuracy.
- Generated evaluation artifacts: results/face_eer.json, results/face_roc.png, results/face_cmc.png, results/face_score_dist.png, and raw score arrays.
- Added comprehensive unit tests in tests/test_face.py.

## [phase-1] 2026-09-30
- Added configs/paths.yaml with dataset, processed, and results paths (seed 42).
- Implemented and ran experiments/00_inspect_data.py to verify dataset file integrity, headers, and structure.
- Resolved D-005: selected dataset/facial_dataset/ (UMDFaces) with >= 20 images threshold; generated results/face_folder_check.png for visual verification.
- Implemented streaming loaders: src/data/face_loader.py and src/data/finger_loader.py (zero disk caching).
- Implemented src/data/pairing.py: created 300 virtual subjects (VS_0001..VS_0300) with 180 train / 120 test subject-disjoint split stratified 60/40 across FVC DB1_A, DB2_A, DB3_A.
- Generated canonical split manifest data/processed/split_manifest.json with SHA-256 bound under D-006.
- Added comprehensive unit tests (tests/test_data.py) verifying subject disjointness, stratification, enroll/probe non-overlap, and deterministic reproducibility.

## [phase-0] 2026-09-29
- Added project scaffolding, directory layout, Docker stubs, and .gitignore.
- Added pyproject.toml with ruff and pytest configuration.
- Installed Phase 0 and Phase 1 dependencies in .venv and pinned exact versions in requirements.txt from pip freeze.
- Implemented C++ pybind11 extension skeleton chaoshash with CMakeLists.txt and ping() stub.
- Built native chaoshash module using MSVC v18/v143 and verified ping() output.
- Added smoke tests (tests/test_smoke.py) and confirmed green pytest and ruff checks.

## [phase-docs] 2026-09-29
- Added documentation pack, master prompt, and phase workflow.
- Updated dataset paths to real layout (dataset/archive, facial_dataset, fingerprint_dataset), added face-source decision rule and Windows notes.

