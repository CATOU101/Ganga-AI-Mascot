# GitHub Copilot Instructions

## Project Context

This repository contains PRJ_316, an academic CSE mini-project.

The project explores the development of an AI-powered, source-grounded conversational agent and interactive digital mascot for Ganga and river conservation awareness.

The system may eventually combine:

- Retrieval-Augmented Generation (RAG)
- Source-grounded environmental knowledge
- Conversational AI
- Adaptive educational interaction
- Quiz functionality
- Voice interaction
- Digital avatar integration
- System evaluation

The project is currently in the research and literature review stage. Do not assume that the final architecture, frameworks, models, APIs, or deployment platform have already been selected.

## Repository Structure

Follow the existing repository structure unless explicitly instructed otherwise.

- research/ — research papers, literature reviews, research logs, and research-gap analysis.
- knowledge_base/ — source documents, datasets, document processing, and knowledge-source information.
- brain/ — AI-related components, including RAG, agent logic, prompts, and evaluation.
- avatar/ — digital avatar and interaction components.
- integration/ — components responsible for connecting the AI system, avatar, voice, and interfaces.
- docs/ — project architecture, requirements, development plans, and technical documentation.

Keep new files organized within the appropriate component instead of placing unrelated files in the repository root.

## General Development Principles

1. This is an academic project. Prioritize clear, understandable, modular, and well-documented implementations.
2. Do not invent research results, datasets, APIs, model performance, or evaluation results.
3. Do not implement major features unless explicitly requested.
4. Before making significant changes, inspect the existing repository structure and relevant documentation.
5. Keep components modular and loosely coupled where possible.
6. Avoid unnecessary complexity. Prefer a simple and maintainable solution unless a more complex approach is justified.
7. Document important architectural decisions and assumptions.
8. Add comments and docstrings when logic is not self-explanatory.
9. Include appropriate error handling and input validation.
10. Add tests for important functionality when implementing code.
11. Do not claim that a feature is complete unless it has been implemented and can be reasonably tested.

## Security and Configuration

1. Never hardcode API keys, passwords, tokens, or other credentials.
2. Use environment variables or appropriate configuration files for secrets.
3. Do not commit sensitive files to the repository.
4. Provide example configuration files when necessary, such as .env.example, without real credentials.
5. Consider privacy and security when handling user input or external data.

## AI and Knowledge Principles

When implementing AI, RAG, or knowledge-base components:

1. Prefer authoritative and trustworthy sources for Ganga and environmental information.
2. Preserve source metadata and provenance during document processing.
3. Keep document ingestion, processing, retrieval, and response generation modular.
4. Support the ability to trace generated responses back to relevant source information where technically possible.
5. Do not present unsupported or fabricated information as verified knowledge.
6. Clearly distinguish between retrieved information and model-generated explanations when appropriate.
7. Consider hallucination reduction, retrieval quality, and answer reliability during system design.

## Research Principles

When working inside the research/ directory:

1. Do not fabricate citations or research papers.
2. Clearly distinguish between information obtained from research papers and proposed ideas for PRJ_316.
3. Record important limitations and research gaps when analyzing previous work.
4. Do not present proposed project features as completed research results.
5. Keep literature review and research documentation suitable for an academic mini-project.

## Collaboration Guidelines

The project is developed by a team.

When modifying shared components:

1. Avoid unnecessary changes to unrelated files.
2. Keep commits focused on a specific task.
3. Use clear commit messages.
4. Document significant changes.
5. Prefer small, reviewable changes over large unrelated modifications.

# Copilot Behaviour

When given a task:

1. First understand the requested task and inspect relevant repository context.
2. If the task is ambiguous, use existing documentation and project structure to make the smallest reasonable assumption.
3. Avoid introducing new technologies or dependencies without a clear reason.
4. Explain important design decisions after completing a task.
5. Do not expand the scope beyond the requested task.
6. When asked to implement a component, consider how it will integrate with the larger PRJ_316 architecture.
7. Preserve consistency with existing code and documentation.

The goal is to assist the development of a reliable, understandable, and academically well-documented AI system rather than generating unnecessary complexity.
