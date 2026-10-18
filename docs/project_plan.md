# Project Plan

**Project:** PRJ_316 — AI-Powered Interactive Digital Mascot for Namami Gange Awareness & River-People Connectivity
**Status snapshot:** 2026-10-19, `main` at `80833751f2a365eb00be5ddeee3392e4a601d38e` (before this documentation-only update)

This plan distinguishes implemented software from provider validation and research evaluation. Code presence and automated regression tests do not establish external-service availability, response quality, usability, or learning impact.

## Current phase

**Integrated prototype; documentation reconciliation and evaluation protocol design in progress.** The Brain, integration service, browser avatar, quiz, multilingual text handling, voice adapters, and limited CPCB station-data route are present in the current main snapshot.

## Status by workstream

| Workstream | Status | Evidence boundary / next work |
| --- | --- | --- |
| Curated GRBMP corpus and ingestion | Implemented | Repository inventory records 86 PDFs, 4,609 pages, 1,111 reviewed sections, and 4,085 indexed chunks; counts are snapshot-specific. |
| Retrieval, evidence gate, and citation assembly | Implemented | Uses local embeddings, Euclidean candidate ranking, lexical heuristics, and metadata-based citations. Requires benchmark and claim-level support evaluation. |
| Hosted answer generation | Implemented; live compatibility requires separate validation | Groq → OpenRouter → extractive by default. Provider tests are mocked. No provider comparison or availability claim follows from those tests. |
| CPCB station route | Implemented for a limited station/parameter set | Integration-layer route is separate from static RAG. Broader network coverage, long-term reliability, and reuse terms remain to be assessed. |
| Multilingual text | Implemented, externally dependent for general translation | English, Hindi, Kannada, and Tamil selection/detection and translation flow exist. Google public GTX translation can receive question/answer text; endpoint terms and retention are not verified. |
| 3D avatar and quiz | Implemented in browser client | Three.js Chacha avatar and quiz UI/scripts are in the active client. Usability and learning impact remain unevaluated. |
| Speech recognition | Partially implemented / provider-limited | Vosk model mapping covers English and Hindi; Kannada/Tamil browser recognition depends on browser/service support. |
| Speech synthesis and lip-sync | Implemented adapters; environment validation incomplete | Edge TTS voices are configured for four languages; Windows SAPI fallback covers English/Hindi. Availability is platform/provider-dependent; cadence fallbacks exist. |
| Research and technical documentation | Reconciliation underway | Align current documentation, equations, source status, and evidence conditions; keep historical snapshots labeled. |

## Next research and engineering work

1. Complete and review the documentation reconciliation recorded in `research/paper_workplan.md`.
2. Finalize a labeled evaluation dataset and protocol before reporting retrieval or answer-quality metrics. The proposed 100-question benchmark is not yet a finalized dataset or completed experiment.
3. Run retrieval, citation alignment, evidence rejection, and groundedness evaluations under documented conditions.
4. Conduct a separately designed provider comparison for Groq, OpenRouter, and extractive generation; report latency and quality only after collecting measurements.
5. Validate CPCB routing, freshness/error behavior, and permitted data reuse with the relevant data owner.
6. Test translation and speech with representative users and supported environments; document external data handling before broader deployment.
7. Conduct usability and educational outcome studies with appropriate review, consent, and methodology before making impact claims.
8. Draft and review the manuscript after valid empirical results are available. Results and Discussion remain deferred.

## Historical milestones

Earlier branch names and milestone reports describe prior development snapshots. They are not the current branch or the current runtime status. See `research/technical_baseline.md` for the preserved historical baseline and dated current-state addendum.
