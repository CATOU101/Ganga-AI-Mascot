# OCR Page Count Reconciliation

## Result

The apparent difference is **112 versus 110 pages**, not a duplicate-page discrepancy.

- `knowledge_base/processed/extraction_report.json` contains **112** no-extractable-text warning entries across **13** PDFs.
- `knowledge_base/processed/ocr_required_manifest.json` requests **110** pages across **11** documents.
- The two excluded documents are the deferred theses:
  - `23_72_M Tech Thesis, 2014 Assessment of Approaches for Eliminating Use of Fresh Water in Tanneries at.pdf`, page 2
  - `57_71_M Tech Thesis Assessment of Provisioning an Appropriate Solid Waste Management Approach in.pdf`, page 2
- Each deferred thesis contributes exactly one extraction warning page.
- Therefore: **112 extraction-warning pages - 2 deferred-thesis pages = 110 manifest-requested pages**.

The manifest also treats `46_57_Surface and GW Modelling of the GRB (2).pdf` as a full-document candidate, covering pages 1-99. Its 99 pages are already included in both counts; they are not an additional discrepancy.

## Evidence checks

The extraction report lists 13 warning PDFs with no-text pages. The OCR manifest lists the same set after removing the two `DEFER` thesis records. No duplicate page warning was found in the extraction report: repeated page number 2 belongs to different PDFs, while pages 23 and 27 are the two distinct affected pages in the sewage-treatment report.

## Consequence

The current OCR execution manifest correctly contains **110** requested page attempts for the selected Knowledge Base scope. The deferred thesis pages remain documented in the extraction report but are intentionally not OCR execution candidates at this stage.