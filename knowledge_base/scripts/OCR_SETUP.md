# OCR Dependency Setup

## Project root and environment

The project root is the Git repository directory containing `.git/`, `.github/`, and `knowledge_base/`. The Python environment must be located exactly at:

```text
<PROJECT_ROOT>/.venv/
```

Activate it from the project root with:

```bash
source .venv/bin/activate
```

`.venv/` must not be committed to Git. The repository `.gitignore` includes `.venv/`, `.env`, `__pycache__/`, and `*.py[cod]`.

## Current environment

Checked on 2026-09-12 from the repository root on macOS:

- Homebrew: available at `/opt/homebrew/bin/brew`
- Active Python: Homebrew Python 3.13.3 at `/opt/homebrew/opt/python@3.13/bin/python3.13`
- Project-local `.venv`: `/Users/madhavan/Documents/Ganga-AI-Mascot/Ganga-AI-Mascot/.venv/`
- `requirements.txt`, `pyproject.toml`, `Pipfile`, `environment.yml`, and lockfiles: not present
- Poppler / `pdftoppm`: system-level Homebrew formula, version 26.09.0
- Tesseract: system-level Homebrew formula, version 5.5.3; `eng` and `osd` language data available
- OCRmyPDF, PyMuPDF, `pdf2image`, `pytesseract`, Pillow, and `pypdf`: unavailable before setup

The existing OCR scripts use Python standard-library modules plus the external `pdftoppm` and `tesseract` executables. No Python OCR binding is required. No `requirements.txt` or competing dependency mechanism exists or is needed for the current scripts.

## Operating-system requirements

- macOS with Homebrew access, or an equivalent local package manager
- Read access to `knowledge_base/raw_documents/GRBMP/`
- Write access to `knowledge_base/processed/ocr/`
- Sufficient temporary disk space for 300-DPI PNG page renders

The workflow is local and does not upload project PDFs.

## Install system dependencies

Documented Homebrew commands:

```bash
brew update
brew install poppler tesseract
```

These commands install system dependencies only. They do not modify PDFs, extracted JSONL, source metadata, or section classifications.

## Verify system dependencies

```bash
command -v pdftoppm
pdftoppm -v
command -v tesseract
tesseract --version
tesseract --list-langs
```

The default workflow expects the English language data to be available as `eng`. Add other language data only when a source-specific review establishes that it is needed.

## Verify Python

```bash
which python
which python3
python --version
python -m pip --version
python -c 'import sys; print(sys.executable); print(sys.version)'
python -m py_compile knowledge_base/scripts/ocr_documents.py knowledge_base/scripts/validate_ocr.py
```

The OCR scripts require only the Python standard library. No `pip install` command is required for the current implementation.

The expected Python path after activation is `<PROJECT_ROOT>/.venv/bin/python`. The current scripts need no third-party Python packages, so the environment is intentionally standard-library-only.

## Reproduce the workflow

From the repository root:

```bash
source .venv/bin/activate
python knowledge_base/scripts/ocr_documents.py --preflight
python knowledge_base/scripts/ocr_documents.py --pilot
python knowledge_base/scripts/validate_ocr.py
```

The pilot is restricted to the first page-level candidate in `ocr_required_manifest.json`: `11_Mission 8 - Environmental Knowledge (1).pdf`, page 2. Do not run the full manifest until the pilot report is successful.

After a successful pilot, the complete explicitly listed manifest can be run with:

```bash
python knowledge_base/scripts/ocr_documents.py --run-manifest
python knowledge_base/scripts/validate_ocr.py
```

The full-document candidate is processed page by page, preserving pages 1-99 separately. The script never discovers or processes every repository PDF.

## Provenance and outputs

OCR outputs are derived files under `knowledge_base/processed/ocr/` and preserve source filename, source ID, page, mode, input path, output path, engine/configuration, timestamp, status, character count, optional Tesseract confidence, and an input PDF SHA-256 hash. Original PDFs and normal extracted JSONL are never overwritten.

The validator checks requested-page coverage, duplicate records, source IDs, page numbers, output existence and non-empty text, input hashes, and success statuses.

## Current status

Dependencies are now available. The mandated pilot was **EXECUTED** for page 2 but produced empty text because the rendered page was blank; the pilot is not a successful OCR validation. Full OCR remains **PENDING** and was not executed. Chunking, embeddings, vector databases, RAG, APIs, and section classification remain out of scope.