"""Analyze review-required section records without changing their classifications."""

import json
import re
from collections import Counter
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "knowledge_base" / "processed"
INPUT = PROCESSED / "section_review.json"

CATEGORY_INFO = {
    "NOISY_EXTRACTION": {
        "typical_reason": "The recorded rationale says the extracted heading is not sufficiently interpretable; the label is missing, malformed, fragmented, abbreviated, or looks like an extraction artifact.",
        "next_action": "Repair or validate the heading against adjacent extracted pages and the PDF structure. Re-run only deterministic heading normalization; do not reclassify content until the repaired context is readable.",
    },
    "OCR_REQUIRED": {
        "typical_reason": "The page has no usable extracted text, so the section cannot be evaluated from the current evidence.",
        "next_action": "Prioritize targeted OCR of the flagged pages after confirming that the page contains substantive content. Preserve the OCR result as a separate derived artifact.",
    },
    "AMBIGUOUS_RELEVANCE": {
        "typical_reason": "After accounting for extraction quality, the available label and excerpt do not establish whether the content answers a likely Brain question.",
        "next_action": "Have a domain reviewer assess the section in document context and record a user-question or topic justification before approving or filtering it.",
    },
    "CONTEXT_DEPENDENT": {
        "typical_reason": "The label or excerpt is too fragmentary to establish the section's meaning without surrounding pages.",
        "next_action": "Review the preceding and following sections together, preserving section boundaries and enough context for any eventual ingestion unit.",
    },
    "TECHNICAL_SCOPE_UNCLEAR": {
        "typical_reason": "The source is technical or data-heavy, but the available evidence does not show whether it provides useful explanation or only specialist detail.",
        "next_action": "Ask a subject-matter reviewer to separate conceptual explanation from specialized calculations, raw inputs, and implementation detail.",
    },
    "HISTORICAL_CONTEXT_UNCLEAR": {
        "typical_reason": "The excerpt contains dated-looking findings, measurements, status, or trends without enough section-level evidence to establish the study/data period.",
        "next_action": "Confirm publication, study, and data periods from nearby pages and label retained content explicitly as historical.",
    },
    "GEOGRAPHIC_SCOPE_UNCLEAR": {
        "typical_reason": "The available section evidence does not establish whether a claim is basin-wide, regional, city-level, or tied to a river stretch.",
        "next_action": "Confirm the study boundary from the title, methods, maps, and nearby text before allowing any basin-level interpretation.",
    },
    "DUPLICATION_UNCLEAR": {
        "typical_reason": "The available section evidence does not establish whether the content materially duplicates another source.",
        "next_action": "Compare the section with overlapping reports after its structure and scope are repaired; retain the stronger source while preserving provenance.",
    },
    "TABLE_FIGURE_CONTEXT": {
        "typical_reason": "The label or excerpt resembles a table, matrix, figure, formula, or value sequence whose meaning depends on missing captions, units, or surrounding explanation.",
        "next_action": "Review the original page with its caption, units, legend, and interpretation; do not ingest the isolated values.",
    },
    "OTHER": {
        "typical_reason": "The evidence does not support a more specific reason category.",
        "next_action": "Perform targeted human review and record the missing evidence before deciding on a classification.",
    },
}


def is_number_table(label, excerpt):
    combined = f"{label} {excerpt}"
    number_count = len(re.findall(r"(?:\d+(?:\.\d+)?|[+×∑])", combined))
    upper_label = label.strip().upper()
    markers = ("TOTAL", "PRIMARY", "YR", "RURAL", "URBAN", "SPACE FOR", "WATER SUPPLY", "+ +")
    return number_count >= 8 or any(marker in upper_label for marker in markers)


def is_noisy(label):
    stripped = label.strip()
    lower = stripped.lower()
    if lower == "unidentified extracted structure":
        return True
    if "@" in stripped or len(stripped) > 100:
        return True
    if re.search(r"\b(?:page|p a g e)\b", lower):
        return True
    if re.match(r"^(?:[a-z]\.?\s*){1,3}(?:to|any|the|a|an)\b", lower):
        return True
    if re.search(r"\b(?:source|expected|government may|which describe|has been convicted)\b", lower) and not re.match(r"^\d", stripped):
        return True
    if len(stripped.split()) >= 7 and not re.match(r"^(?:\d+(?:\.\d+)*|[A-Z])\s*[.)-]\s+", stripped):
        return True
    if stripped.isupper() and len(stripped) <= 35:
        return True
    if re.search(r"\[[^]]+\]|\+\s*\+|\b(?:DDT|STROMATEIDAE|VOP|NUGP|NRGB|UPJN)\b", stripped):
        return True
    return False


def has_historical_signal(label, excerpt):
    text = f"{label} {excerpt}".lower()
    return bool(
        re.search(r"\b(?:19\d{2}|20\d{2})\b", text)
        or re.search(r"\b(?:status|trend|survey|inventory|historical|current|measurement)\b", text)
    )


def has_technical_signal(record):
    text = f"{record['title']} {record['section']} {record['evidence_excerpt']}".lower()
    return bool(
        re.search(r"\b(?:model|modelling|modeling|hydrolog|geomorph|stream power|floodplain|environmental flow|sewage|pollution|technical|calculation|formula|method|framework|mapping|assessment)\b", text)
    )


def classify_reasons(record):
    label = record["section"]
    excerpt = record.get("evidence_excerpt") or ""
    reasons = []
    if record["section_classification"] == "OCR_REQUIRED" or record["OCR_status"] == "REQUIRED":
        return ["OCR_REQUIRED"], "OCR_REQUIRED"
    noisy = is_noisy(label)
    table = is_number_table(label, excerpt)
    if noisy:
        reasons.append("NOISY_EXTRACTION")
    if table:
        reasons.append("TABLE_FIGURE_CONTEXT")
    if noisy or label == "Unidentified extracted structure":
        reasons.append("CONTEXT_DEPENDENT")
    if has_technical_signal(record):
        reasons.append("TECHNICAL_SCOPE_UNCLEAR")
    if has_historical_signal(label, excerpt):
        reasons.append("HISTORICAL_CONTEXT_UNCLEAR")
    if not reasons:
        reasons.append("AMBIGUOUS_RELEVANCE")
    # These are not inferable from the recorded rationale/evidence, so they are
    # intentionally not assigned by this analysis.
    primary_order = [
        "TABLE_FIGURE_CONTEXT",
        "NOISY_EXTRACTION",
        "CONTEXT_DEPENDENT",
        "TECHNICAL_SCOPE_UNCLEAR",
        "HISTORICAL_CONTEXT_UNCLEAR",
        "AMBIGUOUS_RELEVANCE",
    ]
    primary = next(category for category in primary_order if category in reasons)
    return reasons, primary


def example(record):
    return {
        "source_id": record["source_id"],
        "file_name": record["file_name"],
        "section": record["section"],
        "page_start": record["page_start"],
        "page_end": record["page_end"],
        "evidence_excerpt": record.get("evidence_excerpt", ""),
        "recorded_rationale": record["rationale"],
    }


def main():
    review = json.loads(INPUT.read_text(encoding="utf-8"))
    records = [record for record in review["sections"] if record["review_status"] == "HUMAN_REVIEW_REQUIRED"]
    reason_records = []
    category_records = {category: [] for category in CATEGORY_INFO}
    primary_counts = Counter()
    for record in records:
        reasons, primary = classify_reasons(record)
        enriched = {
            "source_id": record["source_id"],
            "file_name": record["file_name"],
            "section": record["section"],
            "page_start": record["page_start"],
            "page_end": record["page_end"],
            "section_classification": record["section_classification"],
            "OCR_status": record["OCR_status"],
            "recorded_rationale": record["rationale"],
            "evidence_excerpt": record.get("evidence_excerpt", ""),
            "reason_categories": reasons,
            "primary_reason": primary,
        }
        reason_records.append(enriched)
        primary_counts[primary] += 1
        for category in reasons:
            category_records[category].append(record)
    denominator = len(records)
    categories = []
    for category, info in CATEGORY_INFO.items():
        category_items = category_records[category]
        categories.append({
            "category": category,
            "count": len(category_items),
            "percentage_of_review_required": round((len(category_items) / denominator) * 100, 2),
            "overlapping_category": category not in {"OCR_REQUIRED", "OTHER"},
            "typical_reason": info["typical_reason"],
            "recommended_next_action": info["next_action"],
            "representative_examples": [example(item) for item in category_items[:5]],
        })
    noise_count = len(category_records["NOISY_EXTRACTION"])
    ocr_count = len(category_records["OCR_REQUIRED"])
    deterministic = sum(
        1
        for record in reason_records
        if record["primary_reason"] == "NOISY_EXTRACTION"
        and "TABLE_FIGURE_CONTEXT" not in record["reason_categories"]
        and record["evidence_excerpt"].strip()
    )
    manual = denominator - ocr_count - deterministic
    analysis = {
        "analysis_version": "stage-2-review-required-analysis",
        "generated_date": date.today().isoformat(),
        "input": "knowledge_base/processed/section_review.json",
        "scope_definition": "All sections with review_status HUMAN_REVIEW_REQUIRED: 542 section_classification REVIEW_REQUIRED records plus 12 OCR_REQUIRED records. Existing classifications were not changed.",
        "method_note": "Categories are evidence-grounded flags, not reclassifications. The source artifact records one dominant non-OCR rationale for 542 records: the extracted heading is not sufficiently interpretable. Suggested categories with no supporting evidence are reported with zero counts rather than inferred.",
        "summary": {
            "review_required_sections_analyzed": denominator,
            "classification_REVIEW_REQUIRED": sum(1 for record in records if record["section_classification"] == "REVIEW_REQUIRED"),
            "classification_OCR_REQUIRED": ocr_count,
            "primarily_extraction_noise": primary_counts["NOISY_EXTRACTION"],
            "extraction_noise_flagged": noise_count,
            "require_actual_human_content_judgement": manual,
            "require_OCR": ocr_count,
            "probably_safely_reclassifiable_using_deterministic_rules": deterministic,
            "genuinely_require_manual_review": manual,
            "category_counts_are_overlapping": True,
        },
        "primary_reason_counts": dict(primary_counts),
        "categories": categories,
        "section_reason_records": reason_records,
        "prioritized_review_plan": [
            {
                "priority": 1,
                "label": "Prevent incorrect knowledge from entering the Brain",
                "focus": ["OCR_REQUIRED", "HISTORICAL_CONTEXT_UNCLEAR", "GEOGRAPHIC_SCOPE_UNCLEAR", "TABLE_FIGURE_CONTEXT"],
                "action": "Resolve missing text, dates, study periods, geographic boundaries, units, captions, and interpretation before approving any section with factual claims or measurements.",
            },
            {
                "priority": 2,
                "label": "Prevent useful knowledge from being excluded",
                "focus": ["AMBIGUOUS_RELEVANCE", "TECHNICAL_SCOPE_UNCLEAR", "CONTEXT_DEPENDENT"],
                "action": "Repair headings and review adjacent pages with a domain reviewer; distinguish useful explanations from specialist detail before filtering.",
            },
            {
                "priority": 3,
                "label": "Repair structural and formatting issues",
                "focus": ["NOISY_EXTRACTION"],
                "action": "Apply deterministic heading cleanup and page-boundary validation, then return unresolved content to the priority 1 or 2 queues.",
            },
        ],
        "unsupported_categories": [
            {"category": category, "reason": "No explicit supporting evidence in the recorded rationale or excerpt; do not infer at this stage."}
            for category in ("GEOGRAPHIC_SCOPE_UNCLEAR", "DUPLICATION_UNCLEAR", "OTHER")
        ],
    }
    (PROCESSED / "review_required_analysis.json").write_text(json.dumps(analysis, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    lines = [
        "# REVIEW_REQUIRED Section Analysis",
        "",
        f"Generated: {analysis['generated_date']}",
        "",
        analysis["scope_definition"],
        "",
        analysis["method_note"],
        "",
        "## Summary",
        "",
    ]
    for key, value in analysis["summary"].items():
        lines.append(f"- {key.replace('_', ' ')}: **{value}**")
    lines += ["", "## Reason categories", "", "Counts overlap where one section has multiple evidence-supported reasons.", ""]
    for category in categories:
        lines += [
            f"### {category['category']}",
            f"- Count: **{category['count']}** ({category['percentage_of_review_required']}% of 554)",
            f"- Typical reason: {category['typical_reason']}",
            f"- Recommended next action: {category['recommended_next_action']}",
            "- Representative examples:",
        ]
        for item in category["representative_examples"]:
            lines.append(f"  - `{item['file_name']}`, pages {item['page_start']}-{item['page_end']}, section `{item['section']}`: {item['evidence_excerpt'][:180]}")
        lines.append("")
    lines += ["## Primary reasons", ""]
    for category, count in sorted(primary_counts.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- {category}: **{count}** ({round(count / denominator * 100, 2)}%)")
    lines += ["", "## Prioritized review plan", ""]
    for item in analysis["prioritized_review_plan"]:
        lines += [f"### Priority {item['priority']}: {item['label']}", f"- Focus: {', '.join(item['focus'])}", f"- Action: {item['action']}", ""]
    lines += ["## Unsupported categories", "", "These categories were not assigned because the current rationale/evidence does not support them:", ""]
    for item in analysis["unsupported_categories"]:
        lines.append(f"- **{item['category']}**: {item['reason']}")
    lines += ["", "## Recommendation", "", "Repair extraction structure first, then perform targeted OCR for the 11 OCR-affected documents. After those repairs, route factual/date/geography/table uncertainties through human review before resolving relevance or technical-scope questions. Do not begin chunking until the repaired records have complete section context and explicit temporal/geographic decisions.", ""]
    (PROCESSED / "review_required_analysis.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()