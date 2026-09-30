# 5-Minute Viva Demo Script & Examiner Q&A Guide

**Project**: ZK-CaMBio: Zero-Knowledge Cancelable Multimodal Biometrics (Phase 8 UI)  
**Target Environment**: Containerized Local Stack (`http://localhost:8501`)  
**Architecture Boundary**: UI communicates strictly via REST API over HTTP; zero models, keys, or chaos engine code are imported into the UI layer.

---

## 1. Five-Minute Viva Demonstration Walkthrough

### Step 1: System Overview & Architecture Boundary (0:00 – 0:45)
- **Presenter Action**: Open `http://localhost:8501`. Highlight the clean sidebar navigation, the `DEV_MODE` status indicator, and the mandatory research disclosure footer:
  > *"Virtual subjects built from UMDFaces + FVC2004 (independent identities paired for research). Research prototype."*
- **Talking Points**:
  - ZK-CaMBio protects multimodal biometrics by fusing InceptionResnetV1 face embeddings and fine-tuned FingerResNet18 embeddings ($w=0.60$), then projecting them into a 512-bit cancelable bitstring using a bit-exact integer logistic-map chaotic projection engine.
  - The Streamlit interface acts strictly as an external client talking to FastAPI; it never handles raw floating-point embeddings, neural weights, or cryptographic master keys.

---

### Step 2: Subject Enrollment & Quality Gates (0:45 – 1:30)
- **Presenter Action**:
  1. Navigate to **Enroll** page.
  2. Enter Username: `alice_demo`.
  3. Select Key Mode: `user_secret`. Enter a secure passphrase: `VivaDemoSecret_2026!`.
  4. Select **Pick Demo Subject (Test Split)**: select `VS_0181 (DB1)`.
  5. Point out the quality check badge: `Quality Check: PASS (≥3 consistent samples)`.
  6. Click **Enroll Subject**.
- **Expected On-Screen Result**:
  - Success banner: `🎉 Enrollment Successful!`
  - Response JSON: `user_id`, `username: "alice_demo"`, `key_mode: "user_secret"`, `key_version: 1`, `m: 512`, `status: "enrolled"`.
  - The UI explicitly highlights: *Stored template is 64 bytes (512 bits). Zero raw biometric images or floating-point embeddings are stored.*
- **Failure Case Demonstration (Optional 15s)**:
  - Switch Source Selection to **Demonstrate Quality Failure Case** -> `Blank / Missing Face (No Face Detected)`.
  - Click **Enroll Subject**.
  - On-screen error: `❌ Enrollment Failed (Status 400): No face detected in impression 1`. Shows quality enforcement (FR-12).

---

### Step 3: Genuine Verification (1:30 – 2:15)
- **Presenter Action**:
  1. Navigate to **Verify (1:1)** page.
  2. Claimed Identity: Username `alice_demo`, Passphrase `VivaDemoSecret_2026!`.
  3. Probe Selection: **Genuine Probe (Same Subject)**.
  4. Review the informational threshold slider: $\tau = 0.3504$ displaying Validation FMR = 0.85% and FNMR = 1.67%.
  5. Click **Verify Probe**.
- **Expected On-Screen Result**:
  - Prominent badge: `✅ MATCH` (Green).
  - In `DEV_MODE`: bold banner appears:
    > `⚠️ DEMO MODE: scores visible; production hides them because scores enable hill-climbing attacks`
  - Metrics: Hamming Distance $\approx 0.21 - 0.28 \le \text{Threshold } 0.3504$.

---

### Step 4: Impostor Verification & Lockout Resilience (2:15 – 3:00)
- **Presenter Action**:
  1. Keep Username `alice_demo`.
  2. Under Probe Selection, choose **Impostor Probe (Pick an Impostor)** (e.g. `VS_0182` or `VS_0190`).
  3. Click **Verify Probe**.
- **Expected On-Screen Result**:
  - Prominent badge: `❌ NO MATCH` (Red).
  - In `DEV_MODE`: Hamming distance displayed $\approx 0.48 - 0.52 > 0.3504$.
  - Demonstrate rate limiting / lockout resilience: show that multiple rapid failed attempts trigger escalating delays in `auth_rate_limits`, and click **Reset Lockout for Demo User** to restore immediate presenter access without restarting the server.

---

### Step 5: Revocation & Key Rotation (3:00 – 3:45)
- **Presenter Action**:
  1. Navigate to **Revoke** page.
  2. Enter Username `alice_demo`. Click **Revoke Active Template**.
  3. Observe the confirmation: Revoked Version `v1` $\to$ New Eligible Version `v2`; KDF salt regenerated.
  4. Under **Revocation Rejection Verification**, click **Test Verify Against Revoked User**.
- **Expected On-Screen Result**:
  - Success alert: `🛡️ Revocation Enforced: Status=400: No active template found for user 'alice_demo'`.
  - Proves **100.00% FNMR against revoked templates** (ISO/IEC 30136 standard requirement).

---

### Step 6: 1:N Identification Boundary (3:45 – 4:15)
- **Presenter Action**:
  1. Navigate to **Identify (1:N)** page.
  2. Point to the explanation banner:
     > *"1:N Identification is enabled ONLY for accounts enrolled in server_key mode. Accounts enrolled with user_secret derive chaotic projection keys client-side from personal passphrases; because the server possesses zero key material for these users, comparing an unkeyed probe against all templates would require brute-forcing all user secrets or performing unkeyed cross-matching, which is cryptographically impossible and explicitly prohibited by the threat model."*
  3. Run identification on enrolled `server_key` gallery to display top-$K$ candidate table.

---

### Step 7: Results Page & Threat Demo (4:15 – 5:00)
- **Presenter Action**:
  1. Navigate to **Results** page:
     - Tab 1: Show ROC and Rank-1 CMC curves (98.81% Scenario K identification).
     - Tab 2: Show ISO/IEC 30136 Unlinkability ($D_\leftrightarrow^{sys} = 0.0245 \ll 0.10$).
     - Tab 3: Show Privacy-Utility Tradeoff figure across $m$.
     - Tab 4: Review the explicit Claims Table.
  2. Navigate to **Threat Demo** page:
     - Point out the 512-bit templates under keys $K_A, K_B$ showing exact Hamming distance 0.5006 (chance correlation).
     - Point out the honest Phase 6 inversion finding table: *Ridge decoder achieves 0.935 cosine when the key is known. System security relies strictly on key secrecy.*

---

## 2. Likely Examiner Questions & Short Honest Answers

### Q1: Is the cancelable template non-invertible?
> **Answer**:  
> *"It depends strictly on whether the adversary possesses the key. If the key is secret (Threat Case A1), the search space is at most $2^{126}$ operations, and distinguishing templates of different subjects performs at chance (AUC = 0.4767). However, if the key leaks (Threat Case A2), random projection binarization is **not** a one-way trapdoor function: our empirical evaluation in Phase 6 proved that a Ridge decoder reconstructs vectors with 0.935 cosine similarity at $m=512$, achieving 100% replay success. We report this transparently as a lower bound on empirical leakage."*

---

### Q2: What happens if the database leaks?
> **Answer**:  
> *"In default `user_secret` mode, the database contains only packed 512-bit binary templates and non-secret per-user salts (`users.kdf_salt`). It contains zero raw images, zero floating-point embeddings, and zero user secrets or keys. An attacker with a leaked database is in Threat Case A1: they cannot invert templates or link users across databases without the keys. If both the database AND the server app salt leak, low-entropy user passphrases could be targeted via offline dictionary search, which is why we enforce $\ge 8$ character complexity and memory-hard `scrypt` key stretching."*

---

### Q3: What happens if a user's key leaks?
> **Answer**:  
> *"If a key leaks, that user's template is compromised (inversion and cross-system linkage become possible). However, ZK-CaMBio fulfills ISO/IEC 30136 Revocability: the compromised template can be immediately revoked via `/revoke`. Revocation retires the template (causing 100.00% rejection of probes under the old key) and generates a fresh per-user salt and new key version $v+1$. Re-enrollment completely restores genuine matching without changing the user's physical biometric."*

---

### Q4: Why did you use chimeric data instead of a real multimodal dataset?
> **Answer**:  
> *"Public datasets with paired face and fingerprint images under open research licenses (like BiosecurID or SDUMLA-HMT) require formal organizational institutional agreements that could not be approved within our project timeline. We constructed 300 virtual chimeric subjects by pairing UMDFaces with FVC2004 sensors DB1–DB3 under seed 42. As documented in ADR D-001 and D-012, chimeric pairing assumes statistical independence between modalities, which is standard practice in multimodal biometric literature, though it may slightly over- or under-estimate real-world cross-modal covariances."*

---

### Q5: Why did the genuine test enrollment rejection drop from 15% to 0.00%?
> **Answer**:  
> *"Originally, enrollment quality thresholds were calibrated on the 180 training subjects ($\tau_{\text{finger}} = 0.70$). Because the FingerResNet18 encoder had slightly overfit training impressions, genuine test impressions exhibited lower intra-subject compactness, causing a 15% false rejection rate. In Phase 7c, we recalibrated thresholds strictly using the 30 validation subjects (whose fingers were never used for encoder training), setting $\tau_{\text{finger}} = 0.60$ and requiring $\ge 3$ consistent impressions. The 0.00% test rejection rate is an observed outcome of a revised gate after a first test-set look, not a pure held-out estimate, and we disclose that the quality gate is slightly weaker at 0.60 than at 0.70."*

---

### Q6: Why is 1:N identification disabled for `user_secret` accounts?
> **Answer**:  
> *"Because chaotic projection keys are derived client-side from the user's secret passphrase, which is never stored on the server. To perform 1:N identification on unkeyed probes, the server would have to either possess all user keys (violating client key ownership) or brute-force every user's secret passphrase upon each query, which is computationally intractable. 1:N identification is therefore restricted to `server_key` mode, where keys are stored in an encrypted database table."*

---

### Q7: Why do `/verify` and `/identify` hide numeric similarity scores outside `DEV_MODE`?
> **Answer**:  
> *"Returning granular similarity scores or Hamming distances provides a numeric gradient signal that enables iterative hill-climbing attacks. An adversary submitting synthetic biometric probes could optimize inputs toward lower Hamming distances until authentication succeeds. Returning only boolean MATCH / NO MATCH eliminates this direct gradient feedback."*
