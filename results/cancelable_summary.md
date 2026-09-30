# Cancelable Biometric Evaluation Summary (Phase 5)

## Primary Performance Table

| System | Modality / Protection | Key Condition | Pooled EER (%) | FNMR @ 1% FMR (%) | FNMR @ 0.1% FMR (%) | Decidability $d'$ | Rank-1 Accuracy (Gallery 40) |
|---|---|---|---|---|---|---|---|
| **S1** | Face Only | Unprotected | 2.00% (95% CI [1.11, 3.60]) | 3.33% | 9.44% | 4.78 | 97.22% |
| **S2** | Fingerprint Only | Unprotected | 5.81% (95% CI [4.72, 7.15]) | 26.67% | 68.06% | 3.42 | 78.89% |
| **S3** | Multimodal Fused ($w=0.60$) | Unprotected | 1.11% (95% CI [0.29, 1.66]) | 1.11% | 1.94% | 5.91 | 99.44% |
| **Scenario K** | Multimodal Fused ($w=0.60, m=512$) | **Known Key** (Worst-Case, Headline) | **1.29% +/- 0.23%** | **1.47% +/- 0.31%** | **3.19% +/- 0.79%** | **5.29** | **98.81% +/- 0.31%** |
| **Scenario U** | Multimodal Fused ($w=0.60, m=512$) | Unique Key per User | 0.0000%* | 0.00%* | 0.00%* | 7.92* | N/A* |

\* *Note on Scenario U: Measures cryptographic separation when each subject holds an independent secret key; cross-key impostor pairs yield random Hamming distance (~0.50). This demonstrates perfect key-space isolation but is NOT a measure of biometric recognition accuracy.*

## Key Findings & Performance Preservation vs S3

1. **Performance Preservation**:
   - Scenario K EER: **1.29% +/- 0.23%** compared to unprotected S3 EER of **1.11%**.
   - Paired bootstrap $\Delta\text{EER} = \text{EER}_K - \text{EER}_{S3} = +0.213\%$ (95% CI [-0.135%, +0.688%]).
   - Excludes zero? **False**. The degradation is statistically indistinguishable from zero performance loss.
   - Genuine trial resolution: 120 test subjects $\times 3$ probes = 360 genuine trials (discrete resolution $1/360 = 0.28\%$).

2. **Revocability (ISO/IEC 30136)**:
   - Genuine probes matched against template enrolled under revoked key: **FNMR = 100.00%** (100% rejection at operating threshold $\tau=0.350$).
   - Re-enrollment with new key version: accuracy completely restored (FNMR = 1.67%).

3. **Unlinkability (ISO/IEC 30136)**:
   - Cancelable multi-system unlinkability: **$D_\leftrightarrow^{sys} = 0.0125$** (well below the ISO/IEC threshold of 0.10, indicating full unlinkability).
   - Counterexample (reusing same key across two systems): **$D_\leftrightarrow^{sys} = 0.9827$** (proves that linkability is strictly controlled by key uniqueness).
