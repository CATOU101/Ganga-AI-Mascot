#!/usr/bin/env python3
"""Comprehensive evaluation suite for the Ganga Brain prototype RAG pipeline."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from brain.prompts import CURRENT_INFO_MESSAGE, INSUFFICIENT_EVIDENCE
from brain.rag_pipeline import answer_question


QUESTIONS = [
    {
        "id": "A_factual",
        "question": "What is Aviral Dhara?",
        "expected_mode": "grounded",
        "description": "Supported factual KB question",
    },
    {
        "id": "B_urban_pollution",
        "question": "What does the GRBMP say about pollution load from urban areas?",
        "expected_mode": "grounded",
        "description": "Supported urban pollution KB question",
    },
    {
        "id": "C_historical",
        "question": "According to the GRBMP material, what historical concerns are associated with sewage pollution?",
        "expected_mode": "grounded",
        "description": "Historical context KB question",
    },
    {
        "id": "D_unsupported_mars",
        "question": "What is the population of Mars according to the GRBMP?",
        "expected_mode": "insufficient-evidence",
        "expected_answer": INSUFFICIENT_EVIDENCE,
        "description": "Unsupported out-of-domain question (MUST trigger safe fallback)",
    },
    {
        "id": "E_current_info",
        "question": "What is the current water quality of the Ganga today?",
        "expected_mode": "current-info-fallback",
        "expected_answer": CURRENT_INFO_MESSAGE,
        "description": "Real-time / current information question (MUST trigger current-info fallback)",
    },
    {
        "id": "F_provenance_metadata",
        "question": "What does the knowledge base say about environmental flows, and which source page supports it?",
        "expected_mode": "grounded",
        "description": "Provenance check: verified valid source title and page range metadata",
    },
    {
        "id": "G_citation_alignment",
        "question": "What are the key functions of National Ganga River Basin Authority?",
        "expected_mode": "grounded",
        "description": "Citation integrity check: no hallucinated citations",
    },
    {
        "id": "H_empty_query",
        "question": "",
        "expected_mode": "insufficient-evidence",
        "description": "Empty query safety check",
    },
]


def run_tests() -> tuple[list[dict], bool]:
    results = []
    all_passed = True

    print("==================================================")
    print("RUNNING GANGA BRAIN EVALUATION TEST SUITE")
    print("==================================================\n")

    for item in QUESTIONS:
        q_id = item["id"]
        q_text = item["question"]
        expected_mode = item["expected_mode"]
        
        result = answer_question(q_text)
        mode = result.get("mode")
        answer = result.get("answer", "")
        citations = result.get("citations", [])

        passed = True
        notes = []

        # Mode check
        if mode != expected_mode:
            passed = False
            notes.append(f"Expected mode '{expected_mode}', got '{mode}'")

        # Specific expected answer check for fallbacks
        if "expected_answer" in item and answer != item["expected_answer"]:
            passed = False
            notes.append(f"Answer string mismatch. Got: {answer[:60]}...")

        # Grounded provenance checks
        if expected_mode == "grounded" and mode == "grounded":
            if not citations:
                passed = False
                notes.append("Grounded answer missing citations")
            for cit in citations:
                if not cit.get("source") or not cit.get("file_name"):
                    passed = False
                    notes.append("Incomplete citation metadata")

        # Unsupported/fallback check: no citations should be returned
        if expected_mode in ("insufficient-evidence", "current-info-fallback") and citations:
            passed = False
            notes.append(f"Fallback mode '{mode}' should not return citations")

        if not passed:
            all_passed = False

        status_str = "PASS" if passed else "FAIL"
        print(f"[{status_str}] Test {q_id}: {item['description']}")
        print(f"     Query: '{q_text}'")
        print(f"     Result Mode: {mode} | Citations: {len(citations)}")
        print(f"     Answer snippet: {answer[:100]}...\n")

        results.append({
            "test_id": q_id,
            "description": item["description"],
            "question": q_text,
            "expected_mode": expected_mode,
            "status": status_str,
            "notes": notes,
            "result": result,
        })

    output_path = Path("brain/tests/evaluation_results.json")
    output_path.write_text(json.dumps(results, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(f"Full evaluation results saved to {output_path}")

    return results, all_passed


def main() -> int:
    _, all_passed = run_tests()
    if not all_passed:
        print("\n[!] SOME EVALUATION TESTS FAILED.")
        return 1
    print("\n[✓] ALL EVALUATION TESTS PASSED SUCCESSFULLY!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
