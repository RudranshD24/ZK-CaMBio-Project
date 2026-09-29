# DECISIONS.md (append-only ADR log)

| # | Date | Decision | Reason | Alternatives |
|---|---|---|---|---|
| D-001 | 2026-09-29 | Use chimeric virtual subjects (labelled face set + FVC2004) | No freely downloadable paired face+fingerprint dataset; requests unanswered | LUTBIO, BiosecurID, SDUMLA-HMT (approval needed) |
| D-002 | 2026-09-29 | "Hash" = key-dependent chaotic random projection + binarization, Hamming matching | Cryptographic hashes cannot match fuzzy biometrics | SHA-256 (rejected), fuzzy extractor (future) |
| D-003 | 2026-09-29 | Enroll N=5 / probe 3 per subject | FVC gives 8 impressions per finger | N=4/4 |
| D-004 | 2026-09-29 | Test set = 120 virtual subjects, subject-disjoint | Comparable to SDUMLA-HMT's 106 | k-fold |
| D-005 | TBD (P1) | Face data source: `facial_dataset/` (if labelled) vs CelebA + identity_CelebA.txt | Kaggle CelebA mirror lacks identity labels | UMDFaces, CelebA |
| D-007 | TBD (P2) | Face encoder choice | fill after P2 | facenet-pytorch vs insightface |
| D-006 | TBD | Split manifest SHA-256 | fill after P1 | |
| D-008 | 2026-09-29 | Use latest stable Python (3.13) | Standardize on modern runtime across native dev and Docker | Downgrade to 3.11. If a Phase 2 package (e.g. facenet-pytorch) has no compatible wheels, choose an alternative encoder or install it in isolation rather than downgrading Python. |

