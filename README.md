# Ganga AI Mascot

**Project ID:** PRJ_316  
**Project title:** AI-Powered Interactive Digital Mascot for Namami Gange Awareness & River-People Connectivity

Ganga AI Mascot is an academic prototype for exploring Ganga-related information through a retrieval-augmented Brain service and a web-based mascot interface. The Brain answers questions using a curated, static collection of official Ganga and Namami Gange documents. A Groq-hosted language model is used for grounded generation after evidence retrieval and filtering; it is not a live web or river-monitoring service.

The project brings together source-grounded question answering, a Three.js character interface, and voice-related adapters. Its educational aim is to make information about Ganga stewardship, pollution, and conservation accessible through text and supported voice interaction.

## Overall system architecture

```text
Browser text or audio input
        ↓
Integration FastAPI service
        ├── Text questions ──→ Brain client ──→ Brain retrieval and answer pipeline
        └── Audio input ──────→ STT adapter ───→ Brain retrieval and answer pipeline
                                                   ↓
Browser UI ← Avatar presentation ← TTS and lip-sync processing ← Answer and citations
```

The integration service exposes its own endpoints and mounts the standalone Brain API under `/brain`. The browser interface is served from `avatar/` when its `index.html` is present. Voice synthesis and lip-sync use the configured integrations and available platform tools; availability can depend on runtime configuration and operating system.

## Brain architecture

```text
Official Ganga/Namami Gange PDF documents
        ↓
Knowledge-base processing and reviewed-section filtering
        ↓
Chunking with source metadata
        ↓
384-dimensional semantic embeddings
        ↓
SQLite metadata + NumPy vector index
        ↓
Hybrid semantic retrieval and lexical reranking
        ↓
Heuristic evidence quality gate
        ↓
Groq grounded generation (or extractive fallback)
        ↓
Trusted citations/provenance and FastAPI response
```

The current knowledge-base inventory contains 86 PDF documents, 4,609 pages, 1,111 approved/reviewed sections, and 4,085 indexed chunks. The semantic embedding model is `all-MiniLM-L6-v2` with 384 dimensions. Runtime storage uses the application-owned SQLite and NumPy index files under `knowledge_base/vector_db/`, with a manifest used for index integrity checks. Chroma-format files in that directory are legacy artifacts, not the active runtime store.

Retrieval combines semantic similarity with lexical reranking. A heuristic evidence gate evaluates retrieved evidence before normal answer generation. Unsupported queries may receive an insufficient-evidence response; questions recognized as requiring current information are handled separately because the knowledge base is static. These checks are not calibrated confidence estimates or guarantees that every generated claim is supported.

## Groq generation and citations

The default generation provider is Groq, using the OpenAI-compatible Python SDK endpoint `https://api.groq.com/openai/v1`. The configured default model is `openai/gpt-oss-120b`. The model receives the question and selected evidence with source metadata only after the evidence gate accepts the query. Citation metadata is assembled from retrieved evidence by the Brain rather than generated as source references by the model.

If the Groq key is missing or the request fails, the existing extractive generator is used. Current-information and insufficient-evidence branches bypass normal LLM generation. LLM tests use mocks and do not make real Groq API requests.

Prompt constants are exposed through the `brain.prompts` package. The current files are `brain/prompts/__init__.py` and `brain/prompts/system.py`; `brain/prompts.py` is no longer part of the project.

## Configuration

Configuration is read from process environment variables. The application does not automatically load `.env` files. `.env` should remain local and must not be committed; `.env.example` documents non-secret settings.

| Variable | Purpose |
| --- | --- |
| `LLM_PROVIDER` | `groq` (default) or `extractive` |
| `GROQ_MODEL` | Groq model; defaults to `openai/gpt-oss-120b` |
| `GROQ_API_KEY` | Secret credential for Groq; provide through a private environment setting |
| `GANGA_BRAIN_EMBEDDING_PROVIDER` | Semantic embedding provider (`semantic` by default) or `local-hash` |
| `GANGA_BRAIN_EMBEDDING_MODEL` | Semantic embedding model (`all-MiniLM-L6-v2` by default) |
| `GANGA_BRAIN_TOP_K` | Maximum returned evidence count |
| `GANGA_BRAIN_CANDIDATE_TOP_K` | Candidate count used during retrieval |
| `GANGA_BRAIN_EVIDENCE_MAX_DISTANCE` | Evidence-gate distance threshold |
| `GANGA_BRAIN_MIN_KEYWORD_OVERLAP` | Evidence-gate lexical overlap threshold |
| `GANGA_BRAIN_ORT_THREADS` | ONNX Runtime thread limit |

To use a local `.env`, add `GROQ_API_KEY` privately, then export the file before starting a server:

```bash
set -a
source .env
set +a
```

Do not paste or commit a real API key.

## Installation and running

Use Python 3.11 or newer and install the project dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Build or validate the derived Brain index when required:

```bash
python -m brain.rag_pipeline --build-index
```

Start the standalone Brain API:

```bash
python -m brain.api --host 127.0.0.1 --port 8000
```

The standalone API provides `GET /health` and `POST /ask`. For example:

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"What is the Ganga River?","input_language":"en","output_language":"en"}'
```

The ask request accepts `question`, optional `input_language` and `output_language` (`en` or `hi`), the legacy `language` field, and optional `top_k` (1–100). Responses include an answer, a response `mode`, citations, and language fields.

The integration application can be started separately:

```bash
python -m integration.server --host 127.0.0.1 --port 8080
```

It defines `/api/integration/health`, `/api/integration/ask`, and `/api/integration/stt`, mounts the Brain API under `/brain`, and serves the avatar frontend when its entry point is available. If the frontend is served, open `http://127.0.0.1:8080/`. The interface supports typed questions and browser-recorded audio input, with input and output language controls for English and Hindi.

## Avatar, voice, and integration components

- **Avatar and browser UI:** `avatar/index.html`, `avatar/app.js`, and `avatar/mascot.js` provide the web interface and Three.js avatar controller. The model asset is `avatar/Member2_Chacha/Chacha_Master.glb`. The controller includes mappings for facial morph targets, Mixamo actions, avatar states, and speech visemes.
- The avatar implementation documents 35 morph targets, nine Mixamo actions, and a 57-bone model rig; its controller also includes procedural blinking and animation/state handling.
- **Speech recognition:** `integration/voice/stt_adapter.py` provides the Vosk adapter for English and Hindi, along with mock and browser-delegation adapters. Audio upload is handled by the integration STT route.
- **Speech synthesis:** `integration/voice/tts_adapter.py` provides Edge TTS and Windows SAPI-backed adapters, a synthetic WAV adapter for testing, and browser Web Speech delegation. Actual provider availability depends on the host environment.
- **Lip-sync and presentation:** `integration/avatar/lipsync.py` wraps Rhubarb when its binary is available and includes fallback timelines and RMS-based mouth-aperture analysis. `mascot_presenter.py` combines Brain responses with optional audio and lip-sync data for the browser.
- **Conversation and Brain connection:** `integration/controller/` manages conversation state; `integration/api/brain_client.py` connects the integration service to the Brain.

These are implemented project components, not a claim that every provider or operating-system path has been validated in every deployment environment.

## Tests

Run the Brain and integration test suites separately:

```bash
python -m pytest -q brain/tests
python -m pytest -q integration/tests
```

The Brain provider tests mock Groq. These test commands do not require a real Groq request.

The Brain suite on the integrated `main` branch was most recently verified with 38 passing tests. Run the commands above to check the current checkout; no fixed result is claimed for the integration suite here.

## Project workstreams

The earlier project documentation records these areas of team work:

- **Brain and RAG:** knowledge-base curation, reviewed-section processing, indexing, hybrid retrieval, and evidence quality gating.
- **Digital avatar and WebGL:** Chacha Chaudhary model and interface work, Three.js rendering, animation, and facial controls.
- **Integration and voice:** FastAPI integration, dialogue state, speech recognition and synthesis adapters, and lip-sync/presentation.

## Repository layout

```text
brain/
  api.py                Standalone Brain FastAPI service
  rag_pipeline.py       Retrieval and generation orchestration
  retriever.py          Hybrid retrieval and ranking
  vector_store.py       SQLite metadata and NumPy vector index
  generator.py          Groq-backed and extractive answer generators
  prompts/              Public prompt interface and system prompt
  tests/                Brain regression and provider tests
knowledge_base/
  raw_documents/        Source document collection
  processed/            Extracted and reviewed content
  vector_db/            Runtime index files and retained legacy artifacts
integration/
  server.py             Integration FastAPI app and frontend hosting
  api/                  Brain client
  controller/           Conversation state and orchestration
  voice/                STT and TTS adapters
  avatar/               Presentation, emotion, gesture, and lip-sync
  tests/                Integration tests
avatar/                 Web interface, Three.js code, and model assets
research/               Research material
docs/                   Project documentation and design material
tools/                  Supporting tools, including lip-sync tooling
```

## Status and limitations

The Brain Phase 1 knowledge pipeline and Phase 2 Groq generation are integrated in the current project branch. The system is a prototype: it uses static documents, heuristic retrieval/evidence thresholds, and an external generation provider. It does not have live web search or real-time water-quality data, does not perform formal claim-level entailment verification, and does not guarantee factual correctness. Translation and optional voice services depend on their configured external or platform-specific components.

Potential future directions recorded in earlier project material include adding live hydrological data sources, expanding language coverage, and exploring physical mascot embodiments; these are not described as implemented features.

This academic project demonstrates an information-access prototype for river-conservation awareness; it is not an operational environmental monitoring or decision-support system.
