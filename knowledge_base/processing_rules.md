# Knowledge Base Processing Rules

## 1. Purpose

This document defines how source documents are transformed into reliable, traceable knowledge for the Ganga Brain Knowledge Base. It applies only to the Brain and its Knowledge Base; Avatar and frontend processing are outside its scope.

The Knowledge Base should prioritize:

- reliable information
- source provenance
- useful conceptual knowledge
- historical context when properly labelled
- separation of stable knowledge from time-sensitive information
- retrieval quality
- prevention of unsupported claims

The Knowledge Base must not simply ingest every document and every piece of text. Source and section selection are required before content becomes retrievable knowledge.

## 2. Processing Pipeline

The intended pipeline is:

```text
PDF/source documents
        |
        v
Document discovery
        |
        v
Text extraction
        |
        v
Text cleaning
        |
        v
Section identification
        |
        v
Content classification
        |
        v
Filtering
        |
        v
Chunking
        |
        v
Metadata assignment
        |
        v
Quality checks
        |
        v
Embedding
        |
        v
Vector database
        |
        v
Retrieval
        |
        v
Grounded answer generation
```

- **Document discovery:** identify candidate documents from the registered project source collection and confirm their source classification.
- **Text extraction:** extract readable text while retaining page references and available document structure.
- **Text cleaning:** remove extraction noise, repair obvious layout artifacts, and avoid changing the meaning of the source.
- **Section identification:** identify titles, headings, subsections, tables, figures, appendices and other context boundaries.
- **Content classification:** assign source status and knowledge type, and identify topic, time period and geographic scope.
- **Filtering:** retain approved sections and content; flag or exclude material that is irrelevant, unsupported, obsolete without historical value, excessively specialized or not interpretable without context.
- **Chunking:** divide approved content into coherent retrieval units while preserving enough context to understand each unit.
- **Metadata assignment:** attach provenance, classification and retrieval metadata to every ingested chunk.
- **Quality checks:** verify readability, context, classification, provenance, relevance and duplication before ingestion.
- **Embedding:** generate representations for chunks that pass quality checks. The embedding model is not selected by this document.
- **Vector database:** store approved chunk representations and metadata in the later-selected vector database. No particular database is specified here.
- **Retrieval:** identify relevant, properly filtered chunks for a Brain question.
- **Grounded answer generation:** use retrieved evidence and provenance to support answers, distinguish historical from current information and avoid unsupported claims.

## 3. Source Selection Rules

The classifications in `knowledge_base/sources.md` must be respected:

### SELECT

The source can contribute relevant knowledge to the initial Knowledge Base after normal processing and quality checks.

### SELECT WITH FILTERING

The source is useful, but only relevant sections and content should be ingested. This includes conceptual sections, definitions, explanations, causes and effects, environmental-management concepts and useful recommendations. This is the expected treatment for most GRBMP Mission Reports and supporting studies.

### DEFER

Keep the document available in the project source collection, but do not include it in the initial Knowledge Base.

### HISTORICAL

Historical information may be retained when it provides useful context. Its publication date and data or study period must be preserved in metadata, and it must not be represented as current information.

### PROJECT REFERENCE

The document may help the project team understand the domain or design the Brain, but it should not normally become user-facing factual knowledge.

## 4. Section-Level Filtering

A PDF is not an all-or-nothing source. A single document can contain useful conceptual material, historical statistics, technical methodology, outdated status information and irrelevant sections. Filtering must happen at the section or content level whenever practical.

Prefer keeping:

- definitions
- conceptual explanations
- causes and effects
- stable environmental principles
- relevant management concepts
- useful recommendations
- clearly identified historical context

Prefer filtering or excluding:

- duplicate material
- irrelevant sections
- excessively specialized technical material
- unsupported claims
- obsolete status information when it has no historical value
- tables whose meaning cannot be correctly interpreted without missing context

Do not delete original PDFs merely because some sections are not ingested. Retain them in the source collection with their processing decision and rationale.

## 5. Knowledge-Type Classification

Every useful chunk should be classified as one of the following:

### STATIC

Stable conceptual or factual knowledge that is not expected to change frequently.

Examples include definitions, environmental concepts, ecological relationships and scientific principles.

### HISTORICAL

Information describing a particular historical period, study, survey or past condition.

Examples include GRBMP findings from the early 2010s, historical pollution measurements, historical flow measurements and historical infrastructure status. Historical information can be retrieved, but its date and context must be preserved.

### DYNAMIC

Information whose correctness depends on the current or changing state of the world.

Examples include current STP status, current water quality, current river discharge, current programme progress, current infrastructure status and current government policies or schemes. GRBMP documents should generally not be treated as authoritative current sources for these values.

### METHODOLOGICAL

Information describing a method, model, assessment framework or technical procedure. Retain it when relevant, but highly specialized methodology should not automatically become core user-facing knowledge.

### IRRELEVANT

Content that does not contribute meaningfully to the Brain's intended knowledge domain. Do not ingest it.

## 6. Historical Information Rules

The GRBMP collection was published primarily around 2015 and contains substantial material based on earlier data. Therefore:

- preserve publication date
- preserve study or data period when available
- never silently convert historical information into present-day information
- keep historical statistics identifiable as historical
- allow historical findings when the user asks about the GRBMP, historical conditions or how the situation was understood at that time

Good:

> According to the 2015 GRBMP assessment, ...

Bad:

> The Ganga currently has ...

when the underlying number comes from an old GRBMP report.

## 7. Dynamic Information Rules

The Knowledge Base is not the authoritative source for current or real-time information. When the Brain encounters a question requiring current information, the application should eventually be able to route that request to an appropriate current and authoritative source or API.

Potential dynamic categories include:

- river flow or discharge
- water quality
- STP status
- current pollution monitoring
- current forest-cover statistics
- current Namami Gange programme status
- current infrastructure status
- current legal or regulatory information

This document does not implement API integration. It only defines the boundary between static or historical RAG knowledge and future dynamic data sources.

## 8. Chunking Rules

Chunks should:

- contain a coherent idea
- preserve enough surrounding context to be understandable
- avoid splitting a definition from the explanation that gives it meaning
- avoid extremely small fragments
- avoid unnecessarily large chunks
- preserve section boundaries where possible

Do not hard-code a token count yet. The final chunking strategy, chunk size, overlap and retrieval behavior should be evaluated experimentally.

## 9. Metadata Schema

Every ingested chunk must preserve provenance. At minimum, metadata must include:

- `source_id`
- `title`
- `author`
- `publisher`
- `publication_date`
- `page`
- `section`
- `topic`
- `knowledge_type`
- `time_period`
- `source_status`
- `relevance`
- `file_name`

Where available, also preserve:

- report or mission number
- geographic scope
- document version
- subsection
- original URL or identifier

Metadata is essential for filtering retrieval, distinguishing historical from current information, debugging, source attribution, evaluation and future updates.

## 10. Provenance and Citations

The Brain must be able to trace retrieved information back to its source. Every chunk must retain enough metadata to identify:

- the document it came from
- the section
- the page
- the publication or version

The system should eventually use this information when presenting source-backed answers. This specification does not define the final user-interface citation format.

## 11. Duplicate Handling

Documents may contain overlapping or duplicated information. Do not blindly delete duplicates.

Instead:

- identify substantial duplication
- retain the strongest or most authoritative version where appropriate
- preserve multiple sources when they provide materially different context
- avoid unnecessarily embedding identical passages multiple times

Duplicate handling should be evaluated during ingestion, with decisions recorded when they affect source coverage or provenance.

## 12. Technical and Specialized Material

Technical material should not automatically be rejected. Classify it according to usefulness.

Keep it when it:

- explains an important concept
- supports an important Brain question
- provides necessary technical context

Defer it when it:

- is highly specialized
- is unlikely to be useful to initial target users
- consists primarily of complex modelling details
- duplicates simpler explanations already available

The original source must remain available even when material is deferred.

## 13. Regional Information

Regional studies must preserve geographic scope. Information specific to Uttarakhand, Uttar Pradesh, Bihar, West Bengal, particular river stretches or individual cities must not automatically be generalized to the entire Ganga basin.

Regional information must include geographic metadata and should identify the relevant location, river stretch, administrative area or study boundary whenever available.

## 14. Quality-Control Rules

Before a chunk enters the vector database, verify that:

1. It belongs to an approved source.
2. It is relevant to the Brain.
3. Its text extraction is readable.
4. Its section context is preserved.
5. Its publication date is known when available.
6. Its historical or current status is classified.
7. Its provenance metadata is complete enough for tracing.
8. It does not contain obvious duplicate or irrelevant material.
9. Tables and figures are not ingested without sufficient context.
10. The chunk does not create a misleading interpretation when separated from surrounding text.

If a chunk cannot satisfy these requirements, flag it for review rather than silently ingesting it.

## 15. Grounding and Unsupported Information

The Knowledge Base should support grounded answers. Retrieval alone does not prove that a statement is correct.

The future Brain should:

- prefer retrieved supporting evidence
- preserve source provenance
- avoid presenting unsupported claims as facts
- distinguish historical information from current information
- indicate when available sources are insufficient

If sufficient supporting information cannot be retrieved, the Brain should eventually tell the user that it cannot reliably answer the question and explain why, rather than inventing an answer. This section defines the Knowledge Base requirement; actual response behavior will be implemented later in the Brain and retrieval layer.

## 16. Current Information Boundary

RAG is primarily responsible for:

- stable knowledge
- conceptual knowledge
- historical knowledge with proper context

Current-data integrations are responsible for:

- real-time measurements
- current programme status
- current infrastructure status
- changing statistics
- other information whose validity depends on the present date

The two systems should eventually work together rather than forcing all information into the vector database.

## 17. Initial Processing Strategy

For the first implementation:

1. Process the approved GRBMP sources.
2. Extract text programmatically.
3. Preserve document, page and section information.
4. Apply source and section filtering.
5. Classify knowledge type.
6. Attach metadata.
7. Generate chunks.
8. Run quality checks.
9. Generate embeddings.
10. Store embeddings in the selected vector database.
11. Test retrieval using representative Brain questions.

The first implementation is not assumed to be final. Chunk size, retrieval parameters, filtering rules and embedding configuration should be evaluated experimentally.

## 18. What This Document Does NOT Define

This file does not define:

- LLM or model selection
- final vector database choice
- embedding model selection
- API implementation
- frontend or Avatar behavior
- conversation or personality design
- final prompt engineering
- production deployment
- authentication
- user interface

Those concerns belong to other parts of the project.

## 19. Current Implementation Status

**Completed:**
- GRBMP source collection (86 PDF files, 4,609 total pages)
- Source registry and classification in `knowledge_base/sources.md`
- Document extraction and cleaning
- Section-level filtering strategy (1,111 approved sections selected)
- Chunking and metadata assignment (4,085 chunks)
- ONNX 384-dimensional dense semantic vector generation (`all-MiniLM-L6-v2`)
- Standalone SQLite metadata database (`chroma.sqlite3`) and NumPy vector matrix (`semantic_vectors.npy`)
- Retrieval, quality gate, and groundedness evaluation harness (`python -m brain.tests.run_evaluation`)

**Not yet completed:**
- Real-time telemetry or external current-data API integration (currently falls back gracefully to `current-info-fallback`)
- Frontend / Avatar runtime integration

