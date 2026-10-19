# Metric Definitions: Ganga AI Mascot Retrieval Benchmark (PRJ_316)

**Project Title:** AI-Powered Interactive Digital Mascot for Namami Gange Awareness & River-People Connectivity  
**Repository:** `https://github.com/CATOU101/Ganga-AI-Mascot`  
**Dataset Reference:** `research/benchmark/domain_queries_30.jsonl`  
**Authoritative SHA-256 Hash:** `66f6df3f8758b3e50ff8f6f5373bd354f98a82eb8e6bbf31dd8c84f38923a999`  

---

## 1. Overview and Operational Scope

This document defines the mathematical models and aggregation rules for evaluating reranking over a shared dense-retrieved candidate pool from the curated Ganga River Basin Management Plan (GRBMP) index ($N = 4,085$ indexed chunks). The retrieval ablation runner obtains up to 15 dense candidates per query before applying each ranking configuration; Config B is therefore lexical reranking within that pool, not full-corpus lexical retrieval. Production-gated runs also apply candidate-coverage and distance filters.

All metrics are evaluated at cutoff rank $K = 5$, reflecting the production RAG pipeline parameter (`GANGA_BRAIN_TOP_K = 5`) defined in `brain/config.py`.

---

## 2. Mathematical Definitions

Let:
* $\mathcal{Q} = \{q_1, q_2, \dots, q_{|\mathcal{Q}|}\}$ denote the benchmark query collection ($|\mathcal{Q}| = 30$).
* For each query $q$, let $\mathcal{G}_q = \{c^*_{1}, c^*_{2}, \dots, c^*_{|\mathcal{G}_q|}\}$ denote the ground-truth set of gold evidence chunk IDs ($\mathcal{G}_q \subseteq \mathcal{C}_{\text{corpus}}$, $|\mathcal{G}_q| \ge 1$).
* Let $\mathcal{R}_q = \langle r_1, r_2, \dots, r_K \rangle$ denote the ordered sequence of top-$K$ candidate chunks retrieved by a retrieval configuration ($K = 5$).
* Let $\mathbb{I}[\cdot]$ denote the indicator function:
  $$\mathbb{I}[r_k \in \mathcal{G}_q] = \begin{cases} 1, & \text{if candidate chunk } r_k \text{ is in gold evidence set } \mathcal{G}_q \\ 0, & \text{otherwise} \end{cases}$$

---

### 2.1. Precision at Rank 5 (P@5)

**Operational Definition:**  
The proportion of top-5 retrieved chunks that are verified gold evidence chunks.

$$\text{P@5}(q) = \frac{1}{K} \sum_{k=1}^{K} \mathbb{I}[r_k \in \mathcal{G}_q] = \frac{|\{r_1, \dots, r_K\} \cap \mathcal{G}_q|}{5}$$

* **Range:** $\text{P@5}(q) \in [0.0, 1.0]$.
* **Interpretation:** Measures retrieval purity and context density. High precision minimizes extraneous noise in the LLM prompt context window.

---

### 2.2. Recall at Rank 5 (R@5)

**Operational Definition:**  
The proportion of gold evidence chunks that are successfully retrieved within the top-5 candidate positions.

$$\text{R@5}(q) = \frac{|\{r_1, \dots, r_K\} \cap \mathcal{G}_q|}{|\mathcal{G}_q|} = \frac{1}{|\mathcal{G}_q|} \sum_{k=1}^{K} \mathbb{I}[r_k \in \mathcal{G}_q]$$

* **Range:** $\text{R@5}(q) \in [0.0, 1.0]$.
* **Interpretation:** Measures retrieval completeness. High recall ensures that all necessary regulatory facts or multi-part evidence passages are provided to the generator.

---

### 2.3. Mean Reciprocal Rank at Rank 5 (MRR@5)

**Operational Definition:**  
The reciprocal of the rank position of the *first* relevant gold chunk in the retrieved sequence $\mathcal{R}_q$, truncated at rank $K = 5$.

$$\text{RR@5}(q) = \begin{cases} 
\frac{1}{k^*}, & \text{if } \exists k \in \{1, \dots, K\} \text{ such that } r_k \in \mathcal{G}_q, \text{ where } k^* = \min \{k \mid r_k \in \mathcal{G}_q\} \\ 
0.0, & \text{if no relevant chunk appears in the top } K \text{ positions} 
\end{cases}$$

* **Range:** $\text{RR@5}(q) \in \{1.0, 0.5, 0.333, 0.25, 0.20, 0.0\}$.
* **Interpretation:** Evaluates ranking effectiveness. Placing a gold chunk at Rank 1 yields $\text{RR} = 1.0$; missing all gold chunks in the top-5 positions yields $\text{RR} = 0.0$.

---

## 3. Boundary Conditions, Tie-Breaking, and Edge Cases

1. **Multiple Gold Chunks per Query:**
   * Queries in the benchmark possess between 1 and 3 gold chunks ($|\mathcal{G}_q| \in \{1, 2, 3\}$).
   * For **Precision@5**, every gold chunk retrieved in the top 5 increments the numerator by 1.
   * For **Recall@5**, the sum of retrieved gold chunks is normalized by $|\mathcal{G}_q|$.
   * For **MRR@5**, the score is determined strictly by the rank of the *first* relevant chunk encountered ($k^*$). Subsequent relevant chunks do not alter $\text{RR@5}(q)$.
2. **Duplicate Chunks in Retrieval Results:**
   * Chunks are guaranteed unique by primary key `chunk_id` in SQLite.
   * If any retrieval configuration returns duplicate chunk IDs, duplicates beyond the first occurrence are discarded and subsequent unique candidates are shifted forward to fill $K=5$.
3. **Zero-Hit / Empty Retrieval Handling:**
   * If a configuration rejects a query (e.g. via evidence gate) or returns fewer than 5 chunks, positions with no candidate are assigned non-matching dummy values ($\mathbb{I} = 0$).
   * If zero relevant chunks appear in the top 5:
     $$\text{P@5}(q) = 0.0, \quad \text{R@5}(q) = 0.0, \quad \text{RR@5}(q) = 0.0$$
4. **Tie behavior in the saved benchmark implementation:**
   * `run_retrieval_benchmark.py` sorts scored candidates by score descending and Euclidean distance ascending (`(score, -distance)` with reverse sorting). It does not apply a chunk ordinal as a secondary key. Candidates tied on both score and distance retain their incoming order, which is inherited from the vector-store candidate query and is not documented as stable. The vector-store implementation likewise does not promise a deterministic tie order. Therefore, the previous deterministic ordinal tie-breaking rule was inaccurate; exact ordering for complete ties is not guaranteed by the current implementation.

---

## 4. Aggregation Categories

Metrics are computed per query and reported as arithmetic means aggregated across four evaluation scopes:

$$\text{Mean Metric} = \frac{1}{|\mathcal{S}|} \sum_{q \in \mathcal{S}} \text{Metric}(q)$$

1. **Overall Benchmark:** All 30 queries ($|\mathcal{S}| = 30$).
2. **Category A (Broad / Thematic):** Queries `Q_BROAD_01` to `Q_BROAD_10` ($|\mathcal{S}| = 10$).
3. **Category B (Technical / Scientific):** Queries `Q_TECH_01` to `Q_TECH_10` ($|\mathcal{S}| = 10$).
4. **Category C (Governance / Policy):** Queries `Q_GOV_01` to `Q_GOV_10` ($|\mathcal{S}| = 10$).

---

## 5. Retrieval Configurations Evaluated in Ablation

The benchmark evaluates four ranking configurations over the same dense top-15 candidates per query from the 4,085-chunk index:

| Configuration ID | Name | Scoring Function ($S$) | Description |
| :--- | :--- | :--- | :--- |
| **Config A** | Dense-Score Reranking | $S_{\text{dense}}(q, c) = \frac{1.0}{1.0 + \|\mathbf{q} - \mathbf{d}_c\|_2}$ | Euclidean score over the shared dense-retrieved candidate pool. |
| **Config B** | Lexical-Overlap Reranking | $S_{\text{lexical}}(q, c) = overlap(q, c) = \frac{\sum \mathbb{I}[w \in c]}{|\mathcal{K}(q)|}$ | Keyword-overlap score over extracted query terms ($|w| \ge 3$, non-stopwords), applied only to the shared dense top-15 candidate pool. |
| **Config C** | Unweighted Hybrid Reranking | $S_{\text{unweighted}}(q, c) = \frac{1.0}{1.0 + \|\mathbf{q} - \mathbf{d}_c\|_2} + 0.5 \cdot overlap(q, c)$ | Linear combination of vector proximity and lexical overlap within the shared candidate pool. |
| **Config D** | Overview-Boosted Hybrid Reranking | $S_{\text{hybrid}}(q, c) = \frac{1.0}{1.0 + \|\mathbf{q} - \mathbf{d}_c\|_2} + 0.5 \cdot overlap(q, c) + 0.25 \cdot \mathbb{I}_{\text{overview}}(q, c)$ | Broad-query detection and overview boost applied to the shared candidate pool. |
