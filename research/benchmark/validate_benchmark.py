#!/usr/bin/env python3
"""Validation harness for the Ganga AI Mascot 30-Query Retrieval Benchmark."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
BENCHMARK_DIR = ROOT_DIR / "research" / "benchmark"
DATASET_PATH = BENCHMARK_DIR / "domain_queries_30.jsonl"
DB_PATH = ROOT_DIR / "knowledge_base" / "vector_db" / "brain_index.sqlite3"

EXPECTED_CATEGORIES = {
    "Broad/Thematic": 10,
    "Technical/Scientific": 10,
    "Governance/Policy": 10,
}


def validate() -> bool:
    print("=" * 60)
    print("VALIDATING RETRIEVAL BENCHMARK DATASET (PRJ_316)")
    print("=" * 60)

    if not DATASET_PATH.exists():
        print(f"[FAIL] Dataset file not found at: {DATASET_PATH}")
        return False

    if not DB_PATH.exists():
        print(f"[FAIL] Vector database not found at: {DB_PATH}")
        return False

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Verify SQLite collection count
    cursor.execute("SELECT count(*) FROM chunks")
    total_corpus_chunks = cursor.fetchone()[0]
    print(f"[OK] Connected to SQLite corpus: {total_corpus_chunks} chunks indexed.")

    # Read dataset
    records = []
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line_str = line.strip()
            if not line_str:
                continue
            try:
                rec = json.loads(line_str)
                records.append(rec)
            except json.JSONDecodeError as err:
                print(f"[FAIL] Invalid JSON at line {line_num}: {err}")
                return False

    # Check query count
    if len(records) != 30:
        print(f"[FAIL] Expected 30 queries, found {len(records)}.")
        return False
    print(f"[OK] Total benchmark queries: {len(records)} (Target: 30)")

    # Category balance check
    category_counts: dict[str, int] = {}
    seen_ids = set()
    seen_texts = set()
    all_gold_chunks = set()
    errors = []

    for rec in records:
        qid = rec.get("query_id")
        qtext = rec.get("query", "").strip()
        cat = rec.get("category")
        gold_cids = rec.get("gold_chunk_ids", [])
        expected_ans = rec.get("expected_answer", "").strip()
        primary_title = rec.get("primary_source_title", "").strip()
        rationale = rec.get("rationale", "").strip()

        # ID uniqueness
        if not qid or qid in seen_ids:
            errors.append(f"Duplicate or empty query_id: {qid}")
        seen_ids.add(qid)

        # Text uniqueness
        if not qtext or qtext.lower() in seen_texts:
            errors.append(f"Duplicate or empty query text: '{qtext}'")
        seen_texts.add(qtext.lower())

        # Category check
        category_counts[cat] = category_counts.get(cat, 0) + 1

        # Content completeness
        if not expected_ans:
            errors.append(f"Missing expected_answer for {qid}")
        if not primary_title:
            errors.append(f"Missing primary_source_title for {qid}")
        if not rationale:
            errors.append(f"Missing rationale for {qid}")
        if not gold_cids:
            errors.append(f"No gold_chunk_ids defined for {qid}")

        # Validate each gold chunk against SQLite
        for cid in gold_cids:
            all_gold_chunks.add(cid)
            cursor.execute("SELECT chunk_id, text, metadata_json FROM chunks WHERE chunk_id = ?", (cid,))
            row = cursor.fetchone()
            if not row:
                errors.append(f"{qid}: Gold chunk '{cid}' does not exist in SQLite database!")
            else:
                chunk_id, text, mjson = row
                if not text or len(text.strip()) < 20:
                    errors.append(f"{qid}: Gold chunk '{cid}' has suspiciously short or empty text.")
                md = json.loads(mjson)
                if not md.get("title") or not md.get("file_name"):
                    errors.append(f"{qid}: Gold chunk '{cid}' has incomplete metadata.")

    # Validate category counts
    for cat, expected in EXPECTED_CATEGORIES.items():
        actual = category_counts.get(cat, 0)
        if actual != expected:
            errors.append(f"Category '{cat}': expected {expected}, found {actual}")
        else:
            print(f"[OK] Category '{cat}': {actual} queries")

    # Content hash
    sha256 = hashlib.sha256(DATASET_PATH.read_bytes()).hexdigest()
    print(f"[OK] Unique gold evidence chunks verified: {len(all_gold_chunks)}")
    print(f"[OK] Dataset SHA-256 Digest: {sha256}")

    if errors:
        print("\n[FAIL] VALIDATION FAILED WITH ERRORS:")
        for err in errors:
            print(f"  - {err}")
        return False

    print("\n[SUCCESS] Dataset structure and gold-chunk existence checks passed.")
    print("Dataset structure and referenced chunk existence checks passed; annotation support and run reproducibility are not established by this validator.")
    return True


if __name__ == "__main__":
    success = validate()
    sys.exit(0 if success else 1)
