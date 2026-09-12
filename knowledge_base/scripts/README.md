# PDF Extraction

`extract_pdfs.py` is the Stage 1 extraction component for the Ganga Brain Knowledge Base. It only discovers PDFs and produces page-level extracted text with provenance metadata. It does not filter sections, classify knowledge, create chunks, generate embeddings, build a vector database, or retrieve answers.

## Dependency

Install the only required third-party dependency:

```bash
python3 -m pip install pypdf
```

No OCR dependency is required. PDFs with little or no extractable text are reported for later OCR or manual review.

## Run

From the project root:

```bash
python3 knowledge_base/scripts/extract_pdfs.py
```

The default input is `knowledge_base/raw/GRBMP/`. This repository currently stores the untouched GRBMP PDFs under `knowledge_base/raw_documents/GRBMP/`; when the requested input directory is absent, the script uses that existing path as a compatibility fallback and logs the choice.

Optional paths can be supplied explicitly:

```bash
python3 knowledge_base/scripts/extract_pdfs.py \
  --input-dir knowledge_base/raw/GRBMP \
  --output-dir knowledge_base/processed
```

Use `--verbose` for debug logging.

## Output

The extractor writes to `knowledge_base/processed/` by default:

- `processed_documents/` contains one JSONL file per source PDF. The relative directory structure under the input directory is preserved, and each page record includes the original page number, filename, relative source path, title, conservative section information, extracted text and extraction status.
- `extraction_report.json` records discovery, processing, page, text-size, warning and failure counts, plus the affected files.

The extractor removes and recreates the generated `processed_documents/` directory on each run, then atomically replaces each document output. Rerunning the command therefore updates the outputs without appending duplicate records or leaving stale processed documents.

There is no consolidated `extracted_pages.jsonl` output. Per-document JSONL files are the single extraction representation, avoiding duplicate copies of the same extracted data. The extraction report remains directly under `knowledge_base/processed/`.

Source IDs are left unresolved unless a confident mapping is available from the source registry. This first component does not invent source IDs; later metadata enrichment can review the unresolved mappings.

## Failure Reporting

A malformed, encrypted, unreadable or otherwise failed PDF is recorded in `failed_files` and does not stop processing of other PDFs. Pages with no extractable text receive a `no_text` status and are listed in `warning_files` with an OCR/manual-review warning. Documents with little or no extractable text are listed in `ocr_candidates`. Page-level extraction errors receive `page_error` status and are also reported.

The original PDFs are never modified, moved or deleted. They remain the raw source layer for later filtering and chunking stages.
