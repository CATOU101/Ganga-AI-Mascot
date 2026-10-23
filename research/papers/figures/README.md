# Reproducible result figures

`generate_figures.py` reads the saved benchmark JSON and JSONL datasets under `research/benchmark/`. It verifies each dataset SHA-256 against the corresponding result metadata and writes `figure_data.json` plus three vector PDF plots. It does not call the retrieval pipeline, hosted models, translation services, CPCB endpoints, or rerun any benchmark.

Run from any directory with Python 3 standard library:

```sh
python3 research/papers/figures/generate_figures.py
```

Inputs and transformations:

- `retrieval_ablation_results.json` / `domain_queries_30.jsonl`: production-gated P@5, R@5, MRR@5 and category MRR@5; retrieval categories rerank a shared dense top-15 pool.
- `evidence_gate_results.json` / `evidence_gate_queries_20.jsonl`: counts of matching selected-set decisions by group.
- `groundedness_results.json` / `groundedness_queries_20.jsonl`: provenance values are recorded in derived data for traceability; no combined groundedness/citation accuracy plot is generated because these checks have different definitions and denominators.

The script emits `fig1_retrieval_ablation.pdf`, `fig2_category_mrr.pdf`, and `fig3_evidence_gate.pdf`. Figure values are read from the existing aggregate JSON; raw benchmark files are not changed. The saved artifacts omit benchmark code revision and index digest, and the groundedness artifact omits provider/model/generation mode, so the plotted results are not an independent reproduction.
