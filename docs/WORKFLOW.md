# WORKFLOW.md: phase prompts to paste in Antigravity
Model tags: [C]=Claude, [G]=Gemini Pro. Always start with: "Read AGENTS.md and docs/DEVELOPMENT_PLAN.md. We are on Phase N only."

**P0 [G]** "Do Phase 0. Create the repo layout from ARCHITECTURE.md, pinned requirements, ruff/pytest config, CMake + pybind11 skeleton, Docker skeleton. No feature code yet. Show me the plan artifact first."

**P1 [G]** "Do Phase 1. Create configs/paths.yaml from DATASET_PLAN.md. Write and run experiments/00_inspect_data.py and show me the output. Then resolve the face-source question exactly as DATASET_PLAN.md says: if there are no identity labels, STOP and ask me. Only after I confirm, build loaders, pairing and the split manifest and add tests asserting subject-disjointness."

**P2 [C]** "Do Phase 2. Implement face embedding with a pretrained model and fingerprint embedding (Gabor baseline, then ResNet18 with metric learning trained only on train subjects). Cache embeddings as .npy. Report per-modality EER on test."

**P3 [G]** "Do Phase 3. Implement fusion and the unprotected baseline evaluation with EER, ROC, CMC. Tune fusion weight on train only."

**P4 [C]** "Do Phase 4. Implement the chaos engine per ARCHITECTURE.md. Include HMAC-based key derivation, transient discard, distribution correction, deterministic ordering, pybind11 binding, and known-answer tests. Explain every design choice in DECISIONS.md."

**P5 [G] then review [C]** "Do Phase 5 per EVALUATION_PLAN.md." Then in a new chat with Claude: "Review the Phase 5 diff and results with the review protocol in AGENT_RULES.md. Look for leakage between train and test."

**P6 [C]** "Do Phase 6 per SECURITY_THREAT_MODEL.md. Report honestly, including where the scheme is weak."

**P7 [G]** "Do Phase 7 per API_SPEC.md and DATABASE.md. Add a test that fails if any biometric field exists in the schema."

**P8 [G]** "Do Phase 8 per UI_UX_SPEC.md."

**P9 [C]** "Do Phase 9. Fill TRACEABILITY_REPORT.md from actual files/tests/results. Draft the paper from EVALUATION_PLAN.md using only numbers in results/."

## Tips
- If the agent drifts: "Stop. Re-read AGENT_RULES.md and restate the current phase and acceptance criteria."
- Commit after every phase. If quota runs out, switch model, do not skip phases.
- Never accept a metric you did not see produced by a script.
