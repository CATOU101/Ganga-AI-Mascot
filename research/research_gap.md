# Research Gap & Contribution Framing: Ganga AI Mascot (PRJ_316)

**Project ID:** PRJ_316  
**Project Title:** AI-Powered Interactive Digital Mascot for Namami Gange Awareness & River-People Connectivity  
**Status:** Comparative gap framing; not an empirical finding or claim of novelty across all literature.
**Historical implementation baseline:** `56032d744b80695be7593c6f85e50d53c7c5a083`
**Current implementation snapshot audited:** `main` at `73602067672fdce4ed4a2f07a4308a7735db55c3` (2026-10-19; before these documentation corrections). R1's DOI/article record is identified; its author metadata needs reconciliation between the publisher page and PDF.

---

## 1. Introduction

Establishing a credible academic contribution for an applied AI system requires separating:
1. Gaps explicitly identified by existing published studies.
2. Gaps observed across the broader body of surveyed literature.
3. Inherent engineering and operational limitations of the current prototype.
4. Defensible candidate contributions that can be experimentally validated.

This document synthesizes these dimensions against sources discussed in the literature review. It is a candidate framing based on a thematic, non-exhaustive review, not proof that the stated gaps are absent from the full literature.

---

## 2. Gaps Explicitly Identified in Published Literature

| Literature Source | Explicitly Identified Research Gap | Direct Relevance to PRJ_316 |
| :--- | :--- | :--- |
| **R1** (2025; author metadata to verify) | Describes an AI-powered Chacha Chaudhary mascot concept for Ganga conservation. Its article description does not document the source-grounded retrieval and citation pipeline implemented here; this comparison is limited to the reviewed article. | Provides application context, not evidence that the proposed mascot improves awareness or behavior. |
| **R2** (Lewis et al., 2020) | Notes that parametric neural language models hallucinate facts, cannot easily update their knowledge without retraining, and fail to provide verifiable provenance for generated statements. | Provides the core technical solution (external non-parametric vector index combined with parametric generator). |
| **R3** (Ganguly et al., 2026) | Identifies hallucination, factual unreliability, lack of explainability, privacy risks, and absence of pedagogical oversight as the primary barriers preventing conversational AI adoption in formal education. | Demands that educational agents incorporate strict evidence quality gating and verifiable citations rather than unconstrained generation. |
| **R4** (Yusuf et al., 2025) | Identifies an over-concentration of educational chatbots on technological novelty rather than instructional purpose; notes that conversational agents rarely separate cognitive reasoning from visual embodiment. | Motivates PRJ_316's modular decoupling: the standalone Brain handles factual reasoning, while the Three.js avatar handles presentation. |
| **R5** (Wang & Li, 2026) | Proposes an expert-consensus design for a flipped AI-chatbot environmental-literacy module. It does not measure classroom learning or behavioral outcomes. | Offers design concepts to consider; it does not validate PRJ_316's educational effect. |
| **R6** (Wang et al., 2025) | The cited heuristic/usability evaluation reports answer-quality concerns in its environmental-education setting, including localization and citation issues. | Motivates evaluating a curated local corpus; one study does not establish that general-purpose LLMs cannot serve such tasks. |
| **R7 & R10** (Schroeder et al., 2013, 2025) | The cited meta-analyses report effects in their studied settings: R7 reports learning $g=0.42$ and motivation $g=0.48$ for its respective analyses; R10 reports an overall learning effect of $g=0.19$. These findings do not directly predict PRJ_316 outcomes. | Motivates evaluating the avatar and Brain separately; does not establish an effect for this system. |

---

## 3. Gaps Observed Across the Surveyed Literature

Beyond individual paper findings, cross-synthesis of R1–R10 reveals three overarching structural gaps in conversational AI for environmental stewardship:

### Gap A: The Domain-Grounding Disconnect in Mascot Systems
- The reviewed sources cover a Ganga mascot concept, pedagogical-agent design, and retrieval-augmented generation, but they do not all examine the same system properties or populations.
- Within this thematic, non-exhaustive set, we did not identify a directly comparable system combining a public-facing environmental mascot with curated government-document RAG. This is a scoped observation, not proof that no comparable system exists.

### Gap B: Citation-Generation Risks in RAG
- Some RAG systems ask the language model to produce references in answer text (for example, numbered or named sources); this review does not estimate how prevalent that design is.
- The reviewed sources discuss citation and attribution risks, but do not establish a universal error rate for generated citations.
- Within the reviewed set, we did not identify a directly comparable educational environmental agent using citation fields assembled separately from generated prose. The thematic review does not establish prevalence across the full literature.

### Gap C: Unhandled Negative Constraint & Dynamic Query Interception
- Current-information handling is an implementation requirement when a system combines static documents with changing environmental measurements. The Brain in this project uses a temporal-intent rule to return a static-knowledge disclaimer for recognized query patterns; a separate integration route handles selected CPCB station queries.
- The reviewed sources do not establish how prevalent such temporal filters are across RAG systems. The project’s 20-query gate artifact is too small and selected to establish comprehensive dynamic-query detection or safety.

---

## 4. Current Repository Limitations (PRJ_316)

To maintain scientific integrity, the current implementation limitations must be acknowledged explicitly rather than concealed:

1. **Static Historical Horizon:** The active knowledge base consists exclusively of GRBMP reports published between 2010 and 2015. It lacks contemporary post-2020 NMCG sewerage infrastructure telemetry.
2. **Limited Live Station Data:** The integration controller has a separate CPCB route for a supported set of main-stem stations and DO/BOD/pH readings. It is not a broad river-monitoring network, does not replace the static GRBMP corpus, and depends on an external service. Data-reuse terms and sustained endpoint availability remain unverified.
3. **Heuristic Evidence Quality Gating:** The evidence gate uses candidate-pool keyword coverage (default $\ge 60\%$) and top-hit lexical overlap (default $\ge 15\%$), along with embedding distance filtering. These deterministic engineering rules are not calibrated probabilities, cross-encoder entailment scores, or proof of claim support; effectiveness remains to be measured.
4. **External Translation and Multilingual Limits:** Text language controls support English, Hindi, Kannada, and Tamil. Script detection is heuristic. General translation uses Google's public GTX endpoint by default on API routes and may send the question and/or generated answer externally; endpoint-specific terms and retention are not verified. A small exact-phrase map works locally, but general translation is not local or offline and no translation cache is retained.
5. **Voice Support Is Uneven:** Vosk model mappings cover English and Hindi only. Browser speech locale controls and Edge TTS voice IDs are configured for four languages, but actual support depends on browser/provider availability and has not been validated consistently. Windows SAPI fallback is configured for English/Hindi. Rhubarb's bundled binary is platform-specific and cadence fallback may be used elsewhere.
6. **Cross-Platform Tooling Variances:** Windows SAPI and the bundled Rhubarb binary do not operate natively on every platform; availability and fallback behavior depend on the host environment.

---

## 5. Defensible Candidate Contributions for PRJ_316

Based on the reviewed literature (with source-specific verification status) and actual source-code implementation, PRJ_316 can frame the following candidate contributions for later peer-reviewed evaluation:

```
                    CORE CONTRIBUTIONS OF PRJ_316

   +-------------------------------------------------------------+
   | 1. Curated Multi-Tier Environmental Corpus Pipeline         |
   |    - 86 GRBMP PDFs, 4,609 pages, 1,111 reviewed sections    |
   |    - Section classification (KEEP/HISTORICAL/METHODOLOGICAL)|
   +------------------------------+------------------------------+
                                  |
                                  v
   +-------------------------------------------------------------+
   | 2. Hybrid Euclidean-Lexical Retrieval with Overview Boost   |
   |    - Unit-normalized MiniLM embeddings (384d, ONNX CPU)     |
   |    - Query-conditioned overview boost for broad inquiries   |
   +------------------------------+------------------------------+
                                  |
                                  v
   +-------------------------------------------------------------+
   | 3. Dual-Stage Pre-Generation Evidence Quality Gating        |
   |    - 60% candidate pool keyword coverage check              |
   |    - Top-hit lexical overlap threshold (tau = 0.15)         |
   |    - Explicit interception of dynamic/current-time queries  |
   +------------------------------+------------------------------+
                                  |
                                  v
   +-------------------------------------------------------------+
   | 4. Decoupled Citation Metadata Assembly                    |
   |    - Citation objects assembled from retrieved-hit metadata |
   |    - Traceable fields; claim-level entailment is not proved  |
   +------------------------------+------------------------------+
                                  |
                                  v
   +-------------------------------------------------------------+
   | 5. Culturally Grounded Three.js WebGL Mascot Integration    |
   |    - Three.js Chacha avatar and quiz are implemented        |
   |    - Voice/provider and learning outcomes remain unevaluated|
   |    - Modular decoupling of Brain reasoning and 3D UI       |
   +-------------------------------------------------------------+
```

### Detailed Contribution Statements

#### Contribution 1: A Curated, Multi-Tier Environmental Knowledge Corpus for River Conservation
The prototype implements a structured curation pipeline for 86 source PDFs associated with the Ganga River Basin Management Plan (GRBMP), covering 4,609 pages. The pipeline uses a multi-tier section review taxonomy (`KEEP`, `KEEP_HISTORICAL`, `KEEP_METHODOLOGICAL`, `EXCLUDE`) with 1,111 approved sections and 4,085 indexed chunks. The groundedness artifact reports 83 unique indexed document names; the available artifacts do not reconcile this with the 86 source PDFs.

#### Contribution 2: Query-Conditioned Hybrid Reranking with Broad-Inquiry Overview Boosting
The prototype ranks a shared dense-retrieved top-15 candidate pool using Euclidean distance, lexical keyword coverage, and an overview boost ($\beta = 0.25$) for detected broad queries matching core overview documents. The saved 30-query evaluation compares reranking configurations within this pool; it does not compare full-corpus dense and lexical retrieval.

#### Contribution 3: Dual-Stage Pre-Generation Evidence Checks and Fallback Paths
Addressing the hallucination and unreliability challenges highlighted by Ganguly et al. (R3) and Wang et al. (R6), the pipeline introduces a two-stage pre-generation gate:
- A candidate pool keyword-coverage threshold ($pool\_coverage \ge 0.60$) that can reject queries before reranking.
- An individual evidence threshold ($overlap(q, c^*) \ge 0.15$) used to screen the top candidate.
- A temporal-predicate filter that detects some real-time/current inquiries and returns a static-knowledge disclaimer; detection coverage and risk reduction have not been established.

#### Contribution 4: Decoupled Citation-Metadata Assembly
The implementation instructs the generative model not to generate source references in its response string. Citation objects are instead assembled deterministically from metadata associated with chunks passed through the evidence gate. This makes returned citation metadata traceable to retrieved hits; it does not by itself validate claim-level entailment or prove that every source record is correct.

#### Contribution 5: Culturally Grounded Multimodal Avatar Prototype
Informed by pedagogical-agent and persona-design literature, the prototype integrates the AI Brain with a browser-native Three.js WebGL mascot (Chacha Chaudhary) featuring 65 bones, 28 body gestures, and acoustic/cadence viseme mapping. The architecture separates Brain processing from character presentation; this does not establish that the avatar improves engagement or that system outputs are scientifically correct.

---

## 6. Summary: Positioning for Peer Review

| Evaluation Dimension | Existing Literature Baseline | PRJ_316 Approach | Validation Method (Stage 6 Work Plan) |
| :--- | :--- | :--- | :--- |
| **Domain Corpus** | Different sources in the reviewed examples | Curated 86 source PDFs; 4,085 chunks (83 indexed document names in groundedness artifact; discrepancy unresolved) | Inventory and schema checks |
| **Retrieval Strategy** | Different retrieval approaches in the reviewed examples | Dense candidate retrieval followed by lexical/hybrid reranking and overview boost | 30-query reranking metrics within a shared dense top-15 pool |
| **Evidence handling**| Prompting and approaches described in reviewed sources | Heuristic evidence gate and decoupled citation-metadata assembly | Small saved heuristic checks; semantic support and general safety not established |
| **Citation metadata**| Practices vary across reviewed sources | Citation fields assembled from retrieved-hit metadata | Benchmark provenance checks do not verify page content or claim-level entailment |
| **Interface / Mascot** | Conceptual robot (R1), 2D chatbot (R5, R6) | Three.js 3D WebGL Avatar (65 bones, 28 clips) | Latency benchmarking, CUQ/SUS user study |
