# Implementation and Evaluation: Ganga AI Mascot (PRJ_316)

**Project ID:** PRJ_316  
**Project Title:** AI-Powered Interactive Digital Mascot for Namami Gange Awareness & River-People Connectivity  
**Status:** Reproducible Implementation Guide & Evaluation Benchmark Protocol  
**Authoritative Baseline:** `56032d744b80695be7593c6f85e50d53c7c5a083`  
**Execution Environment:** macOS / Linux / Windows, Python 3.11–3.13  

---

> [!IMPORTANT]
> **Reproducibility Guarantee & Empirical Deferral:**  
> All commands, paths, and configurations in this document have been verified directly within the repository. In accordance with academic research standards, empirical benchmark performance measurements (Precision@k, Recall@k, MRR, Answer Faithfulness) are **deferred** to Stage 6 of the research work plan. The 8 golden evaluation test results documented below are recorded purely as existing regression assertions, not as a general benchmark claim.

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
|    - `generator.py`: Grounded Groq generation (gpt-oss-120b) and local ExtractiveGenerator.   |
|    - `translator.py`: Bilingual translation between English and Hindi.                        |
|    - `chunking.py`: Paragraph-preserving character chunking with overlap and metadata.        |
+-----------------------------------------------------------------------------------------------+
| 2. KNOWLEDGE BASE SUBSYSTEM (`knowledge_base/`)                                               |
|    - `raw_documents/GRBMP/`: 86 authoritative PDF reports from the IIT Consortium.            |
|    - `processed/`: Ingestion manifests, section reviews (1,111 approved), JSONL extractions.  |
|    - `vector_db/`: `brain_index.sqlite3` (11.9MB) and `brain_semantic_vectors.npy` (6.27MB).   |
+-----------------------------------------------------------------------------------------------+
| 3. INTEGRATION & VOICE SUBSYSTEM (`integration/`)                                             |
|    - `server.py`: Primary FastAPI application (port 8080); serves UI, mounts Brain API.       |
|    - `api/brain_client.py`: In-process and HTTP client routing requests to Brain.             |
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
[Brain Pipeline: brain/rag_pipeline.py]
               │
               ├─► [Language Normalization: if hi -> translate to en for search]
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
               ├─► [Grounded Generation: Groq gpt-oss-120b or Extractive Fallback]
               │
               ├─► [Decoupled Citation Assembly: metadata bound directly from chunks]
               │
               └─► [Output Translation: if target_lang == 'hi' -> translate answer]
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
| `LLM_PROVIDER` | `groq` | Generator backend (`groq` or `extractive`) | Standalone Brain |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | Groq chat completion model | Standalone Brain |
| `GROQ_API_KEY` | *(None)* | Secret Groq API authentication key | Standalone Brain |
| `GANGA_BRAIN_EMBEDDING_PROVIDER` | `semantic` | Embedding backend (`semantic` or `local-hash`) | Standalone Brain |
| `GANGA_BRAIN_EMBEDDING_MODEL` | `all-MiniLM-L6-v2`| ONNX semantic embedding model | Standalone Brain |
| `GANGA_BRAIN_TOP_K` | `5` | Maximum verified evidence chunks returned | Standalone Brain |
| `GANGA_BRAIN_CANDIDATE_TOP_K` | `15` | Nearest neighbors retrieved in Stage 1 | Standalone Brain |
| `GANGA_BRAIN_EVIDENCE_MAX_DISTANCE`| `1.15` | Maximum allowed Euclidean distance threshold | Standalone Brain |
| `GANGA_BRAIN_MIN_KEYWORD_OVERLAP` | `0.15` | Minimum top-candidate lexical overlap | Standalone Brain |
| `GANGA_BRAIN_ORT_THREADS` | `2` | CPU thread allocation for ONNX Runtime | Standalone Brain |
| `BRAIN_URL` | `http://127.0.0.1:8000` | URL for integration service to reach Brain | Integration Server |
| `MOCK_MODE` | `False` | When True, bypasses heavy models for mock tests | Integration Server |

---

## 4. Verified Setup, Build, and Run Commands

All commands have been verified on Python 3.13 within this repository.

### Step 1: Environment Setup
```bash
# From repository root: /Users/madhavan/Documents/Ganga-AI-Mascot/Ganga-AI-Mascot
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

## 5. Test Catalog & Verified Outcomes

### 5.1 Brain Subsystem Automated Test Suite
- **Command:** `PYTHONPATH=. ./.venv/bin/pytest brain/tests`
- **Verified Execution Outcome:** **42 passed** in 2.17 seconds (0 failures, 0 errors).

| Test Module | Test File | Items | Primary Assertions |
| :--- | :--- | :--- | :--- |
| **Brain Hardening** | `brain/tests/test_brain_hardening.py` | 12 | Tests `/health`, `/ask` validation, out-of-domain rejection, empty string safety, language parameter handling, and distance boundary edge cases. |
| **Broad Query Routing**| `brain/tests/test_broad_query_regression.py` | 11 | Tests broad Ganga query detection, overview document matching, overview boost calculations, and regression protection for general inquiries. |
| **LLM Generator & Mocks**| `brain/tests/test_llm_generator.py` | 19 | Tests Groq chat client initialization, prompt bounding (6,000 char limit), temperature configuration, citation assembly, and seamless fallback to `ExtractiveGenerator`. |

### 5.2 Integration Subsystem Automated Test Suite
- **Command:** `PYTHONPATH=. ./.venv/bin/pytest integration/tests -k "not test_end_to_end"`
- **Verified Execution Outcome:** **29 passed, 4 deselected** in 0.72 seconds.

| Test Module | Test File | Items | Primary Assertions |
| :--- | :--- | :--- | :--- |
| **Avatar Mapping** | `integration/tests/test_avatar_mapping.py` | 2 | Verifies legacy animation alias mappings (`explaining` $\to$ `point`, `namaste` $\to$ `thankful`, `greet` $\to$ `wave`). |
| **Brain Client** | `integration/tests/test_brain_client.py` | 4 | Verifies direct in-process RAG calling, HTTP client fallbacks, and error handling. |
| **Chacha New Integration**| `integration/tests/test_chacha_new_integration.py` | 6 | Validates `Chacha_New.glb` binary integrity, non-zero file size, bone hierarchy (65 bones), and 28 embedded animation clips. |
| **Conversation Controller**| `integration/tests/test_conversation_controller.py`| 3 | Validates session dialogue history, context turns, and state machine transitions. |
| **Member2 Asset Guard** | `integration/tests/test_member2_integration.py` | 12 | Validates `Chacha_Master.glb` file size (>100MB), 57 bones, 35 shape keys, and 9 skeletal actions. |
| **STT / TTS Adapters** | `integration/tests/test_stt_tts.py` | 2 | Tests speech adapter instantiation, audio result data classes, and fallback paths. |

### 5.3 Golden Evaluation Suite (Existing Artifact)
- **Script:** `brain/tests/run_evaluation.py`
- **Output Artifact:** `brain/tests/evaluation_results.json`
- **Command:** `PYTHONPATH=. ./.venv/bin/python brain/tests/run_evaluation.py`
- **Verified Execution Outcome:** **8 / 8 PASS** (Executed with local extractive fallback).

| Case ID | Question | Expected Mode | Actual Mode | Citations | Verified Behavior |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **A_factual** | "What is Aviral Dhara?" | `grounded` | `grounded` | 3 | Accurately retrieves and quotes GRBMP e-flows definition. |
| **B_urban_pollution** | "What does the GRBMP say about pollution load from urban areas?" | `grounded` | `grounded` | 4 | Retrieves BOD/COD urban discharge tables. |
| **C_historical** | "According to the GRBMP material, what historical concerns are associated with sewage pollution?" | `grounded` | `grounded` | 3 | Prepends historical notice and cites historical sections. |
| **D_unsupported_mars** | "What is the population of Mars according to the GRBMP?" | `insufficient-evidence` | `insufficient-evidence` | 0 | Gate 1 blocks query; returns safe disclaimer. |
| **E_current_info** | "What is the current water quality of the Ganga today?" | `current-info-fallback` | `current-info-fallback` | 0 | `asks_for_current_information` blocks retrieval; returns disclaimer. |
| **F_provenance** | "What does the knowledge base say about environmental flows, and which source page supports it?" | `grounded` | `grounded` | 3 | Binds valid report title and page range metadata. |
| **G_citations** | "What are the key functions of National Ganga River Basin Authority?" | `grounded` | `grounded` | 3 | Binds NGRBA institutional mandate with 0 hallucinated sources. |
| **H_empty_query** | "" | `insufficient-evidence` | `insufficient-evidence` | 0 | Immediate safety rejection. |

---

## 6. Known Environment Requirements & Reproducibility Risks

1. **Online Translation Failure:** When running in an air-gapped or network-sandboxed environment, HTTP calls to Google Translate GTX fail. End-to-end tests requesting English-to-Hindi translation (`test_all_four_language_combinations`) fail unless pre-translated domain dictionary terms are matched.
2. **Platform Audio Fallback:** 
   - `EdgeTTS` requires outbound internet access to `speech.platform.bing.com`.
   - Local `SAPI` requires Windows PowerShell. On macOS/Linux, offline TTS returns `None`, delegating speech synthesis to the browser's Web Speech API.
3. **Rhubarb Binary Compatibility:** The bundled binary `tools/rhubarb/Rhubarb-Lip-Sync-1.14.0-Windows/rhubarb.exe` is a Windows executable. On non-Windows platforms, `_build_fallback_timeline` generates procedural speech-cadence visemes at 200 ms intervals.
4. **ONNX Thread Limits:** Conservative thread limits (`GANGA_BRAIN_ORT_THREADS=2`) are strictly necessary on multicore workstations to prevent OpenMP/ONNX thread contention.
