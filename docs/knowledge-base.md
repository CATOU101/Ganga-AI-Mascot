# Knowledge Base

This document defines the knowledge-base architecture and data requirements for **Ganga AI Mascot**.

The knowledge base is the factual foundation of the AI brain. It provides the information that the Retrieval-Augmented Generation (RAG) system retrieves and supplies to the language model when answering user questions.

The knowledge base will be curated from reliable and authoritative sources and structured so that information can be traced back to its original source.

---

## 1. Purpose

The purpose of the knowledge base is to provide Ganga AI Mascot with reliable, relevant, and structured information about the Ganga River, its ecosystem, conservation, pollution, biodiversity, and the Namami Gange programme.

The knowledge base should:

- Provide factual information for the AI agent.
- Reduce reliance on unsupported model knowledge.
- Support retrieval of relevant information through RAG.
- Preserve source information for traceability.
- Allow new information to be added without redesigning the system.
- Support evaluation of retrieval and generated responses.

---

## 2. Knowledge Scope

The initial knowledge base will focus on information directly relevant to the Ganga River and its conservation.

### 2.1 Ganga River

Topics include:

- Origin and geography
- River basin
- Major tributaries
- States through which the river flows
- Important locations
- Cultural and historical significance
- River ecosystem
- Hydrology and related environmental information

### 2.2 Ganga Ecosystem

Topics include:

- Aquatic ecosystems
- River ecology
- Wetlands
- Riparian ecosystems
- Ecosystem services
- Ecological importance of the Ganga
- Human interaction with the river ecosystem

### 2.3 Biodiversity

Topics include:

- Aquatic species and fish
- Ganges river dolphin
- Turtles
- Migratory birds
- Other important wildlife
- Threatened species
- Habitat conservation
- Biodiversity protection programmes

### 2.4 Pollution

Topics include:

- Water pollution
- Sewage pollution
- Industrial pollution
- Agricultural runoff
- Solid waste and plastic pollution
- Religious and cultural waste
- Pollution sources and effects
- Water-quality indicators
- Pollution-control measures

### 2.5 Conservation

Topics include:

- River restoration
- Wastewater and sewage treatment
- Industrial effluent management
- Biodiversity conservation
- Afforestation
- Wetland conservation
- Public participation
- Environmental awareness
- Sustainable practices

### 2.6 Namami Gange

This is a major knowledge domain for the project.

Topics include:

- Purpose, objectives, and programme structure
- Major initiatives
- Sewage infrastructure
- Pollution abatement
- River-surface cleaning
- Biodiversity conservation
- Afforestation
- Public awareness and community participation
- Monitoring
- Relevant government programmes and projects

Information about current programmes should be associated with its source and date where possible.

### 2.7 Environmental Awareness

The mascot should also be able to provide practical educational information such as:

- How individuals can reduce river pollution
- Proper waste disposal
- Plastic reduction
- Water conservation
- Responsible behaviour near rivers
- Sustainable practices
- Importance of protecting aquatic ecosystems

Advice should be educational and should not be presented as an official government instruction unless supported by an appropriate source.

### 2.8 Frequently Asked Questions

The knowledge base may contain curated question-and-answer material covering common questions such as:

- What is the Ganga?
- Where does the Ganga originate?
- Why is the Ganga important?
- Why is the Ganga polluted?
- What is Namami Gange?
- What animals live in the Ganga?
- What is the Ganges river dolphin?
- How can people help protect the Ganga?

FAQ content should complement the underlying source documents rather than replace them.

---

## 3. Knowledge Boundaries

The AI should have a clearly defined knowledge boundary.

### In Scope

- Ganga-related environmental information
- Namami Gange information
- River conservation
- Biodiversity
- Pollution
- Environmental education
- Related general scientific information required to explain these topics

### Out of Scope

The system should not be designed as a general-purpose expert in unrelated domains, including:

- Personal medical advice
- Legal advice
- Financial advice
- Political persuasion
- Personal data requests
- Unrelated technical expertise
- Unsupported claims about individuals or organizations

For questions outside the intended scope, the agent should provide an appropriate response rather than inventing an answer.

---

## 4. Source Hierarchy

The reliability of knowledge depends heavily on the quality of its sources.

### Tier 1 — Primary / Official Sources

- Government departments
- Official Namami Gange programme sources
- National Mission for Clean Ganga
- Government reports
- Official environmental agencies
- Official scientific institutions

### Tier 2 — Scientific Sources

- Peer-reviewed research
- Scientific publications
- Academic institutions
- Research organizations
- Established scientific databases

### Tier 3 — Established Secondary Sources

- Reputable educational organizations
- Established environmental organizations
- High-quality reference material

These may be used when appropriate but should generally have lower priority than primary sources.

### Tier 4 — General Web Sources

General websites, blogs, forums, and other unverified sources should not be used as primary factual sources. If used during research, information should be verified against higher-quality sources before being incorporated into the knowledge base.

---

## 5. Source Selection Criteria

A document should be considered for inclusion based on:

- Authority of the publisher
- Relevance to the knowledge scope
- Accuracy
- Recency where applicable
- Evidence provided
- Stability of the source
- Ability to identify the original source
- Usefulness for answering expected user questions

Not every document from an authoritative organization needs to be included. The goal is a **curated knowledge base**, not simply a large collection of documents.

---

## 6. Document Lifecycle

Every document should follow a controlled lifecycle.

```
Source Discovery
	↓
Source Evaluation
	↓
Document Collection
	↓
Document Registration
	↓
Text Extraction
	↓
Cleaning
	↓
Chunking
	↓
Metadata Assignment
	↓
Embedding
	↓
Vector Store
	↓
Evaluation
```

Documents should remain linked to their original source throughout this process.

---

## 7. Document Metadata

Each document should have metadata describing its origin and content.

| Field | Description |
| --- | --- |
| `document_id` | Unique identifier |
| `title` | Document title |
| `source` | Organization or publisher |
| `source_url` | Original source |
| `source_type` | Government, scientific, academic, etc. |
| `publication_date` | Original publication date where available |
| `accessed_date` | Date collected |
| `version` | Document version where applicable |
| `topic` | Primary knowledge domain |
| `language` | Document language |
| `status` | Active, superseded, archived |
| `notes` | Additional information |

---

## 8. Chunk Metadata

After processing, each chunk should retain enough metadata to identify where the information originated.

```json
{
    "document_id": "...",
    "chunk_id": "...",
    "title": "...",
    "source": "...",
    "source_url": "...",
    "topic": "...",
    "section": "...",
    "page": 0,
    "publication_date": "...",
    "chunk_index": 0
}
```

The exact schema may change during implementation. The important requirement is that retrieved information remains traceable to its source.

---

## 9. Document Processing

Documents should be processed before being inserted into the retrieval system.

```
Raw Document
     ↓
Text Extraction
     ↓
Cleaning
     ↓
Normalization
     ↓
Section Detection
     ↓
Chunking
     ↓
Metadata Attachment
     ↓
Embedding
```

Processing should preserve meaningful structure whenever possible. Headings, lists, tables, and section boundaries should not be destroyed unnecessarily during extraction.

---

## 10. Chunking Strategy

Documents will be divided into smaller knowledge units called **chunks**.

Chunking should balance:

- Context preservation
- Retrieval precision
- Chunk size
- Semantic completeness
- LLM context limitations

A chunk should ideally represent a coherent piece of information rather than an arbitrary section of text. The exact chunk size and overlap will be determined experimentally during the RAG implementation phase.

---

## 11. Duplicate and Redundant Information

The knowledge base may contain overlapping information from multiple sources. Duplicates should be identified where practical.

Identical or similar information should not automatically be removed if sources provide useful differences such as:

- Different publication dates
- Different levels of detail
- Updated figures
- Independent scientific confirmation
- Different perspectives

Source provenance must be retained even when content overlaps.

---

## 12. Conflicting Information

Different sources may contain different values or conclusions. The system should not silently merge conflicting information.

When conflicts are identified:

1. Prefer the most authoritative source.
2. Prefer newer information when the subject is time-sensitive.
3. Preserve source dates.
4. Record the conflict where appropriate.
5. Avoid presenting uncertain information as definitive.

For significant disagreements, the final response may explicitly communicate uncertainty.

---

## 13. Temporal Information

Some knowledge is relatively stable, such as river geography, species information, and basic ecology. Other knowledge changes over time, including:

- Government programmes
- Project status
- Water-quality measurements
- Statistics
- Infrastructure
- Policies
- Targets and achievements

Time-sensitive information should retain publication or reporting dates. The system should avoid presenting outdated information as current.

---

## 14. Source Traceability

Where practical, generated factual responses should be traceable to the retrieved knowledge.

```
Answer
  ↓
Retrieved Chunk
  ↓
Document
  ↓
Original Source
```

This will support debugging, evaluation, fact verification, updating outdated information, and demonstrating reliability. Source references may later be exposed directly to users depending on the final interface design.

---

## 15. Knowledge Updates

The knowledge base should support incremental updates. A new document should not require rebuilding the entire system from scratch.

```
New Source
    ↓
Evaluate
    ↓
Process
    ↓
Chunk
    ↓
Embed
    ↓
Add to Knowledge Base
    ↓
Evaluate Retrieval
```

When an updated document replaces an older version, the older version should be marked appropriately rather than silently deleted.

---

## 16. Knowledge Base Structure

The repository may initially use a structure similar to:

```
knowledge/
├── raw/
│   ├── government/
│   ├── scientific/
│   └── educational/
│
├── processed/
├── metadata/
├── datasets/
└── README.md
```

The exact directory structure may change during implementation. Raw documents should remain separate from processed data so that the processing pipeline can be rerun when necessary.

---

## 17. Knowledge Ingestion Pipeline

The planned ingestion system is:

```
		  SOURCE DOCUMENTS
			   │
			   ▼
		  Source Validation
			   │
			   ▼
		  Document Extraction
			   │
			   ▼
		 Cleaning / Parsing
			   │
			   ▼
			Chunking
			   │
			   ▼
		  Metadata Creation
			   │
			   ▼
		 Quality Validation
			   │
			   ▼
		  Embedding Model
			   │
			   ▼
		    Vector Store
```

The ingestion pipeline should eventually be automated where practical.

---

## 18. Quality Control

Before knowledge is added to the production retrieval system, it should pass basic quality checks:

- Source validity
- Text extraction quality
- Missing text
- Duplicate documents
- Incorrect metadata
- Empty or extremely small chunks
- Broken source references
- Encoding problems
- Chunk coherence

A small manually reviewed dataset should be used initially to validate the pipeline before processing a larger collection.

---

## 19. Knowledge Base Evaluation

The knowledge base itself should be evaluated independently from the LLM.

Questions should be created across the major knowledge domains. For each question, identify:

```
Question
   ↓
Expected Information
   ↓
Expected Source
   ↓
Expected Relevant Chunk(s)
```

Example:

```
Question:
"Why is sewage a major source of pollution?"

Expected Topic:
Pollution → Sewage

Expected Source:
Authoritative environmental report

Expected Evidence:
Relevant section/chunk explaining sewage pollution
```

This dataset will later become part of the RAG evaluation process.

---

## 20. Initial Knowledge Base Development Strategy

The project should begin with a **small, high-quality knowledge base** rather than attempting to collect everything about the Ganga.

The initial dataset should cover the core topics:

1. Ganga River
2. Namami Gange
3. Pollution
4. Biodiversity
5. Conservation
6. Environmental awareness

Once retrieval quality is validated, additional documents and topics can be added. This allows the team to test the complete AI pipeline early.

---

## 21. Relationship With the RAG System

The knowledge base provides the information consumed by the RAG layer.

```
		    KNOWLEDGE BASE
			     │
			     ▼
		     Embeddings
			     │
			     ▼
			Vector Store
			     │
			     ▼
			 Retriever
			     │
			     ▼
		  Relevant Knowledge
			     │
			     ▼
			    LLM
```

The knowledge base and RAG system should remain conceptually separate.

The knowledge base answers: **"What information do we have?"**

The RAG system answers: **"Which information is relevant to this question?"**

---

## 22. Current Status

The knowledge-base architecture is currently a **design specification**.

The following implementation decisions remain to be finalized:

- Exact source list
- Document formats
- Extraction tools
- Chunk size
- Chunk overlap
- Embedding model
- Vector database
- Retrieval strategy
- Metadata implementation
- Update mechanism

These decisions will be made during implementation and evaluation rather than being assumed prematurely.

---

## 23. Next Phase

After this specification is reviewed and committed, the next phase will be **Knowledge Source Collection and Ingestion Pipeline Development**.

The immediate objectives will be:

1. Identify authoritative sources.
2. Select an initial set of documents.
3. Establish the repository structure.
4. Build document extraction and cleaning.
5. Implement chunking.
6. Attach metadata.
7. Create a small test dataset.
8. Prepare the data for embedding and retrieval.

The goal is to produce a **small, clean, traceable knowledge dataset** that can be used to build and evaluate the first RAG prototype.
