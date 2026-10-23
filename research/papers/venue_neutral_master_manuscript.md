# AI-Powered Interactive Digital Mascot for Namami Gange Awareness & River-People Connectivity

**Authors and affiliations:** To be supplied from verified institutional records. No author names, affiliations, or contact details are inferred in this draft.

## Abstract

This paper describes a browser-based digital mascot integrated with a retrieval-augmented question-answering system for Ganga River Basin Management Plan (GRBMP) material. The Brain retrieves up to 15 dense candidates, applies lexical-overlap and overview-aware reranking, checks evidence with heuristic gates, and then uses a configurable Groq-to-OpenRouter generation chain with extractive fallback. Citation records are assembled from retrieved metadata. The wider application also includes a Three.js avatar, a quiz, multilingual text paths, voice adapters, and a separate CPCB route for selected water-quality requests. Three saved evaluations are reported without rerunning the underlying experiments: a 30-query retrieval ablation, a selected 20-query evidence-gate check, and a 20-query lexical groundedness and citation-metadata check. Retrieval configurations rerank a shared dense top-15 candidate pool. The overview-boosted configuration had MRR@5 0.1444 versus 0.1261 for lexical and unweighted hybrid configurations, with lower recall (0.1278 versus 0.1333); all configurations had P@5 0.0533. On the selected gate set, 10/10 labeled answerable examples were accepted, and 5/5 examples in each of the out-of-domain and dynamic groups were rejected or intercepted. The groundedness script classified 70/70 answer sentences as passing a lexical heuristic and recorded 56/56 citation metadata checks and 56/56 limited source-or-page alignment checks. These operational results do not establish answer relevance, correctness, semantic entailment, general safety, educational impact, or performance on unseen queries. Missing benchmark code and index digests limit exact reproduction.

## Index Terms

Retrieval-augmented generation, hybrid information retrieval, evidence gating, citation provenance, environmental information, digital mascot, Ganga River.

## I. INTRODUCTION

River-basin management plans combine scientific, ecological, historical, and governance information. A conversational interface may make such material easier to explore, but it must distinguish static document evidence from requests for current measurements and from questions the corpus does not support. A character interface can organize interaction; it does not by itself demonstrate learning or behavior change.

This work studies a software prototype that combines a browser-based Three.js mascot and chat client with a Brain service over reviewed GRBMP sections [1]. The prototype integrates dense candidate retrieval, lexical reranking, heuristic evidence checks, hosted generation with extractive fallback, and citations assembled separately from generated prose. A distinct integration route handles selected CPCB water-quality requests. The reported work is an implementation description and analysis of saved engineering artifacts, not a user study or a comparison of live model providers. The architecture follows the general RAG pattern of combining parametric generation with retrieved non-parametric evidence [2].

The contribution is a traceable account of the implemented pipeline and a narrow descriptive evaluation. We specify its chunking, ranking, and evidence rules; distinguish the shared candidate pool from full-corpus search; and report the saved retrieval, gate, and lexical citation checks with explicit limitations. The paper makes no claim of perfect factuality, guaranteed citation support, general safety, educational effectiveness, or broad retrieval generalization.

## II. EXISTING WORKS

Retrieval-augmented generation (RAG) combines parametric generation with non-parametric document retrieval for knowledge-intensive tasks [2]. This prototype follows that broad architecture using a curated river-basin corpus and a local dense index. It adds lexical-overlap reranking and deterministic citation-record assembly from retrieved metadata; the evaluation below does not establish semantic claim support.

The GRBMP Main Plan Document is a corpus source [1]. A related Ganga-awareness mascot paper provides domain context [3]; its author list here follows the published PDF title-block byline. The publisher’s “How to Cite” field conflicts on one author name, as documented in the research log. The paper describes a proposed system and its awareness aims, not measured outcomes. Reviews of conversational AI in education discuss opportunities and ethical or pedagogical concerns [4], [5]. Environmental-education studies in the reviewed set include an expert-consensus module design [6] and a heuristic/usability assessment of ChatGPT in its own study context [7]; neither evaluates this prototype. Reviews and meta-analyses of pedagogical agents and virtual characters report findings from other settings [8]–[11], which cannot be transferred to the system studied here.

Sentence-level embedding methods provide background for semantic representation [12], while MiniLM describes a transformer compression approach [13]. In the application, `brain/embeddings.py` calls ChromaDB’s built-in ONNX `DefaultEmbeddingFunction` and identifies the model as `all-MiniLM-L6-v2`; Sentence-Transformers is not directly called by the application. The model card [14] describes the named checkpoint, but does not prove that the checked-in ONNX archive matches a particular remote revision.

The literature review is thematic rather than systematic. Within the reviewed sources, a directly comparable combination of an environmental mascot, domain-grounded retrieval, and metadata-based citations was not identified. This bounded observation is not evidence that no comparable system exists.

## III. SYSTEM ARCHITECTURE AND METHODOLOGY

### A. Corpus Processing and Index

The source inventory records 86 GRBMP PDFs and 4,609 pages. Review records identify 1,111 approved or retained sections. The checked-in SQLite index contains 4,085 chunks and 83 distinct source filenames; three inventoried PDFs are absent from that index. The matching chunk and distinct-filename counts in the groundedness artifact do not prove that its run used this exact index because the artifact contains no index digest.

`brain/chunking.py` normalizes whitespace and greedily packs paragraphs toward a 1,400-character target with a 180-character suffix overlap. A subsequent repair merges short chunks below 120 characters into the preceding chunk; a first chunk can remain below this minimum, and oversized paragraphs are not split, so 1,400 is not a hard maximum. The semantic embedding path is configured as 384-dimensional and uses ChromaDB’s default ONNX embedding function for the named `all-MiniLM-L6-v2` checkpoint. A separate normalized 384-dimensional local-hash implementation is available as an alternative, not as the reported semantic index configuration.

### B. Candidate Retrieval, Reranking, and Evidence Gate

For each benchmark query, the runner requests up to 15 dense candidates using Euclidean distance, then applies each scoring configuration to that same pool. The production retriever returns up to five accepted hits by default. Configurations A–D are defined in Section IV. In particular, configuration B is a lexical score used to rerank dense candidates, not a full-corpus lexical search.

The gate first computes the fraction of extracted query keywords found in at least one candidate’s text, title, or section. A nonempty keyword set with coverage below 0.60 is rejected. Candidates beyond the configured distance cutoff (default 1.15 for the semantic path; 1.35 for local-hash) are removed. After reranking, a query with more than one keyword is rejected when the top hit’s overlap is below 0.15. These are lexical and distance heuristics, not semantic relevance judgments or calibrated confidence.

The Brain separately intercepts recognized freshness terms paired with configured dynamic topics and returns a current-information fallback without retrieval or generation. In the integrated controller, selected live water-quality requests are routed to the CPCB service before this Brain fallback. CPCB support is limited to five configured stations—Haridwar, Kanpur, Ghazipur, Farakka, and Nabadwip—and uses external endpoints. Routing does not guarantee availability, freshness, completeness, representativeness, or correctness of the readings.

### C. Generation and Citation Assembly

Generation is reached only after retrieval and the existing evidence gate accept a question. Hosted providers are attempted in configurable order, Groq then OpenRouter by default, once each per request; the configured defaults are `openai/gpt-oss-120b` for Groq and `nvidia/nemotron-3.5-super-vl:free` for OpenRouter. Missing credentials and request failures advance to the next provider, followed by extractive generation. These settings describe code configuration, not a live-provider smoke test. `LLM_PROVIDER=extractive` is the local-only generator mode.

The generator bounds the concatenated evidence text to 6,000 characters; this does not cap the entire prompt. Its output-token parameter is capped at 700. Provider instructions request an answer from supplied evidence and prohibit model-created citation strings. Citation objects are deduplicated from metadata on included retrieved hits. This makes citation-record construction independent of generated text, but does not prove source metadata correctness or claim-level entailment. The extractive fallback may cite only the hits that contributed selected sentences and can return a different citation list.

### D. Mascot and Supporting Interfaces

The integration includes a Three.js browser avatar, quiz interface, optional STT/TTS adapters, and language handling for English, Hindi, Kannada, and Tamil. Voice configuration is not equivalent to experimentally verified recognition or synthesis quality. Edge TTS has configured voices for all four languages; Windows SAPI fallback is limited to English and Hindi. Translation may call an external Google Translate GTX endpoint when enabled; the evaluation does not measure translation quality or establish privacy properties. These capabilities support the application but are not evaluated outcomes in this paper.

## IV. MATHEMATICAL FORMULATION

For the reported semantic-index configuration, let $q$ be a query, $e(q)\in\mathbb{R}^{384}$ its unit-normalized embedding, and $d_i$ a unit-normalized indexed vector. Candidate retrieval orders chunks by Euclidean distance:

\begin{equation}
\delta(q,d_i)=\|e(q)-d_i\|_2,\qquad
\mathcal{C}_{15}(q)=\operatorname{Top15}_{d_i}[-\delta(q,d_i)].
\label{eq:dense}
\end{equation}

For unit vectors, this distance lies in $[0,2]$. Let $K(q)$ be the keyword list produced by lowercasing and tokenization, after removing tokens shorter than three characters and configured English stop words. Repeated occurrences are retained. Let $T(c)$ concatenate lowercased chunk text, title, and section metadata. The implementation’s pool coverage and candidate overlap are substring-presence ratios:

\begin{equation}
\mathrm{cov}(q,\mathcal{C})=\begin{cases}
\frac{\sum_{w\in K(q)}\mathbf{1}[\exists c\in\mathcal{C}:w\subset T(c)]}{|K(q)|},&|K(q)|>0,\\
1,&|K(q)|=0,
\end{cases}
\label{eq:coverage}
\end{equation}

\begin{equation}
\mathrm{ov}(q,c)=\begin{cases}
\frac{\sum_{w\in K(q)}\mathbf{1}[w\subset T(c)]}{|K(q)|},&|K(q)|>0,\\
1,&|K(q)|=0.
\end{cases}
\label{eq:overlap}
\end{equation}

The first gate requires $\mathrm{cov}\geq0.60$. After distance filtering, the second requires $\mathrm{ov}(q,c^*)\geq0.15$ for the top-ranked candidate $c^*$ when $|K(q)|>1$. The score used by the production retriever is

\begin{equation}
S_D(q,c)=\frac{1}{1+\delta(q,c)}+0.5\,\mathrm{ov}(q,c)+0.25\,\mathbf{1}[B(q)\land O(c)],
\label{eq:hybrid}
\end{equation}

where $B(q)$ indicates that the query contains “Ganga” or “river” and no configured specific-topic token, and $O(c)$ identifies a hit using configured overview filenames/titles or qualifying overview-section metadata. The coefficients and cutoffs are fixed heuristics, not learned weights or probabilistic confidence values.

For evaluation, configuration A scores $1/(1+\delta)$; B scores $\mathrm{ov}$; C scores $1/(1+\delta)+0.5\mathrm{ov}$; and D adds the overview term in (3). The benchmark sorts score descending and distance ascending, retaining input order on complete ties. The production retriever sorts only by score descending and inherits input order on ties. Precision@5, recall@5, and reciprocal rank at 5 are computed against annotated gold chunk IDs and averaged over queries as defined in the benchmark documentation.

## V. EXPERIMENTAL SETUP AND EVALUATION

Three saved artifacts are examined; their underlying benchmark runs are not repeated here. The retrieval ablation contains 30 curated queries (10 each broad/thematic, technical/scientific, and governance/policy) with 42 unique annotated gold chunk IDs. Its dataset SHA-256 is `66f6df3f8758b3e50ff8f6f5373bd354f98a82eb8e6bbf31dd8c84f38923a999`. All four ranking configurations share the same dense top-15 candidate pool. Reported metrics are per-query P@5, R@5, and MRR@5 means. There are no uncertainty estimates or repeated runs.

The evidence-gate artifact contains 20 selected examples: 10 labeled answerable, five unsupported out-of-domain, and five dynamic/time-sensitive. Its dataset SHA-256 is `f5d0d77a75a8ce9ec29a0798486eeca3a89649b838aad4324d1a5e09ce288ca2`. The artifact checks outcomes on this set only; it is not an estimate over a population of user queries.

The groundedness artifact covers 20 corpus questions and has dataset SHA-256 `8755cefa4455c31e8c24c858b8ac7113e80657a3a29808488f346d9007b51fcb`. It records sentence-level lexical checks, metadata checks, a permissive source-or-page alignment check, and overlap between cited filenames and annotated gold-document sets. These are separate operational criteria with different denominators; none is semantic entailment or human annotation.

The available result JSONs do not record the benchmark code revision and index digest. The groundedness JSON also omits provider, model, and generation mode. Dataset hashes verify query-file bytes, not annotation validity or index identity. Thus, the figures reproduce saved aggregates, not independent re-executions of retrieval or answer generation.

## VI. RESULTS AND DISCUSSION

### A. Retrieval Ablation

Table I reports the production-gated aggregates saved for the 30-query retrieval set. All configurations have P@5 of 0.0533. D has the highest MRR@5 (0.1444) but its R@5 (0.1278) is lower than B and C (0.1333); this is a ranking trade-off, not a uniform improvement. B and C have equal saved aggregate values. Figure 1 visualizes these aggregate values. The benchmark's lexical configuration reranks dense candidates, so the comparison does not establish the behavior of corpus-wide lexical search.

| Configuration | P@5 | R@5 | MRR@5 |
|---|---:|---:|---:|
| A: dense proximity | 0.0533 | 0.1278 | 0.1083 |
| B: lexical overlap | 0.0533 | 0.1333 | 0.1261 |
| C: dense + weighted overlap | 0.0533 | 0.1333 | 0.1261 |
| D: C + overview boost | 0.0533 | 0.1278 | 0.1444 |

![Figure 1. Production-gated retrieval metrics by configuration.](figures/fig1_retrieval_ablation.pdf)

**Fig. 1.** Saved P@5, R@5, and MRR@5 aggregates for four ranking configurations over the same dense top-15 candidate pool (30 queries). No uncertainty interval is available.

### B. Category-Level Ranking

Figure 2 shows that technical MRR@5 remains 0.0500 in all configurations. Broad-query MRR is higher under D (0.3333), while governance remains low (0.0000–0.0500). Each category contains ten queries; small differences should be interpreted descriptively.

| Configuration | Broad/thematic | Technical/scientific | Governance/policy |
|---|---:|---:|---:|
| A | 0.2750 | 0.0500 | 0.0000 |
| B | 0.3033 | 0.0500 | 0.0250 |
| C | 0.3033 | 0.0500 | 0.0250 |
| D | 0.3333 | 0.0500 | 0.0500 |

![Figure 2. Category MRR@5 by configuration.](figures/fig2_category_mrr.pdf)

**Fig. 2.** Broad/thematic, technical/scientific, and governance/policy MRR@5 from the saved production-gated artifact. Zeros are shown; each category contains ten queries.

### C. Evidence-Gate Outcomes

The artifact records expected decisions for all 20 selected cases: 10/10 labeled answerable queries were accepted, 5/5 out-of-domain queries rejected, and 5/5 dynamic queries intercepted. Figure 3 displays the observed decisions with their group denominators. Dynamic handling was the Brain’s temporal-query fallback; this benchmark did not test the separate integration CPCB route.

![Figure 3. Evidence-gate outcomes.](figures/fig3_evidence_gate.pdf)

**Fig. 3.** Matching observed decisions in each selected query group, with sample sizes shown. These counts do not establish unseen-query behavior or general safety.

### D. Groundedness and Citation Checks

The saved groundedness JSON contains 70 evaluated sentences and classifies all 70 as passing its lexical heuristic. It does not measure whether answers address their questions, establish factual correctness, or adjudicate entailment. Clauses of three words or fewer are accepted automatically, and lexical overlap may classify irrelevant or partially unrelated text as grounded. In existing case Q_BROAD_01, for example, the response to an Aviral Dhara question begins with an Active Flood Plain definition, which the heuristic classified as grounded by high lexical subsumption; this is an artifact example, not a new experiment.

The JSON records 56/56 citation metadata checks, 56/56 source-or-page alignment checks, and at least one exact annotated gold-document filename in 10/20 queries. Metadata checks require corpus filename membership and nonempty source/page fields; alignment accepts a retrieved hit sharing either source or page. Neither checks page text or claim support. The 50% gold-document overlap is not proof that other citations are wrong or that they are valid substitutes. The artifact does not identify which generator or provider produced the saved answers. We therefore do not interpret the legacy JSON complement field as an empirical hallucination rate.

## VII. LIMITATIONS AND THREATS TO VALIDITY

The retrieval set has 30 curated queries, while gate and groundedness sets each have 20. Gold labels and selected gate labels were not independently adjudicated in this paper. Results are from saved artifacts without repeated runs, confidence intervals, or full code/index provenance. Reranking is conditional on a shared dense top-15 pool; candidate-generation recall is not isolated from ranking effects.

The gates use substring overlap, distance thresholds, and lexical temporal phrases. These rules can reject supported questions or accept weakly related candidates. The groundedness script tests lexical overlap, not question relevance, answer correctness, or semantic entailment. Citation metadata and limited alignment tests do not establish that a page supports an answer claim. No zero-hallucination or citation-guarantee conclusion follows.

The index represents 83 source filenames, whereas the inventory lists 86 PDFs; three named source PDFs are absent from the checked-in index. Although the saved groundedness artifact has the same chunk and filename counts, it has no digest tying it to the current index. Retrieval and gate JSONs lack benchmark commit/index digest; the groundedness JSON also lacks provider/model/generation mode. Exact computational reproduction is consequently limited.

External hosted LLM, translation, and CPCB services may be unavailable or change. CPCB coverage is limited to five configured stations, and routed readings are not necessarily fresh or complete. External translation can transmit text when enabled. Configured language and voice identifiers are not a language-quality evaluation. No human participants, learning outcomes, usability, awareness, trust, or behavior change were measured. No physical robot implementation or evaluation is reported. The literature review is non-exhaustive, R1 has conflicting author metadata between its PDF title block and publisher citation field, and R7 remains OnlineFirst without final issue assignment in the checked publisher record.

## VIII. CONCLUSION AND FUTURE WORK

This paper documents a source-grounded conversational prototype integrated with a digital mascot and reports three small saved engineering evaluations. In the 30-query set, overview-aware reranking increased MRR@5 relative to B/C while slightly reducing recall; all configurations had the same P@5. The selected evidence-gate set showed expected decisions in 20 cases. The 70/70 sentence result is a lexical heuristic classification, while citation checks cover metadata and limited alignment only. These findings describe implementation behavior and do not establish semantic faithfulness, general safety, or educational impact.

Future work should version benchmark code and index snapshots, evaluate candidate recall separately, use larger independently annotated held-out sets, and perform claim-level citation adjudication. Separate tests are needed for CPCB availability and data semantics, translation quality and data handling, voice operation, usability, and learning outcomes. These are proposed evaluations, not results of the present study.

## REFERENCES

[1] Consortium of Seven Indian Institutes of Technology, *Ganga River Basin Management Plan: Main Plan Document*, prepared for the Ministry of Environment and Forests, Government of India, Jan. 2015. National Mission for Clean Ganga report record: https://nmcg.nic.in/Grbmpreports_vol_1.aspx.

[2] P. Lewis *et al*., “Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks,” in *Advances in Neural Information Processing Systems*, vol. 33, pp. 9459–9474, 2020. [Online]. Available: https://arxiv.org/abs/2005.11401.

[3] J. Narmada, Dr. A. C. Priya Ranjani, K. Sruthi, P. Harshitha, D. Suchitha, and D. Veera Reddy, “AI-Powered Chacha Chaudhary Mascot for Ganga Conservation Awareness,” *Metallurgical and Materials Engineering*, vol. 31, no. 5, pp. 761–766, 2025, doi: 10.63278/mme.vi.1631. Author order follows the published PDF title-block byline; the publisher’s “How to Cite” field differs. Publisher record: https://metall-mater-eng.com/index.php/home/article/view/1631.

[4] A. Ganguly, N. Mehjabin, A. Malik, and A. Johri, “Conversational AI agents in education: An umbrella review of current utilization, challenges, and future directions for ethical and responsible use,” *AI and Ethics*, vol. 6, art. 72, 2026, doi: 10.1007/s43681-025-00916-0.

[5] H. Yusuf, A. Money, and D. Daylamani-Zad, “Pedagogical AI Conversational Agents in Higher Education: A Conceptual Framework and Survey of the State of the Art,” *Educational Technology Research and Development*, vol. 73, pp. 815–874, 2025, doi: 10.1007/s11423-025-10447-4.

[6] X. Wang and X. Li, “Designing a flipped AI-chatbot learning module to support students’ environmental literacy development: A Fuzzy Delphi Method,” *PLOS ONE*, vol. 21, no. 3, Art. no. e0345027, 2026, doi: 10.1371/journal.pone.0345027.

[7] X. Wang, Z. Zainuddin, C. H. Leng, W. Dong, and X. Li, “Evaluating the efficacy of ChatGPT in environmental education: Findings from heuristic and usability assessments,” *On the Horizon: The International Journal of Learning Futures*, vol. 33, no. 2, pp. 165–185, 2025, doi: 10.1108/OTH-11-2024-0079.

[8] N. L. Schroeder, S. Zhang, C. D. Jaldi, J. R. Gladstone, A. A. López, and E. Dorley, “Virtual Characters Help K–12 Students Learn and Improve Motivation: A Meta-Analysis,” *Review of Educational Research*, OnlineFirst, 2025, doi: 10.3102/00346543251389930.

[9] L. Dai, M. M. Jung, M. Postma, and M. M. Louwerse, “A systematic review of pedagogical agent research: Similarities, differences and unexplored aspects,” *Computers & Education*, vol. 190, Art. no. 104607, 2022, doi: 10.1016/j.compedu.2022.104607.

[10] Y. Tao, G. Zhang, D. Zhang, F. Wang, Y. Zhou, and T. Xu, “Exploring Persona Characteristics in Learning: A Review Study of Pedagogical Agents,” *Procedia Computer Science*, vol. 201, pp. 87–94, 2022, doi: 10.1016/j.procs.2022.03.014.

[11] N. L. Schroeder, O. O. Adesope, and R. B. Gilbert, “How Effective are Pedagogical Agents for Learning? A Meta-Analytic Review,” *Journal of Educational Computing Research*, vol. 49, no. 1, pp. 1–39, 2013, doi: 10.2190/EC.49.1.a.

[12] N. Reimers and I. Gurevych, “Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks,” in *Proc. EMNLP-IJCNLP*, pp. 3982–3992, 2019, doi: 10.18653/v1/D19-1410.

[13] W. Wang, F. Wei, L. Dong, H. Bao, N. Yang, and M. Zhou, “MiniLM: Deep Self-Attention Distillation for Task-Agnostic Compression of Pre-Trained Transformers,” in *Advances in Neural Information Processing Systems*, vol. 33, pp. 5776–5788, 2020.

[14] Sentence-Transformers, “all-MiniLM-L6-v2,” Hugging Face model card, accessed Oct. 20, 2026. [Online]. Available: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2.
