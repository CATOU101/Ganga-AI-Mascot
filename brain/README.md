# Ganga Brain — Demo-Ready RAG Engine

The **Brain** of the Ganga AI Mascot retrieves from the reviewed Ganga River Basin Management Plan (GRBMP) knowledge base and returns grounded answers with source metadata. The default generator uses Groq; set `LLM_PROVIDER=extractive` to use local extractive generation instead.

It uses heuristic checks for unsupported and current-information questions, and reports provenance for retrieved chunks that contribute extracted sentences. These mechanisms are not claim-level evidence verification or a guarantee against unsupported answers.

---

## Architecture

```text
Section Review JSON (KEEP, KEEP_HISTORICAL, KEEP_METHODOLOGICAL)
        ↓
Derived Ingestion Manifest (1,111 sections)
        ↓
Chunking (4,085 chunks preserving metadata & page numbers)
        ↓
ONNX Semantic Embeddings (all-MiniLM-L6-v2, 384-dim dense vectors)
        ↓
Collection-scoped SQLite Metadata + NumPy Vector Matrix
        ↓
Retriever & Candidate Reranking (top_k candidates + hybrid lexical scoring)
        ↓
Heuristic Evidence Gate (keyword overlap and vector-distance thresholds)
        ↓
Grounded Answer Generator & Provenance Assembler
        ↓
FastAPI HTTP API (POST /ask)
```

> **Runtime Backend Note (SQLite + NumPy)**: The active runtime uses the application-owned `brain_index.sqlite3`, `brain_semantic_vectors.npy`, and `brain_index_manifest.json` files. The former Chroma-format `chroma.sqlite3`, `semantic_vectors.npy`, and `semantic_vectors_manifest.json` files are retained unchanged as legacy artifacts; runtime reads are collection-scoped and do not query Chroma's internal schema.

---

## Key Features

1. **Heuristic Unsupported-Query Handling**:
   - Analyzes non-stopword query keywords and vector distances.
   - Unsupported queries (e.g. *"What is the population of Mars according to the GRBMP?"*) trigger the safe fallback:
     `"I couldn't find sufficient supporting information in the current verified knowledge base to answer that reliably."`

2. **Current-Information Limitation Fallback**:
   - Queries matching configured freshness and dynamic-topic phrases trigger the limitation fallback:
     `"The current prototype knowledge base is built from static/historical GRBMP material and does not provide verified current or real-time information for that question."`

3. **Modular Embedding Architecture**:
   - `semantic`: Local ONNX `all-MiniLM-L6-v2` dense vector model (default, running on CPU without paid APIs). The archive SHA-256 and runtime package versions are recorded in the generated index manifest.
   - `local-hash`: Deterministic bag-of-words hash embedding baseline fallback.
   - Configurable via `GANGA_BRAIN_EMBEDDING_PROVIDER`.

4. **Citation Provenance**:
   - Extracted sentences are associated with the source metadata of their contributing retrieved chunks. The generator does not perform claim-level entailment verification.

5. **Clean REST API**:
   - Lightweight FastAPI endpoint (`POST /ask`) ready for avatar / frontend integration.

---

## Configuration

Settings are read from environment variables; `.env` files are not loaded automatically:

```bash
# Embedding provider: 'semantic' (ONNX MiniLM) or 'local-hash'
GANGA_BRAIN_EMBEDDING_PROVIDER=semantic
GANGA_BRAIN_EMBEDDING_MODEL=all-MiniLM-L6-v2

# Final returned evidence count and evidence-gate settings
GANGA_BRAIN_TOP_K=5
GANGA_BRAIN_CANDIDATE_TOP_K=15
GANGA_BRAIN_EVIDENCE_MAX_DISTANCE=1.15
GANGA_BRAIN_MIN_KEYWORD_OVERLAP=0.15

# ONNX runtime thread limit
GANGA_BRAIN_ORT_THREADS=2

# Generator provider: 'groq' or 'extractive'
LLM_PROVIDER=groq
GROQ_MODEL=openai/gpt-oss-120b
# Set GROQ_API_KEY privately in the process environment or ignored local .env.
```

The Groq provider uses the OpenAI Python SDK with Groq's OpenAI-compatible API. `.env` values are not loaded automatically; load them into the process environment before starting the API. The embedding model setting applies to the `semantic` provider; the `local-hash` provider always uses its fixed hash-embedding implementation. Index paths, collection name, and chunk-size defaults are defined in `BrainConfig` rather than loaded from environment variables.

---

## Quick Start Commands

### 1. Installation

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Groq generation

Copy `.env.example` to the ignored local `.env` file, add `GROQ_API_KEY` there, then export the settings before launching:

```bash
cp .env.example .env
# Add GROQ_API_KEY=your_secret_key to the local .env file.
set -a
source .env
set +a
```

Groq is called only after current-information handling, retrieval, and the evidence quality gate accept the query. The model receives selected evidence and trusted metadata; citations are assembled by the Brain from retrieved metadata. If the key is missing or generation fails, the existing extractive generator is used. Current-information and insufficient-evidence responses bypass the LLM.

### 3. Build the complete index

Build the derived ingestion manifest, split approved sections into chunks, write the configured SQLite collection, generate embeddings, and validate the SQLite/vector/manifest identities before publishing the index:

```bash
python -m brain.rag_pipeline --build-index
```

The equivalent vector-store CLI is `python -m brain.vector_store --generate-vectors`. Both commands build the complete index from reviewed/processed knowledge. The pre-existing Chroma-format artifacts are not overwritten.

### 4. Ask a Question via CLI

```bash
python -m brain.rag_pipeline --ask "What is Aviral Dhara?"
```


### 5. Run Evaluation Test Suite

```bash
python -m brain.tests.run_evaluation
```

### 6. Start the HTTP API Server for Integration

```bash
python -m brain.api --host 0.0.0.0 --port 8000
```

---

## REST API Specification for Frontend Team

### Health Check

- **Endpoint**: `GET /health`
- **Ready response**: includes `application: "available"` and `brain: {"ready": true, "collection": "...", "chunks": ...}`.
- **Not-ready response**: returns HTTP 503 with `brain.ready: false` when the index or query embedding cannot be initialized.

### Ask Question

- **Endpoint**: `POST /ask`
- **Content-Type**: `application/json`
- **Request Body**:

```json
{
  "question": "What are the major sources of pollution in the Ganga?",
  "input_language": "en",
  "output_language": "en",
  "top_k": 5
}
```

Omitting language fields defaults both input and output to English. Supported codes are `en` and `hi`. `top_k` controls the maximum number of reranked evidence results returned (1–100); candidate retrieval remains controlled by `GANGA_BRAIN_CANDIDATE_TOP_K`.

- **Grounded Response (`mode: "grounded"`)**:

```json
{
  "answer": "...",
  "mode": "grounded",
  "citations": [
    {
      "source": "Ganga River Basin Management Plan Interim Report",
      "file_name": "25_GRBMPInterim_Rep.pdf",
      "page": "110-110",
      "section": "CHAPTER I",
      "knowledge_type": "STATIC"
    }
  ]
}
```

- **Unsupported Query Fallback (`mode: "insufficient-evidence"`)**:

```json
{
  "answer": "I couldn't find sufficient supporting information in the current verified knowledge base to answer that reliably.",
  "mode": "insufficient-evidence",
  "citations": []
}
```

- **Current Information Fallback (`mode: "current-info-fallback"`)**:

```json
{
  "answer": "The current prototype knowledge base is built from static/historical GRBMP material and does not provide verified current or real-time information for that question.",
  "mode": "current-info-fallback",
  "citations": []
}
```

---

## Limitations

- Prototype uses static GRBMP PDF material; live telemetry/water quality sensor APIs should be integrated behind a dedicated realtime service.
- Groq-assisted phrasing is not a guarantee of factual correctness or claim-level entailment. Translation between English and Hindi uses the existing external Google Translate GTX endpoint; when that endpoint fails, translation raises an explicit error and the API returns HTTP 503 rather than presenting untranslated text as translated.
- `REVIEW_REQUIRED`, `OCR_REQUIRED`, `FILTER`, and `EXCLUDE` sections are excluded.
