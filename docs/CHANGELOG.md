# CHANGELOG.md
Format: `## [phase-N] YYYY-MM-DD` then bullets Added / Changed / Fixed.

## [phase-2b] 2026-09-30
- Implemented robust fingerprint preprocessing pipeline (src/finger/preprocess.py): grayscale conversion, block-variance foreground segmentation & crop, CLAHE contrast enhancement, intensity normalization, and resizing to 128x128. Generated verification contact sheet results/finger_preproc_check.png.
- Created stratified seeded train/val split (src/finger/split.py) on the 180 train fingers: 150 fit / 30 val (50/10 per DB), strictly isolating test subjects.
- Implemented Baseline A (src/finger/gabor.py): classical Gabor filter-bank grid feature extractor (4 orientations, 8x8 grid AAD, 256-d, L2-normalized).
- Implemented Baseline B (src/finger/models.py, src/finger/train_resnet.py): FingerResNet18 fine-tuned with CosFace margin loss (s=30, m=0.35) on the 150 fit fingers (1,200 impressions) with early stopping on the 30 val fingers (stopped at epoch 6, best val separation 0.8668 at epoch 2, ~31-35s/epoch on CPU).
- Implemented feature extractor (src/finger/extractor.py) and cached 256-d embeddings for all 300 virtual subjects in data/processed/finger_embeddings_gabor.npz and data/processed/finger_embeddings_resnet.npz.
- Evaluated both baselines under Protocol D-009 (same-DB impostors only: 40 subjects/DB, 14,040 impostor comparisons pooled):
  - Baseline A (Gabor): Pooled EER = 41.08% (95% CI [38.67%, 43.32%]), Rank-1 (gallery 40) = 21.67%.
  - Baseline B (ResNet18): Pooled EER = 26.37% (95% CI [23.61%, 29.08%]), Rank-1 (gallery 40) = 37.22%.
  - Baseline B selected as primary fingerprint encoder (D-010), outperforming Gabor by +14.71% lower EER.
- Generated evaluation artifacts: results/finger_eer.json, results/finger_roc.png, results/finger_cmc.png, results/finger_score_dist.png, and raw score arrays (.npy).
- Added comprehensive unit tests in tests/test_finger.py verifying preprocessing, model outputs, split isolation, cache shapes, and baseline results (18 total tests passing).
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

