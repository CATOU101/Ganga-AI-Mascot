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

No research findings or implementation claims are presented at this stage.

## Proposed High-Level Architecture

The proposed architecture is organized into the following conceptual layers:

1. **Knowledge base:** Curated source documents are collected, processed, indexed, and documented with their provenance.
2. **RAG layer:** A retrieval pipeline identifies relevant source material for each user query and supplies context to the response generation process.
3. **Agent layer:** The conversational agent interprets the query, applies prompt and response policies, and produces a source-grounded answer.
4. **Avatar layer:** An interactive digital mascot provides the user-facing conversational and visual experience.
5. **Integration layer:** Application components and future interfaces are connected through clearly defined integration boundaries.
6. **Evaluation layer:** Retrieval, grounding, conversation quality, and user experience are assessed against documented criteria.

This architecture is a research-stage proposal and will be refined as the literature review and experimentation progress.

## Repository Structure

```text
Ganga-AI-Mascot/
├── README.md
├── research/
│   ├── papers/
│   ├── literature_review.md
│   └── research_gap.md
├── knowledge_base/
│   ├── raw_documents/
│   ├── processed_documents/
│   └── sources.md
├── brain/
│   ├── rag/
│   ├── agent/
│   ├── prompts/
│   └── evaluation/
├── avatar/
│   └── README.md
├── integration/
│   └── README.md
└── docs/
    ├── architecture.md
    └── project_plan.md
```

## Current Status

**Research and Literature Review in Progress**

The repository currently contains the initial research, knowledge-base, architecture, and planning structure. Application implementation has not started.

## Academic Disclaimer

This repository is an academic mini-project. The proposed architecture, research direction, and project plan are preliminary and may evolve as the team reviews literature, evaluates alternatives, and learns from future experiments.
