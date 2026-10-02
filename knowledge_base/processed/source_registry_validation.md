# Source Registry Validation

Validation performed after applying the reviewed source-resolution recommendations. No PDFs were processed, filtered, chunked, embedded, OCR'd, deleted, or moved.

## Counts

- Source-registry entries before update: **40** existing thematic/mission entries.
- Source-registry entries after update: **117** total entries, consisting of 40 pre-existing thematic entries, 36 prior resolution records, and 41 newly registered records.
- ID-bearing registered source records: **85 unique IDs**.
- Newly added source records: **41**.
- Updated existing records: **8** Mission Report entries, now carrying stable IDs and raw filenames.
- Deferred sources: **2** theses.
- Historical sources: **1** Ganga Action Plan SWOT report.
- Excluded sources: **0**.
- Newly identified relevant sources: **30**.

## ID Validation

- IDs assigned: `GRBMP-M01` through `GRBMP-M08`, `GRBMP-TR-001` through `GRBMP-TR-033`, `GRBMP-TH-001` through `GRBMP-TH-002`, and `GRBMP-HS-001`.
- Duplicate source IDs: **None**.
- ID uniqueness result: **PASS**; 85 IDs found and 85 are unique.

## Filename Traceability

- Previously resolved filenames registered: **36**.
- Newly completed filename relationships: **41**.
- Raw PDFs represented by exact filename relationships: **86 of 86**.
- Duplicate registered filenames: **None**; the two Mission 8 filenames are explicitly alternate copies under `GRBMP-M08`.
- Raw PDFs are not modified.

## Missing Metadata

- Authors: **35 of 36** reviewed records remain `Unknown`; the thesis at Jajmau identifies Rajat Verma.
- Publishers: **1 of 36** remains `Unknown`; the second thesis publisher was not established.
- Publication dates: **0 missing** among the reviewed records; dates were taken from title-page evidence or retained as the reviewed source-resolution value.
- Knowledge types: **18 of 36** remain unassigned at document level because the source-resolution evidence supports mixed static/historical content or requires section-level classification. This is intentional and preserves the distinction between source status and knowledge type.

## Classification Validation

- The two thesis documents are recorded as `DEFER`.
- `50_006GEN.pdf` is recorded as `HISTORICAL` and must not represent current Ganga Action Plan status.
- Three clear existing-category matches are recorded as `SELECT WITH FILTERING` without invented source IDs: `17_028ENB.pdf`, `18_17_005_FGM_DAT_01.pdf`, and `4_013EQP.pdf`.
- Thirty distinct relevant reports are recorded as `UNREGISTERED_RELEVANT_SOURCE` with proposed `SELECT WITH FILTERING` treatment pending human review.
- No source-resolution document remains `UNRESOLVED`.

## Inventory Coverage

- Inventory documents: **86**.
- Source-resolution documents covered by exact filename records: **36 of 36**.
- Provenance-completion documents covered by exact filename or explicit alternate-copy relationships: **50 of 50**.
- Inventory documents with traceable registry relationships: **86 of 86**.
- Remaining unresolved mappings: **0**.

## Result

**PASS:** all 86 raw PDFs have traceable registry relationships, source IDs are unique, the Mission 8 alternate copy is explicit, and no prohibited processing was performed.

`knowledge_base/sources.md` and this validation report were the only registry files modified. `processing_rules.md`, raw PDFs, extraction outputs, and source-resolution artifacts were not modified.
