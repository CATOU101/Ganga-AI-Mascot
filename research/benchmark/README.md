# Ganga AI Mascot: 30-Query Retrieval Benchmark Dataset (PRJ_316)

**Project Title:** AI-Powered Interactive Digital Mascot for Namami Gange Awareness & River-People Connectivity  
**Repository:** `https://github.com/CATOU101/Ganga-AI-Mascot`  
**Dataset File:** `domain_queries_30.jsonl`  
**Metric Specifications:** `metric_definitions.md`  
**Validation Harness:** `validate_benchmark.py`  
**Authoritative SHA-256 Digest:** `66f6df3f8758b3e50ff8f6f5373bd354f98a82eb8e6bbf31dd8c84f38923a999`  
**Corpus Snapshot:** 86 IIT Consortium GRBMP PDFs, 4,609 pages, 1,111 approved sections, 4,085 chunks in `knowledge_base/vector_db/brain_index.sqlite3`.

---

## 1. Overview and Primary Research Question

This curated dataset supports a small, source-referenced retrieval reranking evaluation. Its validation script checks dataset structure and gold chunk ID existence in the local index; it does not independently validate annotation support or establish a general benchmark standard.

### Primary Research Question
> **Within a shared dense-retrieved top-15 candidate pool, how do dense, lexical-overlap, hybrid, and overview-boosted reranking configurations compare on this 30-query set?**

---

## 2. Dataset Schema

The benchmark is provided as a line-delimited JSON (`JSONL`) file where each entry conforms to the following schema:

```json
{
  "query_id": "Q_BROAD_01",
  "query": "What is Aviral Dhara in the context of the Ganga River Basin Management Plan?",
  "category": "Broad/Thematic",
  "expected_answer": "Aviral Dhara refers to the continuous and uninterrupted flow of water...",
  "gold_chunk_ids": [
    "prototype-section-00575::chunk-002",
    "prototype-section-00490::chunk-001"
  ],
  "gold_evidence": [
    {
      "chunk_id": "prototype-section-00575::chunk-002",
      "text_preview": "[Page 27] GRBMP – January 2015: Extended Summary 13 4. Mission Summaries 4.1. Mission 1 – Aviral Dhara...",
      "title": "Ganga River Basin Management Plan - 2015 Extended Summary",
      "file_name": "27_GRBMP - Extended Summary.pdf",
      "page_start": 27,
      "page_end": 31,
      "section": "4. Mission Summaries",
      "knowledge_type": "HISTORICAL"
    }
  ],
  "primary_source_title": "Ganga River Basin Management Plan - 2015 Extended Summary",
  "rationale": "Directly defines Mission 1 (Aviral Dhara) and explains the necessity of continuous flow...",
  "annotation_confidence": "High",
  "limitations": "Focuses on GRBMP 2015 conceptual definition."
}
```

### Field Definitions:
* `query_id` (string): Unique identifier prefixed by category (`Q_BROAD_xx`, `Q_TECH_xx`, `Q_GOV_xx`).
* `query` (string): Natural language question formulated as a user inquiry.
* `category` (string): One of `Broad/Thematic`, `Technical/Scientific`, or `Governance/Policy`.
* `expected_answer` (string): Concise reference answer supported by the underlying corpus.
* `gold_chunk_ids` (list of strings): Primary keys matching `chunks.chunk_id` in `brain_index.sqlite3`.
* `gold_evidence` (list of objects): Detailed metadata and text preview for each gold chunk.
* `primary_source_title` (string): Main document containing the primary evidence.
* `rationale` (string): Explicit justification for why the chunk materially answers the query.
* `annotation_confidence` (string): `High` (unambiguous direct support) or `Medium` (synthesized across sections).
* `limitations` (string): Contextual boundaries or temporal horizon notes.

---

## 3. Query Inventory Summary (30 Queries)

| Query ID | Category | Query Text | Primary Source Document | Gold Chunks |
| :--- | :--- | :--- | :--- | :--- |
| `Q_BROAD_01` | Broad/Thematic | What is Aviral Dhara in the context of the Ganga River Basin Management Plan? | GRBMP - 2015 Extended Summary | 2 |
| `Q_BROAD_02` | Broad/Thematic | What is Nirmal Dhara and what is its primary objective in the GRBMP? | GRBMP - 2015 Main Plan Document | 2 |
| `Q_BROAD_03` | Broad/Thematic | What are the core vision and objectives of the Ganga River Basin Management Plan? | Vision Ganga | 2 |
| `Q_BROAD_04` | Broad/Thematic | What are the eight fundamental missions formulated under the Ganga River Basin Management Plan? | GRBMP - 2015 Main Plan Document | 2 |
| `Q_BROAD_05` | Broad/Thematic | How does the GRBMP define the Ganga River as an ecological and geological entity? | GRBMP - 2015 Extended Summary | 2 |
| `Q_BROAD_06` | Broad/Thematic | What is the concept of Environmental Flows (E-flows) and how is it assessed in the Ganga basin? | River Connectivity, Flow Regimes & E-Flows | 2 |
| `Q_BROAD_07` | Broad/Thematic | What are the major physiographic stretches into which the Ganga river is categorized in the plan? | GRBMP - 2015 Main Plan Document | 3 |
| `Q_BROAD_08` | Broad/Thematic | Why is river connectivity—longitudinal, lateral, and vertical—critical for the health of the Ganga? | River Connectivity, Flow Regimes & E-Flows | 2 |
| `Q_BROAD_09` | Broad/Thematic | What are the fundamental principles and societal goals articulated in Vision Ganga? | Vision Ganga | 2 |
| `Q_BROAD_10` | Broad/Thematic | What are the primary anthropogenic threats to the Ganga river basin identified in the GRBMP? | GRBMP - 2015 Main Plan Document | 2 |
| `Q_TECH_01` | Technical/Scientific | What sewage treatment standards and management approaches are recommended for urban wastewater in the Ganga basin? | Management of Urban Sewage | 2 |
| `Q_TECH_02` | Technical/Scientific | Which primary water quality parameters are monitored to assess the river health of the Ganga, and what are their benchmark levels? | GRBMP - 2015 Main Plan Document | 2 |
| `Q_TECH_03` | Technical/Scientific | What are the ecological habitat requirements and conservation threats for the Gangetic dolphin (Platanista gangetica)? | Floral and Faunal Diversity in Middle Ganga | 2 |
| `Q_TECH_04` | Technical/Scientific | How does agricultural runoff and chemical fertilizer or pesticide use affect water quality and ecology in the basin? | Trends in Agriculture in Ganga Basin | 2 |
| `Q_TECH_05` | Technical/Scientific | What are the impacts of unscientific riverbed sand mining on sediment transport and river morphology? | Legal and Institutional Aspects of GRBMP | 2 |
| `Q_TECH_06` | Technical/Scientific | How do dams and run-of-the-river hydroelectric projects in the Upper Ganga affect downstream hydrology and sediment flow? | GRBMP - 2015 Main Plan Document | 2 |
| `Q_TECH_07` | Technical/Scientific | What solid waste management and disposal restrictions are recommended for riparian towns and pilgrimage sites? | Legal and Institutional Aspects of GRBMP | 2 |
| `Q_TECH_08` | Technical/Scientific | What are the primary industrial effluent sources in the Ganga basin and what remediation strategies are recommended? | Management of Urban Sewage | 2 |
| `Q_TECH_09` | Technical/Scientific | How does the GRBMP propose managing river hazards, including floods, erosion, and climate-induced extreme events? | GRBMP - 2015 Main Plan Document | 2 |
| `Q_TECH_10` | Technical/Scientific | What ecological functions do floodplain wetlands (chaurs, jheels, oxbow lakes) serve in the Ganga basin? | GRBMP - 2015 Main Plan Document | 2 |
| `Q_GOV_01` | Governance/Policy | What were the primary mandate, composition, and institutional powers of the National Ganga River Basin Authority (NGRBA)? | Legal and Institutional Aspects of GRBMP | 2 |
| `Q_GOV_02` | Governance/Policy | What is the rationale and structure of the proposed National River Ganga Act recommended by the IIT Consortium? | Legal and Institutional Aspects of GRBMP | 2 |
| `Q_GOV_03` | Governance/Policy | What roles and enforcement responsibilities do the Central Pollution Control Board and State Pollution Control Boards hold in river basin governance? | Legal and Institutional Aspects of GRBMP | 2 |
| `Q_GOV_04` | Governance/Policy | How does the GRBMP propose restructuring river basin institutions into a multi-tier governance model? | Legal and Institutional Aspects of GRBMP | 2 |
| `Q_GOV_05` | Governance/Policy | What economic instruments, effluent charges, and water tariff mechanisms are proposed to incentivize water conservation? | Legal and Institutional Aspects of GRBMP | 2 |
| `Q_GOV_06` | Governance/Policy | What mechanisms does the GRBMP recommend for public participation and community stewardship in river conservation? | Mission 8 - Environmental Knowledge Building | 2 |
| `Q_GOV_07` | Governance/Policy | What is the role of the National Ganga Council and the National Mission for Clean Ganga (NMCG) in executive implementation? | Vision Ganga | 2 |
| `Q_GOV_08` | Governance/Policy | What land-use and developmental restrictions are proposed within designated River Regulation Zones (RRZ)? | Legal and Institutional Aspects of GRBMP | 2 |
| `Q_GOV_09` | Governance/Policy | What policy recommendations are proposed for regulating groundwater extraction and protecting baseflows to the Ganga? | Legal and Institutional Aspects of GRBMP | 2 |
| `Q_GOV_10` | Governance/Policy | What comprehensive data architecture, monitoring networks, and knowledge dissemination portals are proposed under Mission 8? | Mission 8 - Environmental Knowledge Building | 2 |

---

## 4. Annotation Methodology and Quality Control

1. **Direct Materiality Standard:** A chunk is included as gold evidence *only* if its text explicitly provides factual support for answering the question. Chunks containing incidental keyword matches without answering the query were excluded.
2. **Dataset validation:** `validate_benchmark.py` checks gold chunk ID existence, non-empty text, and presence of title and file-name metadata in the local SQLite index. It does not verify page numbers, compare the annotated preview against source PDFs, or establish independent/double annotation review.
3. **Multi-Chunk Evidence Handling:** Where an answer requires complementary information (e.g. definitions in both an executive summary and a detailed plan section), both chunks are indexed.
4. **Gold-ID scope:** The current dataset contains 42 unique gold chunk IDs, and the validation script checks their existence in the configured SQLite index. This mechanical check is not a guarantee that labels are complete or that the chunks semantically support each answer.

## 5. Evaluation and provenance limits

The retrieval runner obtains up to 15 dense candidates for each query, then applies each scoring configuration to that shared pool. Config B is keyword-overlap reranking, not a full-corpus lexical search. The production-gated condition applies coverage and distance gates. The saved result records dataset hash, runtime/platform, and configuration labels, but not the benchmark code commit or vector-index digest. A fresh run uses the current checkout and index and is not guaranteed to reproduce the saved result unless those inputs match. The corpus inventory lists 86 source PDFs while the groundedness result records 83 unique indexed document names; the current artifacts do not explain the difference.

---

## 6. Execution and Validation

### Running the Validation Harness
To verify dataset integrity, category balance, and SQLite chunk existence:

```bash
PYTHONPATH=. ./.venv/bin/python research/benchmark/validate_benchmark.py
```

### Eventual Benchmark Execution Command
When the retrieval ablation harness is executed in the subsequent phase:

```bash
PYTHONPATH=. ./.venv/bin/python research/benchmark/run_retrieval_benchmark.py
```
*(The benchmark script will evaluate Configurations A, B, C, and D against `domain_queries_30.jsonl` using the formulas in `metric_definitions.md`).*
