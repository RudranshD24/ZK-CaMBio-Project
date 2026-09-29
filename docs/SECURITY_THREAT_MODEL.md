# SECURITY_THREAT_MODEL.md

## Assets
Raw images, embeddings, fused vector (never stored); cancelable template; user key.

## Attacker cases
| ID | Attacker has | Goal | Expected defense |
|---|---|---|---|
| A1 | Template DB only | recover embedding / images | Non-invertibility (m<d, 1-bit) |
| A2 | Template DB + keys | recover or spoof | Weaker; measure inversion success honestly |
| A3 | Two templates of same user (two systems/key versions) | link them | Unlinkability |
| A4 | Stolen template, replays it | authenticate | Hamming replay accepted at API? Mitigate with challenge-response (stretch) |
| A5 | Old template after revocation | authenticate | Revoked key rejected |
| A6 | Brute-force probes | impersonate | Rate limit, threshold on FMR |

## Attacks to run in experiments
1. **Inversion regression**: train a decoder (ridge / small MLP) template -> fused embedding using train subjects (with keys known). Report cosine similarity of reconstruction to true embedding on test subjects and whether the reconstruction, fed to the *unprotected* matcher, gets accepted (attack success rate at FMR=0.1%).
2. **Nearest-neighbor / pre-image attack**: search a public embedding set for vectors mapping to the stolen template.
3. **Stolen-key / same-key impostor** scenario (attacker uses their own biometrics with victim's key).
4. **Cross-match attack** for unlinkability (mated vs non-mated across key versions).

## Honest limitations to write in the paper
Chimeric data; logistic map is not proven cryptographically secure; float determinism across platforms; Python memory not zeroized; no liveness detection.
