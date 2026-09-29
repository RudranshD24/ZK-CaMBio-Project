# CHANGELOG.md
Format: `## [phase-N] YYYY-MM-DD` then bullets Added / Changed / Fixed.

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

