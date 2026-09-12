# Local OCR Workflow

## Environment checked

The initial 2026-09-12 check found no `tesseract` or `pdftoppm`. Homebrew subsequently made Poppler 26.09.0 and Tesseract 5.5.3 available locally. The Python packages `fitz`, `pdf2image`, `pytesseract`, `Pillow`, and `pypdf` remain unavailable and are not required by this subprocess-based workflow.

No dependency was installed automatically and no OCR was executed.

## Selected method

The workflow uses local Poppler `pdftoppm` rendering followed by the Tesseract command-line engine. This is a well-supported, local, reproducible path for image-based PDF pages and avoids uploading project documents to an external service. Python OCR bindings are not required.

Prerequisites on macOS are typically available through a local package manager:

```text
pdftoppm
tesseract
```

Install and configure those tools separately according to the machine's approved dependency policy. The workflow does not install them automatically.

## Inputs and outputs

The source of truth is `knowledge_base/processed/ocr_required_manifest.json`. The script processes only pages explicitly present in that manifest, or the single pilot page when `--pilot` is used.

Derived output is written below:

```text
knowledge_base/processed/ocr/
  page_ocr/<pdf-stem>/page-0002.txt
  document_ocr/<pdf-stem>/page-0001.txt
  manifests/ocr_execution_manifest.json
  reports/ocr_pilot_report.md
  reports/ocr_validation_report.md
```

Original PDFs under `knowledge_base/raw_documents/` and extracted JSONL files are never overwritten.

## Reproduction

Create a non-executing preflight manifest:

```bash
python3 knowledge_base/scripts/ocr_documents.py --preflight
```

Run the one-page pilot:

```bash
python3 knowledge_base/scripts/ocr_documents.py --pilot
```

Run all explicitly listed page-level and full-document jobs only after the pilot passes:

```bash
python3 knowledge_base/scripts/ocr_documents.py --run-manifest
```

The script never discovers or OCRs every PDF automatically. Full-document mode is driven only by the manifest's `FULL_DOCUMENT` entry; the Surface and Groundwater Modelling candidate therefore produces page files for pages 1-99, not one provenance-ambiguous combined file.

## Provenance and validation

Each OCR record preserves `source_id`, original filename, page number, input path, output path, OCR mode, engine/configuration, timestamp, status, character count, and an input PDF SHA-256 hash. Page text is stored separately so `source PDF -> page -> OCR output` remains recoverable.

Validate execution records with:

```bash
python3 knowledge_base/scripts/validate_ocr.py
```

Validation checks requested-page coverage, duplicates, source IDs, page numbers, output existence/non-empty text, and the recorded input hash. OCR output remains clearly marked as derived and is not merged into `processed_documents/`.

## Current status

The workflow is **IMPLEMENTED** and **TESTED** against the local executables. The mandated pilot was **EXECUTED** but returned empty text because the rendered page was blank; validation therefore remains **PENDING/FAIL** for full execution. A successful pilot is required before processing remaining candidates.

## Limitations

- OCR quality depends on scan resolution, page layout, language data, skew, tables, figures, and Tesseract configuration.
- When available, confidence is the mean non-negative word confidence from a second Tesseract TSV pass; a missing confidence value is retained as `null` rather than invented.
- OCR does not repair section classification or decide KEEP/FILTER/EXCLUDE.
- OCR output requires manual readability and provenance review before any downstream knowledge-base use.