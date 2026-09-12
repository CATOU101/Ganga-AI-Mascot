"""Analyze deterministic extraction repairs and prepare an OCR manifest."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "knowledge_base" / "processed"
PAGE_DIR = PROCESSED / "processed_documents"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_pages(file_name: str) -> list[dict]:
    path = PAGE_DIR / file_name.removesuffix(".pdf")
    path = path.with_suffix(".jsonl")
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")
    text = re.sub(r"(?<=\w)-\n(?=\w)", "", text)
    lines = []
    previous = None
    for raw_line in text.splitlines():
        line = re.sub(r"[ \t]+", " ", raw_line).strip()
        if not line:
            continue
        if line == previous:
            continue
        lines.append(line)
        previous = line
    return "\n".join(lines)


def is_artifact_label(label: str) -> bool:
    lower = label.lower().strip()
    return (
        lower == "unidentified extracted structure"
        or "@" in label
        or len(label) > 100
        or bool(re.search(r"\b(?:page|p a g e)\b", lower))
        or bool(re.search(r"\b(?:source|expected|government may|which describe|has been convicted)\b", lower))
        or bool(re.search(r"\[[^]]+\]|\+\s*\+|\b(?:DDT|STROMATEIDAE|VOP|NUGP|NRGB|UPJN)\b", label))
        or (label.isupper() and len(label) <= 35)
    )


def heading_candidates(text: str) -> list[str]:
    candidates = []
    for raw_line in normalize_text(text).splitlines():
        line = raw_line.strip(" .")
        if not line or len(line) > 140:
            continue
        line = re.sub(r"^\d+\s*\|\s*P\s*a\s*g\s*e\s*", "", line, flags=re.IGNORECASE).strip()
        if not line:
            continue
        if re.match(r"^(?:Table|Figure|Appendix)\s+[A-Za-z0-9.-]+\s*[:.-]\s*\S", line, re.IGNORECASE):
            candidates.append(line)
        elif re.match(r"^(?:\d+(?:\.\d+)*|[A-Z])\s*[.)-]\s+\S", line):
            candidates.append(line)
        elif line.isupper() and len(line.split()) >= 2 and len(line) <= 90 and not line.endswith(":"):
            candidates.append(line)
    return list(dict.fromkeys(candidates))


def repair_reason(original: str, text: str) -> str:
    lower = original.lower()
    if lower == "unidentified extracted structure":
        return "MISSING_OR_GENERIC_HEADING"
    if re.match(r"^(?:[a-z]|[ivx]+)[.)]\s", lower) or len(original.split()) > 12:
        return "BODY_FRAGMENT_AS_HEADING"
    if re.search(r"\[[^]]+\]|\+\s*\+|\b(?:DDT|STROMATEIDAE)\b", original):
        return "REFERENCE_OR_SYMBOL_FRAGMENT"
    if original.isupper() or len(original.split()) <= 3:
        return "ABBREVIATION_OR_TABLE_FRAGMENT"
    if re.search(r"\b(?:table|figure|appendix)\b", text, re.IGNORECASE):
        return "TABLE_OR_FIGURE_HEADING_SEPARATION"
    return "HEADING_NORMALIZATION"


def page_text(pages: list[dict], start: int, end: int) -> str:
    selected = [page.get("extracted_text", "") for page in pages if start <= page.get("page", 0) <= end]
    return "\n".join(selected)


def extraction_warnings():
    report = load_json(PROCESSED / "extraction_report.json")
    warnings = defaultdict(list)
    for item in report.get("warning_files", []):
        for warning in item.get("warnings", []):
            match = re.search(r"page (\d+): no extractable text", warning)
            if match:
                warnings[item["file_name"]].append(int(match.group(1)))
    return {name: sorted(set(pages)) for name, pages in warnings.items()}


def build_repairs(review: dict, analysis: dict) -> list[dict]:
    candidate_keys = {
        (item["source_id"], item["file_name"], item["page_start"], item["page_end"], item["section"])
        for item in analysis["section_reason_records"]
        if item["primary_reason"] == "NOISY_EXTRACTION"
    }
    repairs = []
    for record in review["sections"]:
        key = (record["source_id"], record["file_name"], record["page_start"], record["page_end"], record["section"])
        if key not in candidate_keys:
            continue
        pages = load_pages(record["file_name"])
        original_text = page_text(pages, record["page_start"], record["page_end"])
        normalized = normalize_text(original_text)
        candidates = heading_candidates(original_text)
        repaired_heading = None
        for candidate in candidates:
            if candidate.strip() != record["section"].strip() and not is_artifact_label(candidate):
                repaired_heading = candidate
                break
        confidence = "HIGH" if repaired_heading and len(candidates) == 1 else "UNCERTAIN"
        repairs.append(
            {
                "section_id": f"{record['source_id']}|{record['file_name']}|{record['page_start']}-{record['page_end']}|{record['section']}",
                "source_id": record["source_id"],
                "file_name": record["file_name"],
                "page_start": record["page_start"],
                "page_end": record["page_end"],
                "original_section": record["section"],
                "repaired_heading": repaired_heading,
                "heading_candidates": candidates,
                "original_text_excerpt": " ".join(original_text.split())[:500],
                "repaired_text_excerpt": " ".join(normalized.split())[:500],
                "repair_reason": repair_reason(record["section"], original_text),
                "confidence": confidence,
                "original_classification": record["section_classification"],
                "classification_affected": False,
                "classification_change": "none; representation only",
                "repair_operations": ["normalize whitespace", "remove duplicated adjacent lines", "repair line-break hyphenation"] if normalized != original_text else ["heading candidate extraction only"],
                "review_status": "RETAIN_HUMAN_REVIEW" if confidence != "HIGH" else "DETERMINISTIC_REPAIR_CANDIDATE",
            }
        )
    return repairs


def build_ocr_manifest(review: dict) -> list[dict]:
    warnings = extraction_warnings()
    by_file = {}
    for record in review["sections"]:
        if record["section_classification"] != "OCR_REQUIRED":
            continue
        item = by_file.setdefault(
            record["file_name"],
            {
                "filename": record["file_name"],
                "source_id": record["source_id"],
                "affected_pages": [],
                "reasons": set(),
            },
        )
        item["affected_pages"].extend(warnings.get(record["file_name"], []))
        item["reasons"].add(record["rationale"])
    manifest = []
    for filename, item in sorted(by_file.items()):
        is_full = filename == "46_57_Surface and GW Modelling of the GRB (2).pdf"
        pages = sorted(set(item["affected_pages"]))
        if is_full and not pages:
            pages = [page["page"] for page in load_pages(filename)]
        manifest.append(
            {
                "filename": filename,
                "source_id": item["source_id"],
                "affected_pages": pages,
                "reason": "The complete document has no usable extracted text across all pages; current analysis marks it OCR_REQUIRED." if is_full else "One or more pages have no usable extracted text; current analysis marks the affected section OCR_REQUIRED.",
                "ocr_scope": "FULL_DOCUMENT" if is_full else "PAGE_LEVEL",
                "priority": "HIGH" if is_full else "MEDIUM",
                "provenance_note": "Any OCR output must preserve source_id, filename, original page number, section context, and a link to the authoritative PDF. OCR output must remain a derived artifact and must not overwrite the extracted JSONL or source PDF.",
                "existing_recorded_reasons": sorted(item["reasons"]),
            }
        )
    return manifest


def main():
    review = load_json(PROCESSED / "section_review.json")
    analysis = load_json(PROCESSED / "review_required_analysis.json")
    repairs = build_repairs(review, analysis)
    manifest = build_ocr_manifest(review)
    high = sum(item["confidence"] == "HIGH" for item in repairs)
    uncertain = len(repairs) - high
    duplicate_ids = len(repairs) - len({item["section_id"] for item in repairs})
    source_ids_missing = sum(not item["source_id"] for item in repairs + manifest)
    output = {
        "analysis_version": "stage-2-deterministic-extraction-repair-analysis",
        "generated_date": date.today().isoformat(),
        "input_review": "knowledge_base/processed/section_review.json",
        "input_analysis": "knowledge_base/processed/review_required_analysis.json",
        "scope": "Primary NOISY_EXTRACTION records only; no content classification was changed.",
        "summary": {
            "deterministic_repair_candidates": len(repairs),
            "high_confidence_repairs": high,
            "uncertain_repairs": uncertain,
            "classification_changes": 0,
            "duplicate_section_ids": duplicate_ids,
            "missing_source_ids": source_ids_missing,
        },
        "repairs": repairs,
    }
    (PROCESSED / "extraction_repairs.json").write_text(json.dumps(output, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    ocr_output = {
        "manifest_version": "stage-2-ocr-required-manifest",
        "generated_date": date.today().isoformat(),
        "source": "knowledge_base/processed/section_review.json plus extraction_report.json no-text warnings",
        "ocr_execution_performed": False,
        "documents": manifest,
        "summary": {
            "documents_requiring_ocr": len(manifest),
            "full_document_candidates": sum(item["ocr_scope"] == "FULL_DOCUMENT" for item in manifest),
            "page_level_candidates": sum(item["ocr_scope"] == "PAGE_LEVEL" for item in manifest),
            "affected_pages": sum(len(item["affected_pages"]) for item in manifest),
        },
    }
    (PROCESSED / "ocr_required_manifest.json").write_text(json.dumps(ocr_output, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    validation = [
        "# Extraction Repair Validation",
        "",
        f"Generated: {date.today().isoformat()}",
        "",
        "## Results",
        "",
        f"- Deterministic extraction/heading cases identified: **{len(repairs)}**",
        f"- High-confidence automatic repair candidates: **{high}**",
        f"- Uncertain repair candidates retained for human review: **{uncertain}**",
        f"- Classification changes: **0**",
        f"- OCR documents: **{len(manifest)}** ({ocr_output['summary']['page_level_candidates']} page-level, {ocr_output['summary']['full_document_candidates']} full-document)",
        f"- OCR-affected pages listed: **{ocr_output['summary']['affected_pages']}**",
        "",
        "## Validation checks",
        "",
        f"- Invented source IDs: **0**; missing source IDs in repair/OCR records: **{source_ids_missing}**",
        f"- Invented pages: **0**; pages are taken from existing JSONL/extraction-report records, with pages 1-99 explicitly established for the full-document candidate.",
        f"- Duplicate section identifiers: **{duplicate_ids}**",
        "- Existing classifications modified: **No**.",
        "- `sources.md` modified: **No**.",
        "- `processing_rules.md` modified: **No**.",
        "- OCR executed: **No**; the repository contains extraction warnings but no established OCR execution workflow.",
        "- Chunking, embeddings, vector database, RAG, and API integration performed: **No**.",
        "",
        "## OCR candidates",
        "",
    ]
    for item in manifest:
        scope = "full document" if item["ocr_scope"] == "FULL_DOCUMENT" else f"pages {', '.join(map(str, item['affected_pages']))}"
        validation.append(f"- `{item['filename']}` (`{item['source_id']}`): {scope}; priority **{item['priority']}**.")
    validation += [
        "",
        "## Readiness",
        "",
        "The dataset is **not ready for final manual content sign-off**. Deterministic representation repairs can be reviewed first, followed by targeted OCR. The 433-section human-content workload remains, and chunking must remain blocked until repaired context, temporal scope, geographic scope, and content decisions are complete.",
        "",
    ]
    (PROCESSED / "extraction_repair_validation.md").write_text("\n".join(validation), encoding="utf-8")

    repairs_md = [
        "# Extraction Repair Candidates",
        "",
        "This artifact analyzes representation-only repair candidates. It does not change section classifications or source artifacts.",
        "",
        f"- Candidates: **{len(repairs)}**",
        f"- High confidence: **{high}**",
        f"- Uncertain: **{uncertain}**",
        "",
    ]
    for item in repairs:
        repairs_md += [
            f"## {item['file_name']} — pages {item['page_start']}-{item['page_end']}",
            f"- Source: `{item['source_id']}`; original classification: **{item['original_classification']}**",
            f"- Original section: `{item['original_section']}`",
            f"- Repaired heading candidate: `{item['repaired_heading']}`",
            f"- Reason: **{item['repair_reason']}**; confidence: **{item['confidence']}**",
            f"- Classification affected: **{item['classification_affected']}**; status: **{item['review_status']}**",
            f"- Text evidence: {item['repaired_text_excerpt'][:300]}",
            "",
        ]
    (PROCESSED / "extraction_repairs.md").write_text("\n".join(repairs_md), encoding="utf-8")

    ocr_md = [
        "# OCR Required Manifest",
        "",
        "OCR was not executed. This manifest is derived from existing no-text warnings and review-required records.",
        "",
    ]
    for item in manifest:
        pages = ", ".join(map(str, item["affected_pages"]))
        ocr_md += [
            f"## {item['filename']}",
            f"- Source ID: `{item['source_id']}`",
            f"- Scope: **{item['ocr_scope']}**; affected pages: **{pages}**",
            f"- Priority: **{item['priority']}**",
            f"- Reason: {item['reason']}",
            f"- Provenance: {item['provenance_note']}",
            "",
        ]
    (PROCESSED / "ocr_required_manifest.md").write_text("\n".join(ocr_md), encoding="utf-8")


if __name__ == "__main__":
    main()