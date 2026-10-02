"""Main RAG Pipeline entry point and answer orchestrator for Ganga Brain."""

from __future__ import annotations

import argparse
import json

from .config import load_config
from .generator import build_generator, current_information_response, insufficient_evidence_response
from .retriever import Retriever, asks_for_current_information
from .translator import normalize_language, translate_text
from .vector_store import build_index as build_vector_index


def build_index() -> dict:
    """Build the complete SQLite/NumPy index from reviewed sections."""
    return build_vector_index(load_config())


def answer_question(
    question: str,
    top_k: int | None = None,
    input_language: str | None = None,
    output_language: str | None = None,
) -> dict:
    """Answer a question; unspecified language defaults to English."""
    input_lang = normalize_language(input_language, default="en")
    output_lang = normalize_language(output_language, default=input_lang)

    if not question or not question.strip():
        resp = insufficient_evidence_response()
        resp["answer"] = translate_text(resp["answer"], "en", output_lang)
        resp["input_language"] = input_lang
        resp["output_language"] = output_lang
        return resp

    config = load_config()

    # Translate input question to English for retrieval if input is Hindi
    search_question = question
    if input_lang == "hi":
        search_question = translate_text(question, "hi", "en")

    # Step 1: Detect current/realtime information request
    if asks_for_current_information(question) or asks_for_current_information(search_question):
        resp = current_information_response()
        resp["answer"] = translate_text(resp["answer"], "en", output_lang)
        resp["input_language"] = input_lang
        resp["output_language"] = output_lang
        return resp

    # Step 2: Retrieve candidates & run Evidence Quality Gate
    retriever = Retriever(config)
    is_sufficient, hits = retriever.retrieve(search_question, top_k)

    # Step 3: Check Evidence Quality Gate result
    if not is_sufficient or not hits:
        resp = insufficient_evidence_response()
        resp["answer"] = translate_text(resp["answer"], "en", output_lang)
        resp["input_language"] = input_lang
        resp["output_language"] = output_lang
        return resp

    # Step 4: Generate grounded answer with citations
    generator = build_generator(config.llm_provider, config.llm_model)
    result = generator.generate(
        search_question,
        hits,
        is_sufficient,
        input_language=input_lang,
        output_language=output_lang,
    )

    # Step 5: Translate answer to output_language if requested
    if output_lang != "en":
        result["answer"] = translate_text(result["answer"], "en", output_lang)

    result["input_language"] = input_lang
    result["output_language"] = output_lang
    result["retrieved"] = [
        {
            "chunk_id": hit["chunk_id"],
            "distance": hit.get("distance", 0.0),
            "source": hit["metadata"].get("title"),
            "page": f"{hit['metadata'].get('page_start')}-{hit['metadata'].get('page_end')}",
            "section": hit["metadata"].get("section"),
        }
        for hit in hits
    ]
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-index", action="store_true", help="Build the complete reviewed-data SQLite/NumPy index.")
    parser.add_argument("--ask", help="Ask the prototype Brain a question.")
    parser.add_argument("--top-k", type=int, help="Override retriever top-k.")
    args = parser.parse_args()

    if args.build_index:
        print(json.dumps(build_index(), indent=2))
    if args.ask:
        print(json.dumps(answer_question(args.ask, args.top_k), indent=2))
    if not args.build_index and not args.ask:
        parser.error("use --build-index and/or --ask")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
