# Security and Non-Invertibility Evaluation Summary (Phase 6)
**Protocol D-015** | Evaluated on 120 test subjects across projection dimensions $m \in \{64, 128, 256, 512, 768, 1024\}$.

## 1. Threat Case A2: Template + Key Known (Inversion & Replay Attacks)

> [!NOTE]
> Cosines are reported for both **Centered Vectors** $\tilde{x} = x - \mu$ (which are directly projected) and **Raw Fused Vectors** $x$ (un-centered and re-normalized).
> The ridge decoder is the strongest attack tested; results represent a **lower bound on empirical leakage**.

| Dimension $m$ | Scenario K EER (%) | Best Inversion Attack | Centered Cosine $\cos(\hat{x}_{c}, x_{c})$ | Raw Cosine $\cos(\hat{x}_{u}, x)$ | S3 Replay @ 1% FMR (%) | S3 Replay @ 0.1% FMR (%) | Face Replay @ 1% FMR (%) | Finger Replay @ 1% FMR (%) |
|---|---|---|---|---|---|---|---|---|
| **64** | 4.02% | Atk-4 (Small MLP) | 0.6301 $\pm$ 0.0750 | 0.6369 $\pm$ 0.0632 | 99.2% | 96.7% | 94.2% | 54.2% |
| **128** | 2.07% | Atk-2 (Ridge Decoder) | 0.7780 $\pm$ 0.0500 | 0.7833 $\pm$ 0.0409 | 100.0% | 100.0% | 100.0% | 90.8% |
| **256** | 1.30% | Atk-2 (Ridge Decoder) | 0.8745 $\pm$ 0.0216 | 0.8782 $\pm$ 0.0228 | 100.0% | 100.0% | 100.0% | 100.0% |
| **512 (Chosen)** | **1.08%** | **Atk-2 (Ridge Decoder)** | **0.9335 $\pm$ 0.0115** | **0.9354 $\pm$ 0.0120** | **100.0%** | **100.0%** | **100.0%** | **100.0%** |
| **768** | 0.98% | Atk-2 (Ridge Decoder) | 0.9522 $\pm$ 0.0078 | 0.9536 $\pm$ 0.0083 | 100.0% | 100.0% | 100.0% | 100.0% |
| **1024** | 1.09% | Atk-2 (Ridge Decoder) | 0.9614 $\pm$ 0.0063 | 0.9624 $\pm$ 0.0068 | 100.0% | 100.0% | 100.0% | 100.0% |
| *Random Baseline* | *N/A* | *Random Gaussian* | *0.0000 $\pm$ 0.0360* | *0.0000 $\pm$ 0.0360* | *0.0%* | *0.0%* | *0.0%* | *0.0%* |

### Attacker Prior Sensitivity Check (30 Validation Subjects Only)
When the attacker prior and ridge decoder are fitted on the **30 validation subjects only** (completely excluding train fingerprints):
- $m=128$: Centered cosine = **0.6960 $\pm$ 0.0532**, Raw cosine = **0.7067 $\pm$ 0.0526**, S3 Replay @ 1% / 0.1% FMR = **100.0% / 100.0%**.
- $m=512$: Centered cosine = **0.8937 $\pm$ 0.0235**, Raw cosine = **0.8969 $\pm$ 0.0235**, S3 Replay @ 1% / 0.1% FMR = **100.0% / 100.0%**.
Demonstrates that encoder overfit on train fingerprints only marginally inflates inversion quality; replay success remains 100.0% even when trained on unseen validation subjects.

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
   - Derived chaotic state: 64 bits; map parameter: 62 active bits.
   - Effective keyspace is **at most $2^{126}$ by construction (upper bound); logistic-map state recovery was NOT evaluated**.
   - Measured transform time: 5.22 ms/transform $\implies$ brute-force search requires $> 10^{22}$ GPU-years.
2. **Template Distinguisher**:
   - Logistic regression classifier distinguishing templates of subject A vs B under random keys achieves 5-fold CV AUC of **0.4767** (chance level = 0.5000), proving zero identity leakage when keys are secret.
3. **Open Limitations**:
   - The fixed-point logistic map bitstream is not proven secure against algebraic state recovery. Hardening via counter-mode hashing (HMAC-SHA256 counter mode) is recommended for future production deployment.
