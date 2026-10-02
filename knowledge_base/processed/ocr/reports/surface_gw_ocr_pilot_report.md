# Surface/GW Five-Page OCR Pilot Report

## Scope

This controlled pilot processed exactly five pages from `46_57_Surface and GW Modelling of the GRB (2).pdf`.

Only pages classified `IMAGE_BASED_CONTENT` in `knowledge_base/processed/ocr/reports/surface_gw_page_state_analysis.json` were selected. The single `UNCERTAIN` page, page 2, was not processed. The remaining 93 image-based pages were not processed.

Selected pages: **1, 26, 51, 76, 99**.

## Selection Rationale

- Page 1: title/front-matter page with large headings and institutional labels; non-white percentage 14.535603.
- Page 26: figure-heavy page with map and scatter plots; non-white percentage 53.972323.
- Page 51: normal text-heavy narrative page with headings and bullet list; non-white percentage 28.236542.
- Page 76: text-heavy modelling/scenario page with multiple headings; non-white percentage 34.947392.
- Page 99: figure-heavy final page with multiple flow-duration charts; non-white percentage 48.237885.

No content relevance or Knowledge Base classification decision was made.

## Environment And Execution

- Working directory: `/Users/madhavan/Documents/Ganga-AI-Mascot/Ganga-AI-Mascot`
- Python executable: `/Users/madhavan/Documents/Ganga-AI-Mascot/Ganga-AI-Mascot/.venv/bin/python`
- Python version: `3.13.3`
- Poppler executable: `/opt/homebrew/bin/pdftoppm`
- Poppler version: `pdftoppm` 26.09.0
- Tesseract executable: `/opt/homebrew/bin/tesseract`
- Tesseract version: 5.5.3
- Tesseract language data available: `eng`, `osd`
- OCR method: local Poppler page render followed by Tesseract command-line OCR.
- OCR configuration: 300 DPI PNG render, Tesseract `--psm 3`.
- Temporary requested manifest: `/private/tmp/surface_gw_five_page_manifest.json`
- OCR execution manifest: `knowledge_base/processed/ocr/manifests/ocr_execution_manifest.json`
- Source ID: `GRBMP-TR-055`
- OCR mode: `PAGE_LEVEL`
- Raw PDF SHA-256 before and after: `cf5b9736024b0719e303b8020cb949453fb00f8cecc07e6cae3663f564b6b376`
- Existing extracted JSONL SHA-256 before and after: `d8975d3878a0ea9f6f1fadd2abe56514adcd8c5b5e4c9ba95650ee4efa09a365`

## Technical Result

| Page | Status | Characters | Mean confidence | Output |
|---:|---|---:|---:|---|
| 1 | SUCCESS | 212 | 82.21 | `knowledge_base/processed/ocr/page_ocr/46_57_Surface and GW Modelling of the GRB (2)/page-0001.txt` |
| 26 | SUCCESS | 26 | 91.28 | `knowledge_base/processed/ocr/page_ocr/46_57_Surface and GW Modelling of the GRB (2)/page-0026.txt` |
| 51 | SUCCESS | 2728 | 91.29 | `knowledge_base/processed/ocr/page_ocr/46_57_Surface and GW Modelling of the GRB (2)/page-0051.txt` |
| 76 | SUCCESS | 3429 | 94.50 | `knowledge_base/processed/ocr/page_ocr/46_57_Surface and GW Modelling of the GRB (2)/page-0076.txt` |
| 99 | SUCCESS | 33 | 89.69 | `knowledge_base/processed/ocr/page_ocr/46_57_Surface and GW Modelling of the GRB (2)/page-0099.txt` |

- Pages attempted: **5/5**
- Pages successfully OCR'd: **5**
- Pages failed: **0**
- Total OCR characters, from execution records: **6428**

All five page boundaries and page numbers remain separate and recoverable in the execution manifest and page-level output files.

## Validation

The existing validator was run against the temporary five-page requested manifest and the generated OCR execution manifest.

- Total requested pages: **5**
- Pages attempted: **5**
- Page records present: **5**
- Duplicate OCR records: **PASS**; 0 duplicates.
- Provenance/source IDs: **PASS**
- Successful outputs non-empty: **PASS**
- Original PDF unchanged relative to recorded hash: **PASS**
- Existing extracted JSONL unchanged by SHA-256 check: **PASS**
- Validation result: **PASS**

## Page Quality Observations

### Page 1

- Non-empty output: yes.
- Readability: good for the main title and GRBMP line.
- Heading recognition: main title preserved.
- Paragraph reconstruction: not applicable; title/front matter only.
- Character corruption: institutional/logo labels are partially corrupted.
- Missing/repeated text: no major repeated prose, but logo text is incomplete/noisy.
- Table text quality: not applicable.
- Figure/diagram text quality: poor for small logo labels.
- OCR artifacts: duplicated-looking IIT label fragments.
- Provenance: clear.

### Page 26

- Non-empty output: yes, but only 26 characters.
- Readability: poor.
- Heading recognition: failed to capture the figure title reliably.
- Paragraph reconstruction: not applicable.
- Character corruption: severe.
- Missing/repeated text: most map and chart labels are missing.
- Table text quality: not applicable.
- Figure/diagram text quality: poor; map/scatter-plot content is not usable as extracted text.
- OCR artifacts: fragments such as `a>`, `an`, and `Pahistan China`.
- Provenance: clear.

### Page 51

- Non-empty output: yes.
- Readability: usable for human review.
- Heading recognition: section headings such as unconsolidated, semi-consolidated, and consolidated formations are recognizable.
- Paragraph reconstruction: mostly preserved, with line wrapping.
- Character corruption: moderate; examples include `Alluviur`, `Alluviurn`, `Costal`, `Corboniferous`, `crytallines`, and `flaws`.
- Missing/repeated text: no obvious large omissions in the visible narrative sample.
- Table text quality: not applicable.
- Figure/diagram text quality: not applicable.
- OCR artifacts: bullet characters and some words are distorted.
- Provenance: clear.

### Page 76

- Non-empty output: yes.
- Readability: usable for human review.
- Heading recognition: scenario headings are preserved.
- Paragraph reconstruction: mostly preserved.
- Character corruption: moderate; examples include `sarne`, `Gevelopment`, `MOFLOW`, `effiuent`, `loosing`, and `sub-scenarias`.
- Missing/repeated text: no obvious large omissions in the visible narrative sample.
- Table text quality: not applicable.
- Figure/diagram text quality: not applicable.
- OCR artifacts: some misspellings and line-wrap artifacts.
- Provenance: clear.

### Page 99

- Non-empty output: yes, but only 33 characters.
- Readability: poor.
- Heading recognition: failed to capture the chart title reliably.
- Paragraph reconstruction: not applicable.
- Character corruption: severe.
- Missing/repeated text: nearly all chart labels, legends, axes, and captions are absent or unusable.
- Table text quality: not applicable.
- Figure/diagram text quality: poor; flow-duration chart content is not usable as extracted text.
- OCR artifacts: fragments such as `jiftnanee'`, `(oases) moyy vous`, and page number text.
- Provenance: clear.

## Overall OCR Quality Assessment

Technical success and OCR quality are different here.

Technical success: **PASS**. The existing local OCR workflow can render selected pages, run Tesseract, write separate page outputs, preserve provenance, and pass validation for exactly five requested page records.

OCR quality: **mixed**. Dense narrative pages are usable for controlled downstream human review, but figure-heavy pages are not adequately captured by plain Tesseract OCR. The confidence values are high even on pages where the useful visual content is mostly missed, so confidence must not be treated as semantic quality.

## Identified OCR Problems

- Figure-heavy pages lose most map, plot, axis, legend, and caption information.
- Small labels and institutional/logo text are noisy.
- Narrative pages contain word substitutions and OCR spelling errors.
- Bullet/list reconstruction is imperfect.
- Tesseract confidence is not sufficient for deciding whether chart-heavy pages are usable.

## Recommendation

Pilot successful; remaining 93 image-based pages are ready for controlled OCR execution.

However, process them in page-level batches and keep figure/table-heavy pages flagged for separate visual or manual review. Dense narrative OCR can proceed for human review, but chart/map/diagram content should not be accepted as text-only evidence without a separate layout-aware or manual extraction path.
