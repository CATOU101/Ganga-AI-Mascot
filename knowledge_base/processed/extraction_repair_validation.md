# Extraction Repair Validation

Generated: 2026-09-12

## Results

- Deterministic extraction/heading cases identified: **109**
- High-confidence automatic repair candidates: **2**
- Uncertain repair candidates retained for human review: **107**
- Classification changes: **0**
- OCR documents: **11** (10 page-level, 1 full-document)
- OCR-affected pages listed: **110**

## Validation checks

- Invented source IDs: **0**; missing source IDs in repair/OCR records: **0**
- Invented pages: **0**; pages are taken from existing JSONL/extraction-report records, with pages 1-99 explicitly established for the full-document candidate.
- Duplicate section identifiers: **0**
- Existing classifications modified: **No**.
- `sources.md` modified: **No**.
- `processing_rules.md` modified: **No**.
- OCR executed: **No**; the repository contains extraction warnings but no established OCR execution workflow.
- Chunking, embeddings, vector database, RAG, and API integration performed: **No**.

## OCR candidates

- `11_Mission 8 - Environmental Knowledge (1).pdf` (`GRBMP-M08`): pages 2; priority **MEDIUM**.
- `11_Mission 8 - Environmental Knowledge.pdf` (`GRBMP-M08`): pages 2; priority **MEDIUM**.
- `15_37_Stream Power Distribution Pattern for the Ganga River to Determine the Effects of River Energy and.pdf` (`GRBMP-TR-036`): pages 2; priority **MEDIUM**.
- `15_66_Assessment of Domestic Pollution Load from Urban Agglomeration in Ganga Basin Ramganga Kali and Gomati Sub-Basin.pdf` (`GRBMP-TR-037`): pages 2; priority **MEDIUM**.
- `35_70_Assessment of Potential Institutional Models for Sewage Treatment in Ganga Basin and the Way.pdf` (`GRBMP-TR-046`): pages 23, 27; priority **MEDIUM**.
- `36_35_River Style Framework for the Ganga River.pdf` (`GRBMP-TR-047`): pages 2; priority **MEDIUM**.
- `38_44_State of Health in the Ganga River Basin.pdf` (`GRBMP-TR-051`): pages 2; priority **MEDIUM**.
- `46_57_Surface and GW Modelling of the GRB (2).pdf` (`GRBMP-TR-055`): full document; priority **HIGH**.
- `47_73_Assessment of E Flows at Some Select Sites in Upper Ganga Segment.pdf` (`GRBMP-TR-057`): pages 2; priority **MEDIUM**.
- `53_67_Assessment of Domestic Pollution Load from Urban Agglomeration in Ganga BasinGandak and Kosi Sub-Basin.pdf` (`GRBMP-TR-060`): pages 2; priority **MEDIUM**.
- `54_30_Wetlands in Ganga River Basin.pdf` (`GRBMP-TR-063`): pages 2; priority **MEDIUM**.

## Readiness

The dataset is **not ready for final manual content sign-off**. Deterministic representation repairs can be reviewed first, followed by targeted OCR. The 433-section human-content workload remains, and chunking must remain blocked until repaired context, temporal scope, geographic scope, and content decisions are complete.
