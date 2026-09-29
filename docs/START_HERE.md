# START HERE: Building ZK-CaMBio in Antigravity (step by step)

Project: **Zero-Knowledge Cancelable Biometrics via Chaotic Hashing** (face + fingerprint, feature-level fusion, C++ chaotic transform, SQL + Docker, Streamlit, EER/ROC/CMC evaluation).

## 0. Two corrections before you start
1. **FVC2004 structure.** Your DVD readme shows each "a" set has 800 images = **100 fingers x 8 impressions**, and each "b" set has 80 images (10 fingers x 8). An earlier chat said "120 fingers x 12 impressions". That was wrong. Plan for 8 impressions per finger (5 enroll + 3 probe).
2. **"Hash" honesty.** A cryptographic hash (SHA-256) cannot do fuzzy matching, because one changed bit scrambles everything. So the "hash" in this project is a **key-dependent, chaos-driven, non-invertible, binarized template** matched by Hamming distance. Your paper should say this plainly. Also, a logistic map alone is not a proof of non-invertibility. Non-invertibility comes from dimensionality reduction + quantization (many-to-one) + a secret key, and you *demonstrate* it with reconstruction attacks (see EVALUATION_PLAN.md).

## 1. Install prerequisites
- Antigravity IDE (sign in, enable Claude + Gemini models in the model picker)
- Python 3.13, Git, Docker Desktop
- C++ toolchain: on Windows either **Visual Studio Build Tools (MSVC) + CMake** for native work, or **WSL2 (Ubuntu)** (then your data is at `/mnt/d/Biometric Project`). Pick one and tell the agent at preflight. Docker builds the C++ on Linux regardless.
- Kaggle account (already done)
- GPU is optional. Use Google Colab/Kaggle notebooks if the fingerprint CNN trains slowly.

## 2. Create the project folder
Your existing folder `D:\Biometric Project` is the project root. Keep it as is:
```
Biometric Project/
  AGENTS.md            <- already there (use the one from this pack)
  docs/                <- put ALL the other .md files here
  dataset/
    archive/                CelebA (no identity file yet)
    facial_dataset/         inspect first
    fingerprint_dataset/    FVC2004: DB1_A ... DB4_B
  data/processed/          <- generated later (git-ignored)
```
Run `git init` and add `dataset/`, `data/`, `*.tif`, `*.jpg` to `.gitignore`. The SFinGe installer files in your first folder are not needed; you can delete them.

**Do this before starting:** get `identity_CelebA.txt` from the official CelebA page (Anno section) and put it in `dataset/archive/`, unless `dataset/facial_dataset/` turns out to be a labelled face set such as UMDFaces. Either way the agent's Phase 1 inspection settles it. See `DATASET_PLAN.md`.

## 3. Open the folder in Antigravity and configure
- Open `zk-cambio/` as the workspace. Antigravity reads a root `AGENTS.md` (and `GEMINI.md`, which overrides it if present). Rules/workflows folders are also supported (`.agent/rules`, `.agent/workflows`). Check Settings if the folder name differs in your version.
- Optional: make `.agent/workflows/` files from the phase prompts in `WORKFLOW.md` so you can trigger them as slash commands.
- Keep the agent away from `data/`. It should never open raw image folders directly (token waste). Tell it to inspect via small scripts that print summaries.

## 4. Which model for what
| Job | Model |
|---|---|
| Architecture, C++ chaos engine, security/threat model, code review, paper text | Claude (Opus/Sonnet, whichever you have) |
| Scaffolding, Streamlit UI, Docker, boilerplate, multi-file edits | Gemini Pro |
| Tiny edits, renames, docstrings | Gemini Flash |

Rule of thumb: one agent writes, a *different* model reviews it (Phase gate in WORKFLOW.md).

## 5. Run the build
1. Open the **Agent Manager**, start a new conversation in **Planning** mode.
2. Paste the whole of `MASTER_PROMPT.md`.
3. The agent will read docs, ask **preflight questions** (dataset folder layout, GPU, OS), then produce a plan artifact. **Read and approve/edit the plan** before it writes code.
4. Execute **one phase at a time** using the prompts in `WORKFLOW.md` (Phase 0 to Phase 9). After each phase: run the acceptance checks in `DEVELOPMENT_PLAN.md`, commit, and update `CHANGELOG.md` / `DECISIONS.md`.
5. Do not let the agent skip ahead. The evaluation (Phase 5) must exist *before* the UI (Phase 7).

## 6. What "done" looks like
- `results/` holds EER table, ROC plot, CMC plot, score histograms, unlinkability and revocability plots, inversion-attack results
- Docker: `docker compose up` starts API + DB + Streamlit
- `docs/TRACEABILITY_REPORT.md` maps every requirement to code + test + result
- Paper outline in `docs/EVALUATION_PLAN.md` filled with real numbers

## 7. Optional stretch: the "zero-knowledge" part
Your project brief does not actually specify a ZK protocol. Core scope first. If time remains, add a small challenge-response/commitment layer (server never sees the template in the clear during authentication). Treat it as Phase 10 in `DEVELOPMENT_PLAN.md`, and state its limits honestly.

## Files in this pack
AGENTS, AGENT_RULES, PROJECT_MASTER, REQUIREMENTS, ARCHITECTURE, DATASET_PLAN, DATABASE, API_SPEC, SECURITY_THREAT_MODEL, EVALUATION_PLAN, UI_UX_SPEC, DEVELOPMENT_PLAN, WORKFLOW, DECISIONS, CHANGELOG, TRACEABILITY_REPORT, MASTER_PROMPT.
(Skipped from your screenshot list as irrelevant to a college project: PLAY_STORE_LISTING, PRIVACY_POLICY, AUTHORIZATION, SECURITY_SWEEP_REPORT, NFR_BENCHMARK_REPORT. Their useful parts are folded into other files.)
