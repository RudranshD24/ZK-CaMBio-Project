# PROJECT_MASTER.md

**Title:** ZK-CaMBio: Zero-Knowledge Cancelable Multimodal Biometrics via Chaotic Hashing
**Course:** Biometrics (college project + research-style paper)

## Problem
Biometric traits cannot be reset. If a template database leaks, the user is compromised for life.

## Solution
Extract face and fingerprint embeddings, fuse them (feature level), then apply a **key-dependent chaotic non-invertible transform** producing a binary cancelable template. Store only that template. If leaked, revoke: change the key, re-enroll, get an unlinkable new template from the same traits.

## Stack
Python (OpenCV, PyTorch) for extraction and fusion; C++17 + pybind11 for the chaotic engine; FastAPI backend; PostgreSQL (SQLite for dev) + Docker; Streamlit dashboard.

## Data (chimeric / virtual subjects)
- Face: identity-labelled face set from `dataset/facial_dataset/` (if it is one, e.g. UMDFaces) or CelebA (`dataset/archive/`, needs `identity_CelebA.txt`); decided in Phase 1
- Fingerprint: FVC2004 in `dataset/fingerprint_dataset/` (DB1_A-DB3_A real sensors; DB4_A synthetic, optional)
- No public paired dataset was freely downloadable, so face identity *k* is paired with finger *k* using a fixed seed. Face and fingerprint are statistically independent, so this is an accepted protocol in fusion research, but **must be disclosed** as a limitation. Details: DATASET_PLAN.md.

## Four criteria to prove (paper core)
1. Non-invertibility  2. Revocability  3. Unlinkability  4. Performance preservation (EER close to unprotected)

## Required results
EER table, verification ROC, identification CMC, score distributions, plus criteria evidence (EVALUATION_PLAN.md).

## Deliverables
Code repo, Docker stack, Streamlit demo, results folder, docs pack, paper draft, viva slides.

## Out of scope
Liveness/anti-spoofing, mobile app, real hardware sensors.
