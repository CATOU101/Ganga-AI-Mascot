"""Generate the section-level review from resolved metadata and page JSONL."""

import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "knowledge_base" / "processed"
PAGES = PROCESSED / "processed_documents"


def load_json(path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_page_records(path):
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def source_registry_by_file():
    mapping = {}
    line_pattern = re.compile(r"File: `([^`]+)`")
    id_pattern = re.compile(r"(GRBMP-[A-Z0-9-]+)")
    status_pattern = re.compile(
        r"\*\*(SELECT WITH FILTERING|SELECT|HISTORICAL|DEFER|EXCLUDE|PROJECT REFERENCE)\*\*"
    )
    for line in (ROOT / "knowledge_base" / "sources.md").read_text(encoding="utf-8").splitlines():
        file_match = line_pattern.search(line)
        if not file_match:
            continue
        identifier = id_pattern.search(line)
        status = status_pattern.search(line)
        title_match = re.search(r"- \*\*([^*]+)\*\*", line)
        if identifier:
            source_id = identifier.group(1)
        else:
            source_id = None
        mapping[file_match.group(1)] = {
            "source_id": source_id,
            "registry_label": title_match.group(1) if title_match else None,
            "source_status": status.group(1) if status else None,
        }
    return mapping


def heading_from_text(text):
    candidates = []
    for raw_line in text.splitlines():
        line = " ".join(raw_line.split()).strip(" .")
        if not line or len(line) > 140 or "| P a g e" in line:
            continue
        if re.match(r"^(?:\d+(?:\.\d+)*|[A-Z])\s*[.)-]\s+\S", line):
            candidates.append(line)
        elif len(line) <= 90 and line.upper() == line and re.search(r"[A-Z]{4}", line):
            candidates.append(line)
    return candidates[0] if candidates else None


def usable_section(value):
    if not value or value in {"GRB EMP", "IIT", "null"}:
        return False
    if len(value) > 140 or "@" in value or "|" in value:
        return False
    if re.search(r"(?:BOD5|COD|STP|HFL|CAPEX|OPEX|\bINR\b)\s*:", value):
        return False
    return True


def section_label(page):
    value = page.get("section")
    if usable_section(value):
        return " ".join(value.split())
    return heading_from_text(page.get("extracted_text", "")) or "Unidentified extracted structure"


def is_front_matter(label, text, page_start):
    value = f"{label} {text[:600]}".lower()
    if page_start <= 5 and any(
        marker in value for marker in ("preface", "acknowledg", "contents", "the team", "lead persons")
    ):
        return True
    return any(marker in label.lower() for marker in ("references", "bibliography", "acknowledg", "contents"))


def classify(group, metadata):
    label = group["section"].lower()
    text = " ".join(page.get("extracted_text", "") for page in group["pages"])
    text_lower = text.lower()
    pages = [page["page"] for page in group["pages"]]
    if any(page in metadata.get("ocr_pages", []) for page in pages):
        return "OCR_REQUIRED", "IRRELEVANT", "NONE", "The affected page has no usable extracted text; substantive content cannot be reviewed without OCR."
    if not text.strip():
        return "REVIEW_REQUIRED", "IRRELEVANT", "NONE", "The extracted section contains no usable text and needs a page-level review."
    if is_front_matter(group["section"], text, min(pages)):
        return "EXCLUDE", "IRRELEVANT", "NONE", "Administrative or bibliographic front/back matter is outside the Brain knowledge scope."
    if any(marker in label for marker in ("reference", "bibliography", "suggested reading")):
        return "EXCLUDE", "IRRELEVANT", "NONE", "References are preserved for provenance but are not standalone Brain knowledge."
    if any(marker in label for marker in ("table", "annex", "appendix", "raw data", "questionnaire")):
        return "FILTER", "HISTORICAL", "MEDIUM", "Potentially useful source data is too tabular, repetitive, or context-dependent for initial ingestion."
    if any(marker in label or marker in text_lower[:1800] for marker in ("method", "methodology", "framework", "model", "approach", "guideline", "analytical")):
        return "KEEP_METHODOLOGICAL", "METHODOLOGICAL", "HIGH", "The section explains a relevant method, framework, model, or technical procedure."
    if any(marker in label or marker in text_lower[:1200] for marker in ("result", "finding", "assessment", "status", "trend", "profile", "pollution load", "survey", "inventory", "scenario")):
        return "KEEP_HISTORICAL", "HISTORICAL", "HIGH", "The section reports a dated study, assessment, survey, status, or finding; it must retain its source and study period."
    if any(marker in label or marker in text_lower[:1200] for marker in ("conclu", "recommend", "definition", "concept", "introduction", "preamble", "mission", "vision", "principle", "importance")):
        return "KEEP", "STATIC", "HIGH", "The section provides relevant conceptual knowledge, explanations, principles, or recommendations."
    if "data" in label or "calculation" in label or "statistic" in label:
        return "FILTER", "HISTORICAL", "MEDIUM", "The section appears data-heavy; retain only with explicit temporal and geographic context."
    return "REVIEW_REQUIRED", "IRRELEVANT", "MEDIUM", "The extracted heading is not sufficiently interpretable to classify confidently without human review."


def temporal_context(metadata, classification, text):
    publication = metadata.get("publication_date") or "publication date not established"
    if classification == "KEEP_HISTORICAL":
        return f"Historical study/report context; publication date: {publication}. Data or study period must be taken from the section before ingestion."
    if classification == "KEEP_METHODOLOGICAL":
        return f"Method described in a report published {publication}; any dated outputs remain historical."
    if classification == "KEEP":
        return f"Stable/conceptual material from a report published {publication}; no current-state claim inferred."
    return f"Report publication context: {publication}; section-specific period requires confirmation where a claim is retained."


def geographic_context(metadata):
    return metadata.get("geographic_scope") or "Ganga River Basin unless the section establishes a narrower scope"


def duplicate_note(title):
    lowered = title.lower()
    if "pollution load" in lowered:
        return "Overlaps the other regional domestic-pollution-load assessments; preserve regional scope and prefer the basin-wide synthesis where the same claim is repeated."
    if "demographic" in lowered or "socio" in lowered or "urbanization" in lowered:
        return "Overlaps other regional demographic/urbanization studies; preserve location and period rather than generalizing to the basin."
    if "floral" in lowered or "faunal" in lowered or "vertebrate" in lowered or "fish" in lowered:
        return "Overlaps biodiversity reports; retain the geographically specific or taxonomically stronger source when passages repeat."
    if "agriculture" in lowered:
        return "Overlaps the agriculture overview and state reports; prefer the overview for basin-wide concepts and retain regional findings with scope."
    return "No duplicate was established from the available section labels; compare against neighboring reports during ingestion deduplication."


def main():
    inventory = load_json(PROCESSED / "document_inventory.json")
    provenance = {item["file_name"]: item for item in load_json(PROCESSED / "provenance_completion.json")["documents"]}
    resolution = {item["file_name"]: item for item in load_json(PROCESSED / "source_resolution.json")["documents"]}
    registry = source_registry_by_file()
    documents = []
    records = []
    skipped = []
    for item in inventory["documents"]:
        filename = item["file_name"]
        resolved = resolution.get(filename, {})
        completed = provenance.get(filename, {})
        meta = {**item, **completed, **resolved, **registry.get(filename, {})}
        meta["resolved_title"] = resolved.get("title") or completed.get("title") or item.get("title")
        status = meta.get("source_classification") or meta.get("source_status")
        if status in {"DEFER", "PROJECT REFERENCE", "EXCLUDE"}:
            skipped.append({"file_name": filename, "source_id": meta.get("source_id"), "source_status": status, "reason": "Outside the requested SELECT/SELECT_WITH_FILTERING review population."})
            continue
        if status not in {"SELECT", "SELECT WITH FILTERING", "HISTORICAL"}:
            status = "REVIEW_REQUIRED"
        path = PAGES / filename.replace(".pdf", ".jsonl")
        pages = load_page_records(path)
        ocr_pages = item.get("ocr_pages") or meta.get("ocr_pages") or []
        if filename == "46_57_Surface and GW Modelling of the GRB (2).pdf":
            ocr_pages = list(range(1, 100))
        meta["ocr_pages"] = ocr_pages
        groups = []
        for page in pages:
            label = section_label(page)
            if groups and groups[-1]["section"] == label and groups[-1]["pages"][-1]["page"] + 1 == page["page"]:
                groups[-1]["pages"].append(page)
            else:
                groups.append({"section": label, "pages": [page]})
        summary = Counter()
        for group in groups:
            classification, knowledge_type, relevance, rationale = classify(group, meta)
            summary[classification] += 1
            page_start = group["pages"][0]["page"]
            page_end = group["pages"][-1]["page"]
            text = " ".join(page.get("extracted_text", "") for page in group["pages"])
            record = {
                "source_id": meta.get("source_id"),
                "file_name": filename,
                "title": meta.get("resolved_title") or filename.removesuffix(".pdf"),
                "source_status": status,
                "document_type": meta.get("document_type") or item.get("document_type"),
                "section": group["section"],
                "subsection": None,
                "page_start": page_start,
                "page_end": page_end,
                "section_classification": classification,
                "knowledge_type": knowledge_type,
                "relevance": relevance,
                "temporal_context": temporal_context(meta, classification, text),
                "geographic_scope": geographic_context(meta),
                "duplication_notes": duplicate_note(meta.get("title") or filename),
                "rationale": rationale,
                "OCR_status": "REQUIRED" if classification == "OCR_REQUIRED" else ("AFFECTED_PAGE" if any(p in ocr_pages for p in range(page_start, page_end + 1)) else "NOT_REQUIRED"),
                "review_status": "HUMAN_REVIEW_REQUIRED" if classification in {"OCR_REQUIRED", "REVIEW_REQUIRED"} else "INITIAL_REVIEW_COMPLETE",
                "evidence_excerpt": " ".join(text.split())[:280],
            }
            records.append(record)
        documents.append({
            "source_id": meta.get("source_id"),
            "file_name": filename,
            "title": meta.get("resolved_title") or filename.removesuffix(".pdf"),
            "source_status": status,
            "total_sections_identified": len(groups),
            "sections_to_KEEP": summary["KEEP"],
            "sections_to_KEEP_HISTORICAL": summary["KEEP_HISTORICAL"],
            "sections_to_KEEP_METHODOLOGICAL": summary["KEEP_METHODOLOGICAL"],
            "sections_to_FILTER": summary["FILTER"],
            "sections_to_EXCLUDE": summary["EXCLUDE"],
            "sections_requiring_OCR": summary["OCR_REQUIRED"],
            "sections_requiring_human_review": summary["REVIEW_REQUIRED"] + summary["OCR_REQUIRED"],
        })
    counts = Counter(record["section_classification"] for record in records)
    review = {
        "review_version": "stage-2-section-review",
        "generated_date": date.today().isoformat(),
        "scope": "SELECT, SELECT WITH FILTERING, and HISTORICAL sources; DEFER sources are listed as skipped.",
        "rules": "knowledge_base/processing_rules.md",
        "source_registry": "knowledge_base/sources.md",
        "method_note": "Records are grouped from page-preserving extracted section labels. No OCR, chunking, embeddings, vector database, API, or retrieval processing was performed. Noisy or ambiguous extracted structure is explicitly marked REVIEW_REQUIRED.",
        "summary": {
            "documents_reviewed": len(documents),
            "sections_identified": len(records),
            "sections_KEEP": counts["KEEP"],
            "sections_KEEP_HISTORICAL": counts["KEEP_HISTORICAL"],
            "sections_KEEP_METHODOLOGICAL": counts["KEEP_METHODOLOGICAL"],
            "sections_FILTER": counts["FILTER"],
            "sections_EXCLUDE": counts["EXCLUDE"],
            "sections_requiring_OCR": counts["OCR_REQUIRED"],
            "sections_requiring_human_review": counts["REVIEW_REQUIRED"] + counts["OCR_REQUIRED"],
            "documents_skipped": len(skipped),
        },
        "documents": documents,
        "skipped_documents": skipped,
        "sections": records,
    }
    (PROCESSED / "section_review.json").write_text(json.dumps(review, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    lines = [
        "# Section-Level Content Review",
        "",
        f"Generated: {review['generated_date']}",
        "",
        review["method_note"],
        "",
        "## Summary",
        "",
    ]
    for key, value in review["summary"].items():
        lines.append(f"- {key}: **{value}**")
    lines += ["", "## Document summaries", ""]
    for document in documents:
        lines.append(f"### {document['title']} (`{document['source_id']}`)")
        lines.append(f"- File: `{document['file_name']}`; status: **{document['source_status']}**")
        lines.append("- " + "; ".join(f"{key.removeprefix('sections_to_').replace('_', ' ')}: {value}" for key, value in document.items() if key.startswith("sections_to_")))
        lines.append("")
    if skipped:
        lines += ["## Skipped source documents", ""]
        for item in skipped:
            lines.append(f"- `{item['file_name']}` ({item['source_status']}): {item['reason']}")
        lines.append("")
    lines += ["## Section decisions", ""]
    for record in records:
        lines.append(f"### {record['title']} — {record['section']} (pages {record['page_start']}-{record['page_end']})")
        lines.append(f"- Source: `{record['source_id']}`; classification: **{record['section_classification']}**; knowledge type: **{record['knowledge_type']}**; relevance: **{record['relevance']}**")
        lines.append(f"- Temporal context: {record['temporal_context']}")
        lines.append(f"- Geographic scope: {record['geographic_scope']}")
        lines.append(f"- OCR status: **{record['OCR_status']}**; review status: **{record['review_status']}**")
        lines.append(f"- Rationale: {record['rationale']}")
        lines.append(f"- Duplication notes: {record['duplication_notes']}")
        lines.append("")
    (PROCESSED / "section_review.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()