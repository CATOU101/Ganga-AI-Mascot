# Development of AI, ML and Chatbot-powered Interactive Robot Mascot (Chacha Chaudhary) and Digital Avatar to Strengthen the River People Connect Component of Namami Gange

- **Project ID:** PRJ_316
- **Official project title:** Development of AI, ML and Chatbot-powered Interactive Robot Mascot (Chacha Chaudhary) and Digital Avatar to Strengthen the River People Connect Component of Namami Gange
- **Short name:** Ganga AI Mascot

Ganga AI Mascot (PRJ_316) is an academic prototype for exploring Ganga-related information through a retrieval-augmented Brain service and a web-based Chacha Chaudhary mascot. The Brain answers questions from a curated, static collection of Ganga River Basin Management Plan (GRBMP) documents. It retrieves passages, applies heuristic evidence checks, then attempts Groq and OpenRouter generation in order; local extractive generation is the final fallback. This knowledge-answering path is neither live web search nor river monitoring. A separate integration route retrieves a limited set of live CPCB station readings.

The project brings together source-grounded question answering, a Three.js character interface, four-language text handling (English, Hindi, Kannada, and Tamil), and voice-related adapters. These are implemented prototype capabilities; the external translation service and speech providers have operational and privacy limits described below.

## Overall system architecture

```text
Browser text or audio input
        ↓
Integration FastAPI service
        ├── Water-quality questions → CPCB live-data retrieval → Structured response
        ├── Text questions ──────→ Brain client ──→ Brain retrieval and answer pipeline
        └── Audio input ──────────→ STT adapter ───→ Brain retrieval and answer pipeline
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

The checked-in knowledge-base inventory describes 86 PDF documents, 4,609 pages, 1,111 approved/reviewed sections, and 4,085 indexed chunks. The semantic embedding model is `all-MiniLM-L6-v2` with 384 dimensions. Runtime storage uses the application-owned SQLite and NumPy index files under `knowledge_base/vector_db/`, with a manifest used for index integrity checks. Chroma-format files in that directory are legacy artifacts, not the active runtime store. These corpus counts describe the repository snapshot and may change when its reviewed source data is updated.

Retrieval combines semantic similarity with lexical reranking. A heuristic evidence gate evaluates retrieved evidence before normal answer generation. Unsupported queries may receive an insufficient-evidence response; questions recognized as requiring current information are handled separately because the knowledge base is static. These checks are not calibrated confidence estimates or guarantees that every generated claim is supported.

## Hosted generation and citations

Grounded generation tries Groq first, then OpenRouter, and finally the local extractive generator. Both hosted providers use the existing OpenAI-compatible Python SDK with independent keys and endpoints. The default models are `openai/gpt-oss-120b` and `nvidia/nemotron-3.5-super-vl:free`. Hosted models receive the same question and selected evidence only after the evidence gate accepts the query. Citation metadata is assembled from retrieved evidence by the Brain rather than generated as source references by a model.

If one hosted provider is missing or fails, generation tries the next configured provider once. If both are unavailable or fail, the existing extractive generator is used. `LLM_PROVIDER=extractive` forces local-only generation. Current-information and insufficient-evidence branches bypass hosted generation. Groq and OpenRouter preserve the same response schema and assemble citations from retrieved metadata; the extractive fallback uses the same citation schema but cites hits that contributed extracted sentences, so its citation list can differ. Provider logs report safe provider/outcome categories without credentials or request data. Automated provider tests use mocks and do not make real API requests.

Prompt constants are exposed through the `brain.prompts` package. The current files are `brain/prompts/__init__.py` and `brain/prompts/system.py`; `brain/prompts.py` is no longer part of the project.

## Configuration

Configuration is read from process environment variables and the project-root `.env` file. Exported process variables take precedence over values in `.env`. The `.env` file should remain local and must not be committed; `.env.example` documents non-secret settings.

| Variable | Purpose |
| --- | --- |
| `LLM_PROVIDER` | `groq` (default), `openrouter` (defaults its order to OpenRouter first), or `extractive` (local only) |
| `LLM_PROVIDER_ORDER` | Comma-separated `groq` / `openrouter` order; defaults to `groq,openrouter`. Example: `openrouter,groq` |
| `GROQ_MODEL` | Groq model; defaults to `openai/gpt-oss-120b` |
| `GROQ_API_KEY` | Groq credential; provide privately |
| `OPENROUTER_MODEL` | OpenRouter model; defaults to `nvidia/nemotron-3.5-super-vl:free` |
| `OPENROUTER_API_KEY` | OpenRouter credential; provide privately |
| `GANGA_BRAIN_EMBEDDING_PROVIDER` | Semantic embedding provider (`semantic` by default) or `local-hash` |
| `GANGA_BRAIN_EMBEDDING_MODEL` | Semantic embedding model (`all-MiniLM-L6-v2` by default) |
| `GANGA_BRAIN_TOP_K` | Maximum returned evidence count |
| `GANGA_BRAIN_CANDIDATE_TOP_K` | Candidate count used during retrieval |
| `GANGA_BRAIN_EVIDENCE_MAX_DISTANCE` | Evidence-gate distance threshold |
| `GANGA_BRAIN_MIN_KEYWORD_OVERLAP` | Evidence-gate lexical overlap threshold |
| `GANGA_BRAIN_ORT_THREADS` | ONNX Runtime thread limit |

### Language and translation privacy

Text input/output language codes are `en`, `hi`, `kn`, and `ta`. When no input language is supplied, the Brain detects a supported script; an explicit input language takes precedence. When language conversion is needed, the application sends the question and/or generated answer to Google's public Translate endpoint by default. The chat UI has no per-request consent checkbox; API clients can explicitly set `translation_consent: false` to disable external translation for a request. A static set of known system phrases can be translated locally without external requests. No translation cache is retained. The endpoint is not Google's documented Cloud Translation API, and this project has not verified its endpoint-specific terms, retention, reliability, or availability; do not send personal or confidential text. See [Google Translate](https://translate.google.com/) and [Google's privacy policy](https://policies.google.com/privacy).

An earlier local-translation feasibility review reported English↔Hindi packages in the Argos index but no English↔Kannada/Tamil packages, and noted the NLLB-200 distilled 600M model card's CC-BY-NC/research-only and domain-coverage limitations. Those external resources can change and were not rechecked during this documentation audit. No local runtime/latency benchmark was performed on target hardware, so a local model is not enabled. Recheck the [Argos package index](https://github.com/argosopentech/argospm-index/blob/main/index.json) and [NLLB model card](https://huggingface.co/facebook/nllb-200-distilled-600M) before making a deployment decision.

The Vosk adapter has configured speech-recognition models for English and Hindi only. Browser Web Speech locale controls include all four languages, but actual recognition depends on browser and speech-service support. Edge TTS voice identifiers are configured for all four languages; live synthesis availability depends on the external service and is not validated for every environment. Windows SAPI fallback is configured only for English and Hindi. Configuration does not guarantee provider availability or quality.

For local development, set the needed provider keys privately in the project-root `.env` file. Both the standalone Brain and integration server load it automatically, regardless of the shell's current working directory. Explicitly exported variables take precedence. Set `LLM_PROVIDER_ORDER=openrouter,groq` to try OpenRouter first; `LLM_PROVIDER=extractive` avoids hosted providers entirely. OpenRouter's `:free` endpoints may be rate limited and have provider-specific data handling terms; do not send confidential or personal data to this model. Its reasoning is disabled for this request to preserve the existing 700-token output limit and avoid spending that budget on hidden reasoning.

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

The ask request accepts `question`, optional `input_language` and `output_language` (`en`, `hi`, `kn`, or `ta`), the legacy `language` field, optional `translation_consent` (defaults to `true`; set `false` to disable external translation), and optional `top_k` (1–100). Responses include an answer, a response `mode`, citations, and language fields. If a language conversion is needed while external translation is disabled, the API returns HTTP 428; provider failures return a sanitized translation-unavailable response.

The integration application can be started separately:

```bash
python -m integration.server --host 127.0.0.1 --port 8080
```

It defines `/api/integration/health`, `/api/integration/ask`, and `/api/integration/stt`, mounts the Brain API under `/brain`, and serves the avatar frontend when its entry point is available. If the frontend is served, open `http://127.0.0.1:8080/`. The interface supports typed questions, browser-recorded audio input, and English, Hindi, Kannada, and Tamil input/output language controls. Vosk-backed uploaded-audio recognition remains limited to English and Hindi.

## Avatar, voice, and integration components

- **Avatar and browser UI:** `avatar/index.html`, `avatar/app.js`, and `avatar/mascot.js` provide the web interface and Three.js avatar controller. The active production asset is `avatar/Chacha_New/Chacha_New.glb` (65-bone Mixamo armature, 28 skeletal animations, 31,058 draw vertices, calibrated for an 80.5% vertical character viewport occupancy). The previous high-fidelity asset `avatar/Member2_Chacha/Chacha_Master.glb` (57-bone armature, 35 morph targets, 9 Mixamo actions) is preserved intact for backward compatibility.
- The avatar controller includes procedural blinking, frame-by-frame 60 FPS LERP lip-sync smoothing, speech head cadence, and state management.
- **Speech recognition:** `integration/voice/stt_adapter.py` provides the Vosk adapter for English and Hindi, along with mock and browser-delegation adapters. Audio upload is handled by the integration STT route.
- **Speech synthesis:** `integration/voice/tts_adapter.py` provides Edge TTS and Windows SAPI-backed adapters, a synthetic WAV adapter for testing, and browser Web Speech delegation. Actual provider availability depends on the host environment.
- **Lip-sync and presentation:** `integration/avatar/lipsync.py` wraps Rhubarb when its binary is available and includes fallback timelines and RMS-based mouth-aperture analysis. `mascot_presenter.py` combines Brain responses with optional audio and lip-sync data for the browser.
- **Conversation and Brain connection:** `integration/controller/` manages conversation state; `integration/api/brain_client.py` connects the integration service to the Brain.

These are implemented project components, not a claim that every provider or operating-system path has been validated in every deployment environment.

## Tests

Run the focused configuration/generator tests and regression suites separately from the repository root. These commands force local-only generation for regression tests; provider-chain tests use mocked clients and fake credentials:

```bash
./.venv/bin/python -m pytest -q brain/tests/test_config_environment.py brain/tests/test_llm_generator.py
env LLM_PROVIDER=extractive GROQ_API_KEY= OPENROUTER_API_KEY= ./.venv/bin/python -m pytest -q brain/tests
env LLM_PROVIDER=extractive GROQ_API_KEY= OPENROUTER_API_KEY= ./.venv/bin/python -m pytest -q integration/tests --ignore=integration/tests/test_end_to_end.py
```

The Brain provider tests mock Groq and OpenRouter; no automated command above makes a hosted LLM request. The integration command omits `test_end_to_end.py` because its language translation flows may require external network access. Passing mocked tests does not establish live Groq/OpenRouter compatibility or availability. OpenRouter free endpoints may be rate-limited and have provider-specific data-handling terms.

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
  generator.py          Groq/OpenRouter chain and extractive answer generator
  prompts/              Public prompt interface and system prompt
  tests/                Brain regression and provider tests
knowledge_base/
  raw_documents/        Source document collection
  processed/            Extracted and reviewed content
  vector_db/            Runtime index files and retained legacy artifacts
integration/
  server.py             Integration FastAPI app and frontend hosting
  water_quality.py      CPCB live water-quality retrieval, parsing, and response formatting
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

## CPCB live water-quality integration

The conversation controller intercepts questions about current Ganga water quality before the RAG pipeline and returns a structured response drawn directly from the CPCB Real-Time Water Quality Monitoring System.

**Endpoints used (no authentication required):**

```
GET https://rtwqmsdb1.cpcb.gov.in/data/internet/stations/stations.json
GET https://rtwqmsdb1.cpcb.gov.in/data/internet/layers/10/index.json
```

**Supported stations on the main River Ganga:**

| Station | CPCB code | State |
|---|---|---|
| Haridwar (Har Ki Pauri) | UK55 / 11788 | Uttarakhand |
| Kanpur (Luv Kush Barrage) | UT58 / 11791 | Uttar Pradesh |
| Ghazipur (Abdul Hameed Setu) | UT66 / 11798 | Uttar Pradesh |
| Farakka (Farakka Barrage) | WB86 / 11815 | West Bengal |
| Nabadwip (Nabadwip Bathing Ghat) | WB87 / 11816 | West Bengal |

**Parameters reported:** Dissolved Oxygen (DO), Biochemical Oxygen Demand (BOD), and pH.

The system verifies station identity against the CPCB registry before returning readings. Responses include the measurement timestamp, a freshness label (readings older than 90 minutes are marked stale), and a source attribution to CPCB. Responses state clearly that point readings at a monitoring station do not determine whether water is safe to drink.

Successful CPCB responses are returned through the normal chatbot conversation with mode `live-water-quality`. If the CPCB endpoint is unreachable, the system reports the failure and does not substitute stale or unrelated readings. Retrieved payloads are cached for 60 seconds to reduce repeated requests. CPCB's terms for data reuse have not been independently verified and should be reviewed before wider publication or redistribution.

CPCB water-quality queries are detected by the integration-layer conversation controller (`integration/water_quality.py`, `integration/controller/conversation_controller.py`). This happens before the Brain RAG pipeline; all other questions continue through the existing retrieval and generation path. CPCB responses are translated through the same external translation path by default when a non-English output language is selected. If external translation is disabled or fails, the live readings remain in English with an explanatory note.

This is a limited station-data feature, not a comprehensive river-monitoring network. It covers the supported stations and parameters described above; the curated static GRBMP corpus remains the source for educational and historical knowledge questions. Live endpoint availability was not tested as part of this documentation update.

LLM behaviour and voice interaction with CPCB responses have not been systematically evaluated. Do not interpret the availability of live readings as a claim about response quality or accuracy in practice.

## Status and limitations

The knowledge pipeline, Groq/OpenRouter generation chain, multilingual text flow, Three.js avatar, quiz, voice adapters, and CPCB station-data route are integrated in the current main snapshot. The system is a prototype: knowledge questions use static documents, retrieval and evidence thresholds are heuristic, hosted generation requires a configured provider, and the system does not perform formal claim-level entailment verification. Translation and optional voice services depend on external or platform-specific components. CPCB data can be delayed, stale, or unavailable at specific stations.

This academic project demonstrates an information-access prototype for river-conservation awareness; it is not an operational environmental monitoring or decision-support system.
