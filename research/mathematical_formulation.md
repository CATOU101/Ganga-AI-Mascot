# Mathematical Formulation: Ganga AI Mascot (PRJ_316)

**Project ID:** PRJ_316  
**Project Title:** AI-Powered Interactive Digital Mascot for Namami Gange Awareness & River-People Connectivity  
**Status:** Engineering formulation audited against current implementation; thresholds are prototype heuristics, not empirically calibrated.
**Historical baseline:** `56032d744b80695be7593c6f85e50d53c7c5a083`
**Current implementation snapshot audited:** `main` at `80833751f2a365eb00be5ddeee3392e4a601d38e` (2026-10-19; before documentation-only changes)

---

> [!NOTE]
> **Source-Grounded Mathematical Integrity:**  
> Equations below describe implementation details in `brain/chunking.py`, `brain/embeddings.py`, `brain/vector_store.py`, `brain/retriever.py`, and `brain/generator.py`. The hybrid retrieval score is a deterministic engineering heuristic, not a calibrated probability, confidence interval, or likelihood ratio. Thresholds are configuration defaults, not empirically tuned results.

---

## 1. Document Chunking and Segmentation

The text chunking algorithm processes reviewed sections to produce target-sized passages while preserving paragraph boundaries and semantic continuity where possible. A single paragraph longer than the target is not split and can produce an oversized chunk.

### Mathematical Formulation
Let a reviewed document section $S$ be represented as a raw character string of length $|S|$.
Text normalization produces a sanitized string $T$:
$$T = \text{norm}(S)$$
where `normalize_text` converts CRLF/CR to LF, collapses runs of horizontal spaces/tabs to one space, reduces runs of three or more newlines to two, and strips surrounding whitespace.

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

The target is not a hard maximum: an individual paragraph is kept intact when it exceeds $L_{\text{target}}$. A carried overlap prefix can also make the following chunk exceed the target. Thus 1,400 characters is a packing target, not a strict maximum.

### Post-Processing Boundary Constraint (Sub-Minimum Repair)
During a left-to-right post-processing pass, any chunk shorter than $L_{\text{min}}=120$ characters is appended to the preceding repaired chunk when one exists; the first chunk is retained even if shorter than the minimum. The implementation does not apply this rule only to the final chunk.

### Code Traceability
- **File:** `brain/chunking.py`
- **Functions:** `normalize_text`, `split_section_text`, `chunks_from_sections` in `brain/chunking.py`.
- **Parameters:** `target_chars=1400`, `overlap_chars=180`, `min_chunk_chars=120` in `BrainConfig` (`brain/config.py`).
- **Assumptions & Limitations:** Chunking operates on raw character counts rather than BPE/WordPiece token counts. This ensures token-free, deterministic segmentation across Python environments without requiring external tokenizer libraries during indexing.

---

## 2. Semantic Embedding and Normalization

### Vector Embedding Mapping
Let $\mathcal{V}$ denote the vocabulary space of natural language text strings. The embedding function $\mathbf{e}: \mathcal{V} \to \mathbb{R}^d$ maps arbitrary text $t$ into a dense continuous representation of dimensionality $d = 384$:
$$\mathbf{z} = f_{\text{MiniLM}}(t) \in \mathbb{R}^{384}$$
where $f_{\text{MiniLM}}$ is the ONNX Runtime execution of `all-MiniLM-L6-v2`.

The default Chroma `DefaultEmbeddingFunction` normalizes its returned ONNX vectors; `LocalHashEmbedding.embed_query` also normalizes nonzero hash vectors explicitly:
$$\mathbf{e}(t) = \frac{\mathbf{z}}{\|\mathbf{z}\|_2} = \frac{\mathbf{z}}{\sqrt{\sum_{k=1}^{384} z_k^2}}$$
such that $\|\mathbf{e}(t)\|_2 = 1.0$.

### Baseline Hash Embedding (Reproducibility Fallback)
When running without neural weights, `LocalHashEmbedding` computes a 384-dimensional bag-of-words vector using SHA-256 digests:
For each token $w \in \text{tokens}(t)$:
$$h = \text{SHA-256}(w), \quad \text{idx} = \text{uint32}_{\text{big-endian}}(h[0:4]) \bmod d, \quad s = \begin{cases} +1 & \text{if } h[4] \equiv 0 \pmod 2 \\ -1 & \text{otherwise} \end{cases}$$
$$\mathbf{v}_{\text{idx}} \leftarrow \mathbf{v}_{\text{idx}} + s, \qquad \mathbf{e}_{\text{hash}}(t) = \begin{cases}\frac{\mathbf{v}}{\|\mathbf{v}\|_2} & \|\mathbf{v}\|_2 > 0 \\ \mathbf{0} & \text{otherwise}\end{cases}$$

### Code Traceability
- **File:** `brain/embeddings.py`
- **Classes:** `ONNXSemanticEmbedding`, `LocalHashEmbedding`; the default function delegates normalization to the installed Chroma embedding-function implementation.
- **Assumptions & Limitations:** The model truncates input text beyond 256 WordPiece tokens. Because chunk target sizes are 1,400 characters ($\approx 250\text{--}300$ words), semantic representations primarily capture the leading paragraphs of each chunk.

---

## 3. Candidate Vector Retrieval

For the normalized default semantic embedding and normalized hash baseline, an input user question $q$ has query vector:
$$\mathbf{q} = \mathbf{e}(q) \in \mathbb{R}^{384}, \quad \|\mathbf{q}\|_2 = 1.0$$

In the audited index snapshot, the active vector store contains a matrix of pre-computed chunk vectors:
$$\mathbf{D} \in \mathbb{R}^{N \times 384}, \quad N = 4,085$$
where each row $\mathbf{d}_i \in \mathbb{R}^{384}$ corresponds to chunk $i$; for the configured normalized embedding functions, $\|\mathbf{d}_i\|_2=1$ for nonzero vectors.

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
- **Files/functions:** `SQLiteVectorStore.query` in `brain/vector_store.py`; `Retriever.retrieve_candidates` in `brain/retriever.py`.
- **Parameter:** `candidate_top_k=15` by default in `BrainConfig`; actual $K$ is capped by the number of indexed vectors.

---

## 4. Lexical Processing and Keyword Extraction

### Tokenization and Stopword Filtering
Let the query string $q$ be tokenized into discrete alphanumeric words:
$$\mathcal{W}(q) = \text{regex\_match}\big(\text{"[A-Za-z0-9][A-Za-z0-9\_-]*"}, \text{lower}(q)\big)$$

The implementation produces an ordered keyword list $\mathcal{K}(q)$ by filtering the token sequence; repeated keyword occurrences are retained:
$$\mathcal{K}(q) = \langle w_i \in \mathcal{W}(q) \mid |w_i| \ge 3 \land w_i \notin \mathcal{S}_{\text{stopwords}} \rangle$$
where $\mathcal{S}_{\text{stopwords}}$ is the English stop-word and domain-noise set in `brain/retriever.py` (`what`, `is`, `the`, `tell`, `knowledge`, `grbmp`, etc.).

### Candidate Pool Keyword Coverage (Pre-Rerank Gate 1)
To protect against out-of-domain or unsupported queries that accidentally match vector clusters, the system checks whether the query's keywords appear anywhere within the candidate pool $\mathcal{C}_{\text{cand}}$.

Let $\text{text\_corpus}(c)$ denote the concatenated lowercase text, title, and section metadata of candidate chunk $c$:
$$\text{text\_corpus}(c) = \text{lower}\big(\text{text}(c) \mathbin{\Vert} \text{" "} \mathbin{\Vert} \text{title}(c) \mathbin{\Vert} \text{" "} \mathbin{\Vert} \text{section}(c)\big)$$

The pool coverage ratio is:
$$pool\_coverage(q, \mathcal{C}_{\text{cand}}) = \frac{\sum_{i=1}^{|\mathcal{K}(q)|} \mathbb{I}[w_i \text{ occurs as a substring in some } \text{text\_corpus}(c)]}{|\mathcal{K}(q)|}$$
*(Defined as $1.0$ if $\mathcal{K}(q) = \emptyset$)*.

**Gate Condition 1:**
$$\text{If } |\mathcal{K}(q)| > 0 \;\land\; pool\_coverage(q, \mathcal{C}_{\text{cand}}) < 0.60 \implies \text{Reject: return } (\text{False}, \emptyset)$$

### Code Traceability
- **File:** `brain/retriever.py`
- **Functions:** `extract_keywords`, `Retriever.rerank_and_filter` in `brain/retriever.py`.
- **Parameter:** Candidate-pool coverage threshold `0.60` in `Retriever.rerank_and_filter`.

---

## 5. Candidate Distance Filtering and Hybrid Reranking

For all candidates $c \in \mathcal{C}_{\text{cand}}$ that pass Gate 1, individual filtering and scoring proceed as follows:

### 1. Distance Threshold Cutoff
$$\text{If } dist(\mathbf{q}, \mathbf{d}_c) > \theta_{\text{dist}} \implies \text{Discard candidate } c$$
where:
$$\theta_{\text{dist}} = \begin{cases} \texttt{evidence\_max\_distance} & \text{semantic embedding; default }1.15 \\ 1.35 & \text{local-hash embedding} \end{cases}$$
For the default semantic threshold of $1.15$, unit-normalized vectors yield the equivalent cosine bound $\cos(\mathbf{q},\mathbf{d}_c) \ge 1 - 1.15^2/2 \approx 0.339$. This conversion depends on unit normalization; the implemented ranking and gate use Euclidean distance directly.

### 2. Individual Lexical Overlap Ratio
For candidate $c$, the matched keyword-occurrence count is:
$$n_{\text{match}}(q, c) = \sum_{i=1}^{|\mathcal{K}(q)|} \mathbb{I}\big(w_i \text{ is a substring of } \text{text\_corpus}(c)\big)$$
The overlap ratio is:
$$overlap(q, c) = \begin{cases} \frac{n_{\text{match}}(q, c)}{|\mathcal{K}(q)|} & \text{if } |\mathcal{K}(q)| > 0 \\ 1.0 & \text{if } |\mathcal{K}(q)| = 0 \end{cases}$$

### 3. Broad-Query Overview Boost
To prevent broad, general questions from matching narrow, obscure technical subsections, an overview boost is conditionally applied.

**Broad Query Predicate:**
$$is\_broad(q) \iff \big(\text{"ganga"} \in \text{lower}(q) \;\lor\; \text{"river"} \in \text{lower}(q)\big) \;\land\; \big(\mathcal{W}(q) \cap \mathcal{T}_{\text{specific}} = \emptyset\big)$$
where $\mathcal{T}_{\text{specific}}$ is the curated technical-topic set in `brain/retriever.py` (`dolphin`, `stp`, `tannery`, `bod`, `cod`, `pesticide`, etc.).

**Core Overview Document Predicate:**
$$is\_overview(c) \iff \text{core-file-substring}(c) \;\lor\; \text{core-title-substring}(c) \;\lor\; \big(\text{overview-section-substring}(c) \;\land\; \text{summary-title-substring}(c)\big)$$
The implementation uses substring matching against configured core filenames, titles, and section names; a section match also requires one of its configured summary-title substrings in the title. The configured tuples are maintained in `brain/retriever.py`.

**Overview Boost Indicator:**
$$\mathbb{I}_{\text{overview}}(q, c) = \begin{cases} 1 & \text{if } is\_broad(q) \land is\_overview(c) \\ 0 & \text{otherwise} \end{cases}$$

### 4. Hybrid Scoring Function
The total hybrid score $S_{\text{hybrid}}(q, c)$ is computed as:
$$S_{\text{hybrid}}(q, c) = \underbrace{\frac{1.0}{1.0 + dist(\mathbf{q}, \mathbf{d}_c)}}_{\text{Continuous Semantic Proximity}} + \underbrace{0.5 \cdot overlap(q, c)}_{\text{Discrete Lexical Overlap}} + \underbrace{0.25 \cdot \mathbb{I}_{\text{overview}}(q, c)}_{\text{Query-Conditioned Overview Boost}}$$

### Score Bounds
- For the default semantic cutoff, the semantic component $\frac{1}{1 + dist} \in [\frac{1}{1 + 1.15}, 1] \approx [0.465, 1.000]$; the configurable threshold changes the lower bound.
- The lexical component $0.5 \cdot overlap \in [0.000, 0.500]$.
- The overview component $0.25 \cdot \mathbb{I} \in \{0.000, 0.250\}$.
- For the default semantic cutoff, the possible score range is $S_{\text{hybrid}}(q,c)\in[0.465,1.750]$. The local-hash cutoff of 1.35 changes the lower bound to $1/(1+1.35)\approx0.426$; a configured semantic cutoff also changes its bound.

### Code Traceability
- **Functions:** `is_broad_ganga_query`, `is_core_overview_hit`, and `Retriever.rerank_and_filter` in `brain/retriever.py`.
- **Parameters:** Semantic distance default `evidence_max_distance=1.15`, local-hash distance cutoff `1.35`, lexical weight `0.5`, overview weight `0.25`.

---

## 6. Evidence Quality Gate (Post-Rerank Gate 2)

After computing $S_{\text{hybrid}}(q, c)$ for all surviving candidates, candidates are sorted in descending order:
$$\langle c_{(1)}, c_{(2)}, \dots, c_{(U)} \rangle \quad \text{such that } S_{\text{hybrid}}(q, c_{(1)}) \ge S_{\text{hybrid}}(q, c_{(2)}) \ge \dots$$

Let $c^* = c_{(1)}$ denote the highest-scoring candidate.

**Gate Condition 2 (Top-Hit Relevance Check):**
$$\text{If } |\mathcal{K}(q)| > 1 \;\land\; overlap(q, c^*) < \theta_{\text{overlap}} \implies \text{Reject: return } (\text{False}, \emptyset)$$
where $\theta_{\text{overlap}} = 0.15$ (`min_keyword_overlap`).

If Gate 2 passes, the retrieval pipeline accepts the query and returns up to the top $K=5$ hits (or the requested/configured count):
$$\mathcal{E}_{\text{retrieved}} = \langle c_{(1)}, c_{(2)}, \dots, c_{(\min(U, K))} \rangle$$

### Code Traceability
- **Function:** `Retriever.rerank_and_filter` in `brain/retriever.py`.
- **Parameters:** `min_keyword_overlap=0.15`, `top_k=5` defaults in `BrainConfig` (`brain/config.py`); API `top_k` may override the returned count.

---

## 7. Current-Information Detection Predicate

Before invoking retrieval, queries requesting current, real-time measurements are intercepted.

Let $\mathcal{T}_{\text{freshness}}$ and $\mathcal{T}_{\text{dynamic}}$ denote disjoint terminology sets:
$$\mathcal{T}_{\text{freshness}} = \{\text{"current"}, \text{"today"}, \text{"now"}, \text{"latest"}, \text{"real-time"}, \text{"realtime"}, \text{"present status"}\}$$
$$\mathcal{T}_{\text{dynamic}} = \{\text{"water quality"}, \text{"river discharge"}, \text{"stp status"}, \text{"pollution monitoring"}, \text{"programme status"}, \text{"program status"}, \text{"infrastructure status"}, \text{"legal status"}, \text{"regulatory status"}\}$$

**Implemented dynamic/current-information predicate:**
$$is\_current(q) \iff \Big(\exists t_1 \in \mathcal{T}_{\text{freshness}}: t_1 \text{ is in } \text{lower}(q)\Big) \;\land\; \Big(\exists t_2 \in \mathcal{T}_{\text{dynamic}}: t_2 \text{ is in } \text{lower}(q)\Big)$$

The current code stores freshness and topic terms separately and returns true when at least one substring from each group is present in the lowercased question. The earlier baseline commit `56032d7` used a different combined tuple/split; that historical behavior is not the current implementation.

When this predicate evaluates to true for the original question or its translated search text, the Brain pipeline bypasses vector retrieval and returns:
$$\text{Response} = \big\langle \text{answer} = M_{\text{current\_info}}, \; \text{citations} = \emptyset, \; \text{mode} = \text{"current-info-fallback"} \big\rangle$$

### Code Traceability
- **Functions:** `asks_for_current_information` in `brain/retriever.py`; `answer_question` in `brain/rag_pipeline.py`.
- **Historical note:** The combined `CURRENT_TERMS` split existed at baseline `56032d7`; the current implementation uses separate term groups.
- **Constants:** `CURRENT_INFO_MESSAGE` in `brain/prompts/system.py`.
- **System Boundary Note:** In the integrated conversational mascot service (`integration/controller/conversation_controller.py`), live water-quality queries are intercepted before the Brain service to query the CPCB real-time monitoring service (`integration/water_quality.py`). The static fallback predicate above remains active within the standalone Brain RAG pipeline as an internal safety gate.

---

## 8. Generation Context Bounding & Decoupled Citation Assembly

### Evidence Context Truncation
Retrieved hits in $\mathcal{E}_{\text{retrieved}}$ are packed into an evidence context block for the generator subject to a total character budget:
$$\sum_{c \in \mathcal{E}_{\text{included}}} |\text{text}(c)| \le C_{\text{max}} = 6,000 \text{ characters}$$

The generator's `_evidence_records` caps the combined evidence text at 6,000 characters, truncating the hit that crosses the remaining text budget and omitting later text. This limit applies to evidence text only; metadata, JSON framing, system instructions, and question are outside the character limit, so it is not a limit on the full prompt or total model-token usage.

### Decoupled Citation Provenance Mapping
Unlike conventional systems that instruct the LLM to write citations, PRJ_316 constructs citation records deterministically from the metadata of chunks in $\mathcal{E}_{\text{included}}$.

Let $\text{metadata}(c)$ contain the citation fields for hit $c$. The implementation deduplicates citation objects using the key
$$K(c) = \big(\text{title}(c), \text{file\_name}(c), p_{\text{start}}(c), p_{\text{end}}(c), \text{section}(c)\big).$$
The returned citation object also includes $\text{knowledge\_type}(c)$, but that field is not part of the deduplication key.

This separates citation-record construction from free-form model output and ties returned metadata to retrieved hit records. It does not by itself prove that each source record is correct or that each answer claim is entailed by its attached citation.

### Code Traceability
- **Functions:** `citations_from_hits` and `OpenAICompatibleGenerator._evidence_records` in `brain/generator.py`.
- **Parameters:** `MAX_LLM_EVIDENCE_CHARS = 6000`, `MAX_LLM_OUTPUT_TOKENS = 700`.

---

## 9. Mathematical Summary Table

| Operation | Mathematical Representation | Code Implementation |
| :--- | :--- | :--- |
| **Paragraph Packing** | Greedy paragraph packing toward 1,400 chars; 180-char suffix overlap; short-chunk repair at 120 chars | `split_section_text` in `brain/chunking.py` |
| **Vector Normalization** | $\mathbf{e}(t)=\mathbf{z}/\|\mathbf{z}\|_2$ for normalized embeddings | Chroma default function and `LocalHashEmbedding` in `brain/embeddings.py` |
| **Metric Distance** | $dist(\mathbf{q},\mathbf{d})=\|\mathbf{q}-\mathbf{d}\|_2$ | `SQLiteVectorStore.query` in `brain/vector_store.py` |
| **Pool Coverage Gate** | $pool\_coverage(q,\mathcal{C})\ge0.60$ | `Retriever.rerank_and_filter` in `brain/retriever.py` |
| **Distance Cutoff** | Semantic: config default 1.15; local-hash: 1.35 | `Retriever.rerank_and_filter` and `BrainConfig` |
| **Keyword Overlap** | $overlap(q,c)=n_{\text{match}}/\lvert\mathcal{K}(q)\rvert$ | `Retriever.rerank_and_filter` |
| **Hybrid Ranking Score** | $S=\frac{1}{1+dist}+0.5\cdot overlap+0.25\cdot\mathbb{I}$ | `Retriever.rerank_and_filter` |
| **Top Overlap Gate** | $overlap(q,c^*)\ge0.15$ for more than one keyword | `Retriever.rerank_and_filter` |
| **Dynamic Interception** | One freshness term AND one dynamic-topic term occur as substrings | `asks_for_current_information` in `brain/retriever.py` |
