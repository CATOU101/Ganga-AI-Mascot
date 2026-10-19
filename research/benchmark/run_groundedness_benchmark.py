"""Heuristic evaluation runner for answer-text overlap and citation metadata checks.

Project: AI-Powered Interactive Digital Mascot for Namami Gange (PRJ_316)
Evaluates 20 corpus questions spanning Broad, Technical, and Governance domains, plus
four boundary examples that check fallback modes and citation emission.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
OFFICIAL_PROJECT_TITLE = "Development of AI, ML and Chatbot-powered Interactive Robot Mascot (Chacha Chaudhary) and Digital Avatar to Strengthen the River People Connect Component of Namami Gange"
sys.path.insert(0, str(ROOT_DIR))

from brain.config import load_config
from brain.generator import clean_hit_text
from brain.rag_pipeline import answer_question
from brain.vector_store import get_vector_store

BENCHMARK_DIR = ROOT_DIR / "research" / "benchmark"
DATASET_PATH = BENCHMARK_DIR / "groundedness_queries_20.jsonl"
OUTPUT_JSON_PATH = BENCHMARK_DIR / "groundedness_results.json"
OUTPUT_REPORT_PATH = BENCHMARK_DIR / "groundedness_report.md"

EXPECTED_DATASET_HASH = "8755cefa4455c31e8c24c858b8ac7113e80657a3a29808488f346d9007b51fcb"


def evaluate_groundedness_and_citations() -> int:
    print("=" * 75)
    print("GANGA AI MASCOT (PRJ_316) — ANSWER GROUNDEDNESS & CITATION EVALUATION")
    print("=" * 75)

    # 1. Dataset Preflight
    if not DATASET_PATH.exists():
        print(f"[ERROR] Dataset file not found at: {DATASET_PATH}")
        return 1

    actual_hash = hashlib.sha256(DATASET_PATH.read_bytes()).hexdigest()
    if actual_hash != EXPECTED_DATASET_HASH:
        print(f"[ERROR] Dataset hash mismatch!\nExpected: {EXPECTED_DATASET_HASH}\nActual:   {actual_hash}")
        return 1
    print(f"[OK] Verified dataset SHA-256: {actual_hash}")

    # 2. Knowledge Base Preflight
    cfg = load_config()
    store = get_vector_store(cfg)
    chunk_map = {c["chunk_id"]: c for c in store.chunks}
    corpus_files = set(c["metadata"].get("file_name") for c in store.chunks)
    print(f"[OK] Loaded Vector Store: {len(store.chunks)} active chunks across {len(corpus_files)} unique documents.")

    # 3. Load 20 queries
    queries = []
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                queries.append(json.loads(line))

    if len(queries) != 20:
        print(f"[ERROR] Expected exactly 20 queries, found {len(queries)}")
        return 1

    results: dict[str, Any] = {
        "benchmark_metadata": {
            "project_id": "PRJ_316",
            "benchmark_name": "Heuristic Answer-Text and Citation-Metadata Evaluation",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "dataset_sha256": actual_hash,
            "total_queries": len(queries),
            "corpus_chunks": len(store.chunks),
            "corpus_unique_documents": len(corpus_files),
        },
        "query_evaluations": [],
        "category_summary": {},
        "boundary_evaluations": [],
        "overall_summary": {},
    }

    total_sentences = 0
    grounded_sentences = 0
    total_citations = 0
    valid_provenance_citations = 0
    aligned_citations = 0
    gold_document_matches = 0

    category_stats: dict[str, dict[str, Any]] = {}

    start_time = time.time()

    for idx, q in enumerate(queries, 1):
        qid = q["query_id"]
        qtext = q["query"]
        category = q["category"]
        gold_files = set(q.get("gold_files", []))

        if category not in category_stats:
            category_stats[category] = {
                "count": 0,
                "sentences": 0,
                "grounded_sentences": 0,
                "citations": 0,
                "valid_citations": 0,
                "aligned_citations": 0,
                "gold_matches": 0,
            }

        res = answer_question(qtext)
        mode = res.get("mode", "unknown")
        raw_answer = res.get("answer", "")
        citations = res.get("citations", [])
        retrieved = res.get("retrieved", [])

        # Clean answer and extract sentences
        clean_ans = raw_answer.replace("From the retrieved historical GRBMP material: ", "").strip()
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", clean_ans) if len(s.strip()) > 15]

        # Gather retrieved chunk text
        retrieved_texts = [clean_hit_text(chunk_map[r["chunk_id"]]["text"]).lower() for r in retrieved if r["chunk_id"] in chunk_map]
        combined_text = " ".join(retrieved_texts)

        # Check Groundedness for each sentence
        sentence_details = []
        q_grounded_sents = 0
        for s in sentences:
            s_clean = re.sub(r"^\d+(\.\d+)*\s*", "", s).strip().lower()
            words = s_clean.split()
            is_grounded = False
            match_type = "unsupported"

            if len(words) >= 4:
                sub = " ".join(words[:5])
                if sub in combined_text or s_clean[:25] in combined_text:
                    is_grounded = True
                    match_type = "verbatim_n_gram_match"
                else:
                    s_words = set(words) - {"the", "a", "an", "in", "on", "of", "to", "and", "is", "are"}
                    overlap = sum(1 for w in s_words if w in combined_text)
                    if overlap / max(1, len(s_words)) >= 0.70:
                        is_grounded = True
                        match_type = "high_lexical_subsumption"
            else:
                is_grounded = True
                match_type = "short_clause"

            if is_grounded:
                q_grounded_sents += 1

            sentence_details.append({
                "sentence": s,
                "is_grounded": is_grounded,
                "match_type": match_type,
            })

        q_groundedness = q_grounded_sents / len(sentences) if sentences else 1.0

        # Check Citations
        citation_details = []
        q_valid_cits = 0
        q_aligned_cits = 0
        q_gold_match = False

        for c in citations:
            fn = c.get("file_name", "")
            page = c.get("page", "")
            source = c.get("source", "")
            ktype = c.get("knowledge_type", "")

            # Provenance validity: does file exist in corpus
            is_valid_provenance = (fn in corpus_files) and bool(source) and bool(page)
            if is_valid_provenance:
                q_valid_cits += 1

            # Decoupled binding alignment: does citation map to a retrieved hit
            is_aligned = any(r.get("source") == source or r.get("page") == page for r in retrieved)
            if is_aligned:
                q_aligned_cits += 1

            # Gold match: does cited file belong to gold annotated documents
            is_gold = fn in gold_files
            if is_gold:
                q_gold_match = True

            citation_details.append({
                "source": source,
                "file_name": fn,
                "page": page,
                "knowledge_type": ktype,
                "valid_provenance": is_valid_provenance,
                "aligned_to_retrieved": is_aligned,
                "matches_gold_document": is_gold,
            })

        if q_gold_match:
            gold_document_matches += 1

        total_sentences += len(sentences)
        grounded_sentences += q_grounded_sents
        total_citations += len(citations)
        valid_provenance_citations += q_valid_cits
        aligned_citations += q_aligned_cits

        # Accumulate Category Stats
        cstat = category_stats[category]
        cstat["count"] += 1
        cstat["sentences"] += len(sentences)
        cstat["grounded_sentences"] += q_grounded_sents
        cstat["citations"] += len(citations)
        cstat["valid_citations"] += q_valid_cits
        cstat["aligned_citations"] += q_aligned_cits
        if q_gold_match:
            cstat["gold_matches"] += 1

        query_eval = {
            "query_id": qid,
            "category": category,
            "query": qtext,
            "pipeline_mode": mode,
            "answer_length_chars": len(raw_answer),
            "sentence_count": len(sentences),
            "grounded_sentence_count": q_grounded_sents,
            "groundedness_score": round(q_groundedness, 4),
            "lexically_unmatched_sentence_fraction": round(1.0 - q_groundedness, 4),
            "citation_count": len(citations),
            "valid_citation_count": q_valid_cits,
            "citation_provenance_validity": round(q_valid_cits / len(citations) if citations else 1.0, 4),
            "citation_binding_alignment": round(q_aligned_cits / len(citations) if citations else 1.0, 4),
            "matches_gold_document": q_gold_match,
            "citations": citation_details,
            "sentence_evaluations": sentence_details,
        }
        results["query_evaluations"].append(query_eval)
        print(f"[{idx:02d}/20] {qid:12s} ({category[:10]:10s}) | Grounded: {q_grounded_sents}/{len(sentences)} ({q_groundedness*100:.0f}%) | Cits: {q_valid_cits}/{len(citations)} valid")

    # 4. Boundary Condition Tests (OOD and Dynamic)
    boundary_queries = [
        ("BND_OOD_01", "What are the main principles of quantum computing and qubit superposition?", "out_of_domain", "insufficient-evidence"),
        ("BND_OOD_02", "What were the causes and consequences of the French Revolution in 1789?", "out_of_domain", "insufficient-evidence"),
        ("BND_DYN_01", "What is the current water quality of the Ganga at Varanasi today?", "dynamic_telemetry", "current-info-fallback"),
        ("BND_DYN_02", "Show me the latest real-time pollution monitoring at Kanpur today.", "dynamic_telemetry", "current-info-fallback"),
    ]

    for bid, bquery, btype, expected_mode in boundary_queries:
        res = answer_question(bquery)
        b_mode = res.get("mode")
        b_cits = res.get("citations", [])
        b_ans = res.get("answer", "")
        passed = (b_mode == expected_mode) and (len(b_cits) == 0)
        results["boundary_evaluations"].append({
            "boundary_id": bid,
            "query": bquery,
            "boundary_type": btype,
            "expected_mode": expected_mode,
            "observed_mode": b_mode,
            "citation_count": len(b_cits),
            "spurious_citations_emitted": len(b_cits),
            "boundary_handling_passed": passed,
        })
        print(f"[BOUNDARY] {bid:12s} ({btype[:12]:12s}) -> mode={b_mode}, citations={len(b_cits)} | Passed: {passed}")

    elapsed_time = time.time() - start_time

    # 5. Summarize Results
    for cat, stat in category_stats.items():
        results["category_summary"][cat] = {
            "query_count": stat["count"],
            "sentence_count": stat["sentences"],
            "grounded_sentence_count": stat["grounded_sentences"],
            "groundedness_rate": round(stat["grounded_sentences"] / max(1, stat["sentences"]), 4),
            "citation_count": stat["citations"],
            "valid_citation_count": stat["valid_citations"],
            "citation_provenance_rate": round(stat["valid_citations"] / max(1, stat["citations"]), 4),
            "gold_document_match_rate": round(stat["gold_matches"] / max(1, stat["count"]), 4),
        }

    overall_groundedness = grounded_sentences / max(1, total_sentences)
    overall_provenance_validity = valid_provenance_citations / max(1, total_citations)
    overall_alignment = aligned_citations / max(1, total_citations)
    overall_gold_match = gold_document_matches / len(queries)

    results["overall_summary"] = {
        "total_corpus_queries": len(queries),
        "total_sentences_evaluated": total_sentences,
        "grounded_sentences": grounded_sentences,
        "overall_groundedness_rate": round(overall_groundedness, 4),
        "lexically_unmatched_sentence_fraction": round(1.0 - overall_groundedness, 4),
        "total_citations_evaluated": total_citations,
        "valid_provenance_citations": valid_provenance_citations,
        "citation_provenance_validity_rate": round(overall_provenance_validity, 4),
        "citation_binding_alignment_rate": round(overall_alignment, 4),
        "gold_document_match_rate": round(overall_gold_match, 4),
        "boundary_tests_passed": all(b["boundary_handling_passed"] for b in results["boundary_evaluations"]),
        "total_evaluation_time_seconds": round(elapsed_time, 2),
    }

    # Save JSON results
    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] Machine-readable results saved to: {OUTPUT_JSON_PATH}")

    # Generate Markdown Report
    _write_markdown_report(results, OUTPUT_REPORT_PATH)
    print(f"[OK] Markdown evaluation report saved to: {OUTPUT_REPORT_PATH}")

    print("=" * 75)
    print(f"BENCHMARK COMPLETE:")
    print(f"  Sentences passing lexical heuristic: {overall_groundedness*100:.2f}% ({grounded_sentences}/{total_sentences})")
    print("  Hallucination rate:          Not established by lexical check")
    print(f"  Citation metadata checks:   {overall_provenance_validity*100:.2f}% ({valid_provenance_citations}/{total_citations})")
    print(f"  Citation/retrieval heuristic: {overall_alignment*100:.2f}% ({aligned_citations}/{total_citations})")
    print("  Citation correctness:        Not established by metadata checks")
    print(f"  Gold document match:         {overall_gold_match*100:.2f}% ({gold_document_matches}/{len(queries)})")
    print("=" * 75)

    return 0


def _write_markdown_report(results: dict[str, Any], path: Path) -> None:
    meta = results["benchmark_metadata"]
    summary = results["overall_summary"]
    cats = results["category_summary"]
    aligned_citations = sum(
        1
        for query in results["query_evaluations"]
        for citation in query["citations"]
        if citation["aligned_to_retrieved"]
    )
    gold_document_matches = sum(
        1 for query in results["query_evaluations"] if query["matches_gold_document"]
    )

    lines = [
        "# Heuristic Groundedness and Citation-Metadata Benchmark Report",
        "",
        f"**Official Project Title:** {OFFICIAL_PROJECT_TITLE}  ",
        f"**Project:** {meta['project_id']} (Ganga AI Mascot)  ",
        f"**Date:** {meta['timestamp']}  ",
        f"**Dataset SHA-256:** `{meta['dataset_sha256']}`  ",
        f"**Corpus Size:** {meta['corpus_chunks']} chunks across {meta['corpus_unique_documents']} documents  ",
        "",
        "---",
        "",
        "## 1. Executive Summary",
        "",
        "This evaluation applies lexical operational checks to answers and citation metadata for 20 corpus questions. It does not measure semantic entailment or claim-level citation correctness. The result metadata does not identify the generation provider or mode, so outputs cannot be attributed to extractive or hosted generation from this artifact alone.",
        "",
        "| Metric | Result | Benchmark Interpretation |",
        "| :--- | :---: | :--- |",
        f"| **Sentences passing lexical heuristic** | **{summary['overall_groundedness_rate']*100:.1f}%** ({summary['grounded_sentences']}/{summary['total_sentences_evaluated']}) | Phrase/token-overlap classifier result; not semantic entailment. |",
        f"| **Lexically unmatched sentence fraction** | **{summary['lexically_unmatched_sentence_fraction']*100:.1f}%** | Complement of lexical classifier result; not a measured hallucination rate. |",
        f"| **Citation metadata checks passed** | **{summary['citation_provenance_validity_rate']*100:.1f}%** ({summary['valid_provenance_citations']}/{summary['total_citations_evaluated']}) | File-name membership plus non-empty source/page fields. |",
        f"| **Citation/retrieval alignment checks passed** | **{summary['citation_binding_alignment_rate']*100:.1f}%** ({aligned_citations}/{summary['total_citations_evaluated']}) | Retrieved hit shared source OR page; exact citation correctness is not established. |",
        "| **Citation hallucination rate** | **Not established** | Metadata checks do not establish whether cited text supports answer claims. |",
        f"| **Gold Document Match Rate** | **{summary['gold_document_match_rate']*100:.1f}%** | Queries where cited documents overlap annotated ground-truth files. |",
        "",
        "---",
        "",
        "## 2. Category-Level Performance Breakdown",
        "",
        "| Category | Queries | Sentences | Passing lexical check (%) | Citations | Passing metadata check (%) | Gold Match (%) |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    for cat_name, c in cats.items():
        lines.append(
            f"| **{cat_name}** | {c['query_count']} | {c['sentence_count']} | {c['groundedness_rate']*100:.1f}% | {c['citation_count']} | {c['citation_provenance_rate']*100:.1f}% | {c['gold_document_match_rate']*100:.1f}% |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 3. Boundary-Query Behavior Checks",
        "",
        "Checks observed pipeline mode and citation count for two out-of-domain and two dynamic-query examples. These four cases do not establish general fallback safety.",
        "",
        "| Query ID | Boundary Type | Observed Pipeline Mode | Citations Emitted | Fallback Verified |",
        "| :--- | :--- | :--- | :---: | :---: |",
    ])

    for b in results["boundary_evaluations"]:
        lines.append(
            f"| `{b['boundary_id']}` | {b['boundary_type']} | `{b['observed_mode']}` | {b['citation_count']} | {'PASS' if b['boundary_handling_passed'] else 'FAIL'} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 4. Results and interpretation limits",
        "",
        f"1. The JSON records {summary['grounded_sentences']}/{summary['total_sentences_evaluated']} sentences passing the lexical heuristic. Short clauses are classified as grounded automatically; this is not evidence of zero hallucinations or semantic support.",
        f"2. The JSON records {summary['valid_provenance_citations']}/{summary['total_citations_evaluated']} citations passing its metadata condition and {aligned_citations}/{summary['total_citations_evaluated']} passing its alignment condition. Provenance checks file-name membership and non-empty fields; alignment accepts a matching source OR page. Neither verifies page content or claim-level entailment.",
        "3. The boundary table covers two out-of-domain and two dynamic examples only.",
        f"4. Gold-document overlap is {summary['gold_document_match_rate']*100:.1f}% ({gold_document_matches}/{summary['total_corpus_queries']}); the artifact does not establish that other retrieved documents are semantically equivalent alternatives.",
        "",
        "## 5. Reproducibility and provenance limits",
        "The saved result records dataset SHA-256, chunk count, and indexed-document-name count, but not the code commit, index digest, provider/model, or generation mode. The corpus inventory lists 86 source PDFs while this result records the number of unique indexed document names; the available artifacts do not reconcile the difference.",
        "",
    ])

    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(evaluate_groundedness_and_citations())
