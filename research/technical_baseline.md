# Technical Baseline: Ganga AI Mascot (PRJ_316)

**Project ID:** PRJ_316  
**Project Title:** AI-Powered Interactive Digital Mascot for Namami Gange Awareness & River-People Connectivity  
**Repository:** https://github.com/CATOU101/Ganga-AI-Mascot  
**Authoritative Baseline Commit SHA:** `56032d744b80695be7593c6f85e50d53c7c5a083` (`origin/main`, merging PR #25 from `MA_MEM`)  
**Active Working Branch:** `research/repository-preparation`  
**Document Status:** Complete & Verified Technical Baseline  

This document preserves the technical snapshot anchored to the baseline SHA above. Subsequent implementation changes on `research/repository-preparation` are recorded in the dated post-baseline addendum at the end of this document; historical baseline test counts below are not current-checkout validation results.

---

## 1. Project Scope and Purpose

The **Ganga AI Mascot** project is an academic research prototype designed to improve public awareness, environmental education, and community engagement for the **Namami Gange Programme** (National Mission for Clean Ganga - NMCG). 

The system couples a source-grounded conversational AI "Brain" with an interactive web-based 3D digital mascot (Chacha Chaudhary). The primary objective is to communicate authentic information concerning river conservation, water quality management, sewage treatment, ecological restoration (e.g., Aviral Dhara and Nirmal Dhara), and community stewardship without hallucination or unverified factual claims.

---

## 2. Overall System Architecture

The runtime architecture is decoupled into three primary layers:
1. **Interactive Client Layer (Avatar & Web UI):** A client-side WebGL application built on Three.js (`avatar/index.html`, `avatar/app.js`, `avatar/mascot.js`) rendering the 3D Chacha Chaudhary mascot, managing skeletal animations, procedural blinking, speech cadence, and audio playback.
2. **Integration Service Layer (`integration/server.py`):** A FastAPI service operating on port 8080 that coordinates user requests, manages conversational state, exposes speech-to-text (STT) and text-to-speech (TTS) pipelines, generates acoustic/viseme lip-sync timelines, and mounts the Brain API. It also intercepts real-time water-quality queries via `integration/water_quality.py` to retrieve verified live telemetry from CPCB monitoring stations (Haridwar, Kanpur, Ghazipur, Farakka, Nabadwip) with 60-second in-memory caching and freshness labelling.
3. **Knowledge & Reasoning Brain Layer (`brain/api.py`, `brain/rag_pipeline.py`):** A standalone FastAPI service (typically port 8000) hosting a Retrieval-Augmented Generation (RAG) pipeline over curated government documents, featuring hybrid semantic/lexical retrieval, heuristic evidence gating, hosted generation, extractive fallback, and deterministic citation assembly. The post-baseline provider-chain update is described in the addendum.

```
+---------------------------------------------------------------------------------------+
|                                    BROWSER CLIENT                                     |
|               Three.js WebGL Engine (avatar/app.js, avatar/mascot.js)                 |
|               Active 3D Model: avatar/Chacha_New/Chacha_New.glb (65 bones)             |
+-------------------------------------------+-------------------------------------------+
                                            |
                         [Audio WAV / JSON] | [Presentation JSON + Audio Base64]
                                            v
+---------------------------------------------------------------------------------------+
|                             INTEGRATION SERVICE (PORT 8080)                           |
|                                 (integration/server.py)                               |
|                                                                                       |
|  +-----------------------+  +-----------------------+  +---------------------------+  |
|  |     Vosk STT (en/hi)  |  |  EdgeTTS Neural Voice |  |   Rhubarb Lip-Sync /      |  |
|  |  (Offline Kaldi model)|  |  (Prabhat/Madhur)+SAPI|  |   Cadence Fallback Engine |  |
|  +-----------+-----------+  +-----------+-----------+  +-------------+-------------+  |
|              |                          ^                            ^                |
|              v                          |                            |                |
|     [Transcribed Text]                  +--------------+-------------+                |
|              |                                         |                              |
|              v                                         |                              |
|  +-----------------------------------------------------+---------------------------+  |
|  |             Conversation Controller & MascotPresenter Pipeline                  |  |
|  +-------------------------------------+-------------------------------------------+  |
+----------------------------------------|----------------------------------------------+
                                         | In-process call or HTTP POST /ask
                                         v
+---------------------------------------------------------------------------------------+
|                               STANDALONE BRAIN SERVICE                                |
|                                (brain/rag_pipeline.py)                                |
|                                                                                       |
|  [Query] --> [Dynamic Query Detection] --> [Semantic Vector Search (MiniLM 384d)]     |
|                      |                                       |                        |
|                      | (if dynamic)                          v                        |
|                      |                        [Euclidean Candidate Retrieval (k=15)]  |
|                      |                                       |                        |
|                      |                                       v                        |
|                      |                        [Hybrid Reranking & Overview Boost]     |
|                      |                                       |                        |
|                      |                                       v                        |
|                      |                        [Evidence Quality Gate: 60% pool / 15%] |
|                      |                                       |                        |
|                      v (insufficient/fallback)               v (sufficient)           |
|            [Fallback Disclaimers]              [Grounded Groq LLM (gpt-oss-120b)]     |
|                      |                         [or Local Extractive Sentence Fallback]|
|                      |                                       |                        |
|                      +-------------------+-------------------+                        |
|                                          |                                            |
|                                          v                                            |
|                       [Deterministic Citation Provenance Assembly]                    |
|                                          |                                            |
|                                          v                                            |
|                        [HTTP Response: Answer + Citations]                            |
+---------------------------------------------------------------------------------------+
```

---

## 3. Knowledge Base Pipeline & Verified Inventory

The factual foundation of the Brain is derived from official government planning and scientific reports, primarily the **Ganga River Basin Management Plan (GRBMP)** prepared by the Consortium of 7 Indian Institutes of Technology (IITs).

### Verified Document Inventory
Verification was performed against `knowledge_base/processed/document_inventory.json`, `section_review.json`, and `prototype_ingestion_manifest.json`:

| Metric | Repository Claim | Verified Fact | Verification Source |
| :--- | :--- | :--- | :--- |
| **Total Source PDFs** | 86 | **86** | `knowledge_base/raw_documents/GRBMP/` (86 PDF files present) |
| **Total Document Pages** | 4,609 | **4,609** | `knowledge_base/processed/document_inventory.json` |
| **Identified Sections** | Unstated | **1,832** | `knowledge_base/processed/section_review.json` |
| **Approved / Reviewed Sections** | 1,111 | **1,111** | Sum of approved categories: `KEEP` (342) + `KEEP_HISTORICAL` (360) + `KEEP_METHODOLOGICAL` (409) in `section_review.json` |
| **Excluded Sections** | Unstated | **721** | `sections_FILTER` (11) + `sections_EXCLUDE` (156) + `sections_requiring_human_review` (554) |
| **Indexed Vector Chunks** | 4,085 | **4,085** | `knowledge_base/vector_db/brain_index_manifest.json` & `brain_index.sqlite3` |
| **Active Storage Files** | SQLite + NumPy | **Verified** | `knowledge_base/vector_db/brain_index.sqlite3` (11.9 MB) and `brain_semantic_vectors.npy` (6.27 MB, float32) |

### Ingestion & Chunking Specifications
- **Ingestion Script:** `brain/ingest.py` (`load_document_pages`, `build_manifest`).
- **Chunking Algorithm:** `brain/chunking.py` (`split_section_text`, `chunks_from_sections`).
- **Target Chunk Size:** 1,400 characters (`chunk_target_chars`).
- **Chunk Overlap:** 180 characters (`chunk_overlap_chars`).
- **Minimum Chunk Length:** 120 characters (`min_chunk_chars`); sub-minimum fragments are merged back into preceding paragraphs.
- **Metadata Retained per Chunk:** `chunk_id`, `section_id`, `source_id`, `file_name`, `title`, `section`, `subsection`, `page_start`, `page_end`, `section_classification`, `knowledge_type`, `time_period`, `geographic_scope`, `source_status`, `relevance`.

---

## 4. Embeddings and Vector Store

### Embedding Model Configuration
- **Source Module:** `brain/embeddings.py` (`ONNXSemanticEmbedding`, `LocalHashEmbedding`, `get_embedding_function`).
- **Default Provider:** `semantic` (configured via `GANGA_BRAIN_EMBEDDING_PROVIDER`).
- **Model Name:** `all-MiniLM-L6-v2` (`MINILM_MODEL_NAME`).
- **Architecture & Implementation:** ONNX Runtime executing Chroma's native `DefaultEmbeddingFunction` on local CPU.
- **Dimensions:** 384 (`embedding_dimensions = 384`).
- **Model Archive Hash:** SHA-256 `913d7300ceae3b2dbc2c50d1de4baacab4be7b9380491c27fab7418616a16ec3`.
- **Normalization:** Vectors are unit-normalized ($L_2$ norm = 1.0).
- **Thread Concurrency:** Constrained via `GANGA_BRAIN_ORT_THREADS` (default: 2 threads) with `OMP_NUM_THREADS`, `ONNXRUNTIME_SESSION_THREAD_POOL_SIZE`, `OPENBLAS_NUM_THREADS`, and `MKL_NUM_THREADS` bounds set to eliminate thread contention.
- **Baseline Fallback:** `LocalHashEmbedding` (deterministic 384-dimensional bag-of-words hashing baseline using SHA-256 token digests, requiring zero third-party models).

### Active Runtime Vector Store
- **Source Module:** `brain/vector_store.py` (`SQLiteVectorStore`).
- **Active Metadata Store:** SQLite database at `knowledge_base/vector_db/brain_index.sqlite3` containing tables `collections` and `chunks`.
- **Active Vector Index:** NumPy binary memory-mapped file at `knowledge_base/vector_db/brain_semantic_vectors.npy` of shape `(4085, 384)` with `float32` dtype.
- **Integrity Verification:** Verified via `_validate_index_files` which compares chunk text/metadata SHA-256 against `brain_index_manifest.json` (`chunks_sha256: 4b2ee7...`, `vectors_sha256: f198a2...`).
- **Legacy Artifacts:** `chroma.sqlite3` (56.7 MB) and associated UUID subdirectories in `knowledge_base/vector_db/` are deprecated artifacts preserved for historical reproducibility and are not accessed by the active runtime.

---

## 5. Retrieval, Reranking, and Evidence Quality Gate

The retrieval pipeline in `brain/retriever.py` executes in four sequential stages:

### Stage 1: Candidate Search
- **Function:** `Retriever.retrieve_candidates(question, candidate_k=15)`
- **Mechanism:** Computes Euclidean distance between the query vector $\mathbf{q} \in \mathbb{R}^{384}$ and all 4,085 pre-computed document chunk vectors $\mathbf{d}_i \in \mathbb{R}^{384}$:
  $$dist(\mathbf{q}, \mathbf{d}_i) = \|\mathbf{q} - \mathbf{d}_i\|_2$$
- Partitions the top $K_{cand} = 15$ closest candidates using `np.argpartition`.

### Stage 2: Out-of-Domain Candidate Pool Check
- **Function:** `Retriever.rerank_and_filter`
- **Keyword Extraction:** Query tokens of length $\ge 3$ excluding English stop words (`extract_keywords(question)`).
- **Pool Coverage Requirement:** At least 60% of query keywords must appear across the combined text, title, and section metadata of the candidate pool:
  $$\frac{|\{w \in \mathcal{K}(q) \mid \exists c \in \mathcal{C}_{cand}: w \in c\}|}{|\mathcal{K}(q)|} \ge 0.60$$
  If coverage $< 0.60$, the gate fails immediately and returns `(False, [])`.

### Stage 3: Distance Filtering & Hybrid Scoring
- **Distance Cutoff:** Candidate hits with $dist(\mathbf{q}, \mathbf{d}_i) > 1.15$ (for semantic embedding) or $> 1.35$ (for hash embedding) are dropped.
- **Individual Keyword Overlap:** $overlap(q, c) = \frac{|\{w \in \mathcal{K}(q) \mid w \in c\}|}{|\mathcal{K}(q)|}$.
- **Overview Boost:** Evaluates whether the question is a broad inquiry (`is_broad_ganga_query(question)`) and the candidate originates from core overview documents (`CORE_OVERVIEW_FILES` such as `13_GRBMP - MPD.pdf`, `27_GRBMP - Extended Summary.pdf`, `Vision Ganga Eng_Compressed.pdf`).
- **Hybrid Score Calculation:**
  $$S_{hybrid}(q, c) = \frac{1}{1 + dist(q, c)} + 0.5 \cdot overlap(q, c) + 0.25 \cdot \mathbb{I}_{broad \land overview}(q, c)$$

### Stage 4: Evidence Quality Gate
- Scored candidates are sorted in descending order of $S_{hybrid}$.
- **Top Overlap Gate:** The highest-ranked hit must satisfy $overlap(q, c^*) \ge 0.15$ for multi-word queries ($|\mathcal{K}(q)| > 1$).
- If accepted, the top $K=5$ hits (`GANGA_BRAIN_TOP_K`) are returned as verified evidence.

---

## 6. Answer Generation & Provenance Citations

- **Source Modules:** `brain/generator.py`, `brain/prompts/`
- **Configured LLM Provider:** Groq chat completions API (`GroqGenerator`), defaulting to model `openai/gpt-oss-120b` via the official OpenAI Python SDK.
- **System Prompt:** `GROUNDING_SYSTEM_PROMPT` enforces strict grounding on retrieved evidence, third-person objective tone, and forbids fabricating external references or dates.
- **Evidence Formatting:** Retrieved text is bounded to a maximum of 6,000 characters (`MAX_LLM_EVIDENCE_CHARS`), with structured metadata (`title`, `file_name`, `page_start`, `page_end`, `section`, `knowledge_type`). Output tokens are capped at 700 (`MAX_LLM_OUTPUT_TOKENS`), temperature set to 0.
- **Deterministic Extractive Fallback:** If `GROQ_API_KEY` is not provided or the network call fails, `ExtractiveGenerator` activates automatically. It performs sentence segmentation, cleans OCR and running headers, scores sentences by keyword overlap, selects up to 4 supported sentences, and prepends a historical disclaimer if historical sources are cited.
- **Citation Assembly:** Citation objects are constructed programmatically from contributing-hit metadata (`citations_from_hits`) and returned in the JSON payload under `citations`. The LLM is instructed not to generate source strings inline, so citation records are not authored by the model; this does not establish claim-level support or metadata correctness.

---

## 7. Handling of Unsupported and Current-Information Queries

The pipeline implements explicit branching before and during retrieval:

1. **Empty Query:** Returns `mode: "insufficient-evidence"` immediately with 0 citations.
2. **Current / Real-Time Information:** Handled by `asks_for_current_information(question)` in `brain/retriever.py`.
   - Checks for dynamic topic terms (`water quality`, `river discharge`, `stp status`, `pollution monitoring`) combined with freshness keywords (`current`, `today`, `now`, `latest`, `real-time`).
   - If triggered, returns `mode: "current-info-fallback"` with the explicit message:
     *"The current prototype knowledge base is built from static/historical GRBMP material and does not provide verified current or real-time information for that question."*
3. **Insufficient Evidence / Out-of-Domain:** If candidate pool coverage is $< 60\%$ or the top hit lexical overlap is $< 0.15$, retrieval returns `False, []`. The pipeline returns `mode: "insufficient-evidence"` with 0 citations:
   *"I couldn't find sufficient supporting information in the current verified knowledge base to answer that reliably."*
4. **Academic Clarification:** These heuristic filters safeguard against hallucinations but do **not** represent a calibrated probabilistic confidence measure or formal claim-level entailment proof.

---

## 8. Multilingual Translation and Voice System

### Multilingual Translation (`brain/translator.py`)
- **Supported Languages:** English (`en`) and Hindi (`hi`).
- **Translation Engine:** `_http_translate` invokes Google Translate's public endpoint (`translate.googleapis.com/translate_a/single?client=gtx`).
- **Offline / Domain Fallback:** Contains a hardcoded dictionary (`DOMAIN_TRANSLATIONS`) for standard disclaimers and phrases.
- **Architectural Fact:** Translation is **network-dependent**; when internet connectivity is absent and a query is not in `DOMAIN_TRANSLATIONS`, `translate_text` raises `TranslationError`. It is not an offline local multilingual model.

### Speech-to-Text (`integration/voice/stt_adapter.py`)
- **Primary Engine:** `VoskSTTAdapter` wrapping the offline Kaldi-based Vosk library.
- **Capabilities:** Offline transcription for English (`en-us`) and Hindi (`hi`) with Devanagari Unicode NFC normalization.
- **Requirement:** Requires local model directories to be present.

### Text-to-Speech (`integration/voice/tts_adapter.py`)
- **Primary Engine:** `EdgeTTSProvider` using Microsoft Edge neural voices (`en-IN-PrabhatNeural` for English, `hi-IN-MadhurNeural` for Hindi), outputting 16 kHz 16-bit mono PCM WAV.
- **Secondary Fallback:** `LocalSapiTTSProvider` invoking Windows PowerShell `System.Speech.Synthesis`.
- **Architectural Fact:** EdgeTTS requires active outbound internet access (`speech.platform.bing.com`). SAPI is strictly Windows-only. On macOS/Linux in offline mode, TTS returns `None`, delegating speech synthesis to the browser's client-side Web Speech API.

### Lip-Sync & Viseme Timeline (`integration/avatar/lipsync.py`)
- **Acoustic Phonetic Analysis:** Wraps Rhubarb Lip Sync 1.14.0 to map audio phonemes to Chacha Chaudhary's 16 viseme targets (`Viseme_A`, `Viseme_E`, etc.).
- **Architectural Fact:** The bundled binary in `tools/rhubarb/` is a Windows executable (`rhubarb.exe`). On non-Windows platforms without a native Rhubarb binary, the analyzer activates `_build_fallback_timeline`, generating procedural speech-cadence visemes at 200 ms intervals.

---

## 9. 3D Digital Avatar & Web User Interface

- **Web Interface:** Standalone HTML5/CSS/JavaScript application (`avatar/index.html`, `avatar/app.js`, `avatar/style.css`, `avatar/mascot.js`).
- **Active 3D Model:** `avatar/Chacha_New/Chacha_New.glb` (7.56 MB binary glTF 2.0).
  - Geometry: 31,058 draw vertices.
  - Armature: 65 Mixamo bones.
  - Animations: 28 embedded skeletal animation clips (`Idle`, `Acknowledging`, `Talking`, `Pointing`, `Praying`, `Clapping`, `Waving`, etc.).
  - Framing: Responsive Three.js camera calibrated to maintain an 80.5% vertical character viewport occupancy.
- **Preserved High-Fidelity Asset:** `avatar/Member2_Chacha/Chacha_Master.glb` (101.33 MB).
  - Geometry: 60,000 unique vertices (119,507 glTF draw vertices).
  - Armature: 57 Mixamo bones.
  - Morph Targets: 35 facial shape keys (11 modular, 7 composite emotions, 16 phonetic visemes).
  - Animations: 9 Mixamo body actions.
- **Discrepancy Resolution (Unity vs Three.js):** Source code in `avatar/07_Unity/` represents an early exploratory prototype. The active production runtime is 100% Three.js WebGL running directly in standard web browsers.

---

## 10. Test and Evaluation Artifacts

| Test Suite | File Location | Test Count | Status / Outcome | Execution Conditions |
| :--- | :--- | :--- | :--- | :--- |
| **Brain Hardening Suite** | `brain/tests/test_brain_hardening.py` | 12 | **12 / 12 PASS** | Fully offline; verifies API requests, error conditions, edge cases |
| **Broad Query Regression** | `brain/tests/test_broad_query_regression.py` | 11 | **11 / 11 PASS** | Fully offline; tests overview boosting and broad query routing |
| **LLM Generator & Fallback**| `brain/tests/test_llm_generator.py` | 19 | **19 / 19 PASS** | Fully offline; mocks Groq client, tests prompt limits & extractive fallback |
| **Total Brain Suite** | `brain/tests/` | **42** | **42 / 42 PASS** | Verified via `PYTHONPATH=. ./.venv/bin/pytest brain/tests` |
| **Avatar & Asset Tests** | `integration/tests/test_chacha_new_integration.py` | 6 | **6 / 6 PASS** | Offline; parses GLB headers, bone structures, and animations |
| **Member2 Avatar Tests** | `integration/tests/test_member2_integration.py` | 12 | **12 / 12 PASS** | Offline; parses Chacha_Master.glb and shape keys |
| **Integration Unit Tests**| `integration/tests/` (excluding end-to-end) | 29 | **29 / 29 PASS** | Verified via `PYTHONPATH=. ./.venv/bin/pytest integration/tests -k "not test_end_to_end"` |
| **End-to-End Integration** | `integration/tests/test_end_to_end.py` | 4 | **2 PASS, 2 FAIL** | Tests with Hindi translation fail when offline due to Google Translate HTTP dependency |
| **Golden Evaluation Script**| `brain/tests/run_evaluation.py` | 8 | **8 / 8 PASS** | Tested 8 representative queries with extractive fallback; output recorded in `evaluation_results.json` |

---

## 11. Known Technical Limitations & Research Considerations

1. **Static Corpus Horizon:** The knowledge base reflects GRBMP documents published between 2010 and 2015. It lacks contemporary post-2020 NMCG project data.
2. **Absence of Direct IoT Sensor Feeds:** The application does not directly connect to river sensors. CPCB station readings are handled by a separate integration-layer route, as described in the post-baseline update.
3. **External Network Reliance:** Hosted Groq/OpenRouter generation, Google translation, and EdgeTTS require live internet access when selected.
4. **Heuristic Gating:** Lexical overlap and distance thresholds filter irrelevant queries effectively but do not constitute formal semantic entailment proofs.
5. **Cross-Platform Audio/Tooling Gaps:** SAPI speech synthesis and Rhubarb binary analysis are Windows-dependent, requiring fallback paths on macOS/Linux.

---

## 12. Post-Baseline Generation-Layer Resilience Update (2026-10-18)

The working branch adds a configurable hosted-provider chain after the existing Brain retrieval and evidence-quality gate: Groq is the default first provider, OpenRouter is attempted next, and the existing extractive generator is the final fallback. Each configured provider is attempted at most once per request. Missing credentials and provider errors advance to the next provider. `LLM_PROVIDER_ORDER=openrouter,groq` makes OpenRouter primary, while `LLM_PROVIDER=extractive` keeps generation local-only. Groq and OpenRouter keys and model settings remain independent, and project-root `.env` loading does not override exported variables.

The change is confined to generation/configuration orchestration; it does not change retrieval scoring, evidence acceptance, or the citation assembly algorithm. Hosted citation metadata continues to be built from retrieved evidence, while extractive fallback cites only hits contributing selected sentences and may therefore return a different citation list. Current-information and evidence-rejection branches still bypass hosted generation, and CPCB water-quality routing remains in the integration controller.

Provider tests use mocked SDK clients and fake credentials. No real-provider smoke test or comparative quality, latency, or availability experiment is claimed. OpenRouter free endpoints may be rate limited and have provider-specific data-handling terms. See `research/implementation_and_evaluation.md` for current-checkout validation commands and results.
