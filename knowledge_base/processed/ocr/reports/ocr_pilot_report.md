# OCR Pilot Report

- Selected document: `11_Mission 8 - Environmental Knowledge (1).pdf`
- Selected page: **2**
- Selection basis: first explicitly listed page-level OCR candidate; no content classification was made.
- Python executable: `/Users/madhavan/Documents/Ganga-AI-Mascot/Ganga-AI-Mascot/.venv/bin/python`
- Python version: `3.13.3`
- OCR method: local Poppler `pdftoppm` rendering at 300 DPI followed by Tesseract (`--psm 3`).
- Detected `pdftoppm`: `/opt/homebrew/bin/pdftoppm`
- Detected `tesseract`: `/opt/homebrew/bin/tesseract`
- Poppler version: `26.09.0`
- Tesseract version: `5.5.3`
- Input PDF: `knowledge_base/raw_documents/GRBMP/11_Mission 8 - Environmental Knowledge (1).pdf`
- Rendered image path: `/tmp/ganga-pilot-page-2.png`
- Rendered image dimensions: **2550 x 3300 pixels**, RGB, 8-bit
- Rendered image file size: **32,063 bytes**
- Rendered image valid: **No**; it is a valid PNG container but visually blank and contains **0 non-white pixels out of 8,415,000**.
- PDF page properties: 612 x 792 points (letter), rotation 0; PDF has 38 pages, is not encrypted, and page 2 has no embedded image objects.
- Direct Poppler text extraction for page 2: **1 byte only (newline)**.

## Status: FAILED

- Output path reserved: `knowledge_base/processed/ocr/page_ocr/11_Mission 8 - Environmental Knowledge (1)/page-0002.txt` (no output file produced because OCR returned no usable text)
- Character count: **0**
- OCR execution status: **FAILED / EMPTY_OUTPUT**
- Error: Tesseract executed against the rendered page but returned no usable text.
- Interpretation: The source PDF page itself appears blank. This is not a normal OCR-quality failure and is not evidence that OCR can recover missing content from page 2.
- Likely cause: page 2 is an empty/blank page in the source PDF; Poppler rendered the page faithfully. There is no embedded image and no extractable text to OCR.
- Provenance check: source filename and page number are recorded in the execution manifest.
- Validation result: **FAIL/PENDING**; the validator correctly rejects zero-character OCR output and reports 1 attempted page, 0 successful pages, and 110 failed/pending pages.
- Original PDF modified: **No**.
- Existing processed JSONL modified: **No**.
- Other OCR candidates processed: **No**.
