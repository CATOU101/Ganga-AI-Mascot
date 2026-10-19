# Architecture

This document defines the system architecture for **Ganga AI Mascot** (PRJ_316), an AI-powered educational and conversational assistant for the Namami Gange initiative.

**Official project title:** Development of AI, ML and Chatbot-powered Interactive Robot Mascot (Chacha Chaudhary) and Digital Avatar to Strengthen the River People Connect Component of Namami Gange

The system is designed around a knowledge-grounded conversational AI agent that can answer questions about the Ganga River, its ecosystem, pollution, biodiversity, conservation, and Namami Gange programmes. The AI agent forms the core "brain" of the mascot, while the avatar, robot, or other interfaces act as presentation and interaction layers.

The architecture is modular so that the AI brain can be developed and evaluated independently from the avatar and hardware components.

This document combines research-grounded design rationale with the current implementation in `main`. Proposals and historical development notes are labeled where they differ from active behavior; the current component status is summarized in §20.

---

## 0. Research Grounding & Implementation Summary
Eight sources reviewed to date shape this architecture:

Source-status labels are documented in `research/literature_review.md` and reflect prior review work, not a fresh bibliography audit. R1 remains unverified; statements attributed to it are provisional.

IDFocusMain influence on this documentR1AI-powered Chacha Chaudhary mascot for Ganga conservation (closest baseline)Confirms the mascot + chatbot concept, but shows the baseline **does not** clearly define a RAG pipeline, curated knowledge source, or source traceability — the primary gap this architecture is designed to closeR2Retrieval-Augmented Generation (Lewis et al., 2020)Scientific basis for §5–§6 (retriever + generator separation); clarifies that RAG ≠ any single vendor stack (SQLite, NumPy, embeddings, an LLM are independent, swappable parts)R3Umbrella review of conversational AI in educationMotivates §15 principles on privacy, information quality, human oversight, and academic/ethical responsibilityR4Pedagogical AI agent framework (higher ed)Motivates separating **pedagogical purpose** (instructional / pastoral / cognitive) from **technological function** (NLP, retrieval, embodiment) — see new §7.1R5Flipped AI-chatbot module for environmental literacyMotivates treating the agent as more than Q&A: explanation, reflection, optional quiz follow-up — see §7.2R6Usability/heuristic evaluation of ChatGPT in environmental educationMotivates splitting evaluation into **usability** (CUQ/SUS-style) vs. **information quality** (groundedness/accuracy) — see revised §12R7Meta-analysis of virtual characters in K-12 learningEvidence that embodiment helps only when pedagogically purposeful — motivates evaluating the Avatar layer independently from the Brain (§12.3)R8Systematic review of pedagogical agent designReinforces that agent design (voice, appearance, role) should be a deliberate, evaluated choice, not a default — informs §10

> **Implementation Note (Current Brain Implementation)**:  
> The current main snapshot includes the Brain RAG engine, a curated GRBMP corpus, local ONNX embeddings, an application-owned SQLite + NumPy vector index, heuristic evidence checks, a Groq → OpenRouter → extractive generation chain, and a FastAPI API. The SQLite/NumPy backend replaces earlier Chroma runtime storage; the migration is not a guarantee against all runtime failures.


⸻

## 1. Architecture Overview
The system consists of the following major components:

- Knowledge Sources
- Knowledge Processing Pipeline
- Curated Knowledge Base
- Embedding and Vector Store
- Retrieval-Augmented Generation (RAG)
- Conversational AI Agent
- Large Language Model (LLM)
- Application/API Layer
- Avatar and Interactive Interface
- Evaluation and Monitoring (now split: Brain evaluation / Avatar evaluation — see §12)
At a high level:

```
				 GANGA AI MASCOT
					│
		    ┌─────────────┴─────────────┐
		    │                           │
	   USER INTERFACE                 AI BRAIN
		    │                           │
	 ┌────────┴────────┐          ┌───────┴────────┐
	 │                 │          │                │
     Avatar            Voice      AI Agent          RAG
     /Robot             I/O         │          ┌───────┴───────┐
	 │                           │          │               │
	 └────────── API ────────────┤       Retriever      Vector DB
					     │                           │
					     └───────────┬───────────────┘
							     │
							     ▼
							    LLM
							     │
							     ▼
						    Grounded Response
				 KNOWLEDGE FOUNDATION
					    │
			┌───────────────┴───────────────┐
			│                               │
	    Source Documents                  Data Processing
			│                               │
			└───────────────┬───────────────┘
					    ▼
				   Curated Knowledge
					    │
					    ▼
				   Vector Database
			     EVALUATION & MONITORING
					    │
			 ┌──────────────┴──────────────┐
			 │                             │
		  Brain Evaluation             Avatar Evaluation
	  (groundedness, retrieval,        (usability, engagement,
	   factual accuracy — R2, R6)         motivation — R7, R8)
			 │                             │
			 └──────────────┬──────────────┘
					    ▼
				   System Improvement
```
⸻

## 2. Knowledge Sources
The knowledge layer is the factual foundation of the AI system.

The project will prioritize reliable and authoritative information, particularly official government and Namami Gange-related documentation. This directly addresses the R1 baseline gap ("knowledge sources are not clearly defined") and the R6 finding that general-purpose LLMs show limited domain expertise and unreliable fact-checking in environmental education.

The knowledge sources may include:

- Official Namami Gange documentation
- Government reports (NMCG, CPCB, Ministry of Jal Shakti and related bodies)
- Environmental reports
- Scientific and educational material
- Ganga River and ecosystem information
- Biodiversity information
- Pollution and water-quality information
- Conservation programme information
- Frequently asked questions and educational resources
The source hierarchy should favor authoritative sources over general web content. As R2 notes for its own Wikipedia-based index, an external knowledge source is only as reliable as its provenance; this project substitutes a general encyclopedic corpus for a **narrow, authoritative, domain-curated** one, which is both smaller in scope and higher in trust per document.

⸻

## 3. Knowledge Processing Pipeline
Raw documents should not be inserted directly into the retrieval system. They first pass through a processing pipeline.

```
PDF / Web Page / Document
	    │
	    ▼
     Text Extraction
	    │
	    ▼
    Cleaning & Normalization
	    │
	    ▼
	 Chunking
	    │
	    ▼
   Metadata Assignment
	    │
	    ▼
	Embeddings
	    │
	    ▼
    Vector Database
```
Each processed chunk should retain useful metadata where available, including:

- Source
- Document title
- Topic
- Section
- Date
- Page number
- Source URL or reference
This metadata supports source traceability and can support retrieval analysis. Whether it improves retrieval quality or evaluation outcomes has not been measured. The cited R1 paper's publication record remains unresolved, so claims about gaps in that source are provisional (see also §15.4).

⸻

## 4. Curated Knowledge Base
The knowledge base will organize information into the major domains required by the mascot.

### Primary Knowledge Domains

- Ganga River geography and history
- Ganga ecosystem
- Biodiversity and wildlife
- Water pollution
- Sources of pollution
- Sewage and industrial waste
- River conservation
- Namami Gange objectives and programmes
- Government initiatives
- Environmental awareness
- Sustainable practices
- Frequently asked questions
The knowledge base should be treated as a controlled factual foundation rather than simply a collection of documents.

⸻

## 5. Embedding and Vector Store
Processed knowledge chunks are converted into vector representations using an embedding model.

```text
Knowledge Chunk
	│
	▼
Embedding Model (all-MiniLM-L6-v2 ONNX)
	│
	▼
384-dimensional Vector Representation
	│
	▼
SQLite Metadata + NumPy Vector Matrix (semantic_vectors.npy)
```

When a user asks a question, the question is similarly converted into a 384-dimensional embedding and compared against stored knowledge vectors using NumPy Euclidean ($L2$) distance computation.

The vector store enables fast, deterministic semantic retrieval of relevant knowledge.

> **Vector Database Implementation Rationale**:  
> In early prototype testing, ChromaDB 1.5.9 was used as the vector database interface. However, ChromaDB's native Rust binding (`chromadb_rust_bindings.abi3.so`) was associated with repeated macOS kernel `SIGSEGV` segmentation fault crashes during retrieval queries. Runtime retrieval was subsequently migrated to a pure Python backend using SQLite (`knowledge_base/vector_db/brain_index.sqlite3`) for metadata/chunk text storage and a portable NumPy array (`knowledge_base/vector_db/brain_semantic_vectors.npy`) for $L2$ vector similarity, validated via SHA-256 manifests (`brain_index_manifest.json`). This migration does not establish a guarantee of runtime stability. Legacy ChromaDB files in that directory are preserved for historical reproducibility.

**Note (from R2):** Retriever, generator, and knowledge store are conceptually independent — a dense-passage-retrieval-style retriever does not require any particular vector database, and a vector database or matrix store does not require any particular retriever or generator. These remain separable decisions.


⸻

## 6. Retrieval-Augmented Generation
The RAG layer connects the knowledge base to the language model, following the retriever + generator pattern established in R2 (Lewis et al., 2020), adapted from an open-domain Wikipedia index to a narrow, curated Ganga/environmental corpus.

```
User Question
	│
	▼
Query Processing
	│
	▼
Query Embedding
	│
	▼
Similarity Search
	│
	▼
Relevant Knowledge Chunks
	│
	▼
Context Construction
	│
	▼
LLM
	│
	▼
Grounded Response
```
For example, if the user asks:

"Why is the Ganga polluted?"

the retrieval system searches the knowledge base for relevant information about pollution sources and retrieves suitable knowledge chunks. The LLM then uses this retrieved context to generate the response.

This approach reduces dependence on the LLM's pretrained knowledge and helps keep factual responses grounded in the project's curated sources — the property R6 found to be weakest in general-purpose ChatGPT usage for environmental education (limited fact-checking, outdated or superficial information).

**Fallback behaviour:** when retrieval returns no sufficiently relevant chunks, the agent must not silently fall back to unsupported generation. This is the graceful-failure requirement carried from R3/R6 into §15.5 and should be tested explicitly during evaluation (§12) with questions deliberately outside the knowledge base.

⸻

## 7. Conversational AI Agent
The conversational agent is the central orchestration component of the AI brain.

Its responsibilities include:

**Query Understanding** — Determine the user's intent and identify what information is being requested.

**Retrieval** — Determine when knowledge retrieval is required and obtain relevant information from the RAG system.

**Conversation Management** — Maintain relevant context from the current conversation.

**Response Generation** — Provide the retrieved information and conversation context to the LLM and generate a natural-language response.

**Behaviour Control** — Ensure that responses remain appropriate for an educational mascot and its intended audience.

**Unknown-Question Handling** — The agent should avoid confidently generating unsupported factual claims when sufficient information is not available.

```
			   User Input
				 │
				 ▼
		    Query Understanding
				 │
		  ┌──────────┴──────────┐
		  │                     │
	 Knowledge Question     Casual Conversation
		  │                     │
		  ▼                     ▼
	    Retrieval            Direct Response
		  │                     │
		  └──────────┬──────────┘
				 ▼
			  Response
```

### 7.1 Pedagogical Purpose (from R4)
R4's framework distinguishes **pedagogical purpose** from **technological function**. The agent's pedagogical purpose should be explicitly designed rather than left implicit. Candidate purposes for PRJ_316, drawn from R4's eight sub-types:

- **FAQs and knowledge base** — answering grounded questions (the core capability described in §6).
- **Instructional** — explaining pollution, biodiversity, conservation, and Namami Gange concepts.
- **Motivate and inspire** — encouraging environmentally responsible behaviour.
- **Communication** — sustaining natural multi-turn conversation.
Assessment, reflective/metacognitive, and simulation sub-types are noted by R4 as available extensions but are not required for the current project scope.

### 7.2 Beyond Q&A (from R5)
R5's Flipped AI-Chatbot Learning model shows environmental-education chatbots functioning as more than single-turn answer machines: they support explanation, clarification, and optional reflection or follow-up. This suggests an extended (optional, future) interaction shape:

```
User → Question/Interaction → Retrieve Relevant Knowledge →
Generate Educational Explanation → Encourage Reflection →
Optional Quiz / Follow-up
```
This is a design direction, not a required feature of the current architecture — it extends §6's grounded-response flow rather than replacing it.

⸻

## 8. Large Language Model
The Large Language Model acts as the primary language and reasoning component.

The LLM receives:

```
System Instructions
	  +
Conversation Context
	  +
Retrieved Knowledge
	  +
User Question
	  │
	  ▼
	 LLM
	  │
	  ▼
Generated Response
```
The LLM should not be treated as the primary factual source for domain-specific information.

The architectural separation is:

```
Knowledge Base → Factual Foundation
RAG            → Information Retrieval
AI Agent       → System Coordination
LLM            → Reasoning and Language Generation
```
This separation makes the system easier to maintain, evaluate, and improve, and is consistent with R2's separation of retriever and generator as independently replaceable components.

**Current generation behavior:** Hosted generation is constructed only after retrieval and the existing evidence-quality gate accept the question. The default provider order is Groq followed by OpenRouter, with each configured provider attempted at most once; missing credentials or a provider error advances to the next provider. If hosted generation is unavailable, the local extractive generator is the final fallback. `LLM_PROVIDER=extractive` selects local-only generation. Current-information requests bypass this chain, and CPCB water-quality requests are routed separately by the integration controller. Citation objects are built from retrieved metadata. The hosted generators cite the bounded evidence supplied to them; the extractive fallback cites hits that contributed extracted sentences, so the citation list can differ while the response schema remains the same.

**Language handling:** Text language codes are English (`en`), Hindi (`hi`), Kannada (`kn`), and Tamil (`ta`). Input can be detected heuristically by Unicode script when no language is supplied; explicit selections take precedence. When language conversion is needed, API routes enable translation to Google's public Translate endpoint by default and may send the question and/or generated answer. The chat UI has no consent checkbox; API callers can set `translation_consent=false` to disable external translation for a request. Exact known system phrases may be translated from a local phrase map. Translation is not part of citation assembly and does not alter the retrieval/evidence gate. No translation cache is kept. The endpoint is not Google's documented Cloud Translation API; its specific terms and availability have not been verified, so do not send personal or confidential text. Vosk currently configures only English/Hindi models; browser speech and external Edge TTS locale support depend on the host/provider and remain unverified for Kannada/Tamil.

⸻

## 9. Application and API Layer
The application/API layer provides the communication boundary between the AI brain and the user-facing interface.

```
Avatar / UI
     │
     │ User Input
     ▼
Application API
     │
     ▼
AI Agent
     │
     ▼
Application API
     │
     │ AI Response
     ▼
Avatar / UI
```
The interface should not directly depend on internal AI components. This allows the avatar, web interface, or robot implementation to be modified without requiring major changes to the AI brain — the separation R4 and R7 both treat as important for evaluating "what the mascot looks like" independently of "what the mascot knows."

⸻

## 10. Avatar and Interactive Layer
The avatar represents the presentation and interaction layer of the system.

> **Production Implementation Note (Verified Baseline)**:  
> The active production avatar runtime is a browser-native Three.js WebGL application (`avatar/index.html`, `avatar/app.js`, `avatar/mascot.js`) running directly in standard web browsers. It loads `avatar/Chacha_New/Chacha_New.glb` (65-bone Mixamo armature, 28 animations, procedural blinking, 60 FPS LERP lip-sync smoothing, and viewport occupancy calibrated to 80.5%). The high-fidelity 57-bone asset (`avatar/Member2_Chacha/Chacha_Master.glb` with 35 shape keys) is preserved intact for backward compatibility. The early Unity WebGL experiment in `avatar/07_Unity/` is archived and is not part of the active runtime.

Possible interfaces include:

- Digital mascot
- Web interface
- Interactive display
- Physical robot
- Voice-enabled interface
The avatar/interface is responsible for:

- Receiving user input
- Sending input to the application layer
- Displaying responses
- Voice input/output where implemented
- Facial or character animation
- Presenting conversational state
The avatar should not contain the core knowledge, retrieval, or reasoning logic.

```
			AI BRAIN
			   │
			   │ API
			   ▼
		 Avatar / Robot
```
This separation allows the AI and avatar components to be developed independently.

**Design caution (from R7, R8):** R7's meta-analysis found a statistically significant positive effect of virtual characters on learning (g = 0.42) and motivation (g = 0.48) across K–12 studies, but no significant effect on emotions, perceptions, or cognitive load — and R8 stresses that the benefit comes from a character having a well-defined **pedagogical role**(informant, motivator, guide), not from embodiment alone. The avatar layer should therefore be designed with an explicit role (§7.1) rather than as decoration, and its contribution to engagement should be evaluated separately from the Brain's factual quality (§12.3).

⸻

## 11. Voice Interaction
Voice interaction can be implemented as an additional input/output layer.

```
User Speech
     │
     ▼
Speech-to-Text
     │
     ▼
AI Agent
     │
     ▼
Generated Response
     │
     ▼
Text-to-Speech
     │
     ▼
Avatar Speech
```
Voice processing remains separate from core conversational logic so the same Brain can support text and voice interfaces. Text language selection and translation for English, Hindi, Kannada, and Tamil are implemented. Speech support is narrower: Vosk models are configured for English and Hindi; browser speech recognition and Edge TTS locale behavior depend on host/provider support and are not asserted as verified for every language. Language accessibility is a design goal, not a measured outcome.

⸻

## 12. Evaluation
Evaluation is required to determine whether the AI system provides reliable and useful answers. Following R6 and R7, evaluation is split into two tracks that must **not** be conflated: Brain quality (is the information right?) and Avatar/interaction quality (is the experience good?). A system can score well on one and poorly on the other.

### 12.1 Brain Evaluation (information quality)

- **Retrieval Quality** — Whether the correct or useful knowledge chunks are retrieved.
- **Answer Accuracy** — Whether the generated answer correctly represents the available knowledge.
- **Groundedness** — Whether factual claims in the response are supported by retrieved information.
- **Relevance** — Whether the response directly addresses the user's question.
- **Failure Handling** — Whether the system appropriately acknowledges questions for which sufficient information is unavailable (tested with deliberately out-of-scope questions, per R6's recommendation).

### 12.2 Avatar/Interaction Evaluation (experience quality)
Informed by R6's use of established usability instruments (Chatbot Usability Questionnaire, System Usability Scale, User Experience Questionnaire) and R7/R8's distinction between learning, motivation, and agent perception as separate outcomes:

- **Usability** — clarity, navigation, ease of use, error recovery.
- **Engagement / Motivation** — whether interacting with the mascot is perceived as enjoyable or motivating (not assumed — measured).
- **Agent Perception** — how the character/persona itself is perceived, independent of the correctness of what it says.

### 12.3 Why the split matters

```
Evaluation Dataset
	 │
	 ▼
    AI Agent
	 │
	 ▼
 Generated Answer
	 │
	 ▼
    Evaluation
    ┌────┴────┐
    │         │
 Brain Track   Avatar Track
 (§12.1)       (§12.2)
```
Evaluation results should be used to improve the knowledge base, retrieval configuration, prompts, agent behaviour, and — separately — avatar design and interaction flow.

⸻

## 13. Logging and Monitoring
During development, the system should record useful technical information to support debugging and evaluation.

Potential diagnostic information includes:

- Provider and safe outcome/error category
- Non-sensitive retrieval and evaluation metrics
- System errors and timing measurements

Provider diagnostics must not log API keys, authorization headers, prompts, retrieved evidence, generated responses, exception messages, or other private request data. The logging system should avoid storing unnecessary sensitive user information — a point reinforced by R3's identification of data privacy and security as a top-five ethical concern for educational conversational AI.

Monitoring should help identify where problems occur in the pipeline. For example:

```
Correct Information Exists
	    │
	    ▼
Retriever Fails
	    │
	    ▼
Wrong Context
	    │
	    ▼
Poor Answer
```
versus:

```
Correct Information Retrieved
	    │
	    ▼
LLM Produces Poor Answer
	    │
	    ▼
Generation / Prompt Problem
```
This distinction is important for debugging and system improvement.

⸻

## 14. Integration Boundaries
The architecture intentionally separates the AI brain from external interfaces.

**AI Brain Boundary**

```
Input
  │
  ▼
AI Agent
  │
  ├── RAG
  ├── Knowledge Base
  └── LLM
  │
  ▼
Response
```
**Interface Boundary**

```
Avatar / Robot / Web UI
	    │
	    ▼
	API Layer
	    │
	    ▼
	 AI Brain
```
The interface communicates with the AI brain through a defined application/API boundary rather than accessing internal components directly. This enables independent development and replacement of individual components.

⸻

## 15. Core Architectural Principles
The system will follow these principles:

**15.1 Knowledge Grounding** — Domain-specific factual answers should be grounded in the curated knowledge base wherever applicable (R2, and the central gap identified in R1).

**15.2 Modularity** — Major components should have clearly defined responsibilities and interfaces.

**15.3 Separation of Concerns** — The knowledge, retrieval, reasoning, API, and presentation layers should remain logically separate (R4, R7).

**15.4 Traceability** — Knowledge used to generate important factual answers should be traceable to its source where practical. Explicitly required to close the gap R1 identified in the baseline mascot paper.

**15.5 Graceful Failure** — The system should acknowledge insufficient information rather than confidently fabricate an answer (R3, R6).

**15.6 Replaceability** — Individual models and infrastructure components should be replaceable without requiring a complete redesign (R2).

**15.7 Independent Interface Development** — The avatar or robot should be able to evolve independently of the AI brain.

**15.8 Pedagogically Purposeful Design** *(new — R4, R7, R8)* — Both the agent's conversational behaviour and the avatar's presentation should be designed against an explicit pedagogical purpose (§7.1), and their effectiveness should be evaluated rather than assumed.

**15.9 Human and Expert Oversight** *(new — R3, R5, R6)* — The mascot should augment, not replace, teachers, educators, and domain experts. Important or uncertain environmental information should remain open to human review, consistent with the "hybrid human-AI" model R6 recommends.

**15.10 Privacy by Minimization** *(new — R3)* — The system should avoid unnecessary collection or logging of personal or sensitive user information.

⸻

## 16. Component Responsibilities
ComponentResponsibilityKnowledge SourcesProvide authoritative informationData Processing PipelineExtract, clean, chunk, and structure informationKnowledge BaseMaintain curated project knowledgeEmbedding ModelConvert knowledge and queries into vector representationsVector StoreEnable semantic retrievalRAG LayerRetrieve relevant information and construct contextAI AgentCoordinate conversation, retrieval, and generationLLMReason over context and generate responsesAPI LayerConnect the AI brain to external interfacesAvatar / RobotProvide user-facing interaction, embodying an explicit pedagogical roleSpeech LayerHandle speech-to-text and text-to-speechBrain EvaluationMeasure retrieval quality, accuracy, and groundednessAvatar EvaluationMeasure usability, engagement, motivation, and agent perceptionMonitoringTrack errors, performance, and system behaviour⸻

## 17. End-to-End Data Flow
The complete interaction can be represented as:

```
				 USER
				   │
				   ▼
			Avatar / Interface
				   │
				   ▼
			     API Layer
				   │
				   ▼
			  Conversational
			     AI Agent
				   │
				   ▼
			 Query Understanding
				   │
				   ▼
			   RAG Pipeline
				   │
		    ┌──────────┴──────────┐
		    │                     │
	    Query Embedding       Knowledge Base
		    │                     │
		    ▼                     │
	    Vector Search ◄─────────────┘
		    │
		    ▼
	   Relevant Context
		    │
		    ▼
		   LLM
		    │
		    ▼
	  Generated Response
		    │
		    ▼
		API Layer
		    │
		    ▼
	    Avatar / Interface
		    │
		    ▼
		  USER
```
⸻

## 18. Development Responsibility Boundary
The AI brain is the primary development focus for the AI component of the project.

This includes:

- Knowledge-base design
- Knowledge collection and processing
- Embedding pipeline
- Vector retrieval
- RAG architecture
- Conversational agent
- Prompt and behaviour design
- LLM integration
- Evaluation (Brain track and Avatar track)
The avatar, robot, animation, and other presentation components can be developed independently and connected through the application/API layer. This allows the project to maintain a clear boundary between AI intelligence and user-facing presentation.

⸻

## 19. Future Expansion
The architecture is designed to support future extensions without fundamentally changing the core AI system.

Potential future capabilities and extensions include:

- Broader, maintained environmental knowledge beyond the current static GRBMP corpus.
- Image-based educational interactions.
- CPCB coverage beyond the currently supported stations and parameters, and other independently verified data sources.
- More advanced agent workflows (§7.2 — explanation, reflection, quiz follow-up, per R5).
- Personalized educational interactions (R4, R8).
- Additional physical or digital interfaces.

Text multilingual handling, the current browser avatar, voice adapters, and the limited CPCB station route are implemented; implementation does not imply full provider validation or educational effectiveness.
Such capabilities should be added as modular components where possible.

⸻

## 20. Architecture Implementation Status
The architecture in this document is a mix of design rationale and the current `main` implementation. The historical `Knowledge-base-creation` branch is not the active source of truth.

**Implemented Technology Choices:**
- **Knowledge Base**: 86 official GRBMP PDF reports, filtered into 1,111 sections (4,085 chunks).
- **Embedding Model**: Local ONNX `all-MiniLM-L6-v2` dense vector model (384 float32 dimensions).
- **Vector Retrieval Backend**: SQLite metadata (`brain_index.sqlite3`) + NumPy vector matrix (`brain_semantic_vectors.npy`) with manifest integrity checks; Chroma-format files are legacy artifacts.
- **Retriever**: Hybrid (ONNX dense similarity + lexical reranking).
- **Quality Gate**: Multi-Factor Evidence Gate (unsupported query rejection + current-info fallback).
- **Generator**: Evidence-gated Groq → OpenRouter → extractive fallback chain; `LLM_PROVIDER=extractive` selects local-only generation. Provider keys and models are configured independently with `GROQ_API_KEY` / `GROQ_MODEL` and `OPENROUTER_API_KEY` / `OPENROUTER_MODEL`; `LLM_PROVIDER_ORDER` can reverse provider order. The project-root `.env` is loaded without replacing exported environment variables.
- **API Boundary**: FastAPI HTTP Server (`POST /ask`, `GET /health`).
- **CPCB station readings**: A separate integration-controller path retrieves a limited set of live CPCB readings (pH, DO, BOD) for supported main-stem stations, caches payloads for 60 seconds, and labels measurements older than 90 minutes stale. This is not comprehensive river monitoring; external endpoint availability and data reuse terms are not established by this code audit.
- **Multilingual text**: Language selection/detection and translation handling support `en`, `hi`, `kn`, and `ta`. General translation uses Google's public GTX endpoint by default on API routes; requests may send the question and/or generated response outside the application. The route has no UI consent control, API callers may set `translation_consent=false`, and endpoint terms/retention are unverified.
- **Voice**: Vosk model mappings cover English and Hindi; browser speech controls and Edge TTS voices are configured for four languages, with host/provider support not guaranteed. Windows SAPI fallback is configured for English/Hindi. Rhubarb tooling may use a cadence fallback when its platform binary is unavailable.
- **Avatar and quiz**: The active browser implementation is Three.js and includes the Chacha mascot and quiz interface. Legacy Unity and alternate avatar documents/assets are historical or retained assets, not the active runtime description.

The architectural objective remains:

> Build a modular, knowledge-grounded AI brain — designed against an explicit pedagogical purpose and evaluated on both information quality and interaction quality — that can independently power multiple Ganga AI Mascot interfaces while providing reliable, educational, and traceable responses.

