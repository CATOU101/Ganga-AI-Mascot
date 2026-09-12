"""Main RAG Pipeline entry point and answer orchestrator for Ganga Brain."""

from __future__ import annotations

import argparse
import json

from .chunking import chunks_from_sections
from .config import load_config
from .generator import build_generator, current_information_response, insufficient_evidence_response
from .ingest import write_manifest
from .retriever import Retriever, asks_for_current_information
from .vector_store import SQLiteVectorStore, generate_semantic_vectors


def load_manifest_sections(config):
    if not config.prototype_manifest_path.exists():
        write_manifest(config)
    return json.loads(config.prototype_manifest_path.read_text(encoding="utf-8"))["sections"]


def build_index() -> dict:
    """Build or rebuild the portable semantic vector index from approved sections."""
    config = load_config()
    manifest = write_manifest(config)
    return generate_semantic_vectors(config)


def answer_question(question: str, top_k: int | None = None) -> dict:
    """Answer a user question through the complete grounded RAG pipeline."""
    if not question or not question.strip():
        return insufficient_evidence_response()

    config = load_config()

    # Step 1: Detect current/realtime information request
    if asks_for_current_information(question):
        return current_information_response()

    # Step 2: Retrieve candidates & run Evidence Quality Gate
    retriever = Retriever(config)
    is_sufficient, hits = retriever.retrieve(question, top_k)

    # Step 3: Check Evidence Quality Gate result
    if not is_sufficient or not hits:
        return insufficient_evidence_response()

    # Step 4: Generate grounded answer with citations
    generator = build_generator(config.llm_provider, config.llm_model)
    result = generator.generate(question, hits, is_sufficient)

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
    parser.add_argument("--build-index", action="store_true", help="Generate portable semantic_vectors.npy index.")
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
