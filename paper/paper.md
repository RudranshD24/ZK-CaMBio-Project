# ZK-CaMBio: Zero-Knowledge Cancelable Multimodal Biometrics with Provable Revocability and Empirical Non-Invertibility Boundaries

**Author:** Antigravity Research Team  
**Date:** October 2026  
**Status:** Research Prototype & Comprehensive Technical Report  

---

## Abstract

Centralized storage of biometric templates exposes users to irrevocable compromise, as physical biometrics cannot be revoked or reissued when compromised. In this work, we present **ZK-CaMBio** (Zero-Knowledge Cancelable Multimodal Biometrics), a production-engineered cancelable biometric authentication system combining face recognition (InceptionResnetV1) and fingerprint recognition (FingerResNet18 V2) at the feature level, projected via a deterministic, integer-quantized chaotic linear map into a 512-bit binary cancelable template. 

We formally define the term **"zero-knowledge"** in this work strictly as a data-at-rest structural security property: *no raw biometric images are stored, no unquantized floating-point embeddings are stored, and, in user-secret mode, no key material is stored on the authentication server*. We explicitly disclose that *no cryptographic zero-knowledge proof (such as a zk-SNARK or zk-STARK circuit) is implemented*. 

Across 120 test chimeric virtual subjects evaluated under within-sensor impostor restrictions (Protocol D-009, 14,040 impostor comparisons), ZK-CaMBio demonstrates near-perfect preservation of biometric recognition accuracy: the cancelable system achieves an Equal Error Rate (EER) of $1.29\% \pm 0.23\%$ at $m=512$ bits, compared to $1.11\% \pm 0.22\%$ for the unprotected feature-level fused baseline. A paired bootstrap hypothesis test reveals $\Delta\text{EER} = +0.213\%$ (95% CI: $[-0.135\%, +0.688\%]$), establishing that accuracy degradation at the EER operating point is statistically indistinguishable from zero. Under ISO/IEC 30136 evaluations, template revocation yields a 100.00% False Non-Match Rate (FNMR) against retired templates while immediately restoring genuine recognition (FNMR = 1.67%) under new keys, and score-based cross-service linkability remains negligible ($D_\leftrightarrow^{sys} = 0.0245 \ll 0.10$). Crucially, we conduct a rigorous non-invertibility evaluation against four reconstruction attacks; we disclose that random projection binarization is *not* a one-way cryptographic trapdoor function: if the chaotic projection key is compromised, a learned linear Ridge decoder reconstructs fused biometric embeddings with $0.9335 \pm 0.0115$ cosine similarity (100.0% replay success). System privacy therefore depends strictly on key secrecy, establishing an empirical lower bound on information leakage under key disclosure.

---

## 1. Introduction

Biometric authentication systems offer high convenience by binding digital identity to human physical characteristics. However, unlike cryptographic passwords or tokens, compromised biometric traits cannot be re-issued. A stolen fingerprint or facial embedding remains permanently compromised across all services where that physical trait is enrolled.

To mitigate this catastrophic failure mode, **Cancelable Biometrics** was introduced to transform sensitive biometric features into protected, revocable representations using user-specific or system-specific keys [VERIFY: Ratha et al., 2001]. An ideal cancelable biometric system must satisfy four core criteria formalized in ISO/IEC 30136:
1. **Performance Preservation:** Recognition accuracy (EER, ROC, CMC) must not significantly degrade compared to the unprotected biometric baseline.
2. **Revocability (Renewability):** If a template or key is compromised, it must be straightforward to revoke, and probes under the revoked key must be rejected while new templates restore genuine matching.
3. **Unlinkability (Diversity):** Multiple protected templates derived from the same person across different applications must not be linkable to the same identity.
4. **Non-Invertibility:** It must be computationally infeasible to reconstruct the original raw biometric image or unquantized feature vector from the cancelable template.

While the literature contains numerous cancelable biometric proposals, many suffer from three widespread deficiencies: (a) evaluating on synthetic or single-modality benchmarks without rigorous paired confidence intervals; (b) asserting "non-invertibility" based solely on heuristic algebraic arguments without empirical evaluation against trained machine learning decoders; and (c) failing to provide production-grade, air-gapped implementations with timing-safe secrets hygiene and resistance to score-based hill-climbing attacks.

In this paper, we develop and evaluate **ZK-CaMBio**, an end-to-end multimodal cancelable biometric authentication system. We integrate deep facial representations with convolutional fingerprint embeddings, evaluate performance under rigorous cross-validation and paired bootstrap protocols, and subject the system to systematic adversarial inversion and linkage attacks.

---

## 2. Related Work

### 2.1 Cancelable Biometrics and BioHashing
Cancelable biometrics generally falls into two paradigms: non-invertible non-linear transforms and salted random projections. BioHashing [VERIFY: Teoh et al., 2004] computes the inner product between an unquantized biometric feature vector and random orthonormal vectors derived from a user token, thresholding the projection at zero to generate a binary bitstring. While early literature reported zero error rates under identical keys, subsequent studies demonstrated that BioHashing's apparent accuracy boost stems from key entropy rather than biometric discrimination ("stolen token" vs. "stolen biometric" scenarios) [VERIFY: Lumini and Nanni, 2007; Ngo et al., 2009]. In ZK-CaMBio, we evaluate both Scenario K (where keys are identical across enroll and probe, assessing genuine biometric preservation) and Scenario U (where probes and gallery have mismatched keys, measuring cryptographic isolation).

### 2.2 Random Projection and Johnson-Lindenstrauss Embedding
The mathematical foundation of randomized binary embedding rests on the Johnson-Lindenstrauss lemma and hyper-plane locality-sensitive hashing [VERIFY: Indyk and Motwani, 1998; Charikar, 2002]. For any two vectors $x_1, x_2 \in \mathbb{R}^d$ on the unit sphere with angle $\theta = \arccos(\langle x_1, x_2 \rangle)$, a random hyper-plane vector $r \sim \mathcal{N}(0, I)$ satisfies:
$$\Pr[\text{sign}(\langle r, x_1 \rangle) \neq \text{sign}(\langle r, x_2 \rangle)] = \frac{\theta}{\pi}$$
Thus, the normalized Hamming distance between $m$-bit random sign projections directly estimates the angular distance between the original embeddings. We exploit this property to preserve inter-class separation without exposing continuous coordinates.

### 2.3 Multimodal Biometric Fusion
Multimodal biometrics addresses the intrinsic limitations of single biometrics (e.g., poor fingerprint image quality or facial occlusions) [VERIFY: Ross and Jain, 2004]. Fusion can occur at the sensor level, feature level, score level, or decision level. Feature-level fusion concatenates compatible, normalized feature representations prior to matching, capturing cross-modal feature correlations. We employ feature-level concatenation of L2-normalized face and fingerprint vectors with validation-calibrated modality weights.

### Candidate References for Verification:
- [VERIFY: Ratha et al., 2001]: Ratha, N. K., Connell, J. H., & Bolle, R. M. "Enhancing security and privacy in biometrics-based authentication systems." *IBM Systems Journal*, 2001.
- [VERIFY: Teoh et al., 2004]: Teoh, A. B. J., Ngo, D. C. L., & Goh, A. "BioHashing: Two factor authentication featuring fingerprint data and random code." *Pattern Recognition*, 2004.
- [VERIFY: Lumini and Nanni, 2007]: Lumini, A., & Nanni, L. "An improved BioHashing for human authentication." *Pattern Recognition*, 2007.
- [VERIFY: Ngo et al., 2009]: Ngo, D. C. L., Teoh, A. B. J., & Goh, A. "Biometric encryption: The dark side of BioHashing." *IEEE Transactions on Information Forensics and Security*, 2009.
- [VERIFY: Indyk and Motwani, 1998]: Indyk, P., & Motwani, R. "Approximate nearest neighbors: towards removing the curse of dimensionality." *STOC*, 1998.
- [VERIFY: Charikar, 2002]: Charikar, M. S. "Similarity estimation techniques from rounding algorithms." *STOC*, 2002.
- [VERIFY: Ross and Jain, 2004]: Ross, A., & Jain, A. K. "Information fusion in biometrics." *Pattern Recognition Letters*, 2004.
- [VERIFY: Gomez-Barrero et al., 2017]: Gomez-Barrero, M., et al. "Unlinkable and irreversible biometric template protection based on Bloom filters." *Information Sciences*, 2017.

---

## 3. Method

```
+-----------------------------------------------------------------------------------+
|                                ZK-CaMBio Pipeline                                 |
|                                                                                   |
|  [Face Image] -------> InceptionResnetV1 (512-d) ---\                             |
|                                                      +--> L2-Norm Concatenation   |
|  [Finger Image] -----> FingerResNet18 V2 (256-d) ---/     (768-d, w=0.60 face)    |
|                                                                    |              |
|                                                                    v              |
|  [User Passphrase] --> scrypt (16-byte user salt) --> Seed --> Chaos Engine       |
|                                                                    |              |
|                                                                    v              |
|                                                      sign(R * x) (512-bit vector) |
|                                                                    |              |
|                                                                    v              |
|                                                          Packed Binary Bitstring  |
+-----------------------------------------------------------------------------------+
```

### 3.1 Feature Extraction
- **Face Modality:** Evaluated using InceptionResnetV1 pretrained on VGGFace2 [VERIFY: Cao et al., BMVC 2018], taking $160 \times 160$ aligned face crops and producing a 512-dimensional unit-norm embedding vector $x_{\text{face}} \in \mathbb{S}^{511}$.
- **Fingerprint Modality:** Evaluated using FingerResNet18 V2, a modified ResNet-18 trained with cross-entropy and cosine-margin loss on preprocessed $128 \times 128$ fingerprint patches (intensity normalized, block-variance foreground masked, and CLAHE enhanced), producing a 256-dimensional unit-norm embedding $x_{\text{finger}} \in \mathbb{S}^{255}$.

### 3.2 Feature-Level Multimodal Fusion
The two modalities are fused at the feature level via weighted concatenation:
$$x_{\text{fused}} = \left[ \sqrt{w} \cdot x_{\text{face}}^{\top}, \; \sqrt{1 - w} \cdot x_{\text{finger}}^{\top} \right]^{\top} \in \mathbb{R}^{768}$$
where $w \in [0, 1]$ represents the face modality weight. Because $\|x_{\text{face}}\|_2 = 1$ and $\|x_{\text{finger}}\|_2 = 1$, the combined vector is intrinsically L2-normalized:
$$\|x_{\text{fused}}\|_2 = \sqrt{w \|x_{\text{face}}\|^2 + (1 - w) \|x_{\text{finger}}\|^2} = \sqrt{w + (1 - w)} = 1$$
On the 30 validation subjects, grid search in $[0.1, 0.9]$ identified $w = 0.60$ as optimal (validation EER = 0.00%, test EER = 1.11%).

### 3.3 Chaotic Fixed-Point Projection Engine
To generate cancelable binary templates, we construct a deterministic pseudo-random projection matrix $R \in \{-1, +1\}^{m \times 768}$. The matrix is generated using a 1D chaotic logistic map with periodic fixed-point state perturbation:
$$x_{n+1} = r \cdot x_n (1 - x_n)$$
Parameters $x_0 \in (0, 1)$ and $r \in (3.99, 4.0)$ are derived via HMAC-SHA256 from a 32-byte master key, application context string, user identifier, and a user-specific secret salt. The continuous vector $x_{\text{fused}}$ is centered by subtracting the validation population mean vector $\mu_{\text{val}}$ and quantized into fixed-point 32-bit signed integers ($x_q = \text{round}(100000 \cdot (x - \mu_{\text{val}}))$). 

The cancelable template $b \in \{0, 1\}^m$ is obtained by matrix-vector sign binarization:
$$b_j = \begin{cases} 1 & \text{if } \sum_{i=1}^{768} R_{j, i} \cdot x_{q, i} \ge 0 \\ 0 & \text{otherwise} \end{cases}$$
The resulting $m$-bit array is packed into $\lceil m / 8 \rceil = 64$ bytes (for $m=512$) for storage. All arithmetic is implemented in C++17 with fused multiply-add disabled (`-ffp-contract=off`) to guarantee bit-exact cross-platform determinism between Windows (MSVC) and Linux (GCC).

### 3.4 Key Derivation and User Identity Separation
In user-secret mode, user passphrases are stretched using memory-hard scrypt ($N=16384, r=8, p=1, dklen=32$) with a per-user random 16-byte salt stored in `users.kdf_salt`. The HMAC context string explicitly binds the user's primary key (`user_id`), key version $v$, and stretched secret:
$$\text{context} = \text{"zkcambio"} \,\|\, \text{app\_salt} \,\|\, v \,\|\, \text{user\_id} \,\|\, \text{scrypt}(\text{secret}, \text{salt})$$
This guarantees that two users with identical passphrases generate distinct, mutually independent projection keys and templates.

---

## 4. Dataset and Experimental Protocol

### 4.1 Chimeric Dataset Construction
Because publicly available multimodal biometric datasets containing paired face and fingerprint captures under open research licenses are severely restricted by organizational access agreements, we constructed a virtual chimeric dataset:
- **Face Source:** UMDFaces [VERIFY: Bansal et al., 2017], academic open research dataset (creative commons / academic use).
- **Fingerprint Source:** FVC2004 DB1_A, DB2_A, and DB3_A [VERIFY: Maio et al., 2004], standard benchmark fingerprint databases (optical and thermal sweep sensors).
- **Pairing Scheme:** 300 virtual chimeric identities were assembled by pairing unique UMDFaces identities with unique FVC2004 fingers under seed 42. Each subject possesses 5 enrollment impressions (used to fit enrollment quality filters and derive templates) and 3 probe impressions.

### 4.2 Split Disjointness and Protocol D-009
The 300 subjects were partitioned into three strictly disjoint splits:
- **Train Split:** 180 subjects (used solely for training FingerResNet18 and baseline decoders).
- **Validation Split:** 30 subjects (used for tuning modality weight $w$, selecting projection dimension $m$, and fitting enrollment quality gates).
- **Test Split:** 120 subjects (strictly held out for final performance, revocability, unlinkability, and security evaluations).

**Protocol D-009 (Within-Sensor Impostor Pairing):** Because FVC2004 DB1, DB2, and DB3 use different sensors (DB1: optical 500 dpi, DB2: optical 569 dpi, DB3: thermal sweeping), cross-sensor fingerprint impostor comparisons create artificially inflated distinctiveness. Under Protocol D-009, impostor matching is strictly restricted to subjects enrolled on the same sensor database (40 subjects per DB, yielding $40 \times 39 \times 3 \times 3 = 14,040$ impostor comparisons pooled), preventing optimistic bias.

---

## 5. Experimental Results

All tables in this section are generated directly from experimental result files (`results/*.json`) via `scripts/generate_paper_tables.py`.

### 5.1 Unprotected Baselines (Face, Fingerprint, and Fusion)

Table 1 summarizes the recognition performance of single modalities and unprotected multimodal fusion across the 120 test subjects under Protocol D-009.

| System | Modality | Representation | Pooled EER (%) | 95% Bootstrap CI | FNMR @ 1% FMR (%) | FNMR @ 0.1% FMR (%) | Decidability ($d'$) | Rank-1 Acc. (%) |
|---|---|---|---|---|---|---|---|---|
| **S1** | Face Only | InceptionResnetV1 (512-d) | 2.00% | [1.11, 3.60]% | 3.33% | 9.44% | 4.78 | 97.22% |
| **S2** | Fingerprint Only | FingerResNet18 (256-d) | 5.81% | [4.72, 7.15]% | 26.67% | 68.06% | 3.42 | 78.89% |
| **S3** | Feature-Level Fusion | Concatenated Weighted (768-d, $w=0.60$) | **1.11%** | [0.29, 1.66]% | **1.11%** | **1.94%** | **5.91** | **99.44%** |
| **S3b** | Score-Level Fusion | Z-Score Weighted Sum ($w=0.60$) | 1.10% | [0.28, 1.67]% | 1.39% | 1.94% | 5.92 | 99.17% |

*Findings:* Feature-level fusion (S3) achieves significant gains over individual modalities, reducing EER from 2.00% (face) and 5.81% (finger) to 1.11%, while boosting decidability $d'$ to 5.91 and Rank-1 identification to 99.44%.

### 5.2 Cancelable Biometrics: Performance Preservation (Scenario K)

Table 2 evaluates ZK-CaMBio cancelable templates ($m=512$) under Scenario K (same key used for enrollment and verification) across 10 independent random keys.

| Dimension ($m$) | Evaluation Context | EER (%) | FNMR @ 1% FMR (%) | FNMR @ 0.1% FMR (%) | Decidability ($d'$) | Rank-1 Identification (%) |
|---|---|---|---|---|---|---|
| $m=512$ | Scenario K (Same-Key Across Probes, 10 seeds) | 1.29% ± 0.23% | 1.47% ± 0.31% | 3.19% ± 0.79% | 5.29 | 98.81% ± 0.31% |
| $m=512$ | Difference vs S3 Unprotected ($\Delta$) | +0.213% (95% CI: [-0.135%, +0.688%]) | +0.276% (95% CI: [-0.333%, +1.167%]) | +1.311% (95% CI: [+0.333%, +2.722%]) | -0.62 | -0.63% |

*Statistical Significance:* Paired bootstrap resampling (1,000 resamples over test subjects) demonstrates that $\Delta\text{EER} = +0.213\%$ has a 95% confidence interval spanning zero ($[-0.135\%, +0.688\%]$). Thus, binarization and chaotic projection do not introduce statistically detectable accuracy degradation at the equal error rate. At strict operating points ($\text{FMR} = 0.1\%$), a modest degradation of $+1.311\%$ is observed and transparently reported.

### 5.3 ISO/IEC 30136 Revocability and Unlinkability

Table 3 presents standard metrics for template renewability and cross-service unlinkability.

| Evaluation Metric | Standard | Operational Threshold ($\tau$) | Observed Value | Expected Ideal | Outcome |
|---|---|---|---|---|---|
| Revocation Efficacy (FNMR after Revocation) | ISO/IEC 30136 | $\tau_{oper, eer} = 0.3504$ | **100.00%** | 100.00% | Full Revocation |
| Revocation Efficacy (FNMR after Revocation) | ISO/IEC 30136 | $\tau_{oper, 0.1\%} = 0.3010$ | **100.00%** | 100.00% | Full Revocation |
| Genuine Restoration (FNMR with New Key) | ISO/IEC 30136 | $\tau_{oper, eer} = 0.3504$ | 1.67% | Low ($\le 5\%$) | Restored |
| Genuine Restoration (FNMR with New Key) | ISO/IEC 30136 | $\tau_{oper, 0.1\%} = 0.3010$ | 6.94% | Low ($\le 10\%$) | Restored |
| Pseudo-Identity Independence (Mean HD) | ISO/IEC 30136 | - | 0.5006 ± 0.0219 | 0.5000 | Chance Correlation |
| Global System Unlinkability ($D_\leftrightarrow^{sys}$) | Gomez-Barrero (2017) | Score-only (Keys Unknown) | **0.0245** | $\le 0.10$ | Fully Unlinkable |
| Key Reuse Counterexample ($D_\leftrightarrow^{sys}$) | Gomez-Barrero (2017) | Key Reused Across Systems | 0.9827 | 1.0000 | Fully Linkable |

*Analysis:* Revocation completely repudiates compromised templates (100.00% rejection). Unlinkability under distinct keys matches theoretical chance correlation ($D_\leftrightarrow^{sys} = 0.0245 \ll 0.10$), while key reuse across systems predictably collapses unlinkability ($D_\leftrightarrow^{sys} = 0.9827$), demonstrating that cross-service privacy requires distinct application salts.

---

## 6. Security Analysis & Adversarial Inversion

### 6.1 Threat Case A2: Template + Key Known (Inversion & Replay Attacks)

To establish the non-invertibility boundary, we trained four reconstruction decoders on the 180 training subjects:
1. **Atk-1 (Back-Projection):** Analytical Moore-Penrose pseudo-inverse $\hat{x} = R^{\top} (2b - 1)$.
2. **Atk-2 (Learned Linear Decoder):** Ridge regression mapping $b \in \{0, 1\}^m \to \mathbb{R}^{768}$.
3. **Atk-3 (Prior-Regularized Optimization):** Sign constraint hinge loss regularized by Mahalanobis distance to training mean.
4. **Atk-4 (Multi-Layer Perceptron):** Non-linear 2-layer MLP with ReLU activations.

Reconstructed vectors $\hat{x}$ were evaluated on 120 test subjects across projection lengths $m \in \{64, 128, 256, 512, 768, 1024\}$ and replayed against the victim's unprotected enrolled template.

Table 4 reports the empirical inversion results.

| Dimension ($m$) | Best Reconstructor | Centered Cosine | Raw Uncentered Cosine | S3 Replay @ 1% FMR | Face Replay @ 1% FMR | Finger Replay @ 1% FMR |
|---|---|---|---|---|---|---|
| 64 | Atk-4 (Small MLP) | 0.6313 ± 0.0766 | 0.6369 ± 0.0632 | 100.0% | 91.7% | 50.0% |
| 128 | Atk-2 (Ridge Decoder) | 0.7763 ± 0.0397 | 0.7833 ± 0.0409 | 100.0% | 100.0% | 86.7% |
| 256 | Atk-2 (Ridge Decoder) | 0.8745 ± 0.0216 | 0.8782 ± 0.0228 | 100.0% | 100.0% | 100.0% |
| **512** | **Atk-2 (Ridge Decoder)** | **0.9335 ± 0.0115** | **0.9354 ± 0.0120** | **100.0%** | **100.0%** | **100.0%** |
| 768 | Atk-2 (Ridge Decoder) | 0.9522 ± 0.0078 | 0.9536 ± 0.0083 | 100.0% | 100.0% | 100.0% |
| 1024 | Atk-2 (Ridge Decoder) | 0.9614 ± 0.0063 | 0.9624 ± 0.0068 | 100.0% | 100.0% | 100.0% |

### 6.2 Explicit Security Claims Table

Table 5 summarizes the security posture of ZK-CaMBio, distinguishing proven properties from non-guaranteed boundaries.

| Category | Claim | Status | Empirical Grounding & Limitations |
|---|---|---|---|
| **What IS Shown** | Recognition Accuracy Preservation | **Confirmed** | $\Delta\text{EER} = +0.213\%$ (95% CI: $[-0.135\%, +0.688\%]$). Indistinguishable from unprotected baseline ($p > 0.05$). |
| **What IS Shown** | Measurable Degradation at Strict Thresholds | **Confirmed** | $\Delta\text{FNMR@0.1\%} = +1.311\%$ (95% CI: $[+0.333\%, +2.722\%]$). Statistically detectable degradation reported honestly. |
| **What IS Shown** | Provable Revocability (ISO/IEC 30136) | **Confirmed** | FNMR = 100.00% against revoked templates under both EER and 0.1% FMR operating points. Immediate restoration under new keys. |
| **What IS Shown** | Cross-Service Unlinkability Without Keys | **Confirmed** | Score-based distinguisher metric $D_\leftrightarrow^{sys} = 0.0245 \ll 0.10$. Classification performs at chance (AUC = 0.4767). |
| **What is NOT Shown** | Non-Invertibility Given the Key | **Refuted** | Linear decoders achieve $0.9335$ cosine fidelity and 100% replay success if the key leaks. Random projection is **not** a one-way function. |
| **What is NOT Shown** | Unlinkability Given the Keys | **Refuted** | Cross-system linkage with known keys surges to ROC AUC = 0.9980 and $D_\leftrightarrow^{sys} = 0.9649$. |
| **What is NOT Shown** | Inherent Defense Against Bitstring Replay | **Not Inherent** | Verbatim replay of binary templates achieves 0.0000 Hamming distance; requires protocol-level challenge-response freshness. |
| **What is NOT Implemented** | Cryptographic Zero-Knowledge Proofs | **Not Implemented** | No zk-SNARK circuit is constructed. "Zero-knowledge" denotes zero raw biometric storage. |

---

## 7. Limitations

We explicitly document the following technical and methodological limitations:
1. **Chimeric Data Pairing:** Evaluating on virtual subjects formed by pairing UMDFaces with FVC2004 assumes statistical independence between face and fingerprint traits. Real-world physical traits may exhibit subtle biometric covariances.
2. **Subject Scale:** Evaluations are conducted on 120 test subjects (360 genuine trials, 14,040 impostor trials). Testing across national-scale databases ($\ge 10^6$ identities) is necessary to determine performance at extreme scale.
3. **Pretrained Encoder Generalization:** InceptionResnetV1 was pretrained on VGGFace2. While subjects in the evaluation split are formally disjoint from our experimental protocol, potential identity overlap with the public VGGFace2 corpus cannot be completely eliminated.
4. **Sensor Homogeneity:** Fingerprint evaluations were conducted within sensor partitions (Protocol D-009). Cross-sensor interoperability remains a challenge for cancelable biometrics.
5. **Chaos Generator Security:** Standard 1D chaotic maps are susceptible to orbit reconstruction if long trajectories are exposed without re-seeding. We use HMAC-SHA256 and fixed-point perturbators, but recommend evaluating CSPRNG alternatives for mission-critical deployments.
6. **Key Compromise Vulnerability:** As shown in Section 6, cancelable biometrics does not provide computational one-wayness once the projection matrix is known. Key management and HSM storage are paramount.
7. **Lack of Liveness Detection:** The pipeline does not incorporate presentation attack detection (PAD). Spoofed silicone finger impressions or printed facial masks are not detected at the model level.
8. **Memory Hygiene:** Python runtime processes do not zeroise heap memory upon garbage collection, leaving residual intermediate embeddings vulnerable to physical memory dumps.

---

## 8. Conclusion

We have designed, validated, and production-engineered **ZK-CaMBio**, a cancelable multimodal biometric system that reconciles high biometric utility with rigorous privacy preservation. By coupling feature-level face and fingerprint representations with integer-quantized chaotic projection, ZK-CaMBio preserves baseline recognition accuracy ($1.29\%$ EER vs. $1.11\%$ baseline, $p > 0.05$) while offering provable 100% template revocation and cross-service unlinkability. Our comprehensive adversarial evaluations demonstrate that while cancelable biometrics provides robust privacy when keys remain secret, it does not offer mathematical one-wayness under key disclosure. By establishing these empirical boundaries transparently, this work provides a rigorous foundation for deploying privacy-preserving multimodal authentication in real-world infrastructure.
