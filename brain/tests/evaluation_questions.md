# Prototype RAG Evaluation Questions

These questions are smoke tests for the first working RAG Brain prototype. They do not establish retrieval accuracy metrics.

## 1. Factual KB Question

- Question: What is Aviral Dhara?
- Expected behavior: Answer from retrieved GRBMP context and include source/page provenance.
- Retrieved evidence: Filled by `brain/tests/run_evaluation.py`.
- Result: Pending execution.
- Known limitations: Retrieval depends on the baseline local hash embedding model.

## 2. Historical Context Question

- Question: According to the GRBMP material, what historical concerns are associated with sewage pollution?
- Expected behavior: Preserve historical framing and avoid presenting old status figures as current.
- Retrieved evidence: Filled by `brain/tests/run_evaluation.py`.
- Result: Pending execution.
- Known limitations: Some historical periods require later human review.

## 3. Provenance Question

- Question: What does the knowledge base say about environmental flows, and which source page supports it?
- Expected behavior: Include document title, page range, and section provenance.
- Retrieved evidence: Filled by `brain/tests/run_evaluation.py`.
- Result: Pending execution.
- Known limitations: Page ranges come from section-level extraction, not final hand-curated citations.

## 4. Out-Of-KB Question

- Question: What is the mascot's final 3D animation design?
- Expected behavior: Do not hallucinate; return insufficient-evidence fallback.
- Retrieved evidence: Filled by `brain/tests/run_evaluation.py`.
- Result: Pending execution.
- Known limitations: The fallback threshold is heuristic.

## 5. Current Information Question

- Question: What is the current water quality of the Ganga today?
- Expected behavior: State that the static prototype KB does not provide verified current or real-time information.
- Retrieved evidence: Filled by `brain/tests/run_evaluation.py`.
- Result: Pending execution.
- Known limitations: No live current-data API is implemented in this prototype.
