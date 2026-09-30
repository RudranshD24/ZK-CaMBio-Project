# ZK-CaMBio: Viva Presentation Slides

**Project Title:** Zero-Knowledge Cancelable Multimodal Biometrics (ZK-CaMBio)  
**Architecture:** Feature-Level Fused Face-Fingerprint Recognition with Chaos-Derived BioHashing  
**Examiner Review Deck:** 12 Core Slides + Discussion Backup  

---

## Slide 1: Title & Executive Summary
- **Title:** ZK-CaMBio: Provable Template Revocability and Empirical Boundary Analysis in Cancelable Multimodal Biometrics.
- **Problem Statement:** Compromised biometric templates cannot be revoked like passwords; centralized raw biometric databases create single-point catastrophic failure risks.
- **Our Solution:** A client-server cancelable biometric architecture combining InceptionResnetV1 (face) + FingerResNet18 (fingerprint) at feature level ($w=0.60$), transformed into a 512-bit binary cancelable template via an integer-quantized chaotic projection engine.
- **Key Empirical Results:**
  - Accuracy: Scenario K EER = $1.29\% \pm 0.23\%$ (preserves unprotected S3 baseline EER of $1.11\%$; $\Delta\text{EER} = +0.21\%$, $p > 0.05$).
  - Revocability: 100.00% rejection of compromised templates; genuine access fully restored upon re-issuance.
  - Non-Invertibility Reality Check: Linear inversion achieves 0.935 cosine fidelity if the key leaks; security rests entirely on key secrecy.
- **Key Artifact:** System Architecture Block Diagram.

---

## Slide 2: Threat Model & Meaning of "Zero-Knowledge"
- **Threat Architecture:**
  - Case A1: Database compromised (templates only, keys unknown).
  - Case A2: Database + Keys compromised (inversion & replay).
  - Case A3: Cross-system database leaks (linkage attack).
  - Case A5: Key compromised, revocation requested.
- **Definition of "Zero-Knowledge" in this Work:**
  - Defined strictly as: **Zero raw biometrics stored, zero unquantized floating-point embeddings stored, and (in user-secret mode) zero key material stored on the server.**
  - Transparent Disclosure: *No cryptographic zk-SNARK / STARK proof circuit is implemented.* Privacy is achieved through cancelable randomized projection and ephemeral key derivation.
- **Key Artifact:** `docs/SECURITY_THREAT_MODEL.md` Claims Matrix.

---

## Slide 3: Dataset Assembly & Chimeric Protocol Disclosure
- **Modalities & Preprocessing:**
  - Face: UMDFaces (InceptionResnetV1, 512-d embeddings, L2-normalized).
  - Fingerprints: FVC2004 DB1_A, DB2_A, DB3_A (FingerResNet18 V2, 256-d embeddings).
- **Virtual Subject Protocol (Chimeric Pairing):**
  - Total: 300 virtual chimeric subjects (180 train, 30 validation, 120 test).
  - Strictly disjoint subject identities across train/val/test splits.
  - Transparent Disclosure: Chimeric pairing pairs independent face and fingerprint identities; inter-modality biological correlation is zero by construction.
- **Protocol D-009:** Impostor evaluations strictly restricted to within-sensor database pairs (40 subjects/DB, 14,040 impostor comparisons pooled).
- **Key Artifact:** `data/processed/split_manifest.json` and Subject Pairing Table.

---

## Slide 4: Unprotected Baselines (Face, Fingerprint, & Fusion)
- **Face Baseline (S1):** EER = 2.00% [1.11, 3.60]%, Rank-1 = 97.22%.
- **Fingerprint Baseline (S2):**
  - Gabor Filterbank: EER = 41.10% (fails modern benchmarks).
  - FingerResNet18 V2: EER = 5.81% [4.72, 7.15]%, Rank-1 = 78.89%.
- **Multimodal Fusion (S3):**
  - Weight tuned on 30 validation subjects: $w_{face} = 0.60, w_{finger} = 0.40$.
  - Test EER drops to $1.11\% \pm 0.22\%$ (95% CI $[0.29\%, 1.66\%]$).
  - Decidability index $d' = 5.91$, Rank-1 accuracy = $99.44\%$.
- **Key Artifact:** `results/fusion_roc.png` (Comparison ROC Curves).

---

## Slide 5: The C++ Integer Chaos Engine
- **Algorithmic Design:**
  - 1D Chaotic Logistic Map with state perturbator: $x_{n+1} = r \cdot x_n (1 - x_n)$.
  - Seed derivation via HMAC-SHA256 of master key + context + user salt.
  - Deterministic 32-bit fixed-point projection matrix $R \in \{-1, +1\}^{m \times 768}$.
- **Cross-Platform Determinism:**
  - Implemented in C++17 with `-ffp-contract=off` to eliminate fused multiply-add non-determinism between MSVC (Windows) and GCC (Linux).
  - Bit-exact Known-Answer Tests (KAT) validated in Docker container: Server-key `2d8998aa`, User-secret `9ed1a9ad`.
- **Latency:** 3.95 ms per 512-bit template transform (250 ops/sec).
- **Key Artifact:** `results/chaos_hd_vs_angle.png` (Hamming Distance vs. Angle).

---

## Slide 6: Cancelable Biometrics: Performance Preservation (Scenario K)
- **Validation Tuning:** Selected $m=512$ bits on 30 validation subjects ($0.83\% \pm 0.35\%$ EER).
- **Headline Test Accuracy ($m=512$, 10 random keys):**
  - Scenario K EER: $1.29\% \pm 0.23\%$ (vs. S3 unprotected $1.11\%$).
  - Rank-1 Identification: $98.81\% \pm 0.31\%$.
  - Decidability: $d' = 5.29$.
- **Rigorous Paired Bootstrap (1,000 resamples over test subjects):**
  - $\Delta\text{EER} = +0.213\%$ (95% CI $[-0.135\%, +0.688\%]$; $0 \in \text{CI}$, performance degradation statistically indistinguishable from zero).
  - $\Delta\text{FNMR@1\%} = +0.276\%$ (95% CI $[-0.333\%, +1.167\%]$; $0 \in \text{CI}$).
  - Honest disclosure: $\Delta\text{FNMR@0.1\%} = +1.311\%$ (95% CI $[+0.333\%, +2.722\%]$; degradation is detectable at strict operating points).
- **Key Artifact:** `results/cancelable_roc.png` and `results/cancelable_cmc.png`.

---

## Slide 7: Scenario U: Cryptographic Isolation vs. Biometric Accuracy
- **Conceptual Clarification:**
  - In cancelable biometrics, "Scenario U" (matching different keys for the same subject) evaluates **key isolation**, not biometric accuracy.
  - Matching probe (Key $K_B$) against gallery (Key $K_A$) yields pseudo-random bit disagreement: EER = 0.0000%.
  - Genuine HD under identical keys: $0.2214 \pm 0.0503$.
  - Impostor HD under distinct keys: $0.5001 \pm 0.0222$.
- **Examiner Takeaway:** Scenario U confirms that without the matching key, genuine probes are mathematically rejected as impostors.
- **Key Artifact:** `results/cancelable_scenario_u_dist.png`.

---

## Slide 8: Template Revocability (ISO/IEC 30136)
- **Revocation Protocol:**
  - Compromised key is revoked; user is issued fresh key $K_{v+1}$.
  - Stored template is regenerated; old template is marked inactive.
- **Empirical Demonstration:**
  - Genuine probes presented against revoked templates yield **FNMR = 100.00% rejection** at both validation operating thresholds ($\tau_{eer} = 0.3504, \tau_{0.1\%} = 0.3010$).
  - Same subject under different keys produces mean Hamming distance $0.5006 \pm 0.0219$, indistinguishable from cross-subject impostors ($0.4999$).
  - Re-enrollment under new key immediately restores genuine verification (FNMR = 1.67%).
- **Key Artifact:** `results/cancelable_revocability_dist.png`.

---

## Slide 9: Template Unlinkability (ISO/IEC 30136 Benchmarking)
- **Benchmark:** Gomez-Barrero et al. (2017) unlinkability metric across multiple pseudo-identities.
- **Score-Based Adversary (Keys Unknown):**
  - Mated distribution (same person, different keys across services) overlaps non-mated distribution (different persons, different keys).
  - Global linkability metric: $D_\leftrightarrow^{sys} = 0.0245 \ll 0.10$ threshold (fully unlinkable).
- **Linkage Attack under Known Keys (Threat A3):**
  - If keys are leaked across services, an adversary reconstructs embeddings and computes cosine similarity.
  - Linkage AUC surges to 0.9980, and $D_\leftrightarrow^{sys}$ surges to 0.9649 (unlinkability collapses).
- **Key Artifact:** `results/cancelable_unlinkability.png`.

---

## Slide 10: Non-Invertibility Reality Check (Threat A2)
- **The Core Question:** *Is random projection cancelable biometrics one-way?*
- **Empirical Evidence:**
  - Evaluated 4 inversion attacks: Back-projection, Learned Ridge Linear Decoder, Prior-Regularized Optimization, MLP.
  - Ridge decoder recovers fused 768-d biometric vectors with **cosine similarity $0.9335 \pm 0.0115$** ($0.9354$ uncentered) at $m=512$.
  - Replay of reconstructed vectors against unprotected S3 achieves **100.0% false match** at 1% and 0.1% FMR.
- **Critical Conclusion:** Random projection binarization is **NOT** a one-way trapdoor function. System security rests entirely on key secrecy.
- **Key Artifact:** `results/privacy_utility_tradeoff.png`.

---

## Slide 11: Production Engineering & System Hardening
- **FastAPI Backend + Streamlit UI:**
  - Architectural decoupling: UI service communicates strictly via HTTP JSON; zero imports of ML models, key derivations, or C++ chaos engine.
  - Secrets hygiene: Client secrets handled exclusively in masked password inputs; never cached, echoed, or stored.
- **Defense in Depth:**
  - Per-user salt (`users.kdf_salt`, 16 bytes) + Argon2id/scrypt key stretching ($N=16384, r=8, p=1$).
  - Timing-safe authentication token validation (`hmac.compare_digest`).
  - Score suppression outside `DEV_MODE` to mitigate hill-climbing attacks.
  - Database-persisted exponential delay lockout (victim cannot be permanently locked out by third-party attackers).
- **Containerization:** Multi-stage Docker Compose (PostgreSQL 16, API, UI).
- **Key Artifact:** `results/live_docker_lifecycle.txt` and `docs/screenshots/`.

---

## Slide 12: Project Limitations & Future Directions
- **Transparent Engineering Limitations:**
  1. *Chimeric Pairing:* Independent face/fingerprint pairing ignores inter-modal biological correlations.
  2. *Scale:* Evaluated on 120 test virtual subjects; requires million-subject scaling tests.
  3. *Encoder Pretraining:* VGGFace2 pretraining may share identities with UMDFaces.
  4. *Inversion Vulnerability:* Once keys leak, linear decoders invert templates; true non-invertibility requires cryptographic homomorphic encryption or functional commitments.
  5. *Presentation Attack Detection:* Liveness detection is out of scope.
  6. *Raw Bitstring Replay:* Verbatim template replay at network layer requires challenge-response freshness or 2FA key derivation.
- **Examiner Summary:** ZK-CaMBio provides rigorous performance preservation, provable revocability, and cross-service unlinkability, accompanied by an honest, empirically validated appraisal of security boundaries.
