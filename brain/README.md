# Ganga Brain — Demo-Ready RAG Engine

The **Brain** of the Ganga AI Mascot provides grounded, verified answers about the River Ganga derived strictly from official Ganga River Basin Management Plan (GRBMP) / NMCG material.

It strictly enforces **grounding safety** (rejecting unsupported queries like questions about Mars), **current-information safety** (refusing to state static historical data as real-time status), **provenance traceability** (exact citations matching evidence used), and **semantic retrieval** via ONNX dense vector embeddings.

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
ChromaDB Vector Database (knowledge_base/vector_db/)
        ↓
Retriever & Candidate Reranking (top_k candidates + hybrid lexical scoring)
        ↓
Multi-Factor Evidence Quality Gate (rejection of unsupported topics / low relevance)
        ↓
Grounded Answer Generator & Provenance Assembler
        ↓
FastAPI HTTP API (POST /ask)
```

---

## Key Features

1. **Grounding Safety & Unsupported Query Rejection**:
   - Analyzes non-stopword query keywords and distance metrics.
   - Unsupported queries (e.g. *"What is the population of Mars according to the GRBMP?"*) trigger the safe fallback:
     `"I couldn't find sufficient supporting information in the current verified knowledge base to answer that reliably."`

2. **Current vs Historical Information Safety**:
   - Queries requesting real-time or today's water status trigger the limitation fallback:
     `"The current prototype knowledge base is built from static/historical GRBMP material and does not provide verified current or real-time information for that question."`

3. **Modular Embedding Architecture**:
   - `semantic`: Local ONNX `all-MiniLM-L6-v2` dense vector model (default, running on CPU without paid APIs).
   - `local-hash`: Deterministic bag-of-words hash embedding baseline fallback.
   - Configurable via `GANGA_BRAIN_EMBEDDING_PROVIDER`.

4. **Precise Citation Provenance**:
   - Every grounded answer returns citations tied strictly to the retrieved chunks that contributed to the answer.

5. **Clean REST API**:
   - Lightweight FastAPI endpoint (`POST /ask`) ready for avatar / frontend integration.

---

## Configuration

Settings can be customized in `.env` (or via environment variables):

```bash
# Embedding provider: 'semantic' (ONNX MiniLM) or 'local-hash'
GANGA_BRAIN_EMBEDDING_PROVIDER=semantic

# Candidate retrieval & Evidence Gate thresholds
GANGA_BRAIN_TOP_K=5
GANGA_BRAIN_CANDIDATE_TOP_K=15
GANGA_BRAIN_EVIDENCE_MAX_DISTANCE=1.15
GANGA_BRAIN_MIN_KEYWORD_OVERLAP=0.15

# Generator provider: 'extractive' (default local) or 'openai'
GANGA_BRAIN_LLM_PROVIDER=extractive
GANGA_BRAIN_LLM_MODEL=grounded-extractive-v1

# Optional OpenAI key if GANGA_BRAIN_LLM_PROVIDER=openai
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
```

---

## Quick Start Commands

### 1. Installation

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Build the Vector Index

Rebuild the ChromaDB index from approved sections (1,111 sections, 4,085 vectors):

```bash
python -m brain.rag_pipeline --build-index
```

### 3. Ask a Question via CLI

```bash
python -m brain.rag_pipeline --ask "What is Aviral Dhara?"
```

### 4. Run Evaluation Test Suite

```bash
python -m brain.tests.run_evaluation
```

### 5. Start the HTTP API Server for Integration

```bash
python -m brain.api --host 0.0.0.0 --port 8000
```

---

## REST API Specification for Frontend Team

### Health Check

- **Endpoint**: `GET /health`
- **Response**: `{"status": "ok", "service": "ganga-brain-api"}`

### Ask Question

- **Endpoint**: `POST /ask`
- **Content-Type**: `application/json`
- **Request Body**:

```json
{
  "question": "What are the major sources of pollution in the Ganga?"
}
```

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
- Extractive generator uses sentence selection for grounded synthesis without external API fees; set `GANGA_BRAIN_LLM_PROVIDER=openai` for LLM phrasing if an API key is available.
- `REVIEW_REQUIRED`, `OCR_REQUIRED`, `FILTER`, and `EXCLUDE` sections are excluded.
