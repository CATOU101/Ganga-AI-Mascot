# OCR Validation Report

- Validation manifest: `knowledge_base/processed/ocr/manifests/ocr_execution_manifest.json`
- Total requested OCR candidates/pages: **5**
- Page-level documents: **1**
- Full-document candidates: **0**
- Pages attempted: **5**
- Pages successfully OCR'd: **5**
- Pages failed or pending: **0**
- Empty/low-quality outputs: **0**
- Documents completed: **1**
- Documents requiring another attempt: **0**

## Checks

- Every requested page represented: **PASS** (0 missing)
- Duplicate OCR records: **PASS** (0)
- Provenance/source IDs: **PASS**
- Original PDFs unchanged relative to recorded hashes: **PASS**
- No success record without usable text: **PASS**

## Environment and status

- OCR engine information: `{'pdftoppm': '/opt/homebrew/bin/pdftoppm', 'tesseract': '/opt/homebrew/bin/tesseract'}`
- Execution performed: **True**
- Validation result: **PASS**

