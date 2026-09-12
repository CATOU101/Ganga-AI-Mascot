# Ganga AI Mascot

**Project ID:** PRJ_316

## Project Description

Ganga AI Mascot is an academic CSE mini-project exploring an AI-powered, source-grounded conversational agent and interactive digital mascot for river conservation awareness. The project is intended to support the River-People Connect component of the Namami Gange initiative by making reliable, accessible information about river stewardship easier to discover and engage with.

## Project Vision

The vision is to develop a responsible and approachable digital companion that can help people learn about river conservation, connect with trusted sources, and participate more meaningfully in conversations about the Ganga and its communities. The mascot experience will combine conversational interaction with an engaging visual identity while keeping factual responses grounded in an explicitly maintained knowledge base.

## Core Research Direction

The current research focuses on:

- Reviewing literature on river conservation awareness, public engagement, and the River-People Connect perspective.
- Investigating retrieval-augmented generation (RAG) for source-grounded conversational responses.
- Defining an agent architecture that can retrieve, reason over, and cite relevant information responsibly.
- Exploring the role of an interactive mascot in making educational communication more approachable.
- Establishing evaluation criteria for factual grounding, response quality, usability, and conservation relevance.

The core AI Brain implementation is completed on the `Knowledge-base-creation` branch. It provides source-grounded question answering over official Ganga River Basin Management Plan (GRBMP) documentation using a crash-proof SQLite + NumPy vector retrieval backend and a FastAPI server.

## System Architecture

The current system architecture separates the core AI Brain from presentation and future interface layers:

```text
Official GRBMP / NMCG Documentation (86 PDFs, 4,609 pages)
        ↓
Knowledge Processing & Section Filtering (1,111 approved sections)
        ↓
Chunking (4,085 chunks)
        ↓
ONNX Semantic Embeddings (all-MiniLM-L6-v2, 384-dim dense vectors)
        ↓
SQLite Metadata + NumPy Vector Matrix (semantic_vectors.npy)
        ↓
Hybrid Retrieval (Vector Similarity + Lexical Reranking)
        ↓
Evidence Quality Gate (Unsupported Query Rejection & Current-Info Fallback)
        ↓
Grounded Answer Generator & Provenance Assembler
        ↓
FastAPI Brain API (POST /ask, GET /health)
```

### Implementation Status Matrix

| Component | Status | Details |
| :--- | :--- | :--- |
| **Knowledge Base Processing** | **Implemented** | 86 GRBMP PDFs, 4,609 pages, 1,111 selected sections |
| **Vector Indexing & Retrieval** | **Implemented** | SQLite metadata + 4,085 float32 vectors (`semantic_vectors.npy`) using NumPy |
| **Hybrid Retrieval & Quality Gate**| **Implemented** | Dense ONNX similarity + lexical reranking + evidence quality gate |
| **Grounded Answer Generator** | **Implemented** | Extractive local synthesis default / OpenAI LLM option |
| **Brain REST API** | **Implemented** | FastAPI server (`POST /ask`, `GET /health`) |
| **Evaluation Suite** | **Implemented** | Groundedness, retrieval, and failure handling evaluation harness |
| **Frontend / Web UI** | *Not Implemented Yet* | Planned for subsequent integration phase |
| **Digital Avatar Runtime** | *Not Implemented Yet* | Design phase (`avatar/` placeholder) |
| **Voice / Speech (STT/TTS)** | *Not Implemented Yet* | Planned for future accessibility layer |
| **Realtime Telemetry APIs** | *Not Implemented Yet* | Gracefully falls back to `current-info-fallback` |
| **Physical Robot** | *Not Implemented Yet* | Future physical embodiment phase |

## Repository Structure

```text
Ganga-AI-Mascot/
├── README.md
├── requirements.txt
├── .env.example
├── research/
│   ├── literature_review.md
│   ├── research_gap.md
│   └── research_log.md
├── knowledge_base/
│   ├── raw_documents/
│   ├── processed/
│   ├── vector_db/
│   ├── processing_rules.md
│   └── sources.md
├── brain/
│   ├── README.md
│   ├── api.py
│   ├── chunking.py
│   ├── config.py
│   ├── embeddings.py
│   ├── generator.py
│   ├── ingest.py
│   ├── prompts.py
│   ├── rag_pipeline.py
│   ├── retriever.py
│   ├── vector_store.py
│   └── tests/
│       ├── evaluation_questions.md
│       └── run_evaluation.py
├── avatar/
│   └── README.md
├── integration/
│   └── README.md
└── docs/
    ├── architecture.md
    ├── brain_requirements.md
    ├── knowledge-base.md
    └── project_plan.md
```

## Current Status

**Brain Engine Completed — Ready for Integration Phase (50% Milestone)**

The repository contains a fully working, source-grounded RAG Brain engine powered by SQLite and NumPy vector search. It features:
1. **4,085 vector chunks** derived from 1,111 curated sections of 86 official GRBMP PDF reports.
2. **Crash-proof vector retrieval** utilizing NumPy dense matrix operations over local ONNX 384-dimensional embeddings, bypassing native C/Rust database binding issues on macOS.
3. **Multi-Factor Evidence Quality Gate** that rejects out-of-scope queries (*"Mars population"*) and static-historical queries asking for real-time water quality (*"current water status"*).
4. **FastAPI HTTP Server** exposing `/ask` and `/health` endpoints for upcoming avatar and frontend integration.

## Academic Disclaimer

This repository is an academic mini-project (PRJ_316). The architecture and knowledge base are curated specifically for Ganga conservation awareness.

