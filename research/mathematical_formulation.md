# Mathematical Formulation: Ganga AI Mascot (PRJ_316)

**Project ID:** PRJ_316  
**Project Title:** AI-Powered Interactive Digital Mascot for Namami Gange Awareness & River-People Connectivity  
**Status:** Implemented Mathematical Specification  
**Authoritative Baseline:** `56032d744b80695be7593c6f85e50d53c7c5a083`  

---

> [!NOTE]
> **Source-Grounded Mathematical Integrity:**  
> Every equation in this document corresponds directly to the active implementation in `brain/chunking.py`, `brain/embeddings.py`, `brain/vector_store.py`, `brain/retriever.py`, and `brain/generator.py`. The hybrid retrieval score is a deterministic engineering heuristic combining continuous metric-space distance with discrete term coverage and boolean query masks; it is **not** presented as a Bayesian posterior probability, calibrated confidence interval, or likelihood ratio.

---

## 1. Document Chunking and Segmentation

The text chunking algorithm processes reviewed sections to produce target-sized passages while preserving paragraph boundaries and semantic continuity where possible. A single paragraph longer than the target is not split and can produce an oversized chunk.

### Mathematical Formulation
Let a reviewed document section $S$ be represented as a raw character string of length $|S|$.
Text normalization produces a sanitized string $T$:
$$T = \text{norm}(S)$$
where $\text{norm}(\cdot)$ collapses consecutive spaces and carriage returns into single line breaks (`\n\n`).

The normalized text $T$ is partitioned into an ordered sequence of $M$ paragraphs:
$$P = \langle p_1, p_2, \dots, p_M \rangle, \quad p_m \in \text{split}(T, \text{"\textbackslash n\textbackslash s*\textbackslash n"})$$

A greedy sequential packing algorithm constructs chunks $\langle c_1, c_2, \dots, c_J \rangle$. Let $A_j$ denote the accumulator list of paragraphs for chunk $j$:
$$\text{len}(A_j) = \sum_{p \in A_j} |p| + 2(|A_j| - 1)$$

Paragraphs $p_m$ are appended to $A_j$ while:
$$\text{len}(A_j \cup \{p_m\}) \le L_{\text{target}}$$
where $L_{\text{target}} = 1,400$ characters.

When appending a paragraph to a non-empty accumulator would exceed the target, chunk $c_j$ is finalized as $c_j = \text{join}(A_j, \text{"\textbackslash n\textbackslash n"})$. The subsequent chunk $A_{j+1}$ is initialized with an overlap prefix $o_j$ extracted from the terminal suffix of $c_j$:
$$o_j = \text{suffix}(c_j, L_{\text{overlap}})$$
where $L_{\text{overlap}} = 180$ characters.

The target is not a hard maximum: if an individual paragraph exceeds $L_{\text{target}}$ while the accumulator is empty, the implementation keeps that paragraph intact, so the resulting chunk can exceed the target.

### Post-Processing Boundary Constraint (Sub-Minimum Repair)
If the final chunk $c_J$ satisfies $|c_J| < L_{\text{min}}$ (where $L_{\text{min}} = 120$ characters) and $J > 1$:
$$c_{J-1} \leftarrow \text{norm}(c_{J-1} \mathbin{\Vert} \text{"\textbackslash n\textbackslash n"} \mathbin{\Vert} c_J), \quad \text{and } c_J \text{ is discarded}$$

### Code Traceability
- **File:** `brain/chunking.py`
- **Functions:** `normalize_text` (lines 17–22), `split_section_text` (lines 24–56), `chunks_from_sections` (lines 58–81).
- **Parameters:** `target_chars=1400`, `overlap_chars=180`, `min_chunk_chars=120` (defined in `brain/config.py`, lines 30–32).
- **Assumptions & Limitations:** Chunking operates on raw character counts rather than BPE/WordPiece token counts. This ensures token-free, deterministic segmentation across Python environments without requiring external tokenizer libraries during indexing.

---

## 2. Semantic Embedding and Normalization

### Vector Embedding Mapping
Let $\mathcal{V}$ denote the vocabulary space of natural language text strings. The embedding function $\mathbf{e}: \mathcal{V} \to \mathbb{R}^d$ maps arbitrary text $t$ into a dense continuous representation of dimensionality $d = 384$:
$$\mathbf{z} = f_{\text{MiniLM}}(t) \in \mathbb{R}^{384}$$
where $f_{\text{MiniLM}}$ is the ONNX Runtime execution of `all-MiniLM-L6-v2`.

The resulting vector is $L_2$-normalized to project onto the unit hypersphere $\mathbb{S}^{383}$:
$$\mathbf{e}(t) = \frac{\mathbf{z}}{\|\mathbf{z}\|_2} = \frac{\mathbf{z}}{\sqrt{\sum_{k=1}^{384} z_k^2}}$$
such that $\|\mathbf{e}(t)\|_2 = 1.0$.

### Baseline Hash Embedding (Reproducibility Fallback)
When running without neural weights, `LocalHashEmbedding` computes a 384-dimensional bag-of-words vector using SHA-256 digests:
For each token $w \in \text{tokens}(t)$:
$$h = \text{SHA-256}(w), \quad \text{idx} = h[0:4] \pmod d, \quad s = \begin{cases} +1 & \text{if } h[4] \equiv 0 \pmod 2 \\ -1 & \text{otherwise} \end{cases}$$
$$\mathbf{v}_{\text{idx}} \leftarrow \mathbf{v}_{\text{idx}} + s, \qquad \mathbf{e}_{\text{hash}}(t) = \frac{\mathbf{v}}{\|\mathbf{v}\|_2}$$

### Code Traceability
- **File:** `brain/embeddings.py`
- **Classes:** `ONNXSemanticEmbedding` (lines 57–90), `LocalHashEmbedding` (lines 28–55).
- **Assumptions & Limitations:** The model truncates input text beyond 256 WordPiece tokens. Because chunk target sizes are 1,400 characters ($\approx 250\text{--}300$ words), semantic representations primarily capture the leading paragraphs of each chunk.

---

## 3. Candidate Vector Retrieval

Given an input user question $q$, the query vector is computed as:
$$\mathbf{q} = \mathbf{e}(q) \in \mathbb{R}^{384}, \quad \|\mathbf{q}\|_2 = 1.0$$

The active vector store maintains an immutable matrix of pre-computed chunk vectors:
$$\mathbf{D} \in \mathbb{R}^{N \times 384}, \quad N = 4,085$$
where each row $\mathbf{d}_i \in \mathbb{R}^{384}$ corresponds to chunk $i$, with $\|\mathbf{d}_i\|_2 = 1.0$.

### Distance Metric
The distance between the query vector $\mathbf{q}$ and document chunk $\mathbf{d}_i$ is computed as the Euclidean ($L_2$) distance:
$$dist(\mathbf{q}, \mathbf{d}_i) = \|\mathbf{q} - \mathbf{d}_i\|_2 = \sqrt{\sum_{k=1}^{384} (q_k - d_{i,k})^2}$$

*(Relation to Cosine Similarity)*: Because $\mathbf{q}$ and $\mathbf{d}_i$ are unit-normalized:
$$dist(\mathbf{q}, \mathbf{d}_i)^2 = \|\mathbf{q}\|_2^2 + \|\mathbf{d}_i\|_2^2 - 2 \langle \mathbf{q}, \mathbf{d}_i \rangle = 2 - 2 \cos(\mathbf{q}, \mathbf{d}_i)$$
$$dist(\mathbf{q}, \mathbf{d}_i) = \sqrt{2 \big(1 - \cos(\mathbf{q}, \mathbf{d}_i)\big)}$$
Thus, $dist(\mathbf{q}, \mathbf{d}_i) \in [0, 2]$, where $dist = 0$ corresponds to identity ($\cos = 1$) and $dist = \sqrt{2} \approx 1.414$ corresponds to orthogonality ($\cos = 0$).

### Candidate Partitioning
The system retrieves the top $K_{\text{cand}} = 15$ nearest chunks using an efficient partition:
$$\mathcal{C}_{\text{cand}} = \text{argpartition}_{i \in \{1, \dots, N\}} \big( dist(\mathbf{q}, \mathbf{d}_i), K_{\text{cand}} \big)$$

### Code Traceability
- **File:** `brain/vector_store.py` (`SQLiteVectorStore.query`, lines 329–356).
- **File:** `brain/retriever.py` (`Retriever.retrieve_candidates`, lines 108–113).
- **Parameters:** `candidate_top_k = 15` (defined in `brain/config.py`, line 34).

---

## 4. Lexical Processing and Keyword Extraction

### Tokenization and Stopword Filtering
Let the query string $q$ be tokenized into discrete alphanumeric words:
$$\mathcal{W}(q) = \text{regex\_match}\big(\text{"[A-Za-z0-9][A-Za-z0-9\_-]*"}, \text{lower}(q)\big)$$

The non-stopword query keyword set $\mathcal{K}(q)$ is defined as:
$$\mathcal{K}(q) = \big\{ w \in \mathcal{W}(q) \;\big|\; |w| \ge 3 \;\land\; w \notin \mathcal{S}_{\text{stopwords}} \big\}$$
where $\mathcal{S}_{\text{stopwords}}$ is an immutable set of 49 stop words and domain noise terms (`what`, `is`, `the`, `tell`, `knowledge`, `grbmp`, etc.).

### Candidate Pool Keyword Coverage (Pre-Rerank Gate 1)
To protect against out-of-domain or unsupported queries that accidentally match vector clusters, the system checks whether the query's keywords appear anywhere within the candidate pool $\mathcal{C}_{\text{cand}}$.

Let $\text{text\_corpus}(c)$ denote the concatenated lowercase text, title, and section metadata of candidate chunk $c$:
$$\text{text\_corpus}(c) = \text{lower}\big(\text{text}(c) \mathbin{\Vert} \text{" "} \mathbin{\Vert} \text{title}(c) \mathbin{\Vert} \text{" "} \mathbin{\Vert} \text{section}(c)\big)$$

The pool coverage ratio is:
$$pool\_coverage(q, \mathcal{C}_{\text{cand}}) = \frac{\big| \big\{ w \in \mathcal{K}(q) \;\big|\; \exists c \in \mathcal{C}_{\text{cand}}: w \text{ is a substring of } \text{text\_corpus}(c) \big\} \big|}{|\mathcal{K}(q)|}$$
*(Defined as $1.0$ if $\mathcal{K}(q) = \emptyset$)*.

**Gate Condition 1:**
$$\text{If } |\mathcal{K}(q)| > 0 \;\land\; pool\_coverage(q, \mathcal{C}_{\text{cand}}) < 0.60 \implies \text{Reject: return } (\text{False}, \emptyset)$$

### Code Traceability
- **File:** `brain/retriever.py`
- **Functions:** `extract_keywords` (lines 97–101), `rerank_and_filter` pool check (lines 127–135).
- **Parameters:** Stopwords set `STOPWORDS` (lines 18–26), threshold $0.60$ (line 133).

---

## 5. Candidate Distance Filtering and Hybrid Reranking

For all candidates $c \in \mathcal{C}_{\text{cand}}$ that pass Gate 1, individual filtering and scoring proceed as follows:

### 1. Distance Threshold Cutoff
$$\text{If } dist(\mathbf{q}, \mathbf{d}_c) > \theta_{\text{dist}} \implies \text{Discard candidate } c$$
where:
$$\theta_{\text{dist}} = \begin{cases} 1.15 & \text{if using semantic embedding (MiniLM)} \\ 1.35 & \text{if using baseline hash embedding} \end{cases}$$
*(Note: $dist \le 1.15$ corresponds to $\cos(\mathbf{q}, \mathbf{d}_c) \ge 1 - \frac{1.15^2}{2} = 1 - 0.661 = 0.339$)*.

### 2. Individual Lexical Overlap Ratio
For candidate $c$, the matched keyword count is:
$$n_{\text{match}}(q, c) = \sum_{w \in \mathcal{K}(q)} \mathbb{I}\big(w \text{ is a substring of } \text{text\_corpus}(c)\big)$$
The overlap ratio is:
$$overlap(q, c) = \begin{cases} \frac{n_{\text{match}}(q, c)}{|\mathcal{K}(q)|} & \text{if } |\mathcal{K}(q)| > 0 \\ 1.0 & \text{if } |\mathcal{K}(q)| = 0 \end{cases}$$

### 3. Broad-Query Overview Boost
To prevent broad, general questions from matching narrow, obscure technical subsections, an overview boost is conditionally applied.

**Broad Query Predicate:**
$$is\_broad(q) \iff \big(\text{"ganga"} \in \text{lower}(q) \;\lor\; \text{"river"} \in \text{lower}(q)\big) \;\land\; \big(\mathcal{W}(q) \cap \mathcal{T}_{\text{specific}} = \emptyset\big)$$
where $\mathcal{T}_{\text{specific}}$ is a curated set of 38 technical topic terms (`dolphin`, `stp`, `tannery`, `bod`, `cod`, `pesticide`, etc.).

**Core Overview Document Predicate:**
$$is\_overview(c) \iff \text{file}(c) \in \mathcal{F}_{\text{core}} \;\lor\; \text{title}(c) \in \mathcal{T}_{\text{core}} \;\lor\; \big(\text{section}(c) \in \mathcal{S}_{\text{overview}} \;\land\; \text{has\_summary\_title}(c)\big)$$
where $\mathcal{F}_{\text{core}}$ includes `13_GRBMP - MPD.pdf`, `27_GRBMP - Extended Summary.pdf`, `Vision Ganga Eng_Compressed.pdf`, etc.

**Overview Boost Indicator:**
$$\mathbb{I}_{\text{overview}}(q, c) = \begin{cases} 1 & \text{if } is\_broad(q) \land is\_overview(c) \\ 0 & \text{otherwise} \end{cases}$$

### 4. Hybrid Scoring Function
The total hybrid score $S_{\text{hybrid}}(q, c)$ is computed as:
$$S_{\text{hybrid}}(q, c) = \underbrace{\frac{1.0}{1.0 + dist(\mathbf{q}, \mathbf{d}_c)}}_{\text{Continuous Semantic Proximity}} + \underbrace{0.5 \cdot overlap(q, c)}_{\text{Discrete Lexical Overlap}} + \underbrace{0.25 \cdot \mathbb{I}_{\text{overview}}(q, c)}_{\text{Query-Conditioned Overview Boost}}$$

### Score Bounds
- The semantic component $\frac{1}{1 + dist} \in [\frac{1}{1 + 1.15}, \frac{1}{1 + 0}] \approx [0.465, 1.000]$.
- The lexical component $0.5 \cdot overlap \in [0.000, 0.500]$.
- The overview component $0.25 \cdot \mathbb{I} \in \{0.000, 0.250\}$.
- Total possible score range: $S_{\text{hybrid}}(q, c) \in [0.465, 1.750]$.

### Code Traceability
- **File:** `brain/retriever.py`
- **Functions:** `is_broad_ganga_query` (lines 64–73), `is_core_overview_hit` (lines 76–86), scoring loop (lines 138–165).
- **Parameters:** Distance threshold $1.15$ (`evidence_max_distance`, `brain/config.py`, line 35), lexical weight $0.5$, overview weight $0.25$.

---

## 6. Evidence Quality Gate (Post-Rerank Gate 2)

After computing $S_{\text{hybrid}}(q, c)$ for all surviving candidates, candidates are sorted in descending order:
$$\langle c_{(1)}, c_{(2)}, \dots, c_{(U)} \rangle \quad \text{such that } S_{\text{hybrid}}(q, c_{(1)}) \ge S_{\text{hybrid}}(q, c_{(2)}) \ge \dots$$

Let $c^* = c_{(1)}$ denote the highest-scoring candidate.

**Gate Condition 2 (Top-Hit Relevance Check):**
$$\text{If } |\mathcal{K}(q)| > 1 \;\land\; overlap(q, c^*) < \theta_{\text{overlap}} \implies \text{Reject: return } (\text{False}, \emptyset)$$
where $\theta_{\text{overlap}} = 0.15$ (`min_keyword_overlap`).

If Gate 2 passes, the retrieval pipeline accepts the query and returns the top $K = 5$ hits:
$$\mathcal{E}_{\text{retrieved}} = \langle c_{(1)}, c_{(2)}, \dots, c_{(\min(U, K))} \rangle$$

### Code Traceability
- **File:** `brain/retriever.py` (lines 173–179).
- **Parameters:** `min_keyword_overlap = 0.15`, `top_k = 5` (defined in `brain/config.py`, lines 33, 36).

---

## 7. Intended Dynamic / Real-Time Information Detection Predicate

Before invoking retrieval, queries requesting current, real-time measurements are intercepted.

Let $\mathcal{T}_{\text{freshness}}$ and $\mathcal{T}_{\text{dynamic}}$ denote disjoint terminology sets:
$$\mathcal{T}_{\text{freshness}} = \{\text{"current"}, \text{"today"}, \text{"now"}, \text{"latest"}, \text{"real-time"}, \text{"realtime"}, \text{"present status"}\}$$
$$\mathcal{T}_{\text{dynamic}} = \{\text{"water quality"}, \text{"river discharge"}, \text{"stp status"}, \text{"pollution monitoring"}, \text{"programme status"}, \text{"program status"}, \text{"infrastructure status"}, \text{"legal status"}, \text{"regulatory status"}\}$$

**Intended Dynamic Query Predicate:**
$$is\_current(q) \iff \Big(\exists t_1 \in \mathcal{T}_{\text{freshness}}: t_1 \text{ is in } \text{lower}(q)\Big) \;\land\; \Big(\exists t_2 \in \mathcal{T}_{\text{dynamic}}: t_2 \text{ is in } \text{lower}(q)\Big)$$

This formulation expresses the intended rule. At baseline commit `56032d7`, the implementation instead stored these terms in one `CURRENT_TERMS` tuple and split it at index 5. Thus only the first five freshness terms were checked as freshness terms, while `realtime` and `present status` were included in the dynamic-topic slice. The formulation above must not be read as a description of the detector implemented at that baseline.

When the intended predicate evaluates to true, the pipeline bypasses vector retrieval and returns:
$$\text{Response} = \big\langle \text{answer} = M_{\text{current\_info}}, \; \text{citations} = \emptyset, \; \text{mode} = \text{"current-info-fallback"} \big\rangle$$

### Code Traceability
- **File:** `brain/retriever.py` (`asks_for_current_information`, lines 89–95).
- **File:** `brain/rag_pipeline.py` (lines 45–50).
- **Baseline implementation:** `CURRENT_TERMS[:5]` and `CURRENT_TERMS[5:]` in `brain/retriever.py` at commit `56032d7`; this split does not match the intended term groups above.
- **Constants:** `CURRENT_INFO_MESSAGE` in `brain/prompts/system.py`.

---

## 8. Generation Context Bounding & Decoupled Citation Assembly

### Evidence Context Truncation
Retrieved hits in $\mathcal{E}_{\text{retrieved}}$ are packed into an evidence context block for the generator subject to a total character budget:
$$\sum_{c \in \mathcal{E}_{\text{included}}} |\text{text}(c)| \le C_{\text{max}} = 6,000 \text{ characters}$$

Chunks that exceed this limit are truncated or excluded, ensuring the language model context window is not saturated.

### Decoupled Citation Provenance Mapping
Unlike conventional systems that instruct the LLM to write citations, PRJ_316 constructs citation records deterministically from the metadata of chunks in $\mathcal{E}_{\text{included}}$.

Let $\text{metadata}(c)$ contain the citation fields for hit $c$. The implementation deduplicates citation objects using the key
$$K(c) = \big(\text{title}(c), \text{file\_name}(c), p_{\text{start}}(c), p_{\text{end}}(c), \text{section}(c)\big).$$
The returned citation object also includes $\text{knowledge\_type}(c)$, but that field is not part of the deduplication key.

This separates citation-record construction from free-form model output and ties returned metadata to retrieved hit records. It does not by itself prove that each source record is correct or that each answer claim is entailed by its attached citation.

### Code Traceability
- **File:** `brain/generator.py` (`citations_from_hits`, lines 37–54; `_evidence_records`, lines 155–182).
- **Parameters:** `MAX_LLM_EVIDENCE_CHARS = 6000`, `MAX_LLM_OUTPUT_TOKENS = 700`.

---

## 9. Mathematical Summary Table

| Operation | Mathematical Representation | Code Implementation | Line Reference |
| :--- | :--- | :--- | :--- |
| **Paragraph Packing** | $\sum |p| + 2(|A| - 1) \le 1400$ | `split_section_text` | `brain/chunking.py:38` |
| **Vector Normalization** | $\mathbf{e}(t) = \mathbf{z} / \|\mathbf{z}\|_2$ | `DefaultEmbeddingFunction` | `brain/embeddings.py:85` |
| **Metric Distance** | $dist(\mathbf{q}, \mathbf{d}) = \|\mathbf{q} - \mathbf{d}\|_2$ | `np.linalg.norm(vectors - query, axis=1)` | `brain/vector_store.py:344` |
| **Pool Coverage Gate** | $pool\_coverage(q, \mathcal{C}) \ge 0.60$ | `pool_coverage < 0.60` | `brain/retriever.py:133` |
| **Distance Cutoff** | $dist(\mathbf{q}, \mathbf{d}) \le 1.15$ | `distance > max_dist` | `brain/retriever.py:157` |
| **Keyword Overlap** | $overlap(q, c) = n_{\text{match}} / |\mathcal{K}(q)|$ | `matched_count / len(keywords)` | `brain/retriever.py:144` |
| **Hybrid Ranking Score** | $S = \frac{1}{1+dist} + 0.5 \cdot overlap + 0.25 \cdot \mathbb{I}$ | `(1.0 / (1.0 + dist)) + (0.5 * ov) + boost` | `brain/retriever.py:161-163` |
| **Top Overlap Gate** | $overlap(q, c^*) \ge 0.15$ | `top_overlap < min_keyword_overlap` | `brain/retriever.py:175` |
| **Dynamic Interception** | $(\exists t_1 \in \mathcal{T}_{\text{fresh}}) \land (\exists t_2 \in \mathcal{T}_{\text{dyn}})$ | `dynamic_topic and freshness` | `brain/retriever.py:94` |
