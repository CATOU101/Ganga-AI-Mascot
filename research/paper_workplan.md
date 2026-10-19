# Research Paper Work Plan: Ganga AI Mascot (PRJ_316)

**Research Paper Title:** AI-Powered Interactive Digital Mascot for Namami Gange Awareness & River-People Connectivity

**Official Project Title:** Development of AI, ML and Chatbot-powered Interactive Robot Mascot (Chacha Chaudhary) and Digital Avatar to Strengthen the River People Connect Component of Namami Gange
**Target Venue:** Undecided; current master manuscript is venue-neutral
**Historical technical baseline SHA:** `56032d744b80695be7593c6f85e50d53c7c5a083`
**Current implementation branch:** `main`
**Current implementation snapshot audited:** `73602067672fdce4ed4a2f07a4308a7735db55c3` (2026-10-19; before this documentation-only review)
**Execution Status:** Repository integration is implemented. Saved small benchmark artifacts exist, but require documentation/provenance correction and do not support broad performance, safety, or educational-effect claims. Human evaluation and broader empirical evaluation remain deferred.

---

> [!IMPORTANT]
> **Academic Integrity Notice:**  
> A descriptive Results and Discussion draft now summarizes the saved retrieval, evidence-gate, and heuristic groundedness artifacts. These small artifacts do not replace broader experiments, independent annotation, claim-level citation review, or human usability and learning evaluation. No new results are claimed here.

---

## 1. Staged Research Work Plan

```
Stage 1: Repository Audit & Reproducibility Baseline (COMPLETED)
     │
     ▼
Stage 2: Primary Literature Review and Selected Source Checks (IN PROGRESS)
     │
     ▼
Stage 3: Research Gap & Contribution Framing (COMPLETED)
     │
     ▼
Stage 4: Mathematical Algorithm Formulation (COMPLETED)
     │
     ▼
Stage 5: Evaluation & Benchmark Protocol Design (PARTIAL; saved small artifacts, protocol not finalized)
     │
     ▼
Stage 6: Empirical Experimental Execution (DEFERRED - PENDING EXPERIMENTS)
     │
     ▼
Stage 7: Research Paper Manuscript Drafting (DRAFT PREPARED; REVIEW OPEN)
     │
     ▼
Stage 8: Academic & Technical Review / Camera-Ready (FINAL STAGE)
```

---

### Stage 1: Repository Audit & Reproducibility Baseline
- [x] **Task 1.1:** Verify the historical `56032d7` baseline and the multilingual integration on `main`; the current documentation-review baseline is `7360206`.
- [x] **Task 1.2:** Review the feature branch and integrate the multilingual work into `main`; the feature branch is not the current working branch.
- [x] **Task 1.3:** Verify knowledge base inventory (86 PDFs, 4,609 pages, 1,111 approved sections, 4,085 chunks).
- [x] **Task 1.4:** Execute Brain test suite (42 tests) and integration suite (29 tests) using isolated local environment.
- [x] **Task 1.5:** Document active SQLite + NumPy vector runtime and distinguish deprecated Chroma artifacts.
- [x] **Task 1.6:** Produce `research/technical_baseline.md`.
- **Deliverable:** Verified Technical Baseline Document (`research/technical_baseline.md`).

---

### Stage 2: Primary Literature Verification
- [x] **Task 2.1:** Inspect existing research notes in `research/research_log.md` covering papers R1 through R10.
- [x] **Task 2.2:** Record source verification status and note which labels were not rechecked.
- [ ] **Task 2.3:** R1 DOI corrected to `10.63278/mme.vi.1631`; author metadata still requires verification against the version of record because publisher page and PDF differ.
- [x] **Task 2.4:** Expand `research/literature_review.md` from placeholder stub into a structured 8-domain review.
- [x] **Task 2.5:** Update `research/research_log.md` with explicit verification statuses and primary source links.
- **Deliverable:** Literature Review (`research/literature_review.md`) & Research Log (`research/research_log.md`); R1 author metadata and remaining source checks are still open.

---

### Stage 3: Research Gap & Contribution Framing
- [x] **Task 3.1:** Compare PRJ_316 with R1's described mascot concept; the reviewed article does not document the source-grounded retrieval and citation pipeline used in this prototype. This source-level comparison is not a claim about all mascot systems.
- [x] **Task 3.2:** Contrast domain-specific environmental RAG against open-domain RAG (R2).
- [x] **Task 3.3:** Integrate pedagogical agent findings (R7, R8, R9, R10) separating avatar persona engagement from factual Brain reliability.
- [x] **Task 3.4:** Articulate 5 defensible candidate contributions:
  1. Multi-tier curated government corpus processing and section review.
  2. Hybrid Euclidean semantic retrieval with query-type-conditioned overview boosting.
  3. Two-stage pre-generation evidence quality gating (candidate pool coverage + lexical overlap).
  4. Decoupled citation assembly supporting traceable source provenance.
  5. Integrated Three.js mascot and multilingual text handling; empirical accessibility and learning effects remain untested.
- [x] **Task 3.5:** Update `research/research_gap.md` separating literature gaps, observed patterns, and current limitations.
- **Deliverable:** Formalized Research Gap & Contribution Statement (`research/research_gap.md`).

---

### Stage 4: Mathematical Formulation
- [x] **Task 4.1:** Formulate paragraph-preserving text chunking and overlap algorithm with boundary conditions.
- [x] **Task 4.2:** Express 384-dimensional dense semantic embedding mapping and $L_2$ vector normalization.
- [x] **Task 4.3:** Formulate Euclidean candidate retrieval over NumPy memory-mapped matrix.
- [x] **Task 4.4:** Define candidate pool keyword coverage and individual chunk lexical overlap metrics.
- [x] **Task 4.5:** Express hybrid scoring function with broad-query overview boost indicator.
- [x] **Task 4.6:** Define evidence quality gate criteria and current/dynamic inquiry detection predicates.
- [x] **Task 4.7:** Formulate decoupled citation provenance assembly.
- [x] **Task 4.8:** Produce `research/mathematical_formulation.md` with explicit variable definitions and source-code line references.
- **Deliverable:** Mathematical Model Specification (`research/mathematical_formulation.md`).

---

### Stage 5: Evaluation & Benchmark Protocol Design
- [ ] **Task 5.1:** Finalize a broader benchmark protocol. Existing artifacts include a 30-query retrieval set, a 20-query evidence-gate set, and a 20-query groundedness/citation set; these small sets do not substitute for the proposed 100-question evaluation across 5 categories:
  - Factual / Scientific (e.g., Aviral Dhara, water quality parameters, biodiversity).
  - Policy & Institutional (e.g., NGRBA, NMCG mandate, National Ganga Act provisions).
  - Historical / Methodological (e.g., past wastewater reuse case studies, river health indices).
  - Dynamic / Out-of-Scope (e.g., real-time river flow today, unverified trivia).
  - Unsupported Out-of-Domain (e.g., Mars population, unrelated technical topics).
- [ ] **Task 5.2:** Formalize quantitative retrieval metrics:
  - $\text{Precision}@k = \frac{|\text{Relevant Retrieved Documents}|}{k}$
  - $\text{Recall}@k = \frac{|\text{Relevant Retrieved Documents}|}{|\text{Total Known Relevant Documents}|}$
  - $\text{Mean Reciprocal Rank (MRR)} = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\text{rank}_i}$
- [ ] **Task 5.3:** Formalize generation quality metrics:
  - **Factual Groundedness / Faithfulness:** Proportion of generated statements directly supported by cited evidence passages.
  - **Citation Precision & Recall:** Proportion of cited sources that actually contain the supporting claims.
  - **Evidence-gate decision agreement:** Report only on the defined test set and describe the lexical/rule-based criteria; do not interpret as general safety or hallucination prevention.
- [ ] **Task 5.4:** Formalize multimodal interaction metrics:
  - End-to-end latency (Query $\to$ RAG $\to$ TTS $\to$ Lip-sync $\to$ Browser render).
  - Avatar usability via standard Chatbot Usability Questionnaire (CUQ) or System Usability Scale (SUS).
  - Educational knowledge gain (pre-test vs. post-test score differential in user study).
- [ ] **Task 5.5:** Formalize CPCB live water-quality evaluation protocol:
  - Query classification and routing accuracy (distinguishing live telemetry requests from conceptual/educational water-quality questions).
  - LLM behavior and response-length optimization when presenting structured station telemetry.
  - Multimodal voice/TTS interaction testing: evaluate intelligibility and auditory pacing of numeric readings (DO, BOD, pH).
  - Upstream reliability analysis: benchmark 60-second caching performance, stale-measurement tagging (>90 minutes), and error handling during CPCB portal downtime.
  - Administrative clearance: clarify formal data reuse permissions and public licensing with CPCB under NDSAP guidelines.
- **Deliverable:** Evaluation Protocol Specification in `research/implementation_and_evaluation.md`.

---

### Stage 6: Empirical Experimental Execution *(DEFERRED)*
- [ ] **Task 6.1:** Run automated retrieval benchmark across the 100-query evaluation set.
- [ ] **Task 6.2:** Ablation study: Evaluate retrieval performance under:
  - Semantic vector search only.
  - Lexical keyword search only.
  - Hybrid retrieval without overview boost.
  - Full hybrid retrieval with overview boost and evidence gating.
- [ ] **Task 6.3:** Generation comparison: Evaluate Groq, OpenRouter, and local extractive fallback on the same evidence-gated query set. Measure quality, citation behavior, provider availability, and latency under a documented protocol before drawing comparative conclusions. This is proposed future evaluation; no comparative results are available.
- [ ] **Task 6.4:** User study: Conduct controlled user evaluation with students / citizens assessing engagement, trust, and learning outcomes.
- [ ] **Task 6.5:** Record genuine empirical measurements in tables and charts.
- **Deliverable:** Empirical Results Data Package & Analysis.

---

### Stage 7: Research Paper Manuscript Drafting *(DRAFT PREPARED; REVIEW OPEN)*
- [x] **Task 7.1:** Venue-neutral title, abstract, and keywords.
- [x] **Task 7.2:** Introduction and motivation.
- [x] **Task 7.3:** Related work, with source-specific verification limits.
- [x] **Task 7.4:** System architecture and knowledge pipeline.
- [x] **Task 7.5:** Implementation-aligned mathematical formulation.
- [x] **Task 7.6:** Multilingual, voice, avatar, and CPCB scope described with capability limits.
- [x] **Task 7.7:** Descriptive results from existing saved artifacts, without claiming new experiments.
- [x] **Task 7.8:** Discussion, ethics, and limitations.
- [x] **Task 7.9:** Conclusion and future work.
- [ ] Final bibliography reconciliation for R1 authors, stronger provenance, larger empirical evaluation, and venue-specific formatting remain open.
- **Deliverable:** Venue-neutral draft at `research/papers/venue_neutral_master_manuscript.md`; submission preparation remains incomplete.

---

### Stage 8: Final Technical and Academic Review
- [ ] **Task 8.1:** Check mathematical notation consistency across all sections.
- [ ] **Task 8.2:** Cross-verify all citations, author names, DOIs, and bibliography entries.
- [ ] **Task 8.3:** Ensure zero unsubstantiated claims or marketing language.
- [ ] **Task 8.4:** Verify code repository reproducibility instructions against a clean environment.
- **Deliverable:** Camera-Ready Research Paper and Reproducible Code Archive.

---

## 2. Change Log

| Date | Phase | Action / Modification | Author |
| :--- | :--- | :--- | :--- |
| 2026-10-17 | Audit | Completed repository audit; identified authoritative baseline `56032d7`. | Research Team |
| 2026-10-17 | Setup | Created `research/repository-preparation` branch; preserved all local files. | Research Team |
| 2026-10-17 | Baseline | Authored comprehensive technical baseline document (`research/technical_baseline.md`). | Research Team |
| 2026-10-17 | Plan | Formulated staged work plan (`research/paper_workplan.md`) with explicit Results deferral. | Research Team |
| 2026-10-18 | Feature | Integrated CPCB real-time water quality monitoring (Haridwar, Kanpur, Ghazipur, Farakka, Nabadwip) into conversation controller; added Task 5.5 for telemetry evaluation and CPCB data reuse clearance. | Research Team |
| 2026-10-18 | Implementation | Added configurable Groq → OpenRouter → extractive generation fallback after the existing evidence gate. This is a generation-layer resilience change; no live-provider or comparative performance results are claimed. | Research Team |
| 2026-10-19 | Integration | Verified the multilingual integration on `main` at `8083375`; documentation reconciliation follows as a separate milestone. | Research Team |
| 2026-10-19 | Documentation | Reconciled current project, architecture, implementation, and research status against source; benchmark design and empirical work remain open. | Research Team |
