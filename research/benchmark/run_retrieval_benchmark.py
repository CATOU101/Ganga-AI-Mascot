#!/usr/bin/env python3
"""Retrieval ablation benchmark runner for the Ganga AI Mascot (PRJ_316)."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

from brain.config import load_config
from brain.retriever import (
    Retriever,
    extract_keywords,
    is_broad_ganga_query,
    is_core_overview_hit,
)
from brain.vector_store import get_vector_store


ROOT_DIR = Path(__file__).resolve().parents[2]
OFFICIAL_PROJECT_TITLE = "Development of AI, ML and Chatbot-powered Interactive Robot Mascot (Chacha Chaudhary) and Digital Avatar to Strengthen the River People Connect Component of Namami Gange"
BENCHMARK_DIR = ROOT_DIR / "research" / "benchmark"
DATASET_PATH = BENCHMARK_DIR / "domain_queries_30.jsonl"
OUTPUT_JSON_PATH = BENCHMARK_DIR / "retrieval_ablation_results.json"
OUTPUT_REPORT_PATH = BENCHMARK_DIR / "ablation_experiment_report.md"
EXPECTED_DATASET_HASH = "66f6df3f8758b3e50ff8f6f5373bd354f98a82eb8e6bbf31dd8c84f38923a999"


def compute_metrics(retrieved: list[str], gold: set[str]) -> tuple[float, float, float]:
    """Compute Precision@5, Recall@5, and MRR@5 according to metric_definitions.md."""
    top5 = retrieved[:5]
    hits = [r for r in top5 if r in gold]
    
    p5 = len(hits) / 5.0
    r5 = len(hits) / len(gold) if gold else 0.0
    
    mrr5 = 0.0
    for rank, cid in enumerate(top5, start=1):
        if cid in gold:
            mrr5 = 1.0 / rank
            break
            
    return p5, r5, mrr5


def rank_candidates(
    qtext: str,
    candidates: list[dict[str, Any]],
    mode: str,
    apply_gates: bool = True,
    config_distance_cutoff: float = 1.15,
) -> tuple[bool, list[str], str]:
    """Rank candidates under Configuration A, B, C, or D with optional evidence gates."""
    keywords = extract_keywords(qtext)
    
    # Pre-Rerank Gate 1: Candidate pool coverage check
    if apply_gates and keywords:
        pool_terms_found = sum(
            1 for kw in keywords
            if any(kw in (hit["text"] + " " + str(hit["metadata"].get("title", "")) + " " + str(hit["metadata"].get("section", ""))).lower() for hit in candidates)
        )
        pool_coverage = pool_terms_found / len(keywords)
        if pool_coverage < 0.60:
            return False, [], "rejected_pool_coverage"

    is_broad = is_broad_ganga_query(qtext)
    scored = []
    for hit in candidates:
        content_lower = (hit["text"] + " " + str(hit["metadata"].get("title", "")) + " " + str(hit["metadata"].get("section", ""))).lower()
        overlap = sum(1 for kw in keywords if kw in content_lower) / len(keywords) if keywords else 1.0
        dist = hit.get("distance", 999.0)
        
        # Distance cutoff gate
        if apply_gates and dist > config_distance_cutoff:
            continue
            
        if mode == "A":  # Dense-Only
            score = 1.0 / (1.0 + dist)
        elif mode == "B":  # Lexical-overlap reranking within dense candidates
            score = overlap
        elif mode == "C":  # Unweighted Hybrid
            score = (1.0 / (1.0 + dist)) + (0.5 * overlap)
        elif mode == "D":  # Proposed Overview-Boosted Hybrid
            boost = 0.25 if (is_broad and is_core_overview_hit(hit)) else 0.0
            score = (1.0 / (1.0 + dist)) + (0.5 * overlap) + boost
        else:
            raise ValueError(f"Unknown retrieval mode: {mode}")
            
        scored.append((score, overlap, dist, hit["chunk_id"]))
        
    if not scored:
        return False, [], "no_candidates_survived_cutoff"
        
    # Sort by score descending, then distance ascending; complete ties retain input order.
    scored.sort(key=lambda item: (item[0], -item[2]), reverse=True)
    
    # Post-Rerank Gate 2: Top-hit overlap check
    if apply_gates and keywords and len(keywords) > 1:
        top_overlap = scored[0][1]
        if top_overlap < 0.15:
            return False, [], "rejected_top_overlap"
            
    ranked_ids = [item[3] for item in scored[:5]]
    return True, ranked_ids, "accepted"


def run_benchmark() -> int:
    print("=" * 70)
    print("GANGA AI MASCOT (PRJ_316) — RETRIEVAL ABLATION BENCHMARK RUNNER")
    print("=" * 70)
    
    # Step 1: Preflight Verification
    if not DATASET_PATH.exists():
        print(f"[ERROR] Dataset file not found at: {DATASET_PATH}")
        return 1
        
    raw_bytes = DATASET_PATH.read_bytes()
    current_hash = hashlib.sha256(raw_bytes).hexdigest()
    if current_hash != EXPECTED_DATASET_HASH:
        print(f"[ERROR] Dataset SHA-256 mismatch!")
        print(f"  Expected: {EXPECTED_DATASET_HASH}")
        print(f"  Actual:   {current_hash}")
        return 1
        
    print(f"[OK] Verified dataset SHA-256: {current_hash}")
    
    # Load dataset
    queries = []
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                queries.append(json.loads(line))
                
    if len(queries) != 30:
        print(f"[ERROR] Expected exactly 30 queries, found {len(queries)}.")
        return 1
    print(f"[OK] Loaded {len(queries)} benchmark queries.")
    
    # Initialize Vector Store & Retriever
    start_init = time.time()
    cfg = load_config()
    store = get_vector_store(cfg)
    retriever = Retriever(cfg, store)
    init_time = time.time() - start_init
    print(f"[OK] Initialized SQLiteVectorStore (4,085 chunks) in {init_time:.2f}s.")
    
    configurations = {
        "A": "Dense-Score Reranking (Euclidean Proximity)",
        "B": "Lexical-Overlap Reranking (within dense top-15 pool)",
        "C": "Unweighted Hybrid (Dense + 0.5*Lexical)",
        "D": "Proposed Hybrid (Dense + 0.5*Lexical + 0.25*OverviewBoost)",
    }
    
    categories = ["Broad/Thematic", "Technical/Scientific", "Governance/Policy"]
    
    results: dict[str, Any] = {
        "benchmark_metadata": {
            "project_id": "PRJ_316",
            "title": "Ganga AI Mascot Retrieval Ablation Benchmark",
            "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "dataset_path": str(DATASET_PATH.relative_to(ROOT_DIR)),
            "dataset_sha256": current_hash,
            "total_queries": len(queries),
            "configurations": configurations,
        },
        "query_level_results": {},
        "aggregate_summary": {},
    }
    
    # Run evaluation across configurations
    # We evaluate both with production gates (primary) and without gates (pure ranking)
    eval_settings = [
        ("production_gated", True),
        ("ungated_ranking", False),
    ]
    
    for setting_name, apply_gates in eval_settings:
        print(f"\n--- Running Evaluation Setting: {setting_name.upper()} (apply_gates={apply_gates}) ---")
        results["aggregate_summary"][setting_name] = {}
        
        for mode_key, mode_desc in configurations.items():
            conf_start = time.time()
            query_metrics = []
            cat_metrics: dict[str, list[dict[str, float]]] = {c: [] for c in categories}
            
            for q in queries:
                qid = q["query_id"]
                qtext = q["query"]
                qcat = q["category"]
                gold_set = set(q["gold_chunk_ids"])
                
                # Retrieve candidate pool (K_cand=15)
                candidates = retriever.retrieve_candidates(qtext, candidate_k=15)
                
                # Rank candidates
                accepted, retrieved_ids, status = rank_candidates(
                    qtext, candidates, mode=mode_key, apply_gates=apply_gates,
                    config_distance_cutoff=cfg.evidence_max_distance
                )
                
                p5, r5, mrr5 = compute_metrics(retrieved_ids, gold_set)
                
                metric_entry = {
                    "query_id": qid,
                    "query": qtext,
                    "category": qcat,
                    "accepted": accepted,
                    "status": status,
                    "retrieved_chunk_ids": retrieved_ids,
                    "gold_chunk_ids": list(gold_set),
                    "precision_at_5": round(p5, 4),
                    "recall_at_5": round(r5, 4),
                    "mrr_at_5": round(mrr5, 4),
                }
                query_metrics.append(metric_entry)
                cat_metrics[qcat].append({"p5": p5, "r5": r5, "mrr": mrr5})
                
                # Store in query_level_results
                if qid not in results["query_level_results"]:
                    results["query_level_results"][qid] = {
                        "query": qtext,
                        "category": qcat,
                        "gold_chunk_ids": list(gold_set),
                        "evaluations": {},
                    }
                if setting_name not in results["query_level_results"][qid]["evaluations"]:
                    results["query_level_results"][qid]["evaluations"][setting_name] = {}
                results["query_level_results"][qid]["evaluations"][setting_name][mode_key] = metric_entry
                
            elapsed = time.time() - conf_start
            
            # Compute Aggregates
            overall_p5 = float(np.mean([m["precision_at_5"] for m in query_metrics]))
            overall_r5 = float(np.mean([m["recall_at_5"] for m in query_metrics]))
            overall_mrr = float(np.mean([m["mrr_at_5"] for m in query_metrics]))
            
            cat_summary = {}
            for cat in categories:
                cat_p5 = float(np.mean([item["p5"] for item in cat_metrics[cat]]))
                cat_r5 = float(np.mean([item["r5"] for item in cat_metrics[cat]]))
                cat_mrr = float(np.mean([item["mrr"] for item in cat_metrics[cat]]))
                cat_summary[cat] = {
                    "precision_at_5": round(cat_p5, 4),
                    "recall_at_5": round(cat_r5, 4),
                    "mrr_at_5": round(cat_mrr, 4),
                }
                
            conf_agg = {
                "configuration_id": mode_key,
                "description": mode_desc,
                "overall": {
                    "precision_at_5": round(overall_p5, 4),
                    "recall_at_5": round(overall_r5, 4),
                    "mrr_at_5": round(overall_mrr, 4),
                },
                "by_category": cat_summary,
                "latency_total_seconds": round(elapsed, 4),
            }
            results["aggregate_summary"][setting_name][mode_key] = conf_agg
            
            print(f"[{mode_key}] {mode_desc[:35]:35s} | P@5: {overall_p5:.4f} | R@5: {overall_r5:.4f} | MRR@5: {overall_mrr:.4f} ({elapsed:.2f}s)")

    # Save JSON results
    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] Machine-readable results saved to: {OUTPUT_JSON_PATH}")
    
    # Generate Markdown Report
    _generate_markdown_report(results, OUTPUT_REPORT_PATH)
    print(f"[OK] Markdown experiment report saved to: {OUTPUT_REPORT_PATH}")
    
    # Print Paper Table
    _print_paper_tables(results)
    
    print("\n[SUCCESS] Retrieval ablation benchmark completed reproducibly!")
    return 0


def _generate_markdown_report(results: dict[str, Any], path: Path) -> None:
    meta = results["benchmark_metadata"]
    gated = results["aggregate_summary"]["production_gated"]
    ungated = results["aggregate_summary"]["ungated_ranking"]
    
    lines = [
        "# Retrieval Ablation Experiment Report: Ganga AI Mascot (PRJ_316)",
        f"**Official Project Title:** {OFFICIAL_PROJECT_TITLE}",
        "",
        f"**Date:** {meta['date']}  ",
        f"**Python Runtime:** {meta['python_version']} ({meta['platform']})  ",
        f"**Dataset SHA-256:** `{meta['dataset_sha256']}`  ",
        f"**Corpus Size:** 4,085 chunks (86 GRBMP PDFs)  ",
        "",
        "---",
        "",
        "## 1. Overview and Research Question",
        "",
        "> **Research Question (RQ1):** Within a shared dense-retrieved top-15 candidate pool, how do dense, lexical-overlap, hybrid, and overview-boosted reranking configurations compare on this curated GRBMP query set?",
        "",
        "**Evaluation scope:** Each configuration ranks the same dense-retrieved candidate pool. Config B is lexical-overlap reranking, not full-corpus lexical search. Production-gated runs also apply candidate-coverage and distance filters.",
        "",
        "---",
        "",
        "## 2. Overall Benchmark Results (All 30 Queries)",
        "",
        "### A. Production Gated Pipeline (Primary)",
        "Applies pre-rerank candidate pool coverage check ($\\ge 0.60$), Euclidean distance cutoff ($d \\le 1.15$), and post-rerank top-hit overlap gate ($\\ge 0.15$).",
        "",
        "| Configuration | Description | Precision@5 | Recall@5 | MRR@5 | Total Latency (s) |",
        "| :--- | :--- | :---: | :---: | :---: | :---: |",
    ]
    
    for k in ["A", "B", "C", "D"]:
        cfg_res = gated[k]
        lines.append(
            f"| **Config {k}** | {cfg_res['description']} | "
            f"**{cfg_res['overall']['precision_at_5']:.4f}** | "
            f"**{cfg_res['overall']['recall_at_5']:.4f}** | "
            f"**{cfg_res['overall']['mrr_at_5']:.4f}** | "
            f"{cfg_res['latency_total_seconds']:.2f}s |"
        )
        
    lines.extend([
        "",
        "### B. Ungated Reranking (No Evidence-Gate Rejections)",
        "Ranks the same dense candidate pool by each score without early-exit gate rejections; this is not a full-corpus retrieval comparison.",
        "",
        "| Configuration | Description | Precision@5 | Recall@5 | MRR@5 | Total Latency (s) |",
        "| :--- | :--- | :---: | :---: | :---: | :---: |",
    ])
    
    for k in ["A", "B", "C", "D"]:
        cfg_res = ungated[k]
        lines.append(
            f"| **Config {k}** | {cfg_res['description']} | "
            f"{cfg_res['overall']['precision_at_5']:.4f} | "
            f"{cfg_res['overall']['recall_at_5']:.4f} | "
            f"{cfg_res['overall']['mrr_at_5']:.4f} | "
            f"{cfg_res['latency_total_seconds']:.2f}s |"
        )
        
    lines.extend([
        "",
        "---",
        "",
        "## 3. Category-Level Performance (Production Gated)",
        "",
        "| Configuration | Category | Precision@5 | Recall@5 | MRR@5 |",
        "| :--- | :--- | :---: | :---: | :---: |",
    ])
    
    for k in ["A", "B", "C", "D"]:
        cfg_res = gated[k]
        for cat, scores in cfg_res["by_category"].items():
            lines.append(
                f"| Config {k} | {cat} | "
                f"{scores['precision_at_5']:.4f} | "
                f"{scores['recall_at_5']:.4f} | "
                f"{scores['mrr_at_5']:.4f} |"
            )
            
    lines.extend([
        "",
        "---",
        "",
        "## 4. Key Empirical Findings",
        "",
        "The tables report descriptive metrics on this 30-query set. They do not include uncertainty estimates or repeated-run variability, and do not establish general performance or a causal effect of overview boosting.",
        "",
        "---",
        "",
        "## 5. Reproduction command and provenance limits",
        "This command runs the benchmark with the current checkout and index; matching the saved artifact also requires matching code, index, configuration, and environment:",
        "```bash",
        "PYTHONPATH=. ./.venv/bin/python research/benchmark/run_retrieval_benchmark.py",
        "```",
        "The saved JSON records dataset hash, runtime/platform, query count, and configuration labels, but not the benchmark code commit or vector-index digest.",
    ])
    
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _print_paper_tables(results: dict[str, Any]) -> None:
    gated = results["aggregate_summary"]["production_gated"]
    print("\n" + "=" * 70)
    print("TABLE II FOR RESEARCH PAPER (RESULTS SECTION)")
    print("=" * 70)
    print(f"{'Configuration':<20} | {'Precision@5':<12} | {'Recall@5':<12} | {'MRR@5':<12}")
    print("-" * 65)
    for k in ["A", "B", "C", "D"]:
        row = gated[k]["overall"]
        print(f"Config {k:<13} | {row['precision_at_5']:<12.4f} | {row['recall_at_5']:<12.4f} | {row['mrr_at_5']:<12.4f}")
    print("=" * 70)
    
    print("\nCATEGORY-LEVEL MRR@5 BREAKDOWN:")
    print("-" * 65)
    print(f"{'Configuration':<12} | {'Broad/Thematic':<16} | {'Technical/Sci':<16} | {'Governance':<12}")
    print("-" * 65)
    for k in ["A", "B", "C", "D"]:
        b = gated[k]["by_category"]["Broad/Thematic"]["mrr_at_5"]
        t = gated[k]["by_category"]["Technical/Scientific"]["mrr_at_5"]
        g = gated[k]["by_category"]["Governance/Policy"]["mrr_at_5"]
        print(f"Config {k:<5} | {b:<16.4f} | {t:<16.4f} | {g:<12.4f}")
    print("=" * 70)


if __name__ == "__main__":
    sys.exit(run_benchmark())
