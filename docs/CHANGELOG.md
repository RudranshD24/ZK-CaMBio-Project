# CHANGELOG.md
Format: `## [phase-N] YYYY-MM-DD` then bullets Added / Changed / Fixed.

## [phase-6] 2026-09-30
- Phase 5 Follow-Ups Completed:
  - Wording updated across evaluation documentation: replaced "cryptographic isolation" with "key separation"; qualified "full unlinkability" as "unlinkable against a score-based adversary WITHOUT key access"; renamed Scenario K as "claimed-identity key (operational; equals stolen-key case)" and Scenario U as "attacker presents own key/token (best case)".
  - Grounded operating thresholds strictly on 30 validation subjects: $\tau_{oper, eer} = 0.3504$ and $\tau_{oper, 0.1\%} = 0.3010$, achieving 100.00% rejection on revoked keys under both thresholds.
  - Re-evaluated unlinkability with cross-sample pairs ($e_i$ under key 1 vs $p_{i, k}$ under key 2) confirming score-only $D_\leftrightarrow^{sys} = 0.0245 \ll 0.10$.
  - Reported paired bootstrap CIs (1,000 resamples, seed 42) for $\Delta\text{FNMR@1\%} = +0.276\%$ (95% CI $[-0.333\%, +1.167\%]$, excludes 0: False) and $\Delta\text{FNMR@0.1\%} = +1.311\%$ (95% CI $[+0.333\%, +2.722\%]$, excludes 0: True).
  - Extended Hamming-vs-angle plot to include genuine pairs down to $\theta/\pi \sim 0.15$ (slope=1.0084, intercept=-0.0040, $r=0.9849$, $\text{MAE}=0.0170$).
- Phase 6 Security & Non-Invertibility Evaluations (Protocol D-015):
  - Strict attacker training data isolation: 180 TRAIN subjects only (1440 face & 1440 finger per-image embeddings paired into 10,000 synthetic fused vectors); verified zero test-subject leakage in unit tests.
  - Verified Atk-1 back-projection sanity test on Gaussian unit vectors against theoretical formula $\frac{\sqrt{2/\pi} m}{\sqrt{(2/\pi)m^2 + dm}}$ within 0.0006 ($\le 0.03$).
  - Implemented and evaluated inversion attack suite across $m \in \{64, 128, 256, 512, 768, 1024\}$ on 120 test victims under threat case A2 (key known):
    - Linear decodability (Atk-2 Ridge regression) achieves $\cos(\hat{x}, x) = 0.9335 \pm 0.0115$ at $m=512$ ($0.6344$ at $m=64$, $0.7763$ at $m=128$, $0.8745$ at $m=256$, $0.9522$ at $m=768$, $0.9614$ at $m=1024$).
    - Replay success against unprotected S3 matcher: 100.0% at $m=512$ under both FMR=1.0% and FMR=0.1% pre-fixed validation thresholds (vs 0.0% for random Gaussian baseline).
    - Single-modality replay success at $m=512$: 100.0% vs face-only, 100.0% vs finger-only.
  - Evaluated threat case A3 (linkage attack with both keys known):
    - Linkage ROC AUC = 0.9980, EER = 1.63%, and ISO/IEC 30136 $D_\leftrightarrow^{sys} = 0.9649$ (surging from score-only $0.0245$). Disclosed that unlinkability does NOT survive key compromise.
  - Evaluated threat case A1 (template-only, key unknown):
    - Key-space accounting: 256-bit master key $\to 2^{126}$ operations ($> 10^{22}$ GPU-years).
    - Template distinguisher classifier on subject A vs subject B under random keys achieves 5-fold CV AUC of 0.4767 (chance level ~0.50), proving zero identity leakage without the key.
  - Generated privacy-utility trade-off curve `results/privacy_utility_tradeoff.png`, `results/security_eval.json`, and `results/security_summary.md`.
  - Added "What non-invertibility means here" section and Phase 7 key-store separation / 2FA mitigations to `docs/SECURITY_THREAT_MODEL.md`.

## [phase-5] 2026-09-30
- Phase 4 Follow-Ups & Sanity Checks:
  - Computed Hamming-vs-angle linear regression and MAE on centered vectors $\tilde{u} = u - \mu$: slope=1.0219, intercept=-0.0109, $r=0.8789$, MAE=0.0176 for $m=512$; slope=1.0197, intercept=-0.0101, $r=0.9127$, MAE=0.0144 for $m=768$. Regenerated `results/chaos_hd_vs_angle.png`.
  - Verified population bit balance on 180 train subjects: 0.0% (0 / 512) outside $[0.3, 0.7]$; global mean bit value = 0.5001.
  - Reported unprotected S3 Val EER (0.000%) next to Scenario K Val EER (0.784% $\pm$ 0.642%), disclosing that 90 genuine trials have 1.11% discrete resolution and cannot support statistical claims.
  - Recorded Docker CLI status (unavailable on host PATH) as a required Phase 7 acceptance check; confirmed KAT bit string hex hash saved in tests (`83ec0508a8d11c75`).
  - Added integer overflow and quantization sanity test `test_quantization_and_accumulator_bounds` in `tests/test_chaos.py` (max $|x_q| = 175,011 \ll 2^{31}-1$; 0 clipped coordinates across all 300 subjects / 2,700 vectors).
- Parameter Selection of $m$ on Validation Data (Step 1, D-014):
  - Evaluated $m \in \{64, 128, 256, 512, 768, 1024\}$ on 30 validation subjects across 10 random keys (Scenario K).
  - Best $m=1024$ (Val EER = 0.654% $\pm$ 0.430%, 1-SD threshold = 1.084%).
  - Selected $m=512$ as the smallest $m$ within 1 SD of best (Val EER = 0.852% $\pm$ 0.398% $\le 1.084\%$). Saved `results/cancelable_val_m_selection.png`.
- Headline Performance Preservation Benchmark (Scenario K, Steps 2 & 3):
  - Evaluated on 120 test subjects across 10 fixed random master keys with chosen parameters ($w=0.60, m=512$):
    - Pooled EER: $1.29\% \pm 0.23\%$ (vs unprotected S3 1.11%).
    - FNMR @ 1% FMR: $1.47\% \pm 0.31\%$ (vs unprotected S3 1.11%).
    - FNMR @ 0.1% FMR: $3.19\% \pm 0.79\%$ (vs unprotected S3 1.94%).
    - Decidability $d': 5.29$ (vs unprotected S3 5.91).
    - Fair gallery-40 Rank-1 accuracy: $98.81\% \pm 0.31\%$ (DB1: 98.42%, DB2: 98.00%, DB3: 100.00%).
    - Paired bootstrap over test subjects (1000 resamples): $\Delta\text{EER} = +0.213\%$ (95% CI $[-0.135\%, +0.688\%]$). Excludes 0? False (performance degradation is statistically indistinguishable from zero). 360 genuine trials = 0.28% discrete resolution.
    - Saved raw scores `results/scenario_k_gen_scores.npy`, `results/scenario_k_imp_scores.npy`, and comparison curves `results/cancelable_roc.png`, `results/cancelable_cmc.png`.
- Scenario U Cryptographic Isolation (Step 4):
  - Evaluated unique per-user keys yielding EER = 0.0000% and cross-key impostor mean HD = $0.5001 \pm 0.0222$. Saved `results/cancelable_scenario_u_dist.png` (explicitly disclaimed as NOT an accuracy measure).
- Revocability Evaluation (Step 5, ISO/IEC 30136):
  - Evaluated across 5 key versions per test subject. Genuine probes against templates enrolled under revoked keys yielded mean HD = 0.5018 and FNMR = 100.00% (100% rejection at $\tau=0.350$). Re-enrollment under new key restored FNMR to 1.67%. Saved `results/cancelable_revocability_dist.png`.
- Unlinkability Evaluation (Step 6, ISO/IEC 30136):
  - Evaluated Gomez-Barrero mated vs non-mated cross-key score distributions. Multi-system cancelable benchmark achieved global $D_\leftrightarrow^{\text{sys}} = 0.0125$ ($\ll 0.10$ threshold, full unlinkability). Reused key counterexample yielded $D_\leftrightarrow^{\text{sys}} = 0.9827$. Saved `results/cancelable_unlinkability.png`.
- Ablations & Analysis (Step 7):
  - Validation weight grid confirmed $w=0.60$ is optimal ($0.833\%$ EER).
  - Test modality cancelable EERs: Face-only 2.73%, Finger-only 5.98%, Fused 1.08%, proving multimodal fusion gain is preserved under chaotic protection.
  - Generated test-set $m$-sensitivity curve `results/cancelable_test_m_analysis.png` (labeled analysis only).
- Results Artifacts & Reporting (Step 8):
  - Compiled `results/cancelable_summary.md` and `results/cancelable_eer.json`.
  - Recorded ADR D-014 in `docs/DECISIONS.md`, updated `docs/EVALUATION_PLAN.md` and `docs/TRACEABILITY_REPORT.md`.
  - All 32 tests in test suite passing; `ruff` lint checks clean.
- Pre-Phase 4 statistical analysis and protocol alignment (D-012):
  - Completed paired bootstrap over test subjects (1000 resamples, seed 42) for EER difference fused-minus-face: difference = -0.89%, 95% CI [-2.23%, -0.38%] (strictly excludes 0, confirming statistically significant fusion gain).
  - Explained face-only CI shift ([1.11%, 3.89%] -> [1.11%, 3.60%]) from Protocol D-009 same-DB impostor stratification; refactored bootstrap CIs to shared unified function with seed 42.
  - Documented chimeric synthetic pairing and validation-only weight selection limitations.
  - Updated docs/EVALUATION_PLAN.md replacing S4/S5/S6 with Scenario K (known key, headline worst-case) and Scenario U (unknown/unique per-user keys).
- Implemented C++ Chaos Engine (`chaoshash`, cpp/chaos.hpp, cpp/chaos.cpp, cpp/bindings.cpp, src/chaos/):
  - Fully integer fixed-point Q64 pipeline ensuring bit-exact cross-platform determinism across MSVC and GCC.
  - Key derivation in Python using HMAC-SHA256 (`zkcambio|{app_salt}|v{key_version}`) producing 64-bit initial state and map parameter; zero crypto in C++.
  - Portable 64x64->high-64 multiplication without `__int128`.
  - 8192-entry direct-mapped cache guarding against degenerate states and cycles with golden-ratio Weyl reseed; discards first 1,000 iterations.
  - Rademacher random projection matrix sampled from chaotic bit 32 (exact 50.0% balance, zero autocorrelation, chi-square p > 0.05).
  - Public train-only mean centering (data/processed/chaos_mean_vector.npy) and $2^{20}$ fixed-scale integer quantization.
  - Compiled with strict flags (MSVC `/fp:strict`, GCC `-ffp-contract=off`).
- Validated with comprehensive tests in tests/test_chaos.py (7 tests, all passing; 31 total tests in suite):
  - Known-Answer Test (KAT) matching pure-Python big-integer reference bit-for-bit (first 4 bytes hex: 83ec0508).
  - Determinism across processes, runs, and Hamming symmetry.
  - Avalanche effect: 1-bit key flip produces 49.9% bit differences; 1 LSB state perturbation decorrelates within 60 steps.
  - Randomness sanity: 50.0% bit balance, lag-1..10 autocorrelation < 0.003, chi-square p > 0.05.
  - Cycle test: 0 cycles detected within 2,000,000 steps across 100 random keys.
  - Train population bit balance: 0.0% biased bit positions.
- Smoke evaluation on 30 validation subjects ONLY (experiments/04_chaos_smoke_eval.py):
  - Property check on all 300 subjects: HD vs angle ($\theta/\pi$) plotted across $m \in \{64, 128, 256, 512, 768\} \to$ results/chaos_hd_vs_angle.png.
  - Scenario K on 30 validation subjects ($m=512$, 10 random keys): Mean EER = 0.784% +/- 0.642%, histogram saved to results/chaos_val_hamming_hist.png.
  - Timing benchmark: 5.22 ms per transform (~192 transforms/sec).
  - Saved results/chaos_val_smoke.json.
- Documentation:
  - Documented engine architecture, parameters, build commands, and limitations in docs/ARCHITECTURE.md.
  - Recorded ADRs D-012 and D-013 in docs/DECISIONS.md.
  - Updated docs/TRACEABILITY_REPORT.md (FR-05 partial, NFR-05).

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

