"""Build the derived prototype ingestion manifest from approved sections."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .config import APPROVED_CLASSIFICATIONS, BrainConfig, load_config


def load_document_pages(processed_documents_dir: Path, file_name: str) -> dict[int, str]:
    """Load one processed JSONL document once and index its pages."""
    path = processed_documents_dir / Path(file_name).with_suffix(".jsonl").name
    if not path.exists():
        return {}

    pages: dict[int, str] = {}

    with path.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            page = int(record.get("page") or 0)
            text = (record.get("extracted_text") or "").strip()

            if text:
                pages[page] = text

    return pages


def load_page_text(
    processed_documents_dir: Path,
    file_name: str,
    page_start: int,
    page_end: int,
) -> str:
    """Load text for a page range from one processed JSONL document."""
    pages = load_document_pages(processed_documents_dir, file_name)

    selected = []
    for page in range(page_start, page_end + 1):
        text = pages.get(page)
        if text:
            selected.append(f"[Page {page}]\n{text}")

    return "\n\n".join(selected).strip()


def build_manifest(config: BrainConfig) -> dict:
    review = json.loads(
        config.section_review_path.read_text(encoding="utf-8")
    )

    selected = []
    skipped_missing_text = 0

    # Cache processed documents so each JSONL file is read only once.
    document_cache: dict[str, dict[int, str]] = {}

    for index, section in enumerate(review.get("sections", []), start=1):
        classification = section.get("section_classification")

        if classification not in APPROVED_CLASSIFICATIONS:
            continue

        file_name = section["file_name"]

        if file_name not in document_cache:
            document_cache[file_name] = load_document_pages(
                config.processed_documents_dir,
                file_name,
            )

        pages = document_cache[file_name]

        page_start = int(section.get("page_start") or 0)
        page_end = int(section.get("page_end") or page_start)

        page_texts = []

        for page in range(page_start, page_end + 1):
            text = pages.get(page)

            if text:
                page_texts.append(f"[Page {page}]\n{text}")

        text = "\n\n".join(page_texts).strip()

        if not text:
            skipped_missing_text += 1
            continue

        selected.append(
            {
                "section_id": f"prototype-section-{index:05d}",
                "original_section_id": section.get("section_id"),
                "source_id": section.get("source_id"),
                "file_name": file_name,
                "title": section.get("title"),
                "source_status": section.get("source_status"),
                "document_type": section.get("document_type"),
                "section": section.get("section"),
                "subsection": section.get("subsection"),
                "page_start": page_start,
                "page_end": page_end,
                "section_classification": classification,
                "knowledge_type": section.get("knowledge_type"),
                "time_period": section.get("temporal_context"),
                "geographic_scope": section.get("geographic_scope"),
                "relevance": section.get("relevance"),
                "provenance": {
                    "source_id": section.get("source_id"),
                    "file_name": file_name,
                    "title": section.get("title"),
                    "pages": list(range(page_start, page_end + 1)),
                    "section": section.get("section"),
                    "subsection": section.get("subsection"),
                    "original_section_id": section.get("section_id"),
                },
                "text": text,
            }
        )

    return {
        "manifest_version": "prototype-ingestion-v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_review": str(
            config.section_review_path.relative_to(
                config.section_review_path.parents[2]
            )
        ),
        "selection_rule": (
            "Only sections classified KEEP, KEEP_HISTORICAL, "
            "or KEEP_METHODOLOGICAL."
        ),
        "excluded_classifications": [
            "REVIEW_REQUIRED",
            "OCR_REQUIRED",
            "FILTER",
            "EXCLUDE",
        ],
        "summary": {
            "selected_sections": len(selected),
            "skipped_missing_text": skipped_missing_text,
            "documents_loaded": len(document_cache),
        },
        "sections": selected,
    }


def write_markdown(manifest: dict, path: Path) -> None:
    lines = [
        "# Prototype Ingestion Manifest",
        "",
        f"Generated: `{manifest['generated_at_utc']}`",
        "",
        "This is a derived prototype manifest. "
        "It does not change source classifications.",
        "",
        "## Selection Rule",
        "",
        manifest["selection_rule"],
        "",
        "Excluded classifications: `REVIEW_REQUIRED`, `OCR_REQUIRED`, "
        "`FILTER`, `EXCLUDE`.",
        "",
        "## Summary",
        "",
        f"- Selected sections: "
        f"**{manifest['summary']['selected_sections']}**",
        f"- Skipped approved sections with missing text: "
        f"**{manifest['summary']['skipped_missing_text']}**",
        f"- Documents loaded: "
        f"**{manifest['summary']['documents_loaded']}**",
        "",
        "## Included Sections",
        "",
    ]

    for section in manifest["sections"]:
        lines.append(
            f"- `{section['section_id']}` — "
            f"`{section['source_id']}`; "
            f"`{section['file_name']}`; "
            f"pages {section['page_start']}-{section['page_end']}; "
            f"{section['section_classification']}; "
            f"{section['knowledge_type']}; "
            f"section: `{section['section']}`"
        )

    path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def write_manifest(config: BrainConfig) -> dict:
    manifest = build_manifest(config)

    config.prototype_manifest_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    config.prototype_manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    write_markdown(
        manifest,
        config.prototype_manifest_md_path,
    )

    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print manifest summary after writing it.",
    )

    args = parser.parse_args()

    manifest = write_manifest(load_config())

    if args.summary:
        print(json.dumps(manifest["summary"], indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())