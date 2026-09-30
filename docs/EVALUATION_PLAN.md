# EVALUATION_PLAN.md  (also the paper's Results skeleton)

## Systems compared
- **S1**: Face-only baseline (512-d InceptionResnetV1, cosine similarity)
- **S2**: Fingerprint-only baseline (256-d FingerResNet18 V2, cosine similarity)
- **S3**: Fused unprotected baseline (768-d feature-level fusion, w=0.60, cosine similarity)
- **S3b**: Fused score-level baseline (z-score normalized weighted sum)
- **Scenario K (Known Key, HEADLINE, worst case)**: ONE master key is applied to every genuine and every impostor comparison (impostor biometrics transformed with the exact same key). Repeat across 10 random keys and report mean +/- SD of EER; this directly measures biometric discriminability and performance preservation versus S3.
- **Scenario U (Unknown Key / Unique per-user keys)**: Each subject has their own unique key; impostor comparisons cross different keys. Expected Hamming distance is ~0.50 and EER is ~0.0%. Reported for completeness but clearly labeled as NOT a measure of biometric recognition accuracy.

## Metrics (test subjects only, 120)
- **Evaluation Protocol (D-009)**: FVC databases (DB1_A, DB2_A, DB3_A) come from different physical sensors. Cross-DB impostor pairs are trivially separated by sensor noise, artificially suppressing EER. For all fingerprint and fusion evaluations, impostors MUST be **same-DB only** (40 test subjects per DB).
  - Impostor pairs per DB: 40 templates x 39 other subjects x 3 probes = 4,680 impostor comparisons per DB (total 14,040 pooled same-DB impostors across 3 DBs).
  - Genuine pairs per DB: 40 subjects x 3 probes = 120 genuine comparisons per DB (total 360 pooled genuine comparisons).
  - Headline metrics (EER, ROC) are reported for the pooled same-DB scores, along with individual per-DB numbers.
  - CMC curves are computed per-DB (closed-set gallery = 40), and pooled CMC is reported clearly labeled as an easier cross-sensor task.
- Genuine/impostor score histograms, d-prime
- **EER** (with paired bootstrap 95% CI over subjects, 1000 resamples, seed=42)
- FNMR at FMR = 1% and 0.1%
- **ROC** (TPR vs FPR) for all systems on one plot
- **CMC** (rank-1..rank-20 identification, per-DB gallery = 40; pooled gallery = 120 clearly marked)
- Table: EER of S3 vs Scenario K, showing the "performance preservation" gap (target: within ~1-2 percentage points; reported transparently)


## Criteria experiments
1. **Non-invertibility**: attacks in `SECURITY_THREAT_MODEL.md`. Report reconstruction cosine and attack success rate. Also report information-loss argument (d, m, bits). *(Phase 6)*
2. **Revocability (ISO/IEC 30136)**: Evaluated on 120 test subjects across key versions 1..5. Mated cross-key mean HD = 0.5018 +/- 0.0224 (indistinguishable from impostor distribution). Genuine probe against template enrolled under revoked key yields FNMR = 100.00% (100% rejection at operating threshold tau = 0.350). Re-enrollment under new key completely restores genuine accuracy (FNMR = 1.67%). *(Phase 5 Verified)*
3. **Unlinkability (ISO/IEC 30136)**: Evaluated using standard Gomez-Barrero histogram method comparing mated vs non-mated cross-key score distributions. Global metric $D_\leftrightarrow^{sys} = 0.0125$ (well below the ISO/IEC 0.10 threshold, establishing full unlinkability). Reused key counterexample yields $D_\leftrightarrow^{sys} = 0.9827$, confirming cross-system leakage occurs only when keys are reused. *(Phase 5 Verified)*
4. **Performance preservation**: Evaluated under Scenario K (chosen $w=0.60$, chosen $m=512$ selected on 30 validation subjects). Headline pooled EER across 10 fixed random keys is $1.29\% \pm 0.23\%$ vs unprotected S3 EER of $1.11\%$. Paired bootstrap over test subjects (1000 resamples): $\Delta\text{EER} = +0.213\%$ (95% CI $[-0.135\%, +0.688\%]$, excludes 0: False; degradation is statistically indistinguishable from zero). FNMR@1% = $1.47\% \pm 0.31\%$, FNMR@0.1% = $3.19\% \pm 0.79\%$, $d' = 5.29$, fair gallery-40 Rank-1 = $98.81\% \pm 0.31\%$. Modality ablations show cancelable Face-only EER = $2.73\%$ and Finger-only EER = $5.98\%$, confirming multimodal fusion advantage is preserved under chaotic protection. *(Phase 5 Verified)*

## Fusion detail
score/feature normalization: L2 per modality; concat [w*f_face, (1-w)*f_finger]; w tuned on train set only.

## Reproducibility
Every figure comes from `experiments/NN_*.py` -> `results/`. Save the raw score arrays (`.npy`) so plots can be regenerated.

## Paper outline
Abstract, Intro, Related work (cancelable biometrics, BioHashing, multimodal fusion), Method, Dataset & protocol (disclose chimeric), Results, Security analysis, Limitations, Conclusion.
