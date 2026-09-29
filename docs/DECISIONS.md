# DECISIONS.md (append-only ADR log)

| # | Date | Decision | Reason | Alternatives |
|---|---|---|---|---|
| D-001 | 2026-09-29 | Use chimeric virtual subjects (labelled face set + FVC2004) | No freely downloadable paired face+fingerprint dataset; requests unanswered | LUTBIO, BiosecurID, SDUMLA-HMT (approval needed) |
| D-002 | 2026-09-29 | "Hash" = key-dependent chaotic random projection + binarization, Hamming matching | Cryptographic hashes cannot match fuzzy biometrics | SHA-256 (rejected), fuzzy extractor (future) |
| D-003 | 2026-09-29 | Enroll N=5 / probe 3 per subject | FVC gives 8 impressions per finger | N=4/4 |
| D-004 | 2026-09-29 | Test set = 120 virtual subjects, subject-disjoint | Comparable to SDUMLA-HMT's 106 | k-fold |
| D-005 | 2026-09-30 | Face data source: `dataset/facial_dataset/` (folder = identity, 8,277 folders, 367,888 images; matches UMDFaces). Folders with >= 20 images used (7,173 eligible), sorted, shuffled with seed 42, take 300. Face enroll (5) and probe (3) randomly sampled across whole folder with seed 42 (non-consecutive, no overlap). CelebA in `dataset/archive/` is NOT used due to missing identity labels. Cite as UMDFaces (Bansal et al., 2017); research-only use. Note: UMDFaces is web-collected and may contain small label noise; we do NOT filter by embedding similarity to avoid biasing genuine scores (disclosed as paper limitation). | Confirmed ground-truth identity partition across 8,277 folders (7,173 with >= 20 images). 0 corrupt headers. Higher threshold (>= 20) avoids small-folder label noise. | CelebA (rejected: missing identity_CelebA.txt), threshold >= 10 (raised to 20) |
| D-007 | TBD (P2) | Face encoder choice | fill after P2 | facenet-pytorch vs insightface |
| D-006 | 2026-09-30 | Split manifest SHA-256 = `a3454a7c59e609ffccac38ba8d0a584858e128715a7c125ea442ef6809f8f6b4` (`data/processed/split_manifest.json`) | Cryptographically binds the 300 virtual subjects, 180 train / 120 test split (60/40 per DB), and enroll/probe partitions. | Non-deterministic split (rejected) |
| D-008 | 2026-09-29 | Use latest stable Python (3.13) | Standardize on modern runtime across native dev and Docker | Downgrade to 3.11. If a Phase 2 package (e.g. facenet-pytorch) has no compatible wheels, choose an alternative encoder or install it in isolation rather than downgrading Python. |

