#!/usr/bin/env python3
"""Extract page-level text and provenance from GRBMP PDF source documents."""

from __future__ import annotations

import argparse
import json
import logging
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TextIO

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - exercised when the optional dependency is absent
    PdfReader = None  # type: ignore[assignment,misc]


LOGGER = logging.getLogger("extract_pdfs")
PDF_SUFFIX = ".pdf"
DEFAULT_INPUT_RELATIVE = Path("knowledge_base/raw/GRBMP")
LEGACY_INPUT_RELATIVE = Path("knowledge_base/raw_documents/GRBMP")
DEFAULT_OUTPUT_RELATIVE = Path("knowledge_base/processed")
PROCESSED_DOCUMENTS_DIRECTORY = "processed_documents"
REPORT_NAME = "extraction_report.json"


@dataclass
class ExtractionReport:
    total_pdfs_discovered: int = 0
    successfully_processed_pdfs: int = 0
    pdfs_with_extraction_warnings: int = 0
    pdfs_failed: int = 0
    total_pages_processed: int = 0
    pages_with_no_extractable_text: int = 0
    total_extracted_text_size: int = 0
    failed_files: list[dict[str, str]] = field(default_factory=list)
    warning_files: list[dict[str, Any]] = field(default_factory=list)
    ocr_candidates: list[dict[str, Any]] = field(default_factory=list)
    input_directory: str = ""
    output_directory: str = ""
    processed_documents_directory: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "total_pdfs_discovered": self.total_pdfs_discovered,
            "successfully_processed_pdfs": self.successfully_processed_pdfs,
            "pdfs_with_extraction_warnings": self.pdfs_with_extraction_warnings,
            "pdfs_failed": self.pdfs_failed,
            "total_pages_processed": self.total_pages_processed,
            "pages_with_no_extractable_text": self.pages_with_no_extractable_text,
            "total_extracted_text_size": self.total_extracted_text_size,
            "failed_files": self.failed_files,
            "warning_files": self.warning_files,
            "ocr_candidates": self.ocr_candidates,
            "input_directory": self.input_directory,
            "output_directory": self.output_directory,
            "processed_documents_directory": self.processed_documents_directory,
        }


def configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )


def resolve_input_directory(project_root: Path, requested: Path | None) -> Path:
    if requested is not None:
        return requested if requested.is_absolute() else project_root / requested

    preferred = project_root / DEFAULT_INPUT_RELATIVE
    if preferred.exists():
        return preferred

    legacy = project_root / LEGACY_INPUT_RELATIVE
    if legacy.exists():
        LOGGER.warning(
            "Requested input directory %s is absent; using existing repository path %s",
            DEFAULT_INPUT_RELATIVE,
            LEGACY_INPUT_RELATIVE,
        )
        return legacy

    return preferred


def discover_pdfs(input_directory: Path) -> list[Path]:
    if not input_directory.exists():
        return []
    return sorted(
        path
        for path in input_directory.rglob("*")
        if path.is_file() and path.suffix.lower() == PDF_SUFFIX
    )


def clean_text(text: str) -> str:
    """Remove extraction noise without rewriting the source content."""
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")
    text = re.sub(r"(?<=\w)-\n(?=\w)", "", text)

    cleaned_lines: list[str] = []
    previous_nonempty: str | None = None
    blank_count = 0
    for raw_line in text.split("\n"):
        line = re.sub(r"[ \t]+", " ", raw_line).strip()
        if not line:
            blank_count += 1
            if blank_count <= 2:
                cleaned_lines.append("")
            continue

        blank_count = 0
        if line == previous_nonempty:
            continue
        cleaned_lines.append(line)
        previous_nonempty = line

    return "\n".join(cleaned_lines).strip()


def likely_heading(line: str) -> bool:
    if not line or len(line) > 140:
        return False
    words = line.split()
    if len(words) > 14:
        return False
    if re.match(r"^(?:\d+(?:\.\d+)*|[IVXLC]+)[.)]\s+\S", line, re.IGNORECASE):
        return True
    letters = [character for character in line if character.isalpha()]
    return (
        len(letters) >= 3
        and len(words) <= 12
        and line == line.upper()
        and not line.endswith((".", ";", ":", ","))
    )


def detect_section(text: str, previous_section: str | None) -> str | None:
    for line in text.splitlines():
        candidate = line.strip()
        if likely_heading(candidate):
            return candidate
    return previous_section


def reader_title(reader: Any, file_path: Path) -> str:
    metadata = reader.metadata
    title = getattr(metadata, "title", None) if metadata else None
    if isinstance(title, str) and title.strip():
        return title.strip()
    return file_path.stem


def relative_source_path(file_path: Path, project_root: Path) -> str:
    try:
        return file_path.relative_to(project_root).as_posix()
    except ValueError:
        return file_path.name


def page_record(
    *,
    file_path: Path,
    project_root: Path,
    title: str,
    page_number: int,
    section: str | None,
    extracted_text: str,
    extraction_status: str,
    extraction_error: str | None = None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "source_id": None,
        "source_mapping_status": "unresolved",
        "source_status": None,
        "file_name": file_path.name,
        "relative_path": relative_source_path(file_path, project_root),
        "title": title,
        "page": page_number,
        "section": section,
        "topic": None,
        "knowledge_type": None,
        "time_period": None,
        "relevance": None,
        "extracted_text": extracted_text,
        "extraction_status": extraction_status,
    }
    if extraction_error:
        record["extraction_error"] = extraction_error
    return record


def write_jsonl_record(output: TextIO, record: dict[str, Any]) -> None:
    output.write(json.dumps(record, ensure_ascii=True) + "\n")


def output_path_for_pdf(
    file_path: Path,
    *,
    input_directory: Path,
    processed_documents_directory: Path,
) -> Path:
    relative_path = file_path.relative_to(input_directory)
    return (processed_documents_directory / relative_path).with_suffix(".jsonl")


def replace_document_output(file_path: Path, records: list[dict[str, Any]]) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=file_path.parent, prefix=f".{file_path.name}.", delete=False
    ) as temporary:
        for record in records:
            write_jsonl_record(temporary, record)
        temporary_path = Path(temporary.name)
    temporary_path.replace(file_path)


def process_pdf(
    file_path: Path,
    *,
    project_root: Path,
    input_directory: Path,
    processed_documents_directory: Path,
    report: ExtractionReport,
) -> None:
    warnings: list[str] = []
    pages_processed = 0
    no_text_pages = 0
    document_text_size = 0
    section: str | None = None
    title = file_path.stem
    records: list[dict[str, Any]] = []

    try:
        reader = PdfReader(str(file_path))
        if reader.is_encrypted:
            decrypt_result = reader.decrypt("")
            if not decrypt_result:
                raise RuntimeError("PDF is encrypted and could not be opened with an empty password")
        title = reader_title(reader, file_path)
    except Exception as error:
        report.pdfs_failed += 1
        report.failed_files.append(
            {
                "file_name": file_path.name,
                "relative_path": relative_source_path(file_path, project_root),
                "error": str(error),
            }
        )
        LOGGER.error("Failed to open %s: %s", file_path, error)
        return

    try:
        page_count = len(reader.pages)
    except Exception as error:
        report.pdfs_failed += 1
        report.failed_files.append(
            {
                "file_name": file_path.name,
                "relative_path": relative_source_path(file_path, project_root),
                "error": f"could not enumerate pages: {error}",
            }
        )
        LOGGER.error("Failed to enumerate pages in %s: %s", file_path, error)
        return

    for page_number in range(1, page_count + 1):
        pages_processed += 1
        report.total_pages_processed += 1
        try:
            page = reader.pages[page_number - 1]
            raw_text = page.extract_text() or ""
            extracted_text = clean_text(raw_text)
            if extracted_text:
                section = detect_section(extracted_text, section)
                status = "success"
                document_text_size += len(extracted_text)
                report.total_extracted_text_size += len(extracted_text)
            else:
                no_text_pages += 1
                report.pages_with_no_extractable_text += 1
                status = "no_text"
                warnings.append(f"page {page_number}: no extractable text; OCR/manual review may be required")
            records.append(
                page_record(
                    file_path=file_path,
                    project_root=project_root,
                    title=title,
                    page_number=page_number,
                    section=section,
                    extracted_text=extracted_text,
                    extraction_status=status,
                ),
            )
        except Exception as error:
            warnings.append(f"page {page_number}: {error}")
            records.append(
                page_record(
                    file_path=file_path,
                    project_root=project_root,
                    title=title,
                    page_number=page_number,
                    section=section,
                    extracted_text="",
                    extraction_status="page_error",
                    extraction_error=str(error),
                ),
            )
            LOGGER.warning("Failed to extract %s page %d: %s", file_path, page_number, error)

    if pages_processed == 0:
        warnings.append("PDF contains no pages")
    elif no_text_pages == pages_processed:
        warnings.append("document contains no extractable text; OCR/manual review is required")
    elif no_text_pages:
        warnings.append(f"{no_text_pages} of {pages_processed} pages have no extractable text")

    report.successfully_processed_pdfs += 1
    if pages_processed > 0 and (
        no_text_pages == pages_processed
        or no_text_pages / pages_processed >= 0.5
        or document_text_size < 100
    ):
        report.ocr_candidates.append(
            {
                "file_name": file_path.name,
                "relative_path": relative_source_path(file_path, project_root),
                "pages_processed": pages_processed,
                "pages_with_no_extractable_text": no_text_pages,
                "reason": "little or no extractable text; OCR/manual review may be required",
            }
        )

    output_path = output_path_for_pdf(
        file_path,
        input_directory=input_directory,
        processed_documents_directory=processed_documents_directory,
    )
    replace_document_output(output_path, records)

    if warnings:
        report.pdfs_with_extraction_warnings += 1
        report.warning_files.append(
            {
                "file_name": file_path.name,
                "relative_path": relative_source_path(file_path, project_root),
                "warnings": warnings,
            }
        )
        LOGGER.warning("Processed %s with %d warning(s)", file_path, len(warnings))
    else:
        LOGGER.info("Processed %s (%d pages, %d text characters)", file_path, pages_processed, document_text_size)


def write_report(output_directory: Path, report: ExtractionReport) -> None:
    report_path = output_directory / REPORT_NAME
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=output_directory, prefix=f".{REPORT_NAME}.", delete=False
    ) as temporary:
        json.dump(report.as_dict(), temporary, indent=2, ensure_ascii=True)
        temporary.write("\n")
        temporary_path = Path(temporary.name)
    temporary_path.replace(report_path)


def run_extraction(project_root: Path, input_directory: Path, output_directory: Path) -> ExtractionReport:
    if PdfReader is None:
        raise RuntimeError("Missing dependency: install pypdf with `python3 -m pip install pypdf`")

    pdf_files = discover_pdfs(input_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    processed_documents_directory = output_directory / PROCESSED_DOCUMENTS_DIRECTORY
    if processed_documents_directory.exists():
        shutil.rmtree(processed_documents_directory)
    processed_documents_directory.mkdir(parents=True, exist_ok=True)
    report = ExtractionReport(
        total_pdfs_discovered=len(pdf_files),
        input_directory=relative_source_path(input_directory, project_root),
        output_directory=relative_source_path(output_directory, project_root),
        processed_documents_directory=relative_source_path(processed_documents_directory, project_root),
    )

    for file_path in pdf_files:
        process_pdf(
            file_path,
            project_root=project_root,
            input_directory=input_directory,
            processed_documents_directory=processed_documents_directory,
            report=report,
        )

    write_report(output_directory, report)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir",
        type=Path,
        help=f"PDF root directory (default: {DEFAULT_INPUT_RELATIVE.as_posix()})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_RELATIVE,
        help=f"Processed output directory (default: {DEFAULT_OUTPUT_RELATIVE.as_posix()})",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    configure_logging(args.verbose)
    project_root = Path(__file__).resolve().parents[2]
    input_directory = resolve_input_directory(project_root, args.input_dir)
    output_directory = args.output_dir if args.output_dir.is_absolute() else project_root / args.output_dir

    if not input_directory.exists():
        LOGGER.error("Input directory does not exist: %s", input_directory)
        return 2

    try:
        report = run_extraction(project_root, input_directory, output_directory)
    except RuntimeError as error:
        LOGGER.error("%s", error)
        return 2

    LOGGER.info(
        "Extraction complete: %d discovered, %d successful, %d warning, %d failed",
        report.total_pdfs_discovered,
        report.successfully_processed_pdfs,
        report.pdfs_with_extraction_warnings,
        report.pdfs_failed,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
