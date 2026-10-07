# MASTER PROMPT: build the ZK-CaMBio research paper (about 30 pages)
Paste into Antigravity (Planning mode) in the project root `D:\Biometric Project`. Use Claude for writing, theory and review; Gemini for scripts, tables and LaTeX building.

---

You are helping me turn my finished biometrics project into a research paper of about 30 pages. I am a student. The paper must be honest, reproducible and verifiable. Quality is more important than hitting 30 pages: never pad.

## Inputs (read first, in this order)
1. `paper/paper_v0.md` (my current draft) and `docs/PAPER_REVIEW.md` (the fix list; apply every item).
2. `docs/DECISIONS.md`, `docs/SECURITY_THREAT_MODEL.md`, `docs/EVALUATION_PLAN.md`, `docs/ARCHITECTURE.md`, `docs/DATASET_PLAN.md`.
3. `results/` (every number comes from here), `configs/biometric_parameters.json`, the code in `src/`, `cpp/`, `experiments/`.
4. `docs/REFERENCES.md` and `paper/references.bib` (the only allowed bibliography source).

## Hard rules
- **Numbers:** every number in the paper must come from a file in `results/` through `scripts/generate_paper_tables.py`, which writes LaTeX tables and figure lists. No typed-in numbers. If a number is missing, run or write the experiment; do not estimate.
- **Citations:** cite only keys in `references.bib`. Entries marked ⚠️ in REFERENCES.md must stay `[VERIFY]` in the text and be listed in `paper/VERIFY_LIST.md` for me to check. Never invent a reference, quote, page number, DOI or result from another paper. Describe prior work only at the level the REFERENCES.md note supports; if you need more detail, ask me to supply the paper.
- **No overclaims:** never write "provable", "production-grade", "secure", "irreversible" or "non-invertible" without the qualifier it needs ("without the key", "against the attacks tested"). Never claim superiority over prior work (different data, different protocols). No p-values unless computed.
- **Zero-knowledge:** define exactly as "no raw biometrics stored and, in user_secret mode, no key material stored". State that no ZK proof is implemented, and contrast with real ZK-biometric schemes in the references.
- **Chimeric data:** disclose in the abstract, cite Poh and Bengio (2005) as a caution, and report the pairing-sensitivity experiment (E1).
- **Honest negative results go in the paper:** key compromise reconstructs fused vectors with cosine about 0.93; unlinkability fails when keys are known; V1 fingerprint preprocessing failed; the enrollment gate threshold was revised after a test-set look; the extra-data gain is within noise.
- Do not change code or results except to add the experiments below. Commit each stage. After each stage give a 5-line summary and STOP for my approval.

## Format and page budget
Default: LaTeX `article`, 11 pt, single column, 1 inch margins, 1.15 line spacing, numbered sections, BibTeX (numeric style), figures as PDF. Ask me first whether my college requires a template (IEEE, Springer LNCS, or a thesis format); the budget below assumes the default.

| Part | Pages | Content |
|---|---|---|
| Title, abstract, keywords | 1 | abstract about 200 words, limitations stated |
| 1 Introduction | 2.5 | motivation, problem, 4 requirements (ISO/IEC 24745 terms), contributions (modest), paper outline |
| 2 Related work | 4 | themes in REFERENCES.md sections 1-9, one comparison table |
| 3 Preliminaries and threat model | 3 | notation, SimHash/angle proposition (with the +-1 caveat), attacker table A1-A6, what each metric measures |
| 4 Method | 4 | encoders, V2 fingerprint preprocessing, fusion, chaos engine, integer determinism, key derivation (scrypt, per-user salt), algorithms as pseudocode, parameter table |
| 5 Dataset and protocol | 3 | UMDFaces and FVC2004 (correct sensor facts), chimeric pairing, splits, D-009 impostor rule with the counting formula, leakage controls, statistics (bootstrap) |
| 6 Results: recognition | 3.5 | unprotected baselines, fusion, cancelable Scenario K, m and w ablations, per-DB results, pairing sensitivity (E1) |
| 7 Results: privacy properties | 3 | revocability, unlinkability (score-only vs keys known), key-space accounting, template-only distinguisher |
| 8 Security analysis | 3 | four attacks, privacy-utility trade-off versus m, replay, hill-climbing, claims table |
| 9 Discussion and limitations | 2 | why accuracy preservation and invertibility are linked, comparison to the literature (qualitative), all limitations, deployment recommendations (two-factor key mode) |
| 10 Conclusion and future work | 0.7 | includes challenge-response and real ZK as future work |
| References | 2 | |
| Appendices | 3 | A proofs/derivations, B hyperparameters and KATs, C extra plots, D reproducibility checklist, E ethics, data licences, AI-assistance statement |
Total about 33 before trimming; cut Appendix C first if over. If under 30, add only content from the "allowed additions" list.

## Extra experiments (only these; each writes to `results/` with raw scores saved)
- **E1 (required) Pairing sensitivity:** repeat face-finger pairing and the 180/30/120 split-preserving test pairing with 10 seeds (embeddings are cached; the encoders are NOT retrained, so only which test face goes with which test finger changes). Report mean and SD of fused EER, FNMR@0.1%, and Scenario K EER. State clearly what is and is not re-randomised.
- **E2 (required) Consistency of every headline number** across docs, results and code (`docs/CONSISTENCY_AUDIT.md`); list any mismatch with its source.
- **E3 (required) All CIs from one function and seed;** paired bootstrap for K minus S3 at EER, FNMR@1%, FNMR@0.1%.
- **E4 (required) Attack prior sensitivity:** repeat the A2 reconstruction attack with the decoder trained only on the 30 validation subjects, and on synthetic Gaussian data with the correct covariance, at m in {128, 512}.
- **E5 (optional) Hill-climbing on the match endpoint:** with scores (DEV_MODE) versus match/no-match only. Report the number of queries needed to succeed on 20 victims for a fixed budget (e.g. 5,000 queries). This tests the design choice to hide scores.
- **E6 (optional) Two-factor key mode:** attacker with database + master key but no user secret; show reconstruction fails (A1-like), and the offline-guessing cost for 6-digit PINs versus an 8-character passphrase with the pinned scrypt parameters (measured time per guess).
- **E7 (optional) Latency:** enroll and verify latency table (CPU), template size, storage.
Allowed additions beyond these: more per-DB tables, more ablation plots, algorithm boxes, a worked numerical example of the SimHash identity, a notation table, a glossary.

## Staged workflow (stop after each stage)
- **Stage A, audit:** apply PAPER_REVIEW.md to a copy `paper/paper_v1.md`; create `docs/CONSISTENCY_AUDIT.md`; list unresolved questions for me.
- **Stage B, references:** build `references.bib` from my verified entries; produce `paper/VERIFY_LIST.md` of every ⚠️ entry with exactly what I need to check (authors, year, venue, pages). Do not add new references without listing them as ⚠️.
- **Stage C, experiments:** run E1-E4 (and any optional ones I approve); update `results/` and the table generator.
- **Stage D, sections 1-5** in LaTeX with figures and tables generated by script.
- **Stage E, sections 6-10** likewise.
- **Stage F, appendices and front matter.**
- **Stage G, build and QA:** build the PDF (latexmk or tectonic; if no TeX is installed tell me what to install, or fall back to Markdown + pandoc and say so). Report page count, run a spell check, check that every citation resolves, every figure/table is referenced, every number matches `results/`, and that no `[VERIFY]` remains unlisted. Produce `paper/QA_REPORT.md`.

## Writing guide
- Claim, then evidence, then limit. One idea per paragraph. State the number and its CI in the sentence that makes the claim.
- Prefer "we observe" over "we prove". Distinguish what holds by construction (revocation rejects old templates) from what was measured (inversion cosine).
- The central finding to develop in the Discussion: the transform preserves angular similarity (HD about theta/pi), which is why accuracy is preserved and also why the template leaks once the key is known; security therefore rests on key secrecy, so key management (two-factor key derivation, key separation from the template store) is part of the contribution.
- Related work: organise by theme, state what each line of work shows, then where this paper sits. Include literature that contradicts the idea of calling cancelable templates "irreversible".
- Use consistent scenario names (final names from D-012). Define every symbol once in a notation table.
- Disclose AI assistance in the build and writing as my college requires; I will edit that statement.

## Output
`paper/main.tex`, `paper/sections/*.tex`, `paper/references.bib`, `paper/figures/*.pdf`, `paper/tables/*.tex`, `paper/main.pdf`, `paper/VERIFY_LIST.md`, `paper/QA_REPORT.md`, `docs/CONSISTENCY_AUDIT.md`.

## Start now
Do only this: (1) confirm you read the inputs and list, in 10 lines, the biggest problems you see in `paper_v0.md` beyond PAPER_REVIEW.md; (2) ask me the template/format question and any missing information; (3) propose the plan for Stage A and stop.
