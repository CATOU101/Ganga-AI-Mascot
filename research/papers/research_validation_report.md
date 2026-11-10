# Research Paper Validation Report

**Review date:** 2026-10-20
**Repository revision at review:** `fc18b6fa85cdb4c725cde64b845dfb9d61ef040d` on `main`
**Outcome:** The manuscript source and evidence figures are prepared, but the IEEE PDF was not rendered. Exact eight-page compliance is unverified and remains incomplete.

## Scope and sources inspected

The existing master manuscript was revised in place. Review covered `research/paper_workplan.md`, `research/research_gap.md`, `research/research_log.md`, `research/mathematical_formulation.md`, `research/implementation_and_evaluation.md`, `research/technical_baseline.md`, `research/literature_review.md`, benchmark reports, saved JSON/JSONL artifacts and the benchmark scripts. Implementation checks covered `brain/chunking.py`, `brain/embeddings.py`, `brain/vector_store.py`, `brain/retriever.py`, `brain/generator.py`, `brain/rag_pipeline.py`, and the integration controller and CPCB service. Existing Brain and integration tests were inspected as implementation context; no test suite or benchmark experiment was run.

The paper title is **AI-Powered Interactive Digital Mascot for Namami Gange Awareness & River-People Connectivity**. Section II is exactly **II. EXISTING WORKS**. Current-paper author, affiliation, and contact fields remain visibly marked for completion from verified institutional records. No names were inferred from the cited prior mascot paper.

## Implementation facts checked

- The index stores 384-dimensional vectors. The reported semantic path calls ChromaDB's built-in ONNX `DefaultEmbeddingFunction` for the named `all-MiniLM-L6-v2` model. The checked-in model archive hash is recorded in the index provenance; it does not establish equivalence to a remote model-card revision. Sentence-BERT and MiniLM citations are methodological background, not packages directly called by the application.
- The vector store orders dense candidates by NumPy Euclidean distance. The benchmark requests up to 15 candidates; the production retriever returns up to five accepted hits by default. The tested lexical and hybrid configurations rerank this shared dense pool.
- The production score matches the code: reciprocal distance term, 0.5 lexical overlap, and a 0.25 overview boost for broad Ganga/river queries. The evidence gate uses pool coverage 0.60, default semantic distance cutoff 1.15 (local-hash cutoff 1.35), and a 0.15 top-hit overlap check for queries with more than one extracted keyword. These are heuristics, not confidence or semantic-support guarantees. Benchmark ties are sorted by score then distance; production sorting uses score and retains incoming order for exact score ties.
- Chunking uses a 1,400-character target and 180-character overlap. Short chunks below 120 characters are merged into the preceding chunk where one exists; the first chunk can remain short and oversized paragraphs are not split.
- Hosted generation is reached after retrieval and evidence acceptance. Default provider order is Groq then OpenRouter, with one attempt per configured provider before extractive fallback. Evidence input is capped at 6,000 characters; the separate output-token cap is 700. Citation records are assembled from retrieved metadata rather than generated citation text.
- The Brain's current-information response is separate from CPCB routing. The integration has a CPCB path for five configured stations; external routing does not assure availability or freshness. The UI also has a quiz, multilingual paths, and voice adapters. Configured Edge TTS voice IDs cover English, Hindi, Kannada, and Tamil; Windows SAPI fallback is limited to English and Hindi. These settings are not speech-quality validation. External translation may transmit text when enabled.

## Reference audit

Statuses below use the reference audit recorded in `research/research_log.md` and the primary-source links listed there. R7's publisher record was reopened on 2026-10-20; it still identifies the article as OnlineFirst, with no final volume/issue displayed. The R1 publisher page was inaccessible to the current browser check, so its unresolved conflict remains documented using the prior PDF and publisher-record audit.

| Paper ref. | Status | Verification source and result |
|---|---|---|
| [1] | VERIFIED | National Mission for Clean Ganga's [GRBMP report record](https://nmcg.nic.in/Grbmpreports_vol_1.aspx) and the local report title page support the Main Plan Document citation and consortium attribution. |
| [2] | VERIFIED | [Official NeurIPS proceedings record](https://proceedings.nips.cc/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html) and [arXiv record](https://arxiv.org/abs/2005.11401) support the RAG title, authors, year, volume, and pages. |
| [3] | UNRESOLVED | The cited [publisher article record](https://metall-mater-eng.com/index.php/home/article/view/1631) and [published PDF](https://metall-mater-eng.com/index.php/home/article/download/1631/951/5510) support the title and publication details recorded in the research log. The reference preserves the PDF title-block byline, while the publisher “How to Cite” field names Dr. Preethi Jeevani instead of Dr. A. C. Priya Ranjani. Do not resolve or reorder this author conflict without authoritative clarification. DOI: `10.63278/mme.vi.1631`. |
| [4] | VERIFIED | [Springer Nature record](https://link.springer.com/article/10.1007/s43681-025-00916-0) supports authors, title, DOI, volume 6, article 72, and 2026 volume citation. |
| [5] | VERIFIED | [Springer Nature record](https://link.springer.com/article/10.1007/s11423-025-10447-4) supports authors, title, journal, volume, pages, year, and DOI. |
| [6] | VERIFIED | [PLOS ONE record](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0345027) supports authors, title, volume/issue, article number, year, and DOI. |
| [7] | VERIFIED | [Emerald/DOI-linked publisher record](https://doi.org/10.1108/OTH-11-2024-0079) supports authors, title, journal, volume/issue, pages, year, and DOI. |
| [8] | UNRESOLVED | The [SAGE/AERA record](https://journals.sagepub.com/doi/10.3102/00346543251389930) confirms authors, title, DOI, and first-online date of 2025-11-29. On 2026-10-20 it still labels the article OnlineFirst and shows no final volume or issue. The paper cites it as OnlineFirst and does not treat PDF pagination as issue pagination. |
| [9] | VERIFIED | [Elsevier ScienceDirect record](https://www.sciencedirect.com/science/article/pii/S0360131522001786) supports authors, title, journal, volume, article number, year, and DOI. |
| [10] | VERIFIED | [Elsevier proceedings record](https://www.sciencedirect.com/science/article/pii/S1877050922004264) and [DOI record](https://doi.org/10.1016/j.procs.2022.03.014) support authors, title, venue, volume, pages, year, and DOI. |
| [11] | VERIFIED | [SAGE article record](https://journals.sagepub.com/doi/10.2190/EC.49.1.a) supports authors, title, journal, volume/issue, pages, year, and DOI. |
| [12] | VERIFIED | [ACL Anthology record](https://aclanthology.org/D19-1410/) supports the Sentence-BERT paper's authors, title, conference, pages, year, and DOI. |
| [13] | VERIFIED | [Official NeurIPS record](https://proceedings.neurips.cc/paper/2020/hash/3f5ee243547dee91fbd053c1c4a845aa-Abstract.html) supports the MiniLM paper's authors, title, proceedings, volume, pages, and year. |
| [14] | VERIFIED | The [Hugging Face model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) supports information about the named checkpoint. It is not evidence that the local ONNX archive matches any particular remote revision. |

References [1]–[14] appear in first-citation order; all are cited and all citation keys/labels resolve in the IEEE source. The original earlier paper draft referenced in prior editorial correspondence was not present in the repository during its earlier audit, so a complete reference-by-reference reconciliation against that absent file remains unavailable.

## Benchmark evidence and figures

The figure script reads saved artifacts only. It validates the dataset SHA-256 values and query counts, checks reported retrieval aggregates, and derives the gate plot from stored outcomes. It does not run retrieval, generation, or a new experiment.

| Evaluation | Saved evidence | Values represented |
|---|---|---|
| Retrieval ablation | `research/benchmark/retrieval_ablation_results.json`; dataset `domain_queries_30.jsonl`; SHA-256 `66f6df3f8758b3e50ff8f6f5373bd354f98a82eb8e6bbf31dd8c84f38923a999`; 30 queries, 42 unique annotated gold chunk IDs | A: P@5 0.0533, R@5 0.1278, MRR@5 0.1083. B: 0.0533, 0.1333, 0.1261. C: 0.0533, 0.1333, 0.1261. D: 0.0533, 0.1278, 0.1444. Category MRR@5 is A: 0.2750/0.0500/0.0000; B and C: 0.3033/0.0500/0.0250; D: 0.3333/0.0500/0.0500 (broad/technical/governance). |
| Evidence gate | `research/benchmark/evidence_gate_results.json`; dataset `evidence_gate_queries_20.jsonl`; SHA-256 `f5d0d77a75a8ce9ec29a0798486eeca3a89649b838aad4324d1a5e09ce288ca2`; 20 selected queries | 10/10 labeled answerable accepted; 5/5 out-of-domain rejected; 5/5 dynamic examples intercepted by the Brain temporal fallback. This set does not test the separate CPCB route or establish unseen-query safety. |
| Groundedness and citation checks | `research/benchmark/groundedness_results.json`; dataset `groundedness_queries_20.jsonl`; SHA-256 `8755cefa4455c31e8c24c858b8ac7113e80657a3a29808488f346d9007b51fcb`; 20 queries | 70/70 sentences pass the implemented lexical heuristic; 56/56 citation metadata checks and 56/56 limited source-or-page alignment checks pass; exact gold-document overlap occurs for 10/20 questions. The script accepts sentences of three words or fewer automatically. It does not measure whether an answer addresses its question, factual correctness, or semantic entailment; lexical overlap can accept irrelevant or partly unrelated text. No semantic-faithfulness or zero-hallucination conclusion is made. |

Figures generated by `research/papers/figures/generate_figures.py`:

1. `fig1_retrieval_ablation.pdf` — overall P@5, R@5, and MRR@5 for A–D.
2. `fig2_category_mrr.pdf` — broad, technical, and governance MRR@5 for A–D, including zero values.
3. `fig3_evidence_gate.pdf` — observed decisions and denominators for the selected gate groups.

Each figure is one-page vector PDF. The figure-generation README records how to reproduce them. Figure 4 was omitted because the lexical, metadata, alignment, and gold-overlap checks have different meanings and denominators and could be misleading if presented as a common accuracy plot.

### Corpus and provenance limits

Existing artifacts distinguish 86 source PDFs, 4,609 pages, 1,111 approved/retained sections, and a checked-in index with 4,085 chunks across 83 source filenames. Three named source PDFs are absent from the index. The checked-in manifest identifies its current chunk/vector snapshot with SHA-256 values `02757645cb613a703ef128dcc3ecb45c0a0d2dd85ba1ddc072eac96924c6673a` and `ed0ec6e081d9e806e46c40bad57a2ea6c237a88327620598f320e62f7c16c455`; the model archive SHA-256 is `913d7300ceae3b2dbc2c50d1de4baacab4be7b9380491c27fab7418616a16ec3`. The saved result JSONs do not bind their runs to these index digests or record the benchmark code commit. The groundedness JSON also omits generator/provider/model/mode. Current repository HEAD is not asserted as the benchmark code revision.

## Claims corrected or qualified

- The manuscript distinguishes dense candidate retrieval from reranking and does not describe lexical configuration B as corpus-wide search.
- Heuristic gate and lexical groundedness findings are confined to their selected query sets. The 70/70 count is not framed as relevance, correctness, entailment, answer quality, or safety.
- Citation checks are described as metadata and limited source-or-page alignment checks; they do not establish claim support.
- The retrieval result discussion reports the MRR/recall trade-off rather than a uniform win.
- Voice IDs are described as configured settings, not proof of reliable live speech across environments. CPCB routing, translation, and hosted generation are described with their external-service limitations.
- The paper does not claim educational impact, general safety, or broad generalization. The administrative project identifier is absent from the master and IEEE source.

## Build and validation results

| Check | Result |
|---|---|
| `python3 research/papers/figures/generate_figures.py` | PASS. Three dataset hashes and counts validated; all three PDFs and `figure_data.json` generated from saved artifacts. |
| Source-structure check | PASS after correcting the checker to account for citation ranges and LaTeX groups spanning lines. Confirmed exact title, required Section II, no administrative identifier in paper sources, three in-text figure references, 14 ordered and resolved citations, balanced environments/braces, and resolved labels. |
| `pdfinfo` on the three generated figure PDFs | PASS. Each is one page: 516 x 205 pt, 516 x 188 pt, and 258 x 155 pt respectively. |
| `pdftotext` checks on figure PDFs | PASS. Extracted metric labels and values match the saved artifacts, including category zero and 10/10, 5/5, 5/5 gate outcomes. |
| IEEE LaTeX build | NOT RUN: `pdflatex`, `latexmk`, `xelatex`, `lualatex`, `tectonic`, `kpsewhich`, `bibtex`, and `biber` are not on `PATH`. Compiler version: unavailable. |
| Installation search | No compiler executable found in `/Library/TeX/texbin`, `/usr/local/texlive`, `/opt/homebrew/bin`, `/usr/local/bin`, the user's TinyTeX locations, or common TeX paths; no `IEEEtran.cls` found in the checked common TeX roots. Homebrew exists at `/opt/homebrew`, but its Cellar has no TeX distribution or Tectonic package. MacPorts and Conda are unavailable. |
| Main-paper PDF and page count | No `main.pdf` exists in `research/papers/ieee_submission/`; no build command ran, so rendered page count is unavailable. Exactly-eight-page compliance is unmet/unverified. |
| Main-paper visual layout, overflow, and page inspection | NOT COMPLETED because no IEEE PDF could be compiled. Figure PDFs were inspected separately; this does not verify the manuscript layout. |
| Application tests and benchmark experiments | NOT RUN; this task's deliverables were paper and figure assets, and no new experimental campaign was authorized. |
| `git diff --check` | PASS after all text deliverables were written; no whitespace errors. |

Compiler discovery commands included `command -v` checks for the tools listed above and read-only checks of common TeX locations and `/opt/homebrew/Cellar`. A Homebrew inventory probe (`brew list --versions`) attempted to refresh its cached package API and reported `packages.arm64_tahoe.jws.json: update failed, falling back to cached version`, followed by an `Operation not permitted` cache-write error. The probe yielded no installed package inventory; direct read-only Cellar inspection found no TeX packages. No software was installed and no system configuration was changed.

Commands used for the checks that ran:

```sh
python3 research/papers/figures/generate_figures.py
pdfinfo research/papers/figures/fig1_retrieval_ablation.pdf | rg '^(Pages|Page size):'
pdfinfo research/papers/figures/fig2_category_mrr.pdf | rg '^(Pages|Page size):'
pdfinfo research/papers/figures/fig3_evidence_gate.pdf | rg '^(Pages|Page size):'
pdftotext research/papers/figures/fig1_retrieval_ablation.pdf - | rg '0\.0533|0\.1278|0\.1083|0\.1333|0\.1261|0\.1444'
pdftotext research/papers/figures/fig2_category_mrr.pdf - | rg '0\.2750|0\.3033|0\.3333|0\.0500|0\.0250|0\.0000'
pdftotext research/papers/figures/fig3_evidence_gate.pdf - | rg '10/10|5/5'
git diff --check
```

The source-structure, dataset-hash, reference-order, and derived-data checks were run as inline Python 3 standard-library validation; no validation script was saved outside the reproducible figure generator.

The master source is an editable Markdown manuscript. `research/papers/ieee_submission/main.tex` uses the IEEE conference `IEEEtran` class, but this system has no compiler or class-discovery tool with which to render or validate a final PDF. The safe next step is to use an already provisioned TeX environment that provides `IEEEtran.cls`, or have the user approve installing a TeX distribution that includes the IEEE conference class; no installation was attempted. Then run the documented two-pass `pdflatex` build, inspect every page, and iterate to exactly eight pages before claiming completion.

## Changed and created files

- Updated: `research/papers/venue_neutral_master_manuscript.md`.
- Added IEEE source and instructions: `research/papers/ieee_submission/main.tex`, `research/papers/ieee_submission/README.md`.
- Added reproducible figure assets and instructions: `research/papers/figures/generate_figures.py`, `research/papers/figures/figure_data.json`, `research/papers/figures/README.md`, `fig1_retrieval_ablation.pdf`, `fig2_category_mrr.pdf`, and `fig3_evidence_gate.pdf`.
- Added: `research/papers/research_validation_report.md`.
- No raw benchmark result, application source, or research-supporting document was modified.

## Remaining before submission

1. Supply the present paper's verified author and affiliation details.
2. Resolve the base mascot paper's conflicting author metadata with the publisher; preserve the PDF title-block byline unless authoritative evidence resolves the conflict.
3. Recheck R7 for final issue metadata if it becomes available.
4. Record benchmark code revision, evaluated index identity, and groundedness generation provenance if reliable run records exist; do not infer them from current repository state.
5. Compile the IEEE source with the official conference class, inspect the complete PDF, and iterate to exactly eight pages without reducing required template typography or omitting limitations.

**Readiness:** The paper is not ready for final submission or a claim of exactly eight pages. It can proceed to author completion and a real IEEE build; unresolved bibliography and provenance items remain explicit.

## Editable Word deliverable

**Output:** `research/papers/ieee_submission/Ganga_AI_Mascot_IEEE_Paper.docx`

The editable DOCX was generated directly from `research/papers/venue_neutral_master_manuscript.md` with `python-docx` 1.2.0 using the workspace Python 3.12.13 runtime. `research/papers/ieee_submission/main.tex` and the Markdown manuscript were not changed for this deliverable. No LaTeX build was attempted. The title and all required sections, including the exact heading `II. EXISTING WORKS`, are present. The author/affiliation placeholder is retained. No `PRJ_316` text appears in the DOCX.

The three existing benchmark-derived figure PDFs were rasterized to temporary PNGs and embedded as images; all three captions are included. Equations are editable Unicode math text, rather than screenshots. The two result tables are editable, pipe-separated text rows with captions. Native Word table objects collapsed in the available renderer, so the document uses aligned text rows to keep the values readable; this is a semantic/accessibility limitation compared with native table structures.

Validation performed:

- Opened the output with `python-docx` and checked DOCX ZIP integrity: PASS.
- Checked the required title, abstract, index terms, all eight numbered sections, and References: PASS.
- Checked numbered references [1]–[14], absence of `PRJ_316`, three embedded figure parts, and three figure captions: PASS.
- Rendered with the installed artifact-tool renderer (version 2.7.2; Node v24.14.0) to `/private/tmp/ganga_docx_render`; five page images were produced. Each rendered page was visually inspected. The three figures and result values are visible, and no clipping or missing figure was observed.
- `git diff --check`: PASS.

Commands used for DOCX creation and visual validation:

```sh
/Users/madhavan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 /private/tmp/build_ganga_ieee_docx.py
sips -s format png --resampleWidth 2200 research/papers/figures/fig1_retrieval_ablation.pdf --out /private/tmp/fig1_retrieval_ablation.png
sips -s format png --resampleWidth 2200 research/papers/figures/fig2_category_mrr.pdf --out /private/tmp/fig2_category_mrr.png
sips -s format png --resampleWidth 1800 research/papers/figures/fig3_evidence_gate.pdf --out /private/tmp/fig3_evidence_gate.png
/Users/madhavan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 /private/tmp/render_docx.py research/papers/ieee_submission/Ganga_AI_Mascot_IEEE_Paper.docx --output_dir /private/tmp/ganga_docx_render --renderer artifact-tool
git diff --check
```

The five-page count is for the rendered DOCX only; it is not an IEEE PDF page count and does not establish compliance with an eight-page PDF requirement. The manuscript's existing author, reference, corpus/index, and benchmark provenance limitations listed above remain unresolved.
