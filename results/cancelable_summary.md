# Cancelable Biometric Evaluation Summary (Phase 5)

## Primary Performance Table

| System | Modality / Protection | Key Condition | Pooled EER (%) | FNMR @ 1% FMR (%) | FNMR @ 0.1% FMR (%) | Decidability $d'$ | Rank-1 Accuracy (Gallery 40) |
|---|---|---|---|---|---|---|---|
| **S1** | Face Only | Unprotected | 2.00% (95% CI [1.11, 3.60]) | 3.33% | 9.44% | 4.78 | 97.22% |
| **S2** | Fingerprint Only | Unprotected | 5.81% (95% CI [4.72, 7.15]) | 26.67% | 68.06% | 3.42 | 78.89% |
| **S3** | Multimodal Fused ($w=0.60$) | Unprotected | 1.11% (95% CI [0.29, 1.66]) | 1.11% | 1.94% | 5.91 | 99.44% |
| **Scenario K** | Multimodal Fused ($w=0.60, m=512$) | **claimed-identity key (operational; equals stolen-key case)** | **1.29% +/- 0.23%** | **1.47% +/- 0.31%** | **3.19% +/- 0.79%** | **5.29** | **98.81% +/- 0.31%** |
| **Scenario U** | Multimodal Fused ($w=0.60, m=512$) | **attacker presents own key/token (best case)** | 0.0000%* | 0.00%* | 0.00%* | 7.92* | N/A* |

\* *Note on Scenario U: Measures key separation when each subject holds an independent secret key; cross-key impostor pairs yield random Hamming distance (~0.50). This demonstrates perfect key separation but is NOT a measure of biometric recognition accuracy.*

## Key Findings & Performance Preservation vs S3

1. **Performance Preservation & Paired Bootstrap CIs (1,000 subject-level resamples)**:
   - Scenario K EER: **1.29% +/- 0.23%** compared to unprotected S3 EER of **1.11%**.
   - $\Delta\text{EER} (K - S3) = +0.213\%$ (95% CI [-0.135%, +0.688%], excludes 0: **False**).
   - $\Delta\text{FNMR@1\%} (K - S3) = +0.276\%$ (95% CI [-0.333%, +1.167%], excludes 0: **False**).
   - $\Delta\text{FNMR@0.1\%} (K - S3) = +1.311\%$ (95% CI [+0.333%, +2.722%], excludes 0: **True**).
   - Genuine trial resolution: 120 test subjects $\times 3$ probes = 360 genuine trials (discrete step size $1/360 = 0.28\%$).

2. **Revocability (ISO/IEC 30136)**:
   - Operating thresholds derived strictly from 30 VALIDATION subjects under Scenario K:
     - Validation Scenario K EER threshold: $\tau = 0.3504$ (similarity 0.6496).
     - Validation Scenario K FMR=0.1% threshold: $\tau = 0.3010$ (similarity 0.6990).
   - FNMR with revoked key against enrolled template: **100.00%** at Val EER threshold and **100.00%** at Val FMR=0.1% threshold (100.00% rejection in both cases).
   - Re-enrollment with new key version completely restores genuine recognition (FNMR = 1.67% at $\tau=0.3504$).

3. **Unlinkability (ISO/IEC 30136)**:
   - Evaluated using **DIFFERENT biological samples** ($e_i$ under key 1 vs $p_{i, k}$ under key 2) to eliminate within-sample correlation artifacts.
   - Cancelable multi-system unlinkability: **$D_\leftrightarrow^{sys} = 0.0245$** (well below the ISO/IEC 30136 benchmark threshold of 0.10, indicating unlinkability against a score-based adversary WITHOUT key access).
   - Counterexample (reusing same key across two systems): **$D_\leftrightarrow^{sys} = 0.9827$** (demonstrates that linkability is strictly controlled by key uniqueness).
