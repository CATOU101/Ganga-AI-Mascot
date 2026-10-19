# Heuristic Groundedness and Citation-Metadata Benchmark Report


**Project:** PRJ_316 (Ganga AI Mascot)  
**Date:** 2026-10-19T12:44:41Z  
**Dataset SHA-256:** `8755cefa4455c31e8c24c858b8ac7113e80657a3a29808488f346d9007b51fcb`  
**Corpus Size:** 4085 chunks across 83 documents  

The saved JSON retains legacy field names `extrinsic_hallucination_rate` and `citation_hallucination_rate`. These are derived from lexical and metadata checks and must not be interpreted as empirical hallucination rates. The current benchmark runner names the sentence-level complement `lexically_unmatched_sentence_fraction` and does not emit a citation-hallucination metric. The saved artifact has not been rewritten.

---

## 1. Executive Summary

This evaluation applies lexical operational checks to answers and citation metadata for 20 corpus questions spanning Broad Thematic, Technical/Scientific, and Governance/Policy domains. It does not measure semantic entailment or establish claim-level citation correctness. The saved result metadata does not identify the generation provider or mode, so the output cannot be attributed to extractive or hosted generation from this artifact alone.

| Metric | Result | Benchmark Interpretation |
| :--- | :---: | :--- |
| **Sentences passing lexical heuristic** | **100.0%** (70/70) | Script's phrase/token-overlap rule classified these sentences as matching retrieved text; not semantic entailment. |
| **Lexically unmatched sentence fraction** | **0.0%** | Complement of the lexical classifier result; not a measured hallucination rate. |
| **Citation metadata checks passed** | **100.0%** (56/56) | File-name membership plus non-empty source and page fields under the script's rule. |
| **Citation/retrieval alignment checks passed** | **100.0%** (56/56) | Script found a retrieved hit sharing source OR page; this does not verify exact source-page-section alignment. |
| **Citation hallucination rate** | **Not established** | The implemented provenance checks do not establish whether a cited passage supports an answer claim. |
| **Gold Document Match Rate** | **50.0%** | Queries where cited documents overlap annotated ground-truth files. |

---

## 2. Category-Level Performance Breakdown

| Category | Queries | Sentences | Grounded (%) | Citations | Valid Citations (%) | Gold Match (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Broad/Thematic** | 7 | 25 | 100.0% | 21 | 100.0% | 71.4% |
| **Technical/Scientific** | 7 | 26 | 100.0% | 19 | 100.0% | 42.9% |
| **Governance/Policy** | 6 | 19 | 100.0% | 16 | 100.0% | 33.3% |

---

## 3. Boundary-Query Behavior Checks

Checks the observed pipeline mode and citation count for two out-of-domain and two dynamic-query examples. These four cases do not establish general fallback safety.

| Query ID | Boundary Type | Observed Pipeline Mode | Citations Emitted | Fallback Verified |
| :--- | :--- | :--- | :---: | :---: |
| `BND_OOD_01` | out_of_domain | `insufficient-evidence` | 0 | PASS |
| `BND_OOD_02` | out_of_domain | `insufficient-evidence` | 0 | PASS |
| `BND_DYN_01` | dynamic_telemetry | `current-info-fallback` | 0 | PASS |
| `BND_DYN_02` | dynamic_telemetry | `current-info-fallback` | 0 | PASS |

---

## 4. Key Scientific Findings for Research Paper

1. **Lexical sentence check:** The JSON records 70/70 sentences passing the benchmark's lexical heuristic. This is not evidence of zero hallucinations or semantic support; the script also classifies clauses of three or fewer words as grounded automatically.
2. **Citation metadata checks:** The JSON records 56/56 citations passing the script's provenance condition and 56/56 passing its alignment condition. Provenance checks file-name membership and non-empty fields; alignment accepts a matching source OR page. Neither validates page content or claim-level entailment.
3. **Boundary examples:** The report records zero citations for two out-of-domain and two dynamic cases. This describes those four examples only.
4. **Gold document match:** The JSON records **50.0% (10/20)**. The artifact does not establish that the other ten queries retrieved semantically equivalent alternate reports, so no such characterization is made here.

## 5. Reproducibility and provenance limits

The saved artifact records dataset SHA-256, 4,085 chunks, and 83 indexed document names. It does not record the code commit, vector-index digest, provider/model, or generation mode. The checked-in index manifest and read-only SQLite metadata contain 4,085 chunks and 83 distinct source filenames; three PDFs in the source inventory are not represented in that index. The matching counts explain the current 86-source-PDF versus 83-indexed-name difference, but the benchmark artifact has no index digest to establish that it used this exact index snapshot. Do not attribute this result to a particular generator mode without independent run provenance.
