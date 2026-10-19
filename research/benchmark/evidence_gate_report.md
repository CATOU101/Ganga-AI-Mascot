# Evidence-Gate Evaluation Report: Ganga AI Mascot (PRJ_316)

**Official Project Title:** Development of AI, ML and Chatbot-powered Interactive Robot Mascot (Chacha Chaudhary) and Digital Avatar to Strengthen the River People Connect Component of Namami Gange

**Date:** 2026-10-19T12:34:10Z  
**Runtime:** Python 3.13.3 on macOS-26.7.1-arm64-arm-64bit-Mach-O  
**Dataset:** `research/benchmark/evidence_gate_queries_20.jsonl` (repository-relative path)
**Dataset SHA-256:** `f5d0d77a75a8ce9ec29a0798486eeca3a89649b838aad4324d1a5e09ce288ca2`  
**Total Queries:** 20  

The saved JSON retains the legacy field name `overall_safety_accuracy`; it is ordinary decision accuracy on this selected 20-query set, not a measure or guarantee of general safety. The current benchmark runner uses the more precise name `selected_set_decision_agreement` for newly generated results. The saved artifact has not been rewritten.

---

## 1. Overview and Evaluation Objective

This evaluation benchmarks the two-stage pre-generation evidence quality gate and dynamic query interception mechanism implemented in `brain/retriever.py` and `brain/rag_pipeline.py`. The objective is to verify that:
1. **Answerable in-domain questions** successfully pass the gates without false rejection.
2. **Unsupported out-of-domain questions** are rejected by the candidate-pool coverage gate ($pool\_coverage < 0.60$) or top-hit overlap gate, returning `mode: insufficient-evidence`.
3. **Dynamic / time-sensitive queries** are intercepted by `asks_for_current_information` before retrieval, returning `mode: current-info-fallback`.

---

## 2. Table III for Research Paper (Safety & Gating Performance)

| Query Category | Total Queries | Correct Acceptance Rate | Correct Rejection Rate | False Acceptance Rate | False Rejection Rate | Primary Gating Mechanism |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Answerable In-Domain** | 10 | **100.0%** (10/10) | N/A | N/A | **0.0%** (0/10) | None (Passed all gates) |
| **Unsupported Out-of-Domain** | 5 | N/A | **100.0%** (5/5) | **0.0%** (0/5) | N/A | Candidate-pool coverage gate ($<60\%$) |
| **Dynamic / Time-Sensitive** | 5 | N/A | **100.0%** (5/5) | **0.0%** (0/5) | N/A | Dynamic query interception (`asks_for_current_information`) |
| **Overall / Combined** | **20** | **100.0%** (10/10) | **100.0%** (10/10) | **0.0%** (0/10) | **0.0%** (0/10) | **Decision agreement on this selected set: 100.0%** |

---

## 3. Confusion Matrix and Operational Denominators

| Actual Condition \ System Decision | Accepted (`mode: grounded`) | Rejected (`mode: insufficient-evidence` or `current-info-fallback`) | Total |
| :--- | :---: | :---: | :---: |
| **Answerable In-Domain** | **TP = 10** | **FN = 0** | 10 |
| **Unanswerable (OOD + Dynamic)** | **FP = 0** | **TN = 10** | 10 |
| **Total** | 10 | 10 | **20** |

### Operational Metric Definitions:
* **Correct Acceptance Rate (Sensitivity / Recall on Answerable):** $\frac{\text{TP}}{\text{TP} + \text{FN}} = \frac{10}{10} = 1.000$ (100.0%)
* **False Rejection Rate:** $\frac{\text{FN}}{\text{TP} + \text{FN}} = \frac{0}{10} = 0.000$ (0.0%)
* **Correct Rejection Rate (Specificity on Unanswerable):** $\frac{\text{TN}}{\text{TN} + \text{FP}} = \frac{10}{10} = 1.000$ (100.0%)
* **False Acceptance Rate (Fallout):** $\frac{\text{FP}}{\text{TN} + \text{FP}} = \frac{0}{10} = 0.000$ (0.0%)

---

## 4. Analysis and Gate-Specific Behavior

1. **Decision agreement in the tested set:** The saved result records correct decisions for 10 answerable, 5 out-of-domain, and 5 dynamic queries. This is a result on these 20 selected queries, not a general safety or hallucination guarantee.
2. **Candidate-pool coverage:** The report records low coverage for the five tested out-of-domain queries. The threshold is a lexical heuristic, not a calibrated safety score.
3. **Dynamic-query interception:** The five tested temporal inquiries matched `asks_for_current_information` rules. This does not establish comprehensive detection of time-sensitive language.
4. **Answerable examples:** All ten selected in-domain questions passed in this run; broader false rejection rates have not been established.

---

## 5. Limitations

* **Sample Size:** Evaluated on a targeted 20-query benchmark ($N=20$), with five examples in each unanswerable category.
* **Engineering Heuristic Scope:** The gates use keyword coverage, lexical overlap, distance thresholds, and rule-based predicates. They do not constitute a calibrated safety classifier or a formal proof of Natural Language Inference (NLI) entailment.
* **Provenance:** The result JSON records dataset hash and runtime/platform information, but not the code commit, index digest, or generation provider/mode. The dataset path is repository-relative here; the saved JSON still contains the original machine-specific path.
