# AGENT_RULES.md

## Session protocol
1. At session start read: `docs/PROJECT_MASTER.md`, `docs/DEVELOPMENT_PLAN.md` (current phase), `docs/DECISIONS.md`.
2. Work on **one phase at a time**. State the phase and its acceptance criteria before coding.
3. Ask a preflight question when information is missing. **Do not guess** paths, dataset layouts, or hyperparameters.
4. After each phase: run tests, update `CHANGELOG.md`, append to `DECISIONS.md` if a choice was made, update `TRACEABILITY_REPORT.md`.

## Hard rules
- **Subject-disjoint splits.** Encoder training identities never appear in evaluation. Split manifest is generated once with a fixed seed and saved to `data/processed/split_manifest.json` (with its SHA-256).
- **No raw biometric persistence.** Images and raw embeddings live in memory only during enrollment/verification. Never write them to DB, logs, or disk (except offline experiment caches under `data/processed/`, which are git-ignored and never used by the app).
- **No fake results.** Never invent metrics. Every number in docs comes from a script in `experiments/` that writes to `results/`.
- **Reproducibility.** Fixed seeds, pinned `requirements.txt`, deterministic C++ (same binary for enroll and verify), a known-answer test for the chaos engine.
- **Baseline first.** Unprotected fused system evaluated before the cancelable one.
- **No secrets in git.** Keys/seeds come from env vars or the DB key table, never source files.
- Do not open `dataset/` folders wholesale. Use scripts that print counts and 3 sample names.
- All dataset paths come from `configs/paths.yaml` (relative to project root, `pathlib`). Never hard-code `D:\` or `/mnt/d`.
- **Identity labels are never invented.** If the chosen face dataset lacks identity labels, stop and ask the user (see DATASET_PLAN.md).

## Code standards
Python 3.13, type hints, `ruff` + `pytest`. C++17, CMake, exposed to Python with pybind11 as module `chaoshash`. One module = one responsibility (see ARCHITECTURE.md). Every public function has a test.

## Definition of done (per phase)
Code + tests pass, acceptance criteria in DEVELOPMENT_PLAN met, docs updated, changes committed with message `phase-N: summary`.

## Review protocol
The reviewing model must read the diff and answer: (1) does it violate any hard rule? (2) does it meet acceptance criteria? (3) what is the weakest point? Output a short verdict.
