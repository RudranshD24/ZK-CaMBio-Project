# Consistency Audit: Documentation vs. Experimental Results

This document performs an exhaustive line-by-line reconciliation of every numerical claim across project documentation against the empirical ground-truth JSON files generated in `results/`.

**Audit Date:** 2026-10-01  
**Auditor:** Antigravity Automated Verification Agent  
**Reference Source Files:**
- `results/face_eer.json`
- `results/finger_eer.json`
- `results/fused_unprotected.json`
- `results/cancelable_eer.json`
- `results/security_eval.json`
- `results/chaos_val_smoke.json`

---

## 1. Metric Audit and Comparison Matrix

| Domain | Metric / Parameter | Value in `docs/` | Value in `results/*.json` | Discrepancy / Status |
|---|---|---|---|---|
| **Face Baseline** | VGGFace2 Pretrained Model | InceptionResnetV1 (512-d) | InceptionResnetV1 (512-d) | **MATCH** |
| | Number of Test Subjects | 120 | 120 | **MATCH** |
| | Total Genuine Comparisons | 360 | 360 | **MATCH** |
| | Total Impostor (Protocol D-009) | 14,040 (same-DB) | 14,040 | **MATCH** |
| | Pooled EER (Same-DB) | 2.00% (or 1.99% all-pair) | 2.00% (same-DB), 1.99% (all-pair) | **MATCH** (Documented distinction) |
| | 95% Bootstrap CI | [1.11%, 3.89%]% | [1.11%, 3.89%]% | **MATCH** |
| | Rank-1 Identification | 97.22% (same-DB), 94.72% (all) | 97.22% (same-DB), 94.72% (all) | **MATCH** |
| | Per-DB EERs | DB1: 1.56%, DB2: 1.73%, DB3: 1.54% | DB1: 1.56%, DB2: 1.73%, DB3: 1.54% | **MATCH** |
| **Fingerprint Baseline** | Baseline A (Gabor) Pooled EER | 41.10% [38.89, 43.11]% | 41.10% [38.89, 43.11]% | **MATCH** |
| | Baseline B (ResNet18) Pooled EER | 5.81% [4.72, 7.15]% | 5.81% [4.72, 7.15]% | **MATCH** |
| | Baseline B Per-DB EER | DB1: 5.06%, DB2: 8.50%, DB3: 3.35% | DB1: 5.06%, DB2: 8.50%, DB3: 3.35% | **MATCH** |
| | Baseline B Rank-1 (Gallery 40) | 78.89% | 78.89% | **MATCH** |
| **Multimodal Fusion** | Validation Weight Tuning | $w_{face} = 0.60, w_{finger} = 0.40$ | $w_{face} = 0.60, w_{finger} = 0.40$ | **MATCH** |
| | S1 (Face Only) Test EER | 2.00% [1.11, 3.60]% | 2.00% [1.11, 3.60]% | **MATCH** |
| | S2 (Finger Only) Test EER | 5.81% [4.72, 7.15]% | 5.81% [4.72, 7.15]% | **MATCH** |
| | S3 (Feature Fused) Test EER | 1.11% [0.29, 1.66]% | 1.11% [0.29, 1.66]% | **MATCH** |
| | S3 FNMR@1% FMR | 1.11% | 1.11% | **MATCH** |
| | S3 FNMR@0.1% FMR | 1.94% | 1.94% | **MATCH** |
| | S3 Decidability Index $d'$ | 5.91 | 5.91 | **MATCH** |
| | S3 Rank-1 Identification (G40) | 99.44% | 99.44% | **MATCH** |
| | S3b (Score Fused) Test EER | 1.10% [0.28, 1.67]% | 1.10% [0.28, 1.67]% | **MATCH** |
| **Cancelable Biometrics** | Chosen Bit Length $m$ | 512 | 512 | **MATCH** |
| | Validation $m$ Selection EER | $m=512: 0.83\% \pm 0.35\%$ | $0.833\% \pm 0.354\%$ | **MATCH** |
| | Scenario K Headline EER (10 seeds) | $1.29\% \pm 0.23\%$ | $1.285\% \pm 0.230\%$ | **MATCH** |
| | Scenario K FNMR@1% FMR | $1.47\% \pm 0.31\%$ | $1.472\% \pm 0.306\%$ | **MATCH** |
| | Scenario K FNMR@0.1% FMR | $3.19\% \pm 0.79\%$ | $3.194\% \pm 0.788\%$ | **MATCH** |
| | Scenario K Decidability $d'$ | 5.29 | 5.288 | **MATCH** |
| | Scenario K Rank-1 Identification | $98.81\% \pm 0.31\%$ | $98.806\% \pm 0.306\%$ | **MATCH** |
| | Paired Bootstrap $\Delta\text{EER}$ vs S3 | $+0.213\%$ (95% CI $[-0.135\%, +0.688\%]$) | $+0.213\%$ (CI $[-0.135\%, +0.688\%]$) | **MATCH** (Excludes 0: False) |
| | Paired Bootstrap $\Delta\text{FNMR@1\%}$ | $+0.276\%$ (95% CI $[-0.333\%, +1.167\%]$) | $+0.276\%$ (CI $[-0.333\%, +1.167\%]$) | **MATCH** (Excludes 0: False) |
| | Paired Bootstrap $\Delta\text{FNMR@0.1\%}$ | $+1.311\%$ (95% CI $[+0.333\%, +2.722\%]$) | $+1.311\%$ (CI $[+0.333\%, +2.722\%]$) | **MATCH** (Excludes 0: True) |
| | Scenario U EER | 0.00% (Cryptographic isolation) | 0.00% | **MATCH** |
| | Scenario U Impostor / Genuine HD | Imp: $0.5001 \pm 0.0222$, Gen: $0.2214 \pm 0.0503$ | Imp: 0.5001, Gen: 0.2214 | **MATCH** |
| **Revocability** | Operational Threshold $\tau_{oper, eer}$ | 0.3504 | 0.3504 | **MATCH** |
| | Operational Threshold $\tau_{oper, 0.1\%}$ | 0.3010 | 0.3010 | **MATCH** |
| | FNMR After Revocation | 100.00% (both thresholds) | 100.00% | **MATCH** |
| | FNMR Restored with New Key | 1.67% ($\tau_{eer}$), 6.94% ($\tau_{0.1\%}$) | 1.667% ($\tau_{eer}$), 6.944% ($\tau_{0.1\%}$) | **MATCH** |
| | Same Subject Different Keys HD | $0.5006 \pm 0.0219$ | 0.500596 | **MATCH** |
| **Unlinkability** | Score-Based Adversary $D_\leftrightarrow^{sys}$ | 0.0245 (Gomez-Barrero benchmark) | 0.024477 | **MATCH** |
| | Reused Key Counterexample $D_\leftrightarrow^{sys}$ | 0.9827 | 0.982687 | **MATCH** |
| **Threat A2 (Inversion)** | Best Attack Type | Ridge Regression (learned linear decoder) | Ridge Regression | **MATCH** |
| | Reconstructed Cosine ($m=512$, centered) | $0.9335 \pm 0.0115$ | $0.93346 \pm 0.01150$ | **MATCH** |
| | Reconstructed Cosine ($m=512$, raw uncentered) | $0.9354 \pm 0.0120$ | $0.9354 \pm 0.0120$ | **MATCH** |
| | Replay Success against S3 @ 1% FMR | 100.0% | 100.0% | **MATCH** |
| | Replay Success against S3 @ 0.1% FMR | 100.0% | 100.0% | **MATCH** |
| | Replay Success Face-Only @ 1% FMR | 100.0% | 100.0% | **MATCH** |
| | Replay Success Finger-Only @ 1% FMR | 100.0% | 100.0% | **MATCH** |
| | Validation-Only Sensitivity Cosine ($m=512$) | Centered: $0.8937 \pm 0.0235$, Raw: $0.8969 \pm 0.0235$ | $0.8937 \pm 0.0235$, $0.8969 \pm 0.0235$ | **MATCH** |
| **Threat A3 (Linkage with Keys)** | Linkage ROC AUC | 0.9980 | 0.99802 | **MATCH** |
| | Linkage EER | 1.63% | 1.633% | **MATCH** |
| | Linkage $D_\leftrightarrow^{sys}$ with Keys Known | 0.9649 | 0.96485 | **MATCH** |
| **Threat A1 (Template Only)** | Key-Space Formulation | "At most $2^{126}$ by construction (upper bound)" | "At most $2^{126}$ by construction (upper bound)" | **MATCH** |
| | Template Distinguisher AUC | 0.4767 (indistinguishable from chance) | 0.4767 | **MATCH** |
| **API & KDF Verification** | Scrypt Stretch Parameters | $N=16384, r=8, p=1, dklen=32$ | $N=16384, r=8, p=1, dklen=32$ | **MATCH** |
| | Per-User Random Salt Length | 16 bytes (`users.kdf_salt`) | 16 bytes | **MATCH** |
| | Parameter Checksum SHA-256 | `13ce83aca7af7611f0d654ce7563a1bebf9a16437e8eda89187dde118acdaa82` | `13ce83aca7af7611f0d654ce7563a1bebf9a16437e8eda89187dde118acdaa82` | **MATCH** |
| | Linux KAT Server-Key Prefix | `2d8998aa` | `2d8998aa` | **MATCH** |
| | Linux KAT Stretched Secret Prefix | `9ed1a9ad` | `9ed1a9ad` | **MATCH** |

---

## 2. Identified Discrepancies and Fixes Applied

1. **Test Rejection Rate Notation (Phase 7b vs 7d):**
   - *Previous state:* An earlier draft noted fingerprint enrollment rejection at 14.17% (17/120 test subjects) under train-calibrated threshold 0.70.
   - *Audit Fix:* Clarified in `docs/DECISIONS.md` (ADR D-016 & D-017) and `docs/SECURITY_THREAT_MODEL.md` that recalibration to 0.60 on the 30 validation subjects yielded 0.00% test rejection, but this 0.00% is an observed outcome of a threshold revised after observing test failures, and that the quality gate is weaker at 0.60.
2. **Centered vs. Raw Reconstructed Embeddings:**
   - *Audit Fix:* Explicitly reported both centered cosine ($0.9335 \pm 0.0115$) and raw uncentered cosine ($0.9354 \pm 0.0120$) across all projection dimensions $m \in \{64, 128, 256, 512, 768, 1024\}$ in `docs/SECURITY_THREAT_MODEL.md` and the viva presentation slides.
3. **Definition of "Zero-Knowledge":**
   - *Audit Fix:* Confirmed everywhere that "zero-knowledge" in ZK-CaMBio refers to the structural privacy property: **no raw biometrics stored, and in user-secret mode no key material stored on the server**. Confirmed that no cryptographic zk-SNARK proof is implemented (FR-13 explicitly recorded as Not Implemented).

---

## 3. Certification of Consistency

All numbers across documentation, test suites, API configurations, and experimental result manifests are 100% consistent with the underlying empirical data files.
