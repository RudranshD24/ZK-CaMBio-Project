# EVALUATION_PLAN.md  (also the paper's Results skeleton)

## Systems compared
S1 face-only | S2 finger-only | S3 fused-unprotected (cosine) | S4 fused-cancelable, **legit key** (Hamming) | S5 cancelable, **stolen key / impostor uses victim key** | S6 cancelable, **wrong key** (attacker guesses key)

## Metrics (test subjects only, 120)
- Genuine/impostor score histograms, d-prime
- **EER** (with bootstrap 95% CI over subjects, 1000 resamples)
- FNMR at FMR = 1% and 0.1%
- **ROC** (TPR vs FPR) for all systems on one plot
- **CMC** (rank-1..rank-20 identification, closed set, gallery = 120 templates)
- Table: EER of S3 vs S4, showing the "performance preservation" gap (target: within about 1-2 percentage points; report honestly whatever you get)

## Criteria experiments
1. **Non-invertibility**: attacks in SECURITY_THREAT_MODEL.md. Report reconstruction cosine and attack success rate. Also report information-loss argument (d, m, bits).
2. **Revocability**: for each test user create key versions 1..5; compare same-user cross-key Hamming scores against the impostor distribution. Expected: cross-key mated scores ~ impostor scores. Also show the revoked-key template is rejected.
3. **Unlinkability**: mated vs non-mated cross-key score distributions; report the Gomez-Barrero D_sys-style measure (0 = fully unlinkable, 1 = fully linkable) and overlap plots.
4. **Performance preservation**: S3 vs S4 (above) + ablation over m in {128, 256, 512, 1024} and fusion weight w in {0.3..0.7}.

## Fusion detail
score/feature normalization: L2 per modality; concat [w*f_face, (1-w)*f_finger]; w tuned on train set only.

## Reproducibility
Every figure comes from `experiments/NN_*.py` -> `results/`. Save the raw score arrays (`.npy`) so plots can be regenerated.

## Paper outline
Abstract, Intro, Related work (cancelable biometrics, BioHashing, multimodal fusion), Method, Dataset & protocol (disclose chimeric), Results, Security analysis, Limitations, Conclusion.
