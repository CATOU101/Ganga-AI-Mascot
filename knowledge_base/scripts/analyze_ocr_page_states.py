#!/usr/bin/env python3
"""Diagnose page-level OCR candidates using rendering and PDF object evidence only."""

from __future__ import annotations

import argparse
import json
import re
import struct
import subprocess
import tempfile
import zlib
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "knowledge_base" / "processed" / "ocr_required_manifest.json"
REPORT_DIR = ROOT / "knowledge_base" / "processed" / "ocr" / "reports"


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, check=False)


def png_statistics(path: Path) -> tuple[int, int, int, int]:
    data = path.read_bytes()
    position = 8
    idat: list[bytes] = []
    width = height = depth = color_type = None
    while position < len(data):
        length = struct.unpack(">I", data[position : position + 4])[0]
        kind = data[position + 4 : position + 8]
        chunk = data[position + 8 : position + 8 + length]
        position += length + 12
        if kind == b"IHDR":
            width, height, depth, color_type, _, _, _ = struct.unpack(">IIBBBBB", chunk)
        elif kind == b"IDAT":
            idat.append(chunk)
    if depth != 8 or color_type not in {0, 2, 3, 4, 6}:
        raise ValueError(f"unsupported PNG format depth={depth} color_type={color_type}")
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color_type]
    bytes_per_pixel = max(1, channels)
    row_bytes = width * channels
    raw = zlib.decompress(b"".join(idat))
    previous = bytearray(row_bytes)
    offset = 0
    non_white = 0
    for _ in range(height):
        filter_type = raw[offset]
        current = bytearray(raw[offset + 1 : offset + 1 + row_bytes])
        offset += row_bytes + 1
        for index in range(row_bytes):
            left = current[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
            above = previous[index]
            upper_left = previous[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
            if filter_type == 1:
                current[index] = (current[index] + left) & 255
            elif filter_type == 2:
                current[index] = (current[index] + above) & 255
            elif filter_type == 3:
                current[index] = (current[index] + ((left + above) // 2)) & 255
            elif filter_type == 4:
                estimate = left + above - upper_left
                distances = (abs(estimate - left), abs(estimate - above), abs(estimate - upper_left))
                predictor = (left, above, upper_left)[distances.index(min(distances))]
                current[index] = (current[index] + predictor) & 255
            elif filter_type != 0:
                raise ValueError(f"unsupported PNG filter {filter_type}")
        for index in range(0, row_bytes, channels):
            if any(value < 255 for value in current[index : index + channels]):
                non_white += 1
        previous = current
    return width, height, width * height, non_white


def direct_text_count(pdf: Path, page: int) -> int:
    result = run(["pdftotext", "-f", str(page), "-l", str(page), "-layout", str(pdf), "-"])
    return len(result.stdout)


def embedded_object_count(pdf: Path, page: int) -> int:
    result = run(["pdfimages", "-f", str(page), "-l", str(page), "-list", str(pdf)])
    count = 0
    for line in result.stdout.splitlines():
        if re.match(r"^\s*\d+\s+\d+\s+\S+\s+\d+\s+\d+\s+", line):
            count += 1
    return count


def page_metadata(pdf: Path) -> dict[str, str]:
    result = run(["pdfinfo", str(pdf)])
    metadata = {}
    for line in result.stdout.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip()
    return metadata


def diagnose(text_count: int, object_count: int, non_white: int, total_pixels: int) -> tuple[str, str, str, str]:
    ratio = non_white / total_pixels if total_pixels else 0
    if non_white == 0 and text_count <= 1 and object_count == 0:
        return "BLANK_SOURCE_PAGE", "HIGH", "The rendered page is entirely white, direct extraction is empty/newline-only, and no embedded image objects were reported.", "Remove this page from OCR execution consideration after human confirmation that it is an intentional blank page."
    if non_white == 0 and (text_count > 1 or object_count > 0):
        return "UNCERTAIN", "MEDIUM", "The render is entirely white, but PDF text/object evidence indicates content may exist; inspect the source page and renderer behavior.", "Human inspection required before changing OCR treatment."
    if text_count <= 1 and non_white > 0:
        return "OCR_REQUIRED", "HIGH" if ratio > 0.001 else "MEDIUM", "The page visibly contains non-white rendered content but direct extraction is empty/newline-only.", "Retain as an OCR candidate; run OCR only after this diagnostic review is accepted."
    if text_count > 1 and non_white > 0:
        return "EXTRACTION_VALID", "MEDIUM", "The page contains visible rendered content and direct extraction produced text; OCR is not objectively required by this page-state test.", "Compare extracted text quality manually; do not run OCR solely because the page was previously flagged."
    return "UNCERTAIN", "LOW", "Available render and extraction evidence is insufficient for a confident state.", "Human inspection required."


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    records = []
    for document in manifest["documents"]:
        if document["ocr_scope"] != "PAGE_LEVEL":
            continue
        pdf = ROOT / "knowledge_base" / "raw_documents" / "GRBMP" / document["filename"]
        metadata = page_metadata(pdf)
        for page in document["affected_pages"]:
            with tempfile.TemporaryDirectory(prefix="ganga-page-state-") as temporary:
                output_base = Path(temporary) / "page"
                render = run(["pdftoppm", "-f", str(page), "-l", str(page), "-r", "300", "-png", "-singlefile", str(pdf), str(output_base)])
                image = output_base.with_suffix(".png")
                if render.returncode != 0 or not image.exists():
                    records.append({
                        "filename": document["filename"], "source_id": document.get("source_id"), "page": page,
                        "direct_text_character_count": direct_text_count(pdf, page), "embedded_object_count": embedded_object_count(pdf, page),
                        "rendered_width": None, "rendered_height": None, "rendered_file_size": None, "total_pixels": None, "non_white_pixel_count": None,
                        "extraction_state": "UNCERTAIN", "confidence": "LOW", "evidence": f"Poppler rendering failed: {render.stderr.strip()}",
                        "recommended_next_step": "Human inspection and renderer diagnosis required.", "page_metadata": metadata,
                    })
                    continue
                width, height, total_pixels, non_white = png_statistics(image)
                text_count = direct_text_count(pdf, page)
                object_count = embedded_object_count(pdf, page)
                state, confidence, evidence, next_step = diagnose(text_count, object_count, non_white, total_pixels)
                records.append({
                    "filename": document["filename"], "source_id": document.get("source_id"), "page": page,
                    "direct_text_character_count": text_count, "embedded_object_count": object_count,
                    "rendered_width": width, "rendered_height": height, "rendered_file_size": image.stat().st_size,
                    "total_pixels": total_pixels, "non_white_pixel_count": non_white,
                    "extraction_state": state, "confidence": confidence, "evidence": evidence,
                    "recommended_next_step": next_step, "page_metadata": metadata,
                })
    counts = {state: sum(record["extraction_state"] == state for record in records) for state in ("BLANK_SOURCE_PAGE", "OCR_REQUIRED", "EXTRACTION_VALID", "UNCERTAIN")}
    output = {
        "analysis_version": "stage-3-page-state-analysis",
        "generated_date": date.today().isoformat(),
        "input_manifest": str(args.manifest.relative_to(ROOT)),
        "scope": "PAGE_LEVEL entries only; the full-document Surface and Groundwater Modelling candidate was not processed.",
        "ocr_executed": False,
        "summary": {
            "page_level_candidate_documents_examined": len({record["filename"] for record in records}),
            "page_level_candidate_pages_examined": len(records),
            **{f"{key}_count": value for key, value in counts.items()},
        },
        "records": records,
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "page_state_analysis.json").write_text(json.dumps(output, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    lines = [
        "# OCR Candidate Page-State Analysis", "", "No OCR was executed. The full-document modelling candidate was not processed.", "",
        f"- Page-level candidate documents examined: **{len({record['filename'] for record in records})}**",
        f"- Page-level candidate pages examined: **{len(records)}**",
        f"- BLANK_SOURCE_PAGE: **{counts['BLANK_SOURCE_PAGE']}**",
        f"- OCR_REQUIRED: **{counts['OCR_REQUIRED']}**",
        f"- EXTRACTION_VALID: **{counts['EXTRACTION_VALID']}**",
        f"- UNCERTAIN: **{counts['UNCERTAIN']}**", "",
    ]
    for record in records:
        lines += [
            f"## {record['filename']} — page {record['page']}",
            f"- Source ID: `{record['source_id']}`; state: **{record['extraction_state']}**; confidence: **{record['confidence']}**",
            f"- Direct text characters: **{record['direct_text_character_count']}**; embedded objects: **{record['embedded_object_count']}**",
            f"- Render: **{record['rendered_width']} x {record['rendered_height']}**, {record['rendered_file_size']} bytes; total pixels: **{record['total_pixels']}**; non-white pixels: **{record['non_white_pixel_count']}**",
            f"- Evidence: {record['evidence']}", f"- Recommended next step: {record['recommended_next_step']}", "",
        ]
    (REPORT_DIR / "page_state_analysis.md").write_text("\n".join(lines), encoding="utf-8")
    reconciliation = [
        "# OCR Candidate Reconciliation", "", "Only page-level manifest candidates were examined; the 99-page modelling document was not processed.", "",
        f"- Total page-level candidate documents examined: **{len({record['filename'] for record in records})}**",
        f"- Total page-level candidate pages examined: **{len(records)}**",
        f"- BLANK_SOURCE_PAGE: **{counts['BLANK_SOURCE_PAGE']}**",
        f"- OCR_REQUIRED: **{counts['OCR_REQUIRED']}**",
        f"- EXTRACTION_VALID: **{counts['EXTRACTION_VALID']}**",
        f"- UNCERTAIN: **{counts['UNCERTAIN']}**", "",
        "## Genuine OCR requirements", "",
    ]
    for record in records:
        if record["extraction_state"] == "OCR_REQUIRED":
            reconciliation.append(f"- `{record['filename']}`, page {record['page']}: {record['evidence']}")
    reconciliation += ["", "## Pages no longer objectively supported as OCR problems", ""]
    for record in records:
        if record["extraction_state"] == "BLANK_SOURCE_PAGE":
            reconciliation.append(f"- `{record['filename']}`, page {record['page']}: blank render, no text, and no embedded objects.")
    reconciliation += ["", "## Suspicious cases", "", "No page was classified UNCERTAIN by the objective checks." if not counts["UNCERTAIN"] else "Review the UNCERTAIN records in page_state_analysis.json.", "", "No source, manifest, classification, PDF, or extracted JSONL files were modified. No OCR was executed.", ""]
    (REPORT_DIR / "ocr_candidate_reconciliation.md").write_text("\n".join(reconciliation), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())