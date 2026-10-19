# Implementation and Evaluation: Ganga AI Mascot (PRJ_316)

**Project ID:** PRJ_316  
**Project Title:** AI-Powered Interactive Digital Mascot for Namami Gange Awareness & River-People Connectivity  
**Status:** Implementation guide and proposed evaluation protocol
**Historical baseline:** `56032d744b80695be7593c6f85e50d53c7c5a083`
**Implementation snapshot audited:** `main` at `80833751f2a365eb00be5ddeee3392e4a601d38e` (2026-10-19; before documentation-only changes)
**Execution Environment:** macOS / Linux / Windows, Python 3.11–3.13  

---

> [!IMPORTANT]
> **Execution and empirical status:** Commands below describe how to run the software; they were not all executed during this documentation update. Saved retrieval, evidence-gate, and groundedness benchmark artifacts exist; their corrected reports describe the limited operational checks represented by those artifacts. They do not establish broad performance, semantic faithfulness, safety, or educational impact. The eight-case golden evaluation artifact is a small regression fixture, not a general benchmark or performance claim.

---

## 1. System Components and Responsibilities

The codebase is organized into four core architectural components:

```
+-----------------------------------------------------------------------------------------------+
|                                    GANGA AI MASCOT SYSTEM                                     |
+-----------------------------------------------------------------------------------------------+
| 1. BRAIN SUBSYSTEM (`brain/`)                                                                 |
|    - `api.py`: Standalone FastAPI service exposing GET /health, POST /ask.                    |
|    - `rag_pipeline.py`: Orchestrates translation, dynamic checking, retrieval, and generation.|
|    - `retriever.py`: Vector similarity retrieval, lexical overlap reranking, evidence gate.    |
|    - `vector_store.py`: Thread-safe SQLite metadata and memory-mapped NumPy vector index.     |
|    - `embeddings.py`: Local CPU ONNX execution of all-MiniLM-L6-v2 (384d).                    |
|    - `generator.py`: Evidence-gated Groq → OpenRouter → extractive generation chain.          |
|    - `translator.py`: English/Hindi/Kannada/Tamil selection, detection, and translation handling.|
|    - `chunking.py`: Paragraph-preserving character chunking with overlap and metadata.        |
+-----------------------------------------------------------------------------------------------+
| 2. KNOWLEDGE BASE SUBSYSTEM (`knowledge_base/`)                                               |
|    - `raw_documents/GRBMP/`: 86 authoritative PDF reports from the IIT Consortium.            |
|    - `processed/`: Ingestion manifests, section reviews (1,111 approved), JSONL extractions.  |
|    - `vector_db/`: `brain_index.sqlite3` (11.9MB) and `brain_semantic_vectors.npy` (6.27MB).   |
+-----------------------------------------------------------------------------------------------+
| 3. INTEGRATION & VOICE SUBSYSTEM (`integration/`)                                             |
|    - `server.py`: Primary FastAPI application (port 8080); serves UI, mounts Brain API.       |
|    - `water_quality.py`: CPCB live water-quality retrieval, station/parameter parsing,        |
|       freshness checking, response formatting. Intercepted before Brain query.                 |
|    - `api/brain_client.py`: In-process and HTTP client routing requests to Brain.             |
|    - `controller/conversation_controller.py`: Routes CPCB vs. Brain queries; state machine.   |
|    - `voice/stt_adapter.py`: Offline Vosk speech recognition (English and Hindi).             |
|    - `voice/tts_adapter.py`: Microsoft EdgeTTS neural speech with Windows SAPI fallback.       |
|    - `avatar/lipsync.py`: Rhubarb acoustic lip-sync wrapper with procedural cadence fallback. |
|    - `avatar/mascot_presenter.py`: Bundles audio, visemes, gestures, and citations.           |
+-----------------------------------------------------------------------------------------------+
| 4. DIGITAL AVATAR & CLIENT SUBSYSTEM (`avatar/`)                                              |
|    - `index.html`, `app.js`, `style.css`: Responsive client interface with chat and mic.      |
|    - `mascot.js`: Three.js WebGL engine; manages 3D model, bone transforms, and animations.  |
|    - `Chacha_New/Chacha_New.glb`: Active 3D character asset (65 bones, 28 Mixamo animations).  |
|    - `Member2_Chacha/Chacha_Master.glb`: Preserved high-fidelity asset (57 bones, 35 morphs). |
+-----------------------------------------------------------------------------------------------+
```

---

## 2. End-to-End Data Flow

```
[User Input: Text or Audio WAV]
               │
               ▼
[Integration Server: integration/server.py]
               │
   ┌───────────┴───────────┐
   │ (Audio Input)         │ (Text Input)
   ▼                       │
[Vosk STT Transcription]   │
   │                       │
   └───────────┬───────────┘
               │
               ▼ [Question String + Target Language]
[Conversation Controller: integration/controller/conversation_controller.py]
               │
               ├─► [CPCB Live Water-Quality Detection: is_water_quality_query(q)]
               │        │ (if True) ──► parse_water_quality_request(q)
               │                                │
               │                    CPCBWaterQualityService.readings(request)
               │                                │
               │              Fetches station registry + layer-10 snapshot
               │              (CPCB endpoints; 60s in-memory cache)
               │                                │
               │                    format_water_quality_answer(request, records)
               │                                │
               │        Returns AvatarPresentation (mode="live-water-quality")
               │        with CPCB attribution and freshness labels
               │        ◄── (stops here; Brain pipeline is not called)
               │
               ▼ [Non-water-quality questions continue to Brain pipeline]
[Brain Pipeline: brain/rag_pipeline.py]
               │
               ├─► [Language Normalization: if hi → translate to en for search]
               │
               ├─► [Dynamic Query Detection: asks_for_current_information(q)]
               │        │ (if True) ──► Return Static Knowledge Disclaimer
               │
               ├─► [Vector Search: SQLiteVectorStore.query(q, candidate_k=15)]
               │        │ (Computes Euclidean distance over 4,085 vectors)
               │
               ├─► [Pre-Rerank Gate 1: Pool Keyword Coverage >= 60%]
               │        │ (if < 60%) ──► Return Insufficient Evidence
               │
               ├─► [Distance Cutoff: dist <= 1.15]
               │
               ├─► [Hybrid Reranking: S_hybrid = 1/(1+dist) + 0.5*overlap + 0.25*overview]
               │
               ├─► [Post-Rerank Gate 2: Top Candidate Overlap >= 15%]
               │        │ (if < 15%) ──► Return Insufficient Evidence
               │
               ├─► [Evidence-Gated Generation: Groq → OpenRouter → Extractive Fallback]
               │
               ├─► [Decoupled Citation Assembly: metadata bound directly from chunks]
               │
               └─► [Output Translation: if target_lang == 'hi' → translate answer]
               │
               ▼ [Brain Response JSON: answer, citations, mode, retrieved chunks]
[MascotPresenter: integration/avatar/mascot_presenter.py]
               │
               ├─► [Emotion & Gesture Mapping: selects animation clip e.g. 'Pointing']
               │
               ├─► [TTS Synthesis: EdgeTTS generates 16kHz WAV audio]
               │
               ├─► [Lip-Sync Analysis: Rhubarb or Cadence generator produces visemes]
               │
               ▼ [AvatarPresentation Payload: audio_base64, visemes, gesture, answer, citations]
[Browser Client: avatar/mascot.js]
               │
               ├─► Play synthesized WAV audio
               ├─► Drive skeletal lip-sync & facial expressions frame-by-frame (60 FPS)
               ├─► Execute Mixamo gesture clip
               └─► Render text response with interactive provenance citations
```

---

## 3. Configuration & Environment Variables

All settings are configured via environment variables or specified with sensible local defaults in `brain/config.py` and `integration/config/integration_config.py`.

| Variable Name | Default Value | Description | Production Scope |
| :--- | :--- | :--- | :--- |
| `LLM_PROVIDER` | `groq` | Generator selection (`groq`, `openrouter`, or strict local-only `extractive`) | Standalone Brain |
| `LLM_PROVIDER_ORDER` | `groq,openrouter` | Comma-separated hosted order; `openrouter,groq` reverses priority | Standalone Brain |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | Groq chat completion model | Standalone Brain |
| `GROQ_API_KEY` | *(None)* | Secret Groq API authentication key | Standalone Brain |
| `OPENROUTER_MODEL` | `nvidia/nemotron-3.5-super-vl:free` | OpenRouter chat completion model | Standalone Brain |
| `OPENROUTER_API_KEY` | *(None)* | Secret OpenRouter API authentication key | Standalone Brain |
| `GANGA_BRAIN_EMBEDDING_PROVIDER` | `semantic` | Embedding backend (`semantic` or `local-hash`) | Standalone Brain |
| `GANGA_BRAIN_EMBEDDING_MODEL` | `all-MiniLM-L6-v2`| ONNX semantic embedding model | Standalone Brain |
| `GANGA_BRAIN_TOP_K` | `5` | Maximum verified evidence chunks returned | Standalone Brain |
| `GANGA_BRAIN_CANDIDATE_TOP_K` | `15` | Nearest neighbors retrieved in Stage 1 | Standalone Brain |
| `GANGA_BRAIN_EVIDENCE_MAX_DISTANCE`| `1.15` | Maximum allowed Euclidean distance threshold | Standalone Brain |
| `GANGA_BRAIN_MIN_KEYWORD_OVERLAP` | `0.15` | Minimum top-candidate lexical overlap | Standalone Brain |
| `GANGA_BRAIN_ORT_THREADS` | `2` | CPU thread allocation for ONNX Runtime | Standalone Brain |
| `BRAIN_URL` | `http://127.0.0.1:8000` | URL for integration service to reach Brain | Integration Server |
| `MOCK_MODE` | `False` | When True, bypasses heavy models for mock tests | Integration Server |

The project-root `.env` is loaded at startup when present, without replacing explicitly exported environment variables. Groq and OpenRouter use independent keys and models. Each configured hosted provider is tried at most once after the static retrieval evidence gate accepts the query; missing credentials and provider errors advance to the next provider. Local extractive output is the final fallback. Current-information and evidence-rejection branches bypass hosted generation, while CPCB water-quality requests are routed separately by the integration controller. Citations are assembled from retrieved metadata; the extractive fallback can return a different citation subset because it cites the hits that contributed extracted sentences. No live-provider compatibility or availability is implied by these implementation details.

---

## 4. Verified Setup, Build, and Run Commands

All commands have been verified on Python 3.13 within this repository.

### Step 1: Environment Setup
```bash
# From the repository root
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Build / Verify Knowledge Base Vector Index
*(Note: Pre-built index files already exist at `knowledge_base/vector_db/`. This command rebuilds them from reviewed sections.)*
```bash
PYTHONPATH=. ./.venv/bin/python -m brain.rag_pipeline --build-index
```
**Verified Outcome:** Reads `section_review.json` (1,111 sections), chunks text into 4,085 chunks, generates MiniLM 384d vectors, validates SHA-256 checksums, and atomically writes `brain_index.sqlite3` and `brain_semantic_vectors.npy`.

### Step 3: Run Standalone Brain API
```bash
PYTHONPATH=. ./.venv/bin/python -m brain.api --host 127.0.0.1 --port 8000
```
**Verification Test:**
```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Aviral Dhara?", "input_language": "en", "output_language": "en"}'
```

### Step 4: Run Integration Server & Web Mascot UI
```bash
PYTHONPATH=. ./.venv/bin/python -m integration.server --host 127.0.0.1 --port 8080
```
Open `http://127.0.0.1:8080/` in a WebGL-compatible browser to interact with the 3D Chacha Chaudhary mascot.

---

## 5. Test Catalog and Previously Reported Evidence

No application test suite was run for this documentation audit. The results below are historical reports supplied from earlier runs, not fresh verification of the current checkout.

### 5.1 Brain Subsystem Automated Test Suite
- **Previously reported command:** `env LLM_PROVIDER=extractive GROQ_API_KEY= OPENROUTER_API_KEY= ./.venv/bin/python -m pytest -q brain/tests`
- **Previously reported outcome:** **76 passed, 19 subtests**. This was run with explicit extractive mode and blank hosted-provider variables; it is not a new result from this audit.

| Test Module | Test File | Items | Primary Assertions |
| :--- | :--- | :--- | :--- |
| **Brain Hardening** | `brain/tests/test_brain_hardening.py` | 12 | Tests `/health`, `/ask` validation, out-of-domain rejection, empty string safety, language parameter handling, and distance boundary edge cases. |
| **Broad Query Routing**| `brain/tests/test_broad_query_regression.py` | 11 | Tests broad Ganga query detection, overview document matching, overview boost calculations, and regression protection for general inquiries. |
| **LLM Generator & Mocks**| `brain/tests/test_llm_generator.py` | Suite dependent | Mocks Groq and OpenRouter clients and checks provider ordering, fallback, request compatibility, citations, and safe logging. |
| **Multilingual handling** | `brain/tests/test_multilingual_support.py` | Included in prior full-suite report | Exercises language selection/detection and mocked translation/error paths; external translation is not live-validated by mocked tests. |

### 5.2 Integration Subsystem Automated Test Suite
- **Previously reported command:** `env LLM_PROVIDER=extractive GROQ_API_KEY= OPENROUTER_API_KEY= ./.venv/bin/python -m pytest -q integration/tests --ignore=integration/tests/test_end_to_end.py`
- **Previously reported outcome:** **54 passed**. This used explicit extractive mode and blank hosted-provider variables; network-dependent `integration/tests/test_end_to_end.py` was excluded. It is not a new result from this audit.

| Test Module | Test File | Items | Primary Assertions |
| :--- | :--- | :--- | :--- |
| **Avatar Mapping** | `integration/tests/test_avatar_mapping.py` | 2 | Verifies legacy animation alias mappings (`explaining` $\to$ `point`, `namaste` $\to$ `thankful`, `greet` $\to$ `wave`). |
| **Brain Client & LLM Route** | `integration/tests/test_brain_client.py`, `integration/tests/test_llm_route.py` | Current checkout | Verifies direct in-process RAG calling, HTTP client fallbacks, error handling, and mocked eligible-question routing. |
| **Chacha New Integration**| `integration/tests/test_chacha_new_integration.py` | 6 | Validates `Chacha_New.glb` binary integrity, non-zero file size, bone hierarchy (65 bones), and 28 embedded animation clips. |
| **Conversation Controller**| `integration/tests/test_conversation_controller.py`| 3 | Validates session dialogue history, context turns, and state machine transitions. |
| **Member2 Asset Guard** | `integration/tests/test_member2_integration.py` | 12 | Validates `Chacha_Master.glb` file size (>100MB), 57 bones, 35 shape keys, and 9 skeletal actions. |
| **STT / TTS Adapters** | `integration/tests/test_stt_tts.py` | 2 | Tests speech adapter instantiation, audio result data classes, and fallback paths. |
| **CPCB Water Quality Chat**| `integration/tests/test_water_quality_chat.py` | 20 | Tests query classification, multi-station parsing, parameter extraction (DO, BOD, pH), stale measurement labelling (>90m), registry validation, 60s caching, unsupported station rejection, and API failure handling. |
| **Multilingual route** | `integration/tests/test_multilingual_route.py` | Included in prior full-suite report | Checks route language handling, UI controls, and configured-provider limits using mocks. |

### 5.3 Golden Evaluation Suite (Existing Artifact)
- **Script:** `brain/tests/run_evaluation.py`
- **Output Artifact:** `brain/tests/evaluation_results.json`
- **Command:** `PYTHONPATH=. ./.venv/bin/python brain/tests/run_evaluation.py`
- **Prior artifact report:** **8 / 8 PASS** with local extractive fallback; this documentation task did not rerun the script or independently revalidate its output artifact.

| Case ID | Question | Expected Mode | Prior artifact mode | Citations | Prior artifact note (not correctness validation) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **A_factual** | "What is Aviral Dhara?" | `grounded` | `grounded` | 3 | Returned a grounded-mode answer and citation metadata. |
| **B_urban_pollution** | "What does the GRBMP say about pollution load from urban areas?" | `grounded` | `grounded` | 4 | Retrieves BOD/COD urban discharge tables. |
| **C_historical** | "According to the GRBMP material, what historical concerns are associated with sewage pollution?" | `grounded` | `grounded` | 3 | Prepends historical notice and cites historical sections. |
| **D_unsupported_mars** | "What is the population of Mars according to the GRBMP?" | `insufficient-evidence` | `insufficient-evidence` | 0 | Gate 1 blocks query; returns safe disclaimer. |
| **E_current_info** | "What is the current water quality of the Ganga today?" | `current-info-fallback` | `current-info-fallback` | 0 | `asks_for_current_information` blocks retrieval; returns disclaimer. |
| **F_provenance** | "What does the knowledge base say about environmental flows, and which source page supports it?" | `grounded` | `grounded` | 3 | Binds valid report title and page range metadata. |
| **G_citations** | "What are the key functions of National Ganga River Basin Authority?" | `grounded` | `grounded` | 3 | Returned citation objects associated with retrieved metadata; no claim-level source audit is implied. |
| **H_empty_query** | "" | `insufficient-evidence` | `insufficient-evidence` | 0 | Immediate safety rejection. |

### 5.4 Provider-Chain Validation
- **Command:** `./.venv/bin/python -m pytest -q brain/tests/test_config_environment.py brain/tests/test_llm_generator.py`
- **Previously reported outcome:** **34 passed, 12 subtests**. Provider SDK calls were mocked and fake credentials used; no real hosted API call. The earlier report recorded no warnings.

Earlier focused multilingual tests were reported as **22 passed**, and quiz tests as **5 passed**. These are prior reports; the exact invocation is not preserved here. Translation/LLM/CPCB/STT/TTS dependencies were mocked where covered. The quiz count is an automated software test, not a user study. `git diff --check` was also previously reported as passing. None of these reports establishes current live-provider compatibility or availability.

---

## 6. Known Environment Requirements & Reproducibility Risks

1. **Online Translation Failure:** When running in an air-gapped or network-sandboxed environment, HTTP calls to Google Translate GTX fail. End-to-end tests requesting English-to-Hindi translation (`test_all_four_language_combinations`) fail unless pre-translated domain dictionary terms are matched.
2. **Platform Audio Fallback:** 
   - `EdgeTTS` requires outbound internet access to `speech.platform.bing.com`.
   - Local `SAPI` requires Windows PowerShell. On macOS/Linux, offline TTS returns `None`, delegating speech synthesis to the browser's Web Speech API.
3. **Rhubarb Binary Compatibility:** The bundled binary `tools/rhubarb/Rhubarb-Lip-Sync-1.14.0-Windows/rhubarb.exe` is a Windows executable. On non-Windows platforms, `_build_fallback_timeline` generates procedural speech-cadence visemes at 200 ms intervals.
4. **ONNX Thread Limits:** Conservative thread limits (`GANGA_BRAIN_ORT_THREADS=2`) are strictly necessary on multicore workstations to prevent OpenMP/ONNX thread contention.
