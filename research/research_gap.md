# Research Gap & Contribution Framing: Ganga AI Mascot (PRJ_316)

**Project ID:** PRJ_316  
**Project Title:** AI-Powered Interactive Digital Mascot for Namami Gange Awareness & River-People Connectivity  
**Status:** Comparative gap framing; not an empirical finding or claim of novelty across all literature.
**Historical implementation baseline:** `56032d744b80695be7593c6f85e50d53c7c5a083`
**Current implementation snapshot audited:** `main` at `80833751f2a365eb00be5ddeee3392e4a601d38e` (2026-10-19; before documentation-only changes). R1's publication record remains unverified in the literature review; R1-based statements are provisional.

---

## 1. Introduction

Establishing a credible academic contribution for an applied AI system requires separating:
1. Gaps explicitly identified by existing published studies.
2. Gaps observed across the broader body of surveyed literature.
3. Inherent engineering and operational limitations of the current prototype.
4. Defensible candidate contributions that can be experimentally validated.

This document synthesizes these dimensions against sources discussed in the literature review. R1's publication record remains unresolved, so statements attributed to R1 are provisional. This comparison is a candidate framing based on reviewed sources, not proof that the stated gaps are absent from the full literature.

---

## 2. Gaps Explicitly Identified in Published Literature

| Literature Source | Explicitly Identified Research Gap | Direct Relevance to PRJ_316 |
| :--- | :--- | :--- |
| **R1** (Narmada et al., 2025) | Identifies that traditional civic river awareness campaigns suffer from low engagement among youth, proposing an AI mascot. **However**, the paper explicitly notes the absence of structured technical knowledge bases, domain-specific retrieval, or provenance tracking. | Establishes the application rationale for an AI-powered Chacha Chaudhary mascot, while leaving the knowledge engine completely unformulated. |
| **R2** (Lewis et al., 2020) | Notes that parametric neural language models hallucinate facts, cannot easily update their knowledge without retraining, and fail to provide verifiable provenance for generated statements. | Provides the core technical solution (external non-parametric vector index combined with parametric generator). |
| **R3** (Ganguly et al., 2026) | Identifies hallucination, factual unreliability, lack of explainability, privacy risks, and absence of pedagogical oversight as the primary barriers preventing conversational AI adoption in formal education. | Demands that educational agents incorporate strict evidence quality gating and verifiable citations rather than unconstrained generation. |
| **R4** (Yusuf et al., 2025) | Identifies an over-concentration of educational chatbots on technological novelty rather than instructional purpose; notes that conversational agents rarely separate cognitive reasoning from visual embodiment. | Motivates PRJ_316's modular decoupling: the standalone Brain handles factual reasoning, while the Three.js avatar handles presentation. |
| **R5** (Wang & Li, 2026) | Demonstrates that environmental chatbots frequently deliver disjointed factual trivia rather than structured environmental literacy (awareness $\to$ understanding $\to$ action). | Motivates structuring Brain retrieval to support pedagogical explanations (Aviral Dhara, Nirmal Dhara) and historical context. |
| **R6** (Wang et al., 2025) | Heuristic evaluation of general LLMs (ChatGPT) reveals high error rates in regional environmental contexts, over-generalized guidance, and a tendency to fabricate citations when answering localized environmental questions. | Confirms that general-purpose commercial LLMs cannot replace curated local regulatory corpora (e.g., GRBMP). |
| **R7 & R10** (Schroeder et al., 2013, 2025) | Meta-analyses reveal that pedagogical agent embodiment produces small to moderate learning gains ($g \approx 0.19\text{--}0.25$), but these gains collapse if agent speech is discordant with visual cues or if the underlying instruction is flawed. | Confirms that visual embodiment (Three.js avatar) is an engagement amplifier, not a substitute for knowledge accuracy in the Brain. |

---

## 3. Gaps Observed Across the Surveyed Literature

Beyond individual paper findings, cross-synthesis of R1–R10 reveals three overarching structural gaps in conversational AI for environmental stewardship:

### Gap A: The Domain-Grounding Disconnect in Mascot Systems
- Existing mascot and educational chatbot literature (R1, R7, R8, R9) focuses heavily on character design, speech synthesis, and engagement metrics. When conversational intelligence is integrated, it is implemented either as fixed rule-based decision trees or as unconstrained zero-shot commercial LLM prompts.
- There is a noticeable absence of systems coupling culturally resonant public mascots with curated government-document RAG pipelines.

### Gap B: The Citation-Generation Fallacy in Standard RAG
- Mainstream RAG implementations (exemplified by R2 and commercial frameworks) prompt the language model to generate citations within its output text (e.g., "[1]", "(Source: Report X, p. 12)").
- Empirical research (R3, R6) shows that generative models routinely confabulate citation details—attributing real claims to wrong page numbers or fabricating plausible report titles.
- Systems that programmatically decouple citation binding (assembling trusted metadata directly from retrieved vector chunks and passing it outside the LLM prompt) remain underexplored in educational conversational agents.

### Gap C: Unhandled Negative Constraint & Dynamic Query Interception
- Most conversational agents attempt to generate an answer for every user input. In environmental monitoring, users frequently inquire about dynamic or real-time parameters (e.g., "What is the water quality at Varanasi right now?").
- Standard RAG pipelines either hallucinate plausible current metrics or present historical baseline data as contemporary facts. A formal query-classification layer that explicitly intercepts temporal/dynamic queries and safely disclaims static knowledge limits is rarely formalized in literature.

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
Unlike open-domain RAG systems built on Wikipedia (R2) or ungrounded mascot chatbots (R1), this work designs, implements, and releases a structured curation pipeline processing 86 official Ganga River Basin Management Plan (GRBMP) scientific reports (4,609 pages). The pipeline introduces a multi-tier section review taxonomy (`KEEP`, `KEEP_HISTORICAL`, `KEEP_METHODOLOGICAL`, `EXCLUDE`) yielding 1,111 approved sections and 4,085 indexed chunks with granular page, chapter, and temporal metadata.

#### Contribution 2: Query-Conditioned Hybrid Retrieval with Broad-Inquiry Overview Boosting
Standard dense retrieval often fails on broad conceptual queries (e.g., "What is the Ganga River?") by matching narrow technical subsections rather than executive summaries. We formulate a hybrid retrieval algorithm combining Euclidean vector distance over unit-normalized embeddings with lexical keyword coverage, augmented by an automated query-type detection rule that applies an overview boost ($\beta = 0.25$) when broad thematic queries match core executive plan documents.

#### Contribution 3: Dual-Stage Pre-Generation Evidence Quality Gating & Safe Failure Modes
Addressing the hallucination and unreliability challenges highlighted by Ganguly et al. (R3) and Wang et al. (R6), the pipeline introduces a two-stage pre-generation gate:
- A candidate pool keyword coverage gate ($pool\_coverage \ge 0.60$) that rejects out-of-domain queries before reranking.
- An individual evidence threshold ($overlap(q, c^*) \ge 0.15$) that validates top candidate relevance.
- A temporal-predicate filter that intercepts real-time/current inquiries and transparently returns static knowledge disclaimers, preventing misleading answers.

#### Contribution 4: Hallucination-Resistant Decoupled Citation Provenance
The implementation instructs the generative model not to generate source references in its response string. Citation objects are instead assembled deterministically from metadata associated with chunks passed through the evidence gate. This makes returned citation metadata traceable to retrieved hits; it does not by itself validate claim-level entailment or prove that every source record is correct.

#### Contribution 5: Culturally Grounded Multimodal Avatar Architecture for Public Environmental Literacy
Extending the pedagogical agent findings of Schroeder et al. (R7, R10) and persona design principles of Tao et al. (R9), the system integrates the AI Brain with an interactive, browser-native Three.js WebGL mascot (Chacha Chaudhary) featuring 65 bones, 28 body gestures, and acoustic/cadence viseme mapping. Crucially, the architecture strictly decouples factual reasoning from character presentation, ensuring that visual engagement never compromises scientific veracity.

---

## 6. Summary: Positioning for Peer Review

| Evaluation Dimension | Existing Literature Baseline | PRJ_316 Approach | Validation Method (Stage 6 Work Plan) |
| :--- | :--- | :--- | :--- |
| **Domain Corpus** | None (R1), Wikipedia (R2), General Web (R6) | Curated 86 GRBMP reports (4,085 chunks) | Inventory manifest verification & schema validation |
| **Retrieval Strategy** | Keyword only (R1), DPR Dense (R2) | Euclidean Dense + Lexical Overlap + Overview Boost | Precision@k, Recall@k, MRR ablation benchmark |
| **Hallucination Control**| Prompting only (R6) | Dual Evidence Gating + Decoupled Provenance | Groundedness score, safe rejection rate on 100 queries |
| **Citation Verifiability**| Unverified / confabulated (R2, R6) | Immutable metadata binding from chunk index | Citation precision & page-level source alignment |
| **Interface / Mascot** | Conceptual robot (R1), 2D chatbot (R5, R6) | Three.js 3D WebGL Avatar (65 bones, 28 clips) | Latency benchmarking, CUQ/SUS user study |
