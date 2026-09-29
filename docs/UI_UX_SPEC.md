# UI_UX_SPEC.md (Streamlit, calls FastAPI only)

Pages (sidebar navigation):
1. **Enroll**: username; upload/select 5 face + 5 fingerprint images (or a "pick demo subject" dropdown from the test split); quality check preview; Enroll button; shows template length and key version only (never embeddings).
2. **Verify (1:1)**: username + one face + one fingerprint -> big MATCH / NO MATCH badge, score vs threshold gauge.
3. **Identify (1:N)**: probe pair -> ranked candidate table (top-5) with scores.
4. **Revoke**: pick user -> confirm -> shows new key version; verify with old vs new template to demonstrate revocation.
5. **Results**: renders `results/` plots (ROC, CMC, histograms, EER table).
6. **Threat demo** (nice-to-have): show two templates of the same user under different keys and their Hamming distance (~0.5).

UX rules: no raw data displayed after processing, clear error states (no face found), loading spinners, threshold slider labeled with resulting FMR/FNMR from the test set, footer disclosure "virtual subjects from UMDFaces + FVC2004".
