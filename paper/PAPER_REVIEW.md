# Review of your draft (paper.md): fix list before expanding to 30 pages

Status legend: **[ERROR]** factually wrong or contradicted by a source I checked; **[OVERCLAIM]** wording stronger than your evidence; **[INCONSISTENT]** differs from what the project docs say you built (verify against DECISIONS.md and the code); **[MISSING]** needed for a credible paper.

## A. Citation and factual errors
1. **[ERROR] VGGFace2 venue.** Cited as "BMVC 2018". It is IEEE FG 2018 (Cao, Shen, Xie, Parkhi, Zisserman; arXiv 1710.08092).
2. **[ERROR] Unlinkability metric source.** You cite "Gomez-Barrero et al., 2017, Information Sciences" for D_sys. The metric is from "General Framework to Evaluate Unlinkability in Biometric Template Protection Systems", IEEE Transactions on Information Forensics and Security, vol. 13, pp. 1406-1420, 2018 (DOI 10.1109/TIFS.2017.2788000). Fix the in-text cite and Table 3.
3. **[ERROR / unverified] "Ngo et al., 2009, Biometric encryption: The dark side of BioHashing".** I could not find this paper. Do not cite it. For the stolen-token problem cite Teoh, Kuan and Lee (Pattern Recognition 41(6), 2008) and Lumini and Nanni (Pattern Recognition 40, 2007); for the "zero EER rests on a hidden assumption" argument cite Kong et al. (Pattern Recognition, 2006).
2b. **[CHECK] Ross and Jain, "Information fusion in biometrics".** I believe it is Pattern Recognition Letters 24(13), 2003, not 2004. Verify.
4. **[ERROR] FVC2004 sensors.** You write DB2 "optical 569 dpi". 569 dpi is FVC2002's DB2. FVC2004 DB1 is optical, 640x480, 500 dpi; DB2 is optical, 328x364, about 500 dpi; DB3 is a thermal sweeping sensor, 300x480, 512 dpi; DB4 is synthetic (SFinGe). Check against the Handbook of Fingerprint Recognition 3rd ed. that you own.
5. **[OVERCLAIM] ISO/IEC 30136 attribution.** The irreversibility / unlinkability / renewability requirements come from ISO/IEC 24745; ISO/IEC 30136:2018 specifies performance testing and reporting of template protection schemes. "FNMR after revocation = 100%" is not an ISO/IEC 30136 metric. Label those rows "evaluated following the ISO/IEC 30136 guidance and the Gomez-Barrero et al. framework". Also: 100% rejection after a key change is largely true by construction (different key gives Hamming distance near 0.5, above the threshold). Say it is a sanity check, not a deep result.
6. **[ERROR] "Moore-Penrose pseudo-inverse" for Atk-1.** x_hat = R^T(2b-1) is back-projection (the transpose), not the pseudo-inverse. Rename it.
7. **[ERROR / precision] Section 2.2.** Pr[sign differs] = theta/pi is exact for Gaussian (rotation-invariant) r. Your R has +-1 entries, so it holds approximately (your measured slope about 1.01 is consistent). State this. Cite Goemans-Williamson (1995) and Charikar (2002).
8. **[CHECK] UMDFaces licence.** "creative commons / academic use" is unverified. Say "released for research use; see umdfaces.io for terms" and state that you used a 112x112 crop version.

## B. Overclaims
9. **Title.** "Provable Revocability" and "Zero-Knowledge" are not supported. Nothing is proven; revocability is measured; no ZK proof exists. Suggested title: *"ZK-CaMBio: Cancelable Multimodal Biometrics via Chaotic Projection: Accuracy, Revocability, Unlinkability and Key-Compromise Leakage"*. If you keep "Zero-Knowledge", define it in the abstract exactly as you already do.
10. **"production-engineered", "production-grade", "air-gapped".** Use "research prototype".
11. **"p > 0.05"** (Table 5, Conclusion). You computed bootstrap confidence intervals, not p-values. Remove, or compute a bootstrap p-value.
12. **"statistically indistinguishable from zero".** Write "no statistically detectable difference (the CI includes 0); with 120 test subjects, differences of up to about 0.7 points cannot be excluded".
13. **Abstract baseline "1.11% +- 0.22%".** The unprotected baseline is deterministic (no keys), so there is no SD over keys. Report the CI [0.29, 1.66]%.
14. **"D_sys = 0.0245 << 0.10 ... Fully Unlinkable".** The framework defines 0 as fully unlinkable and 1 as fully linkable; it has no official 0.10 cut-off. Say "close to 0 against a score-based adversary without key access".
15. **Intro claims "many suffer from three deficiencies".** Cite examples or soften.
16. **Conclusion "provable 100% template revocation".** See 5 and 9.
17. **"Scenario U measuring cryptographic isolation".** Use "key separation" (your own D-012 wording) and use the final scenario names.

## C. Inconsistencies with your own project record (verify each in DECISIONS.md / code)
18. **Quantization scale:** paper says round(100000 * ...); the engine used 2^20 as the fixed scale.
19. **Centering mean:** paper says mu_val (validation mean); the design said the public mean fitted on TRAIN subjects.
20. **Logistic-map range:** paper says r in (3.99, 4.0); the plan said [3.9, 4.0). Also "periodic fixed-point state perturbation" versus what was built (8192-entry cycle guard with Weyl reseed).
21. **Fingerprint encoder training:** paper says "trained solely on the 180 train subjects", with "cross-entropy and cosine-margin loss". The record says: fine-tuned ResNet18 (ImageNet-initialised) with CosFace-style margin loss on 150 fit fingers + 100 DB4_A synthetic + 40 DB*_B fingers, with early stopping on 30 validation fingers. Describe exactly that, including the synthetic data.
22. **Preprocessing:** paper describes block-variance masking; the final pipeline is the V2 fixed-scale, centroid-centred crop. Describe V2 and mention V1 failed (that is a useful honest paragraph).
23. **Face crops:** the data are 112x112 crops resized to 160x160, not "160x160 aligned crops".
24. **Impostor count:** "40 x 39 x 3 x 3 = 14,040" is ambiguous. Write: 40 subjects x 3 probes x 39 other subjects x 3 databases = 14,040.
25. **FR-12 enrollment threshold:** if you mention enrollment quality gates, note that the fingerprint threshold was revised from 0.70 to 0.60 after a first look at test-set rejection (D-017); the 0.00% test rejection is an observed outcome, not a clean held-out estimate.
26. **Replay row in Table 5** ("0.0000 Hamming distance"): say whether this was measured or follows by construction. If not measured, write "by construction".

## D. Missing content (this is where the extra pages should come from, honestly)
27. **Related work is thin (8 references).** Add: template-protection surveys (Nandakumar and Jain 2015; Patel, Ratha and Chellappa 2015), BioHashing attacks (preimage attacks, stolen-token analyses), inverse biometrics (Gomez-Barrero and Galbally 2020; Mai et al.), multibiometric template protection (Nagar et al. 2012), fuzzy commitment / vault / fuzzy extractors, ZK-proof-based biometric authentication, and chaos-based crypto critique. See REFERENCES.md.
28. **Chimeric-data validity.** Poh and Bengio (MLMI 2005) argued that using chimeric users in multimodal experiments is "questionable" for a large share of their experiments. Your draft and earlier advice called pairing "accepted"; that is too strong. Cite them, and add a sensitivity experiment: repeat the pairing with 10 different seeds and report the mean and SD of the fused EER (this is cheap because embeddings are cached).
29. **Threat model section** with an explicit attacker table (A1 template only, A2 template + key, A3 two templates + keys, A4 replay, A5 hill-climbing on the match endpoint, A6 brute force).
30. **Theory section:** SimHash/angle proposition, why leakage grows with m, ridge-decoder analysis, key-space accounting.
31. **Ablations:** m, w, fingerprint preprocessing V1 vs V2, extra training data, per-database results, score-level vs feature-level fusion.
32. **Discussion of the central finding:** cancelable biometrics trades privacy against accuracy because the transform is designed to preserve similarity (HD about theta/pi); that same property makes inversion easy once the key is known. Compare with prior reports that longer BioHash codes leak more (see Dong et al. in REFERENCES.md).
33. **Ethics and data statement; reproducibility checklist; AI-assistance disclosure** (check your college's policy for the latter).
34. **Author line.** "Antigravity Research Team" is the name of the IDE. Use your name and institution.
