# SECURITY_THREAT_MODEL.md

## Assets
Raw images, embeddings, fused vector (never stored in database; transient in memory); cancelable template (stored in database); user master key (stored in secure credential vault/hardware token).

## Attacker Cases
| ID | Attacker has | Goal | Expected defense | Empirical Finding (Phase 6, D-015) |
|---|---|---|---|---|
| A1 | Template DB only (key unknown) | Recover embedding / images; distinguish identities | Key secrecy; massive key-space ($2^{126}$); zero-information distinguishing | Distinguisher AUC = 0.4767 (chance ~0.50); brute force $> 10^{22}$ GPU-years |
| A2 | Template DB + keys known | Invert template & replay against unprotected matchers | Weak defense; empirical reconstruction measured honestly | High inversion: ridge cosine = 0.9335 ($m=512$), 100% replay success vs S3 |
| A3 | Two templates + both keys known | Link accounts across systems / key versions | System cross-matching | Unlinkability collapses ($D_\leftrightarrow^{sys} = 0.9649$, AUC = 0.9980) |
| A4 | Stolen template, replays it | Authenticate against cancelable API | Zero-knowledge proof of freshness / challenge-response | Replay blocked if challenge-response freshness enforced (Phase 7) |
| A5 | Old template after revocation | Authenticate with revoked key | Revocation threshold ($\tau = 0.350$) | FNMR = 100.00% (100% rejection under revoked key) |
| A6 | Brute-force probes | Impersonate victim | Rate limiting; decision threshold on low FMR | FMR operating point fixed at $\le 0.1\%$ |

## What Non-Invertibility Means Here
In this work, "non-invertibility" does **not** denote an information-theoretic or cryptographic one-way proof. Instead, it refers to **empirical resistance measured against specific, realistic threat models**:
1. **No Cryptographic Proof**: Random projection with 1-bit binarization is not a one-way trapdoor function. While individual sign bits discard magnitude information ($d=768 \to m$ bits), collective linear measurements under a known matrix $R$ yield a well-conditioned linear inversion problem.
2. **Leakage Scales with Projection Dimension $m$**: When the key $K$ (and thus $R$) is known (Threat Case A2), reconstruction quality increases monotonically with $m$: from $\cos(\hat{x}, x) = 0.6344$ at $m=64$ to $0.9335$ at $m=512$, and $0.9614$ at $m=1024$.
3. **Protection Relies on Key Secrecy**: The system provides strong protection **if and only if the key remains secret** (Threat Case A1). Without the key, the effective search space is $2^{126}$ operations, and distinguishing templates is statistically at chance (AUC = 0.4767).
4. **Revocation Limits Damage**: If a key and template are compromised, the victim's biometric is revocable. Issuing a new key $K_{v+1}$ immediately restores biometric security and repudiates the compromised template (FNMR = 100% rejection).

## Mitigations for Phase 7 (Architecture & Key Storage)
1. **Strict Key Separation**: Master keys are NEVER stored alongside cancelable templates in the application database (`DATABASE.md`). Templates reside in Postgres; keys are held in client secure storage (WebAuthn/hardware token) or a separate HSM/KMS.
2. **Two-Factor Key Derivation (2FA)**:
   $$K = \text{HMAC-SHA256}(\text{MasterKey}, \text{UserSecret} \parallel \text{Domain})$$
   If the database/server is compromised, an attacker lacking the user's secret PIN/token is relegated to Threat Case A1 (template-only), preventing template inversion and cross-system linkage.

## Open Security Limitations for Paper Disclosure
- **Encoder Overfitting**: Train fingerprint embeddings are slightly tighter than unseen ones; sensitivity checks show prior regularization is dominated by direct ridge regression when $m \ge 256$.
- **Logistic Map Cryptanalysis**: The fixed-point logistic map bitstream is not proven secure against algebraic state reconstruction from long bit sequences. Hardening with HMAC in counter mode is recommended for production.
- **Cross-Platform Integer Determinism**: Exact bit determinism achieved via Q64 fixed-point integer arithmetic; Linux container KAT test required prior to release.
