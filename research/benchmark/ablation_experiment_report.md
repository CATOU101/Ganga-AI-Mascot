# Retrieval Ablation Experiment Report: Ganga AI Mascot (PRJ_316)

**Date:** 2026-10-19T12:26:43Z  
**Python Runtime:** 3.13.3 (macOS-26.7.1-arm64-arm-64bit-Mach-O)  
**Dataset SHA-256:** `66f6df3f8758b3e50ff8f6f5373bd354f98a82eb8e6bbf31dd8c84f38923a999`  
**Corpus Size:** 4,085 chunks (86 GRBMP PDFs)  

---

## 1. Overview and Research Question

> **Research Question (RQ1):** Within a shared dense-retrieved top-15 candidate pool, how do dense, lexical-overlap, hybrid, and overview-boosted reranking configurations compare on this curated GRBMP query set?

**Evaluation scope:** The benchmark first obtains up to 15 dense candidates per query and ranks each configuration within that same candidate pool. Config B is therefore lexical-overlap reranking of dense candidates, not a full-corpus lexical search. In the production-gated condition, all configurations also use the candidate-coverage and distance gates. These results do not compare independent full-corpus retrieval systems.

---

## 2. Overall Benchmark Results (All 30 Queries)

### A. Production Gated Pipeline (Primary)
Applies pre-rerank candidate pool coverage check ($\ge 0.60$), Euclidean distance cutoff ($d \le 1.15$), and post-rerank top-hit overlap gate ($\ge 0.15$).

| Configuration | Description | Precision@5 | Recall@5 | MRR@5 | Total Latency (s) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Config A** | Dense-Score Reranking (Euclidean Proximity) | **0.0533** | **0.1278** | **0.1083** | 2.00s |
| **Config B** | Lexical-Overlap Reranking (within dense pool) | **0.0533** | **0.1333** | **0.1261** | 1.99s |
| **Config C** | Unweighted Hybrid (Dense + 0.5*Lexical) | **0.0533** | **0.1333** | **0.1261** | 2.01s |
| **Config D** | Proposed Hybrid (Dense + 0.5*Lexical + 0.25*OverviewBoost) | **0.0533** | **0.1278** | **0.1444** | 1.96s |

### B. Ungated Reranking (No Evidence-Gate Rejections)
Ranks the same dense top-15 candidate pool by each configured score without early-exit gate rejections. It is not a full-corpus retrieval comparison.

| Configuration | Description | Precision@5 | Recall@5 | MRR@5 | Total Latency (s) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Config A** | Dense-Score Reranking (Euclidean Proximity) | 0.0600 | 0.1444 | 0.1194 | 2.02s |
| **Config B** | Lexical-Overlap Reranking (within dense pool) | 0.0533 | 0.1333 | 0.1261 | 1.97s |
| **Config C** | Unweighted Hybrid (Dense + 0.5*Lexical) | 0.0533 | 0.1333 | 0.1261 | 1.97s |
| **Config D** | Proposed Hybrid (Dense + 0.5*Lexical + 0.25*OverviewBoost) | 0.0533 | 0.1278 | 0.1444 | 2.03s |

---

## 3. Category-Level Performance (Production Gated)

| Configuration | Category | Precision@5 | Recall@5 | MRR@5 |
| :--- | :--- | :---: | :---: | :---: |
| Config A | Broad/Thematic | 0.1400 | 0.3333 | 0.2750 |
| Config A | Technical/Scientific | 0.0200 | 0.0500 | 0.0500 |
| Config A | Governance/Policy | 0.0000 | 0.0000 | 0.0000 |
| Config B | Broad/Thematic | 0.1200 | 0.3000 | 0.3033 |
| Config B | Technical/Scientific | 0.0200 | 0.0500 | 0.0500 |
| Config B | Governance/Policy | 0.0200 | 0.0500 | 0.0250 |
| Config C | Broad/Thematic | 0.1200 | 0.3000 | 0.3033 |
| Config C | Technical/Scientific | 0.0200 | 0.0500 | 0.0500 |
| Config C | Governance/Policy | 0.0200 | 0.0500 | 0.0250 |
| Config D | Broad/Thematic | 0.1200 | 0.2833 | 0.3333 |
| Config D | Technical/Scientific | 0.0200 | 0.0500 | 0.0500 |
| Config D | Governance/Policy | 0.0200 | 0.0500 | 0.0500 |

---

## 4. Key Empirical Findings

1. **Overall MRR@5 in this run:** In the production-gated condition, Config D has MRR@5 **0.1444**, compared with Config A **0.1083** and Config C **0.1261**. These are descriptive results on this 30-query set; no uncertainty estimate or repeated-run comparison is available.
2. **Broad/Thematic subset:** The saved result JSON reports Config D MRR@5 **0.3333**, Config A **0.2750**, and Config C **0.3033**. Config D's recall is **0.2833**, compared with **0.3000** for Config C. This descriptive difference does not establish a causal mechanism or prove that summaries moved to rank 1.
3. **Technical and Governance subsets:** Technical MRR@5 is **0.0500** for A, C, and D. Governance MRR@5 is **0.0000** for A, **0.0250** for C, and **0.0500** for D. Thus, the governance ranking is not identical between C and D.
4. **Interpretation limits:** The ungated aggregate recall for Config A is **0.1444**, compared with **0.1278** for D; ungated MRR@5 is **0.1194** for A and **0.1444** for D. These are single-run descriptive metrics over the same dense candidate pool, not evidence of statistical significance or general performance.

---

## 5. Reproduction command and provenance limits
The following command runs the benchmark with the current checkout and local vector index; it does not by itself reproduce the historical artifact unless code, index, configuration, and environment match the original run:
```bash
PYTHONPATH=. ./.venv/bin/python research/benchmark/run_retrieval_benchmark.py
```

The saved JSON records the dataset SHA-256, runtime version/platform, query count, and configuration labels. It does not record the code commit or a digest/version for the vector index and corpus. The report records 4,085 chunks and 86 source PDFs; the separate groundedness artifact records 4,085 chunks across 83 indexed document names. The available artifacts do not explain that count difference. Reported latency is one aggregate timing per configuration, without repeated-run variability or uncertainty estimates.
