# CHANGELOG.md
Format: `## [phase-N] YYYY-MM-DD` then bullets Added / Changed / Fixed.

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

