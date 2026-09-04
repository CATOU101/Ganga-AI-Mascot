# PRJ_316 Brain Requirements

## 1. Purpose

The Brain is the AI component of PRJ_316 responsible for answering user questions about the Ganga, river conservation, environmental awareness, and related topics using a combination of a source-grounded knowledge base and approved real-time data sources.

The Brain should prioritize factuality, source grounding, explainability, educational usefulness, and appropriate handling of current information.

## 2. Core Objective

The first prototype should support:

User Question
→ Query Processing
→ Determine Information Type
→ Static Knowledge Retrieval and/or Real-Time Data Retrieval
→ Context Construction
→ Response Generation
→ Source/Data Attribution

The system should be able to distinguish between questions that can be answered from the knowledge base and questions that require current or real-time information.

## 3. Core Features

### 3.1 Question Answering

The Brain should answer questions related to the information contained in its approved knowledge base.

### 3.2 Retrieval-Augmented Generation

The prototype should use RAG so that generated answers are based on retrieved knowledge rather than relying only on the language model's internal knowledge.

### 3.3 Real-Time Information Retrieval

The Brain should support a separate real-time information path for questions requiring current data.

Potential sources may include:

- CPCB real-time water-quality monitoring data
- Relevant NMCG data/services
- Appropriate datasets or APIs available through India's Open Government Data platform (data.gov.in)
- Other authoritative environmental APIs or services identified during development

A source should only be integrated after its availability, update frequency, API/interface, coverage, and suitability for the project have been verified.

The real-time path should not be assumed to provide information for every location or parameter.

### 3.4 Hybrid Knowledge Routing

The Brain should determine whether a question requires:

- Static knowledge from the RAG knowledge base
- Real-time information from an approved API/data source
- Both static and real-time information

Conceptually:

User Question
→ Query Classification
→ Static Knowledge / Real-Time API / Both
→ Retrieve Required Context
→ Response Generation

Examples:

"What is Namami Gange?"
→ RAG knowledge base

"What is the current water quality of the Ganga?"
→ Real-time data source, if appropriate current data is available

"What is dissolved oxygen and what is its current value at a monitoring station?"
→ RAG for the explanation + real-time source for the current value

### 3.5 Source and Data Attribution

For RAG responses, the Brain should identify the relevant document/source where technically possible.

For real-time responses, the Brain should provide:

- Data source
- Monitoring station/location where applicable
- Parameter
- Latest available timestamp
- Value and unit where applicable

The system should distinguish current measurements from historical information.

### 3.6 Grounding and Fallback

The Brain must avoid presenting unsupported information as verified fact.

When the system cannot obtain sufficient reliable information, it should clearly explain the limitation to the user.

Possible reasons include:

- Required information is not present in the current knowledge base.
- Available sources do not provide sufficient evidence.
- An approved real-time source does not cover the requested location or parameter.
- The available real-time data is not sufficiently current for the question.
- The question is outside the defined project knowledge scope.
- A required external API/data source is unavailable.

The Brain should not guess or fabricate missing information.

The fallback response should explain why a reliable answer cannot currently be provided rather than simply saying "I don't know."

Example:

"I can't provide a reliable current water-quality value for that location because the approved monitoring data available to the system does not currently contain a measurement for that location."

Another example:

"I can't provide a reliable current value because the real-time data source required for this question is currently unavailable. I don't want to present older information as if it were current."

## 4. Knowledge Scope

The initial knowledge base should focus on:

- Ganga
- Ganga pollution
- River conservation
- Environmental awareness
- Namami Gange and related initiatives
- Relevant water/environmental information

The exact knowledge scope will be refined during knowledge-source selection.

Real-time data should initially focus on environmental information directly relevant to the Ganga and river conservation use case.

## 5. Knowledge Sources

The prototype should prioritize authoritative sources.

Potential sources include:

- Government publications
- Official environmental organizations
- Research papers
- Official reports and guidelines
- Verified government datasets/APIs for real-time information

Every ingested document should retain provenance metadata.

Every real-time data source should retain source and update metadata.

## 6. Knowledge Pipeline

The static knowledge pipeline should be:

Document
→ Text Extraction
→ Cleaning
→ Chunking
→ Metadata
→ Embedding
→ Vector Database

The real-time pipeline should be:

User Query
→ Identify Required Live Data
→ Call Approved API/Data Source
→ Validate Response
→ Normalize Data
→ Attach Source + Timestamp
→ Context for Response Generation

## 7. Retrieval Pipeline

### 7.1 Static Retrieval

The retrieval pipeline should be:

User Query
→ Query Embedding
→ Vector Search
→ Relevant Chunks
→ Retrieved Context

The retrieval system should be independently testable before being connected to the LLM.

### 7.2 Real-Time Retrieval

The real-time retrieval pipeline should be:

User Query
→ Required Parameter/Location/Time Identification
→ Approved Data Source
→ Latest Available Data
→ Validation
→ Structured Context

The system should validate that the returned data corresponds to the requested location, parameter, and time context where applicable.

## 8. Generation Pipeline

The generation pipeline should be:

User Query
+
Retrieved Static Context
+
Real-Time Context where required
+
Relevant Conversation Context
→
LLM
→
Grounded Response

The generation component must be instructed not to fabricate unsupported information.

When real-time information is used, the generated response should make clear that the information comes from a live/current data source and should include the latest available timestamp where appropriate.

## 9. Conversation Context

The Brain should support basic follow-up questions using relevant conversation context.

Example:

User:
"What is dissolved oxygen?"

Brain:
Explanation.

User:
"Why is it important?"

Brain:
Uses previous context.

User:
"What is its current value in the Ganga?"

Brain:
Uses the conversation context to identify the requested parameter and retrieves the appropriate current data if available.

Conversation history should be controlled rather than sending unlimited history to the model.

## 10. Educational Interaction

The Brain should eventually support educational interactions such as:

- Simplified explanations
- Follow-up questions
- Quizzes
- Conservation suggestions
- Age-appropriate explanations
- Educational storytelling where appropriate

Educational responses should remain grounded in approved knowledge.

## 11. Prototype Output

The Brain should eventually expose a structured response containing at minimum:

- Answer
- Sources

For responses using real-time data, additional structured information may include:

- Data source
- Location/station
- Parameter
- Value
- Unit
- Timestamp

For fallback responses, the Brain should provide:

- A clear statement that a reliable answer cannot currently be provided
- The reason for the limitation

Additional fields may be added later if required by the integration layer.

## 12. Prototype Architecture

The initial architecture should remain modular:

User
→ Query Processing / Routing
→
┌──────────────────────┬──────────────────────┐
│ Static Knowledge     │ Real-Time Data       │
│ RAG                  │ Approved APIs        │
└──────────┬───────────┴──────────┬───────────┘
           ↓                      ↓
              Context Fusion
                    ↓
               Generation
                    ↓
          Answer + Attribution
                    ↓
              Brain Interface

The architecture should allow individual components to be changed without rewriting the entire system.

## 13. Evaluation

The prototype should eventually be evaluated for:

### Retrieval

- Relevance of retrieved information
- Retrieval accuracy
- Appropriate routing between static and real-time sources

### Generation

- Factual correctness
- Groundedness
- Relevance
- Completeness
- Correct use of real-time information

### Real-Time Data

- Correct API/source selection
- Correct location/station selection
- Correct parameter selection
- Timestamp accuracy
- Handling of unavailable/stale data

### Fallback

- Correct detection of insufficient evidence
- Clear explanation of why an answer cannot be provided
- No fabricated values or unsupported claims

### System

- Response time
- API failure handling
- Retrieval failure handling
- Overall failure rate

### Educational Interaction

- User engagement
- Knowledge gain
- Quiz performance where applicable

## 14. Current Limitations

The first prototype will not attempt to implement:

- Fine-tuning
- Multi-agent architecture
- Complex autonomous agents
- Large-scale web crawling
- Advanced emotion detection
- Complex personalization

Real-time integration will initially be limited to authoritative and technically accessible sources that can be verified and reliably queried.

Additional real-time sources may be added later if they provide meaningful value to the project.

## 15. Development Milestone

### 20 September 2026 — 50% Prototype

The target is a working end-to-end prototype demonstrating:

Authoritative Knowledge
→ RAG Retrieval
→ Real-Time Data Path where applicable
→ Grounded AI Response
→ Source/Data Attribution
→ Basic Conversation
→ Brain Interface/API

The avatar and voice components may initially remain at prototype/integration level.

## 16. Current Status

Status: DEVELOPMENT STARTING

Research and literature review: COMPLETED

Brain requirements: INITIAL VERSION

Knowledge-source verification: NOT STARTED

Brain implementation: NOT STARTED