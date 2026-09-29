# Ganga AI Mascot

**Project ID:** PRJ_316  
**Project Title:** AI-Powered Interactive Digital Mascot for Namami Gange Awareness & River-People Connectivity  

---

## 1. Project Overview

**Ganga AI Mascot** is an artificial intelligence and machine learning academic project (PRJ_316) that combines a source-grounded Retrieval-Augmented Generation (RAG) AI engine with an interactive 3D digital mascot (**Chacha Chaudhary**). 

The system is designed to support the **River–People Connect** component of the **Namami Gange** initiative by providing an approachable, factual, and engaging conversational companion. Users can interact with the digital mascot using text or voice in English and Hindi to learn about river stewardship, water quality monitoring, pollution sources, and conservation guidelines.

---

## 2. Project Objectives

1. **Source-Grounded Question Answering:** Deliver factual, verifiable responses derived directly from official Ganga River Basin Management Plan (GRBMP) documentation.
2. **Provenance & Citation Transparency:** Ensure every generated response provides traceable citations referencing specific PDF documents, page numbers, and section identifiers.
3. **Interactive 3D Avatar Experience:** Render a 3D digital mascot in WebGL with facial expressions, body gestures, procedural blinking, and lip synchronization.
4. **Multi-Modal Voice Interaction:** Support speech-to-text (STT) voice input and neural text-to-speech (TTS) voice synthesis for accessible public engagement.
5. **Robust Integration Layer:** Maintain a modular FastAPI backend that coordinates dialogue state, RAG retrieval, audio synthesis, and avatar presentation.

---

## 3. Key Features

- **Interactive 3D WebGL Avatar:** Renders Chacha Chaudhary using Three.js with full body armature, 35 shape key facial blendshapes, and Mixamo skeletal actions.
- **Source-Grounded RAG Engine:** Queries 4,085 indexed knowledge base chunks with multi-factor evidence quality checks and fallback mechanisms.
- **Traceable Provenance:** Returns explicit citations (document title, source file name, page numbers, section ID) for every grounded response.
- **Bilingual Voice System:** Speech recognition and neural voice synthesis supporting English (`en-IN-PrabhatNeural`) and Hindi (`hi-IN-MadhurNeural`).
- **Acoustic Lip-Sync & RMS Signal:** Synchronizes avatar mouth movement with audio playback using Rhubarb phonetic viseme alignment and RMS amplitude signals.
- **Unified FastAPI Integration:** Single-command server hosting the web frontend, dialogue controller, voice services, and AI Brain.

---

## 4. System Architecture

```text
User
  │
  ▼  (Browser Interface)
Three.js WebGL 3D Avatar UI  (http://localhost:8080/)
  │
  ▼  (HTTP POST /api/integration/ask)
FastAPI Integration Server  (integration/server.py)
  ├── ConversationController & Dialogue State Machine
  ├── Speech-to-Text Adapter  (Vosk / Kaldi Offline STT)
  ├── Brain Client  (In-Process / HTTP RAG Engine)
  │     │
  │     ▼
  │   SQLite Metadata  (chroma.sqlite3) + NumPy Vector Store  (semantic_vectors.npy)
  │     │  (4,085 Retrieval Chunks derived from 86 GRBMP PDFs)
  │     ▼
  │   Grounded Answer Generator & Provenance Assembler
  │
  ├── Text-to-Speech Adapter  (EdgeTTS Neural Voices + SAPI Fallback)
  └── Lip-Sync Engine  (Rhubarb Phoneme Visemes + RMS Amplitude Fallback)
  │
  ▼  (AvatarPresentation Payload: Base64 WAV + Visemes + Emotion + Gesture)
3D WebGL Avatar Presentation & Audio Playback
```

---

## 5. Knowledge Base

The AI Brain is built upon an officially curated collection of Namami Gange and Ganga River Basin Management Plan (GRBMP) reports.

### Dataset Statistics

| Metric | Value |
| :--- | :--- |
| **Source PDF Documents** | 86 official reports |
| **Processed Pages** | 4,609 pages |
| **Reviewed Sections** | 1,111 approved sections |
| **Retrieval Chunks** | 4,085 text chunks |
| **Embedding Vector Dimensions** | 384 dimensions |
| **Embedding Model** | `all-MiniLM-L6-v2` (ONNX Runtime) |

### Vector Database Files

- **SQLite Database (`knowledge_base/vector_db/chroma.sqlite3`):** Stores document chunks, section metadata, titles, and page provenance.
- **NumPy Matrix (`knowledge_base/vector_db/semantic_vectors.npy`):** Stores the 4,085 float32 dense embedding vectors (~6.27 MB).
- **Manifest (`knowledge_base/vector_db/semantic_vectors_manifest.json`):** Contains SHA256 checksums and vector index mappings.

---

## 6. RAG / Brain Engine

The AI Brain implementation (`brain/`) operates as a standalone, crash-proof RAG pipeline:

- **Hybrid Semantic & Lexical Retrieval:** Combines ONNX vector similarity with keyword reranking for optimal precision over technical GRBMP reports.
- **Evidence Quality Gate:** Evaluates candidate evidence distance and keyword overlap. Rejects out-of-scope queries (e.g., *"population of Mars"*) by returning `insufficient-evidence` mode.
- **Broad Query Handler:** Automatically structures overview answers when users ask general questions (e.g., *"Tell me about Ganga"*).
- **Extractive Answer Generation:** Synthesizes factual answers directly from retrieved text passages without requiring external cloud LLM API keys at runtime.
- **FastAPI Endpoint (`brain/api.py`):** Exposes `/ask` and `/health` endpoints for standalone RAG queries.

---

## 7. Digital Avatar Specifications

The interactive avatar is located in `avatar/Member2_Chacha/Chacha_Master.glb`.

### Avatar Technical Specifications

| Specification | Details |
| :--- | :--- |
| **Model Asset** | `avatar/Member2_Chacha/Chacha_Master.glb` (101.3 MB binary glTF 2.0) |
| **Geometry** | 60,000 unique positions (120,000 triangles / 119,507 draw vertices) |
| **Armature & Rig** | 57-bone Mixamo skeletal armature (`mixamorig:Hips` to toes) |
| **Facial Controls** | **35 Shape Keys / Morph Targets** (7 emotions, 11 modular, 16 visemes) |
| **Mixamo Actions (9 Clips)** | `Chacha_Idle`, `Chacha_Nod`, `Chacha_Point`, `Chacha_Shrug`, `Chacha_Thinking`, `Chacha_Laughing`, `Chacha_Waving`, `Chacha_Thankful`, `Chacha_ShakingHands` |
| **Procedural Blinking** | Natural autonomous eye blinking (3–7s random interval, 150ms duration) |
| **Rendering Engine** | Three.js WebGL renderer with studio 3-point lighting rig and shadow maps |

---

## 8. Voice Interaction & Lip Synchronization

- **Speech-to-Text (STT):** Powered by offline Vosk/Kaldi speech recognition (`stt_adapter.py`) supporting English and Hindi voice inputs.
- **Text-to-Speech (TTS):** Uses EdgeTTS neural speech synthesis (`tts_adapter.py`):
  - **English Voice:** `en-IN-PrabhatNeural`
  - **Hindi Voice:** `hi-IN-MadhurNeural`
  - **Fallback:** 100% offline Windows SAPI fallback.
- **Lip Synchronization:**
  - **Rhubarb Phonetic Alignment:** Converts speech audio into acoustic viseme timelines (`Viseme_A` through `Viseme_Silence`).
  - **Platform Fallback (macOS / Linux):** Drives mouth blendshapes (`Mouth_Open`, `Mouth_O`) using continuous RMS audio amplitude signals (`rms_lip_sync` frames).

---

## 9. Brain–Avatar Integration Layer

The integration layer (`integration/`) unifies the AI Brain, voice services, and avatar UI:

- **`integration/server.py`:** Main FastAPI application hosting static WebGL assets and API routes.
- **`ConversationController` (`integration/controller/`):** Manages mascot dialogue states (`IDLE`, `LISTENING`, `THINKING`, `SPEAKING`).
- **`BrainClient` (`integration/api/`):** Connects to the RAG Brain via HTTP, with seamless in-process fallback if the standalone Brain server is offline.
- **`MascotPresenter` (`integration/avatar/`):** Bundles answer text, citations, base64 16kHz WAV audio, and viseme/RMS lip-sync frames into a unified `AvatarPresentation` payload.
- **Configuration:** `MOCK_MODE` is disabled by default (`false`), ensuring all interactions query the real GRBMP knowledge base.

---

## 10. Testing & Verification

The codebase includes automated test suites covering avatar mappers, Brain client, dialogue controller, voice adapters, and end-to-end integration flows.

### Automated Test Results

- **Test Suite Command:** `python -m pytest integration/tests`
- **Results:** **25 Passed, 0 Failed (100% Pass Rate)**

### Verified Query Categories

1. **Ganga Pollution Sources:** `mode: grounded`, returns 2 GRBMP citations.
2. **Aviral Dhara Concept:** `mode: grounded`, returns 2 GRBMP citations.
3. **Out-of-Scope Query (*Mars*):** `mode: insufficient-evidence`, 0 citations, triggers `thinking` emotion and gesture.
4. **Broad Ganga Overview:** `mode: grounded`, returns GRBMP overview citation.
5. **STP Recommendations:** `mode: grounded`, returns technical Sewage Treatment Plant citation.

---

## 11. How to Run

### Prerequisites

- Python 3.11+ (Tested on Python 3.13)
- Modern web browser with WebGL support

### Step 1: Install Dependencies

```bash
# Clone the repository
git clone https://github.com/CATOU101/Ganga-AI-Mascot.git
cd Ganga-AI-Mascot

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### Step 2: Start the Unified Integration Server

```bash
# Run the integration server (hosts WebGL UI + API)
python -m integration.server --port 8080
```

### Step 3: Access the Web Interface

Open your browser and navigate to:
👉 **`http://localhost:8080/`**

- Type your question in English or Hindi, or click the microphone button to speak.
- The 3D Chacha avatar will respond with neural speech, grounded text, GRBMP citations, and lip-sync animations.

### Step 4: Run Automated Tests

```bash
python -m pytest integration/tests
```

---

## 12. Project Structure

```text
Ganga-AI-Mascot/
├── README.md                                    # Official project documentation
├── requirements.txt                              # Python dependencies
├── .env.example                                  # Environment variables configuration
├── .gitattributes                                # Git LFS tracking rules
├── verify_final_production_suite.py              # End-to-end runtime verification script
├── avatar/
│   ├── index.html                               # WebGL UI HTML entry point
│   ├── mascot.js                                # Three.js 3D avatar animation engine
│   ├── app.js                                   # Main UI application orchestrator
│   ├── style.css                                # Interface styling & responsive design
│   ├── Member2_Chacha/
│   │   ├── Chacha_Master.glb                    # Primary 3D avatar GLB asset (101.3 MB)
│   │   ├── Chacha_Master.blend                  # Blender 3.6 master source file
│   │   ├── viseme_mapping.json                  # Rhubarb phoneme-to-viseme mapping
│   │   └── chacha_avatar_controller.py          # Python avatar controller pipeline
│   └── 08_Final/                                # Source models and inspection data
├── brain/
│   ├── api.py                                   # Standalone Brain FastAPI server
│   ├── rag_pipeline.py                          # Core RAG pipeline & quality gate
│   ├── vector_store.py                          # SQLite + NumPy vector retrieval engine
│   ├── retriever.py                             # Hybrid semantic + lexical retriever
│   ├── generator.py                             # Extractive local answer generator
│   ├── embeddings.py                            # ONNX all-MiniLM-L6-v2 embedding wrapper
│   ├── chunking.py                              # Document section chunking logic
│   ├── config.py                                # Brain paths & configuration
│   └── tests/                                  # RAG evaluation scripts
├── integration/
│   ├── server.py                                # Main FastAPI unified application
│   ├── api/
│   │   └── brain_client.py                      # Robust client connecting to RAG Brain
│   ├── avatar/
│   │   ├── mascot_presenter.py                  # AvatarPresentation payload packager
│   │   ├── lipsync.py                           # Rhubarb & RMS lip-sync processor
│   │   ├── emotion_mapper.py                    # Query mode to facial emotion mapper
│   │   └── gesture_mapper.py                    # Query mode to body gesture mapper
│   ├── controller/
│   │   └── conversation_controller.py          # Dialogue state machine manager
│   ├── models/
│   │   └── brain_response.py                    # Pydantic data schemas
│   ├── voice/
│   │   ├── stt_adapter.py                       # Vosk / Kaldi STT adapter
│   │   └── tts_adapter.py                       # EdgeTTS & SAPI TTS adapter
│   └── tests/                                  # Integration test suites
├── knowledge_base/
│   ├── raw_documents/                           # Source PDF documents
│   ├── processed/                               # Extracted section JSON files
│   ├── vector_db/
│   │   ├── chroma.sqlite3                       # SQLite chunk database (56.8 MB)
│   │   ├── semantic_vectors.npy                 # NumPy embedding matrix (6.27 MB)
│   │   └── semantic_vectors_manifest.json       # Index checksums & mappings
│   ├── processing_rules.md                      # Section curation rules
│   └── sources.md                               # Source PDF bibliography
├── research/                                    # Literature review & research logs
├── tools/                                       # Rhubarb lip-sync binaries
└── docs/                                        # Architecture & requirement docs
```

---

## 13. Technologies Used

- **Programming Language:** Python 3.11+
- **Backend Framework:** FastAPI, Uvicorn, Pydantic
- **AI / Embeddings:** ONNX Runtime, `all-MiniLM-L6-v2`, Sentence Transformers
- **Vector Retrieval:** SQLite (`sqlite3`), NumPy (`numpy`)
- **3D Graphics & WebGL:** Three.js (r128), WebGL, Blender 3.6, glTF 2.0 / GLB
- **Rigging & Animation:** Mixamo Armature (57 bones), Shape Keys (35 facial blendshapes)
- **Speech Recognition (STT):** Vosk / Kaldi Speech Recognition
- **Speech Synthesis (TTS):** EdgeTTS (`edge-tts`), Windows SAPI (`pyttsx3`)
- **Lip-Sync Processing:** Rhubarb Lip Sync, Audio RMS Amplitude Analysis
- **Version Control & LFS:** Git, Git Large File Storage (Git LFS)

---

## 14. Current Status

The core software prototype of the **Ganga AI Mascot** project is fully implemented and locally verified. The system successfully demonstrates source-grounded question answering over GRBMP documentation, speech recognition, neural voice synthesis, and real-time WebGL 3D avatar presentation with lip synchronization and facial expressions.

---

## 15. Future Work

- **Real-Time Hydrological Telemetry:** Integration with live water quality and river discharge monitoring APIs from CPCB/NMCG stations.
- **Multilingual Expansion:** Enhancing support for regional Indian languages across STT, RAG, and TTS.
- **Advanced Conversational Agent:** Integrating larger open-source LLMs for enhanced conversational fluidity while retaining strict RAG citation grounding.
- **Physical Robot Embodiment:** Transitioning from WebGL 3D avatar to physical mascot hardware for deployment at interactive public exhibits.

---

## 16. Team & Component Allocation

- **AI Brain & RAG Architecture:** Knowledge base curation, section processing, SQLite + NumPy vector search, hybrid retrieval, and evidence quality gate.
- **Digital Avatar & WebGL Engine:** 3D Chacha Chaudhary character modeling, Blender shape key creation, Mixamo animation rigging, and Three.js mascot engine.
- **Integration & Voice System:** Unified FastAPI server, dialogue state machine, Vosk STT adapter, EdgeTTS neural speech synthesis, and Rhubarb/RMS lip synchronization.

---

## Academic Disclaimer

This project is an academic mini-project (PRJ_316) developed for educational purposes under the CSE curriculum to demonstrate AI-driven public awareness tools for river conservation.
