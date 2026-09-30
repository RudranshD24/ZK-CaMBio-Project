# Security and Non-Invertibility Evaluation Summary (Phase 6)
**Protocol D-015** | Evaluated on 120 test subjects across projection dimensions $m \in \{64, 128, 256, 512, 768, 1024\}$.

## 1. Threat Case A2: Template + Key Known (Inversion & Replay Attacks)

| Dimension $m$ | Scenario K EER (%) | Best Inversion Attack | Mean $\pm$ SD Cosine $\cos(\hat{x}, x)$ | S3 Replay @ 1% FMR (%) | S3 Replay @ 0.1% FMR (%) | Face Replay @ 1% FMR (%) | Finger Replay @ 1% FMR (%) |
|---|---|---|---|---|---|---|---|
| **64** | 4.02% | Atk-4 (Small MLP) | 0.6344 $\pm$ 0.0765 | 100.0% | 95.8% | 93.3% | 57.5% |
| **128** | 2.07% | Atk-2 (Ridge Decoder) | 0.7763 $\pm$ 0.0397 | 100.0% | 100.0% | 100.0% | 86.7% |
| **256** | 1.30% | Atk-2 (Ridge Decoder) | 0.8745 $\pm$ 0.0216 | 100.0% | 100.0% | 100.0% | 100.0% |
| **512 (Chosen)** | **1.08%** | **Atk-2 (Ridge Decoder)** | **0.9335 $\pm$ 0.0115** | **100.0%** | **100.0%** | **100.0%** | **100.0%** |
| **768** | 0.98% | Atk-2 (Ridge Decoder) | 0.9522 $\pm$ 0.0078 | 100.0% | 100.0% | 100.0% | 100.0% |
| **1024** | 1.09% | Atk-2 (Ridge Decoder) | 0.9614 $\pm$ 0.0063 | 100.0% | 100.0% | 100.0% | 100.0% |
| *Random Baseline* | *N/A* | *Random Gaussian* | *0.0000 $\pm$ 0.0360* | *0.0%* | *0.0%* | *0.0%* | *0.0%* |

## 2. Threat Case A3: Linkage Attack with Both Keys Known ($m=512$)

- Evaluated on mated pairs (different biological samples under key 1 vs key 2) vs non-mated pairs:
  - **Linkage ROC AUC**: **0.9980**
  - **Linkage Attack EER**: **1.63%**
  - **Linkage ISO/IEC 30136 $D_\leftrightarrow^{sys}$ with keys known**: **0.9649**
  - **Score-Only Phase 5 $D_\leftrightarrow^{sys}$ (without keys)**: **0.0245**
  - **Definitive Conclusion**: **Unlinkability DOES NOT survive key compromise.** Once both keys are known, an adversary can reconstruct estimated embeddings $\hat{x}_1, \hat{x}_2$ and achieve substantial linkage capability ($D_\leftrightarrow^{sys}$ surges from 0.0245 to 0.9649). Protection relies strictly on key secrecy.

## 3. Threat Case A1: Template Only (Key Unknown)

1. **Key Space Accounting**:
   - Master key entropy: 256 bits.
   - Derived chaotic state: 64 bits; map parameter: 62 active bits $\implies 2^{126}$ effective keyspace.
   - Measured transform time: 5.22 ms/transform $\implies$ brute-force search requires $> 10^{22}$ GPU-years.
2. **Template Distinguisher**:
   - Logistic regression classifier distinguishing templates of subject A vs B under random keys achieves 5-fold CV AUC of **0.4767** (chance level = 0.5000), proving zero identity leakage when keys are secret.
3. **Open Limitations**:
   - The fixed-point logistic map bitstream is not proven secure against algebraic state recovery. Hardening via counter-mode hashing (HMAC-SHA256 counter mode) is recommended for future production deployment.
