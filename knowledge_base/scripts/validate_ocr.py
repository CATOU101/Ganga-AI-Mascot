#!/usr/bin/env python3
"""Validate OCR execution records against the explicit OCR-required manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OCR_ROOT = ROOT / "knowledge_base" / "processed" / "ocr"
REQUESTED = ROOT / "knowledge_base" / "processed" / "ocr_required_manifest.json"
EXECUTED = OCR_ROOT / "manifests" / "ocr_execution_manifest.json"
REPORT = OCR_ROOT / "reports" / "ocr_validation_report.md"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requested", type=Path, default=REQUESTED)
    parser.add_argument("--executed", type=Path, default=EXECUTED)
    args = parser.parse_args()
    requested = json.loads(args.requested.read_text(encoding="utf-8"))
    executed = json.loads(args.executed.read_text(encoding="utf-8"))
    expected = {(item["filename"], page): item for item in requested["documents"] for page in item["affected_pages"]}
    records = executed.get("records", [])
    seen = {(item.get("filename"), item.get("page")) for item in records}
    duplicate_count = len(records) - len(seen)
    missing = sorted(set(expected) - seen)
    invalid = []
    success = []
    failed = []
    low_quality = []
    for record in records:
        key = (record.get("filename"), record.get("page"))
        source = expected.get(key)
        if source is None:
            invalid.append(f"unexpected record {key}")
            continue
        if record.get("source_id") != source.get("source_id"):
            invalid.append(f"source_id mismatch for {key}")
        input_path = ROOT / record.get("input_path", "")
        if not input_path.exists():
            invalid.append(f"missing input PDF for {key}")
        elif record.get("input_sha256") and digest(input_path) != record["input_sha256"]:
            invalid.append(f"input PDF hash changed for {key}")
        if record.get("status") == "SUCCESS":
            output = ROOT / record.get("output_path", "")
            if not output.exists() or not output.read_text(encoding="utf-8").strip():
                invalid.append(f"successful record has no usable output for {key}")
            else:
                success.append(key)
            if not record.get("character_count", 0):
                low_quality.append(key)
        elif record.get("status") in {"FAILED", "PENDING_MISSING_DEPENDENCY", "NOT_ATTEMPTED"}:
            failed.append(key)
            if record.get("status") == "SUCCESS" and not record.get("attempted"):
                invalid.append(f"success record not marked attempted for {key}")
        else:
            invalid.append(f"unknown status for {key}: {record.get('status')}")
    original_unchanged = not any("input PDF hash changed" in item for item in invalid)
    validation_ok = not missing and duplicate_count == 0 and not invalid and not low_quality and not failed
    report_lines = [
        "# OCR Validation Report",
        "",
        f"- Validation manifest: `{args.executed.relative_to(ROOT)}`",
        f"- Total requested OCR candidates/pages: **{len(expected)}**",
        f"- Page-level documents: **{sum(item['ocr_scope'] == 'PAGE_LEVEL' for item in requested['documents'])}**",
        f"- Full-document candidates: **{sum(item['ocr_scope'] == 'FULL_DOCUMENT' for item in requested['documents'])}**",
        f"- Pages attempted: **{sum(bool(item.get('attempted')) for item in records)}**",
        f"- Pages successfully OCR'd: **{len(success)}**",
        f"- Pages failed or pending: **{len(failed)}**",
        f"- Empty/low-quality outputs: **{len(low_quality)}**",
        f"- Documents completed: **{len({key[0] for key in success})}**",
        f"- Documents requiring another attempt: **{len({key[0] for key in failed})}**",
        "",
        "## Checks",
        "",
        f"- Every requested page represented: **{'PASS' if not missing else 'FAIL'}** ({len(missing)} missing)",
        f"- Duplicate OCR records: **{'PASS' if duplicate_count == 0 else 'FAIL'}** ({duplicate_count})",
        f"- Provenance/source IDs: **{'PASS' if not invalid else 'FAIL'}**",
        f"- Original PDFs unchanged relative to recorded hashes: **{'PASS' if original_unchanged else 'FAIL'}**",
        f"- No success record without usable text: **{'PASS' if not low_quality else 'FAIL'}**",
        "",
        "## Environment and status",
        "",
        f"- OCR engine information: `{executed.get('environment')}`",
        f"- Execution performed: **{executed.get('execution_performed')}**",
        f"- Validation result: **{'PASS' if validation_ok else 'PENDING/FAIL'}**",
        "",
    ]
    if missing:
        report_lines.append(f"Missing records: `{missing[:10]}`")
    if invalid:
        report_lines.extend(["Validation issues:", *[f"- {item}" for item in invalid]])
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    return 0 if validation_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())