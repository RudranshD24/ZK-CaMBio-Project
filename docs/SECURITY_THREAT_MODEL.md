# SECURITY_THREAT_MODEL.md

## Assets
Raw images, embeddings, fused vector (never stored in database; transient in memory); cancelable template (stored in database); user master key (stored in secure credential vault/hardware token or derived with client user secret).

## Attacker Cases
| ID | Attacker has | Goal | Expected defense | Empirical Finding (Phase 6, D-015) |
|---|---|---|---|---|
| A1 | Template DB only (key unknown) | Recover embedding / images; distinguish identities | Key secrecy; massive key-space; zero-information distinguishing | Distinguisher AUC = 0.4767 (chance ~0.50); brute force $> 10^{22}$ GPU-years; key space at most $2^{126}$ by construction |
| A2 | Template DB + keys known | Invert template & replay against unprotected matchers | Weak defense; empirical reconstruction measured honestly | High inversion: ridge decoder centered cos = 0.9335, raw cos = 0.9354 ($m=512$), 100% replay success vs S3 |
| A3 | Two templates + both keys known | Link accounts across systems / key versions | System cross-matching | Unlinkability collapses ($D_\leftrightarrow^{sys} = 0.9649$, AUC = 0.9980) |
| A4 | Stolen template, replays it | Authenticate against cancelable API | Zero-knowledge proof of freshness / challenge-response | Replay blocked if challenge-response freshness enforced (Phase 7) |
| A5 | Old template after revocation | Authenticate with revoked key | Revocation threshold ($\tau_{oper} = 0.350$) | FNMR = 100.00% (100% rejection under revoked key) |
| A6 | Brute-force probes | Impersonate victim | Rate limiting; decision threshold on low FMR | FMR operating point fixed at $\le 0.1\%$ |

## Explicit Claims Table

| Category | Claim | Status | Empirical Evidence & Rigor |
|---|---|---|---|
| **What IS Shown** | **Accuracy Preservation vs Unprotected S3** | **Confirmed** | Scenario K EER = $1.29\% \pm 0.23\%$ vs S3 EER $1.11\%$. Paired bootstrap over test subjects (1000 resamples): $\Delta\text{EER} = +0.213\%$ (95% CI $[-0.135\%, +0.688\%]$, excludes 0: False; degradation indistinguishable from 0). $\Delta\text{FNMR@1\%} = +0.276\%$ (95% CI $[-0.333\%, +1.167\%]$, excludes 0: False). |
| **What IS Shown** | **$\Delta\text{FNMR@0.1\%}$ Degradation Detectable** | **Confirmed** | $\Delta\text{FNMR@0.1\%} = +1.311\%$ (95% CI $[+0.333\%, +2.722\%]$, excludes 0: True; statistically detectable increase at strict operating point). Reported transparently. |
| **What IS Shown** | **Revocability (ISO/IEC 30136)** | **Confirmed** | Genuine probes matched against revoked templates yield FNMR = 100.00% rejection under validation operating thresholds ($\tau_{oper, eer}=0.3504$, $\tau_{oper, 0.1\%}=0.3010$). Re-enrollment with new key version completely restores genuine recognition (FNMR = 1.67%). |
| **What IS Shown** | **Unlinkability Without Keys (Score-Based Adversary)** | **Confirmed** | Gomez-Barrero benchmark evaluated with different biological samples across systems: $D_\leftrightarrow^{sys} = 0.0245 \ll 0.10$. Template distinguisher classifier performs at chance (AUC = 0.4767). |
| **What is NOT Shown** | **Non-Invertibility Given the Key** | **Refuted / Weak** | Random projection binarization is NOT a one-way trapdoor function. Given the key (matrix $R$), linear decodability (Ridge decoder) reconstructs vectors with high cosine similarity ($\cos(\hat{x}_c, x_c) = 0.9335 \pm 0.0115$, $\cos(\hat{x}_u, x) = 0.9354 \pm 0.0120$ at $m=512$). Replay against unprotected S3 achieves 100.0% success at 1% and 0.1% FMR. Results are a lower bound on empirical leakage. |
| **What is NOT Shown** | **Unlinkability Given the Keys** | **Refuted / Collapses** | When both keys are known, reconstructing estimated embeddings enables cross-system account linkage: ROC AUC = 0.9980, EER = 1.63%, and $D_\leftrightarrow^{sys}$ surges to 0.9649. Unlinkability does NOT survive key compromise. |
| **What is NOT Shown** | **Resistance to Raw Template Replay at API** | **Not Inherent** | If an adversary obtains the packed bitstring template and replays it verbatim across the network to an API accepting identical bitstrings, Hamming distance is 0.0000. Resistance requires challenge-response freshness or 2FA key derivation (implemented in Phase 7). |

## What Non-Invertibility Means Here
In this work, "non-invertibility" does **not** denote an information-theoretic or cryptographic one-way proof. Instead, it refers to **empirical resistance measured against specific, realistic threat models**:
1. **No Cryptographic Proof**: Random projection with 1-bit binarization is not a one-way trapdoor function. While individual sign bits discard magnitude information ($d=768 \to m$ bits), collective linear measurements under a known matrix $R$ yield a well-conditioned linear inversion problem.
2. **Leakage Scales with Projection Dimension $m$**: When the key $K$ (and thus $R$) is known (Threat Case A2), reconstruction quality increases monotonically with $m$: from $\cos(\hat{x}_c, x_c) = 0.6229$ at $m=64$ to $0.9335$ at $m=512$, and $0.9614$ at $m=1024$. The ridge decoder is the strongest attack tested; results are a **lower bound on empirical leakage**.
3. **Protection Relies on Key Secrecy**: The system provides strong protection **if and only if the key remains secret** (Threat Case A1). Without the key, the effective search space is **at most $2^{126}$ by construction (upper bound; logistic-map state recovery was NOT evaluated)**, and distinguishing templates of different subjects is statistically at chance (AUC = 0.4767).
4. **Revocation Limits Damage**: If a key and template are compromised, the victim's biometric is revocable. Issuing a new key $K_{v+1}$ immediately restores biometric security and repudiates the compromised template (FNMR = 100% rejection).

## Implemented Mitigations in Phase 7 & 7b (Architecture, Key Storage & API Hardening)
1. **Strict Key Separation, User Secret Mode & Key Stretching (ADR D-016)**:
   - Master keys are NEVER stored alongside cancelable templates in the application database (`docs/DATABASE.md`).
   - **User Secret Mode (`key_mode = "user_secret"`, Default & Enforced for Verification)**:
     $$\text{stretched\_secret} = \text{scrypt}(\text{user\_secret}, \text{salt}=\text{app\_salt}, N=16384, r=8, p=1, dklen=32)$$
     $$K = \text{HMAC-SHA256}(\text{app\_salt}, \text{stretched\_secret} \parallel \text{key\_version})$$
     - **Secret Complexity Policy**: Enforces minimum length $\ge 8$ characters and rejects common weak dictionary values (`password123`, `12345678`, `admin123`, etc.).
     - **Offline Brute-Force Disclosure**: The user secret is provided only during enroll and verify in volatile RAM and is never stored in the database. If the server database is breached, the attacker possesses only cancelable bitstring templates (Threat Case A1) and cannot invert them without the key. However, **if the server master key (app_salt) AND the stored template both leak, low-entropy user secrets can be brute-forced offline** by guessing secrets, deriving candidate keys, projecting known biometric priors, and checking matching scores. The memory-hard `scrypt` key stretching parameter ($N=16384, r=8, p=1$, maxmem 32 MB) significantly increases the cost of dictionary and GPU-based offline search.
     - Identification (`/identify`) is strictly disabled for user_secret accounts to prevent unkeyed or dictionary matching.
   - **Server Key Mode (`key_mode = "server_key"`)**: Enrolled keys are encrypted using AES-256-GCM and stored in the dedicated `user_keys` table. Exclusively used when 1:N identification is required.

2. **Score Suppression & Hill-Climbing Defense (Phase 7b)**:
   - `/verify` and `/identify` return **ONLY** boolean match/no-match status (and integer candidate rank for `/identify`) by default.
   - Numeric similarity scores (Hamming distance) are suppressed from API responses and returned ONLY when `DEV_MODE=true` is explicitly set in backend configuration.
   - The persistent `audit_log` table stores no numeric similarity scores outside `DEV_MODE=true`.
   - **Hill-Climbing Defense Rationale**: In a biometric hill-climbing attack, an adversary submits synthetic probe images and observes granular similarity score feedback (or distance deltas). By iteratively perturbing synthetic face or fingerprint inputs in the direction of score improvement, the adversary can reconstruct a synthetic biometric that matches the enrolled template without direct access to the template or key. By quantizing the API output to a single binary bit (match/no-match), the gradient signal is eliminated, preventing score-guided iterative convergence.

3. **Persistent Escalating Delay Lockout (A6 / DoS Defense, Phase 7b)**:
   - Failed verification attempts are tracked in the database table `auth_rate_limits`, persisting across server restarts and multi-worker API deployments.
   - **Escalating Delays**: Instead of a crude permanent or fixed 15-minute lock, delays scale smoothly per identifier ($k < 3$: 0s; $k=3$: 2s; $k=4$: 5s; $k=5$: 15s; $k=6$: 30s; $k \ge 7$: $\min(60 \cdot 2^{k-7}, 300)$s).
   - **Dual IP & Username Counters**: Failures are counted independently per username AND per client IP address. An attacker on an external IP cannot permanently lock out a legitimate victim user because:
     1. IP-based limits throttle the attacker's network rate directly.
     2. Username lockout applies an escalating delay window rather than a permanent denial-of-service, ensuring legitimate users can authenticate once the delay period lapses.

4. **Timing-Safe Authentication**:
   - Bearer authentication tokens are compared strictly using `hmac.compare_digest` to prevent timing side-channel leaks against the API secret.

5. **In-Memory Biometric Processing**:
   - Images are streamed, processed, and garbage-collected in `try ... finally` blocks. Database schema enforces zero columns capable of holding biometric images or raw embeddings ([test_schema_whitelist_no_raw_biometrics](file:///D:/Biometric%20Project/tests/test_schema_no_biometrics.py)).

6. **Cross-Platform Bit-Level Determinism (Verified)**:
   - Exact bit determinism was verified via Docker container KAT (`tests/run_linux_kat.sh` and `tests/linux_kat_test.py`). Linux GCC and Windows MSVC produce identical KAT hashes:
     - Server key KAT: `83ec0508a8d11c75`
     - Stretched user secret KAT: `a8a71999ef4a6015`

## Open Security Limitations for Paper Disclosure
- **Encoder Overfitting Sensitivity**: Attacker prior/decoder trained on 30 validation subjects only (no train fingerprints) still achieves centered cosine $0.8937 \pm 0.0235$ and 100.0% replay success at $m=512$, confirming vulnerability is structural to known linear projections, not an artifact of encoder overfit.
- **Offline Dictionary Attack Risk**: In user_secret mode, joint leakage of the server app salt and template database enables offline dictionary search against weak user passphrases.
- **Logistic Map Cryptanalysis**: The fixed-point logistic map bitstream is not proven secure against algebraic state reconstruction from long bit sequences. Hardening with HMAC in counter mode is recommended for production.
- **Cross-Platform Integer Determinism**: Exact bit determinism achieved via Q64 fixed-point integer arithmetic and validated across MSVC and Linux GCC containers.

