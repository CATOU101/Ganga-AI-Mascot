#!/usr/bin/env python3
"""Diagnose Surface/GW page states without executing OCR."""

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
FILENAME = "46_57_Surface and GW Modelling of the GRB (2).pdf"
SOURCE_ID = "GRBMP-TR-055"
PDF = ROOT / "knowledge_base" / "raw_documents" / "GRBMP" / FILENAME
REPORT_DIR = ROOT / "knowledge_base" / "processed" / "ocr" / "reports"
CHECKPOINT = REPORT_DIR / "surface_gw_page_state_checkpoint.json"


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, check=False)


def png_stats(path: Path) -> tuple[int, int, int, int]:
    data = path.read_bytes()
    position = 8
    idat = []
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


def pdf_metadata() -> dict[str, str]:
    result = run(["pdfinfo", str(PDF)])
    metadata = {}
    for line in result.stdout.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip()
    return metadata


def direct_text(page: int) -> tuple[int, str]:
    result = run(["pdftotext", "-f", str(page), "-l", str(page), "-layout", str(PDF), "-"])
    return len(result.stdout), result.stdout[:240].replace("\n", " ")


def image_objects(page: int) -> tuple[int, list[str]]:
    result = run(["pdfimages", "-f", str(page), "-l", str(page), "-list", str(PDF)])
    objects = []
    for line in result.stdout.splitlines():
        if re.match(r"^\s*\d+\s+\d+\s+\S+\s+\d+\s+\d+\s+", line):
            objects.append(" ".join(line.split()))
    return len(objects), objects


def classify(text_count: int, image_count: int, non_white: int, total_pixels: int) -> tuple[str, str, str, str]:
    percentage = non_white / total_pixels * 100 if total_pixels else 0
    if non_white == 0 and text_count <= 1 and image_count == 0:
        return "BLANK_SOURCE_PAGE", "HIGH", "The rendered page is entirely white, direct extraction is empty/newline-only, and no raster image objects were found.", "No OCR is indicated by this page-state evidence; retain the page as a documented blank source page."
    if non_white == 0:
        return "UNCERTAIN", "LOW", "The render is blank but PDF structure indicates possible content; page-level inspection is required.", "Inspect the source page and PDF object structure manually before choosing an extraction method."
    if text_count > 1:
        return "EXTRACTION_VALID", "MEDIUM", f"The page has visible content ({percentage:.4f}% non-white) and direct extraction returned text.", "Review extraction quality; OCR is not justified solely by the existing full-document flag."
    if image_count > 0:
        return "IMAGE_BASED_CONTENT", "HIGH", f"The page has visible content ({percentage:.4f}% non-white), no usable direct text, and {image_count} raster image object(s).", "Use a page-rendering OCR workflow only after manual confirmation that the image content is substantive."
    return "VECTOR_GRAPHICS_CONTENT", "MEDIUM", f"The page has visible content ({percentage:.4f}% non-white) but no usable direct text or raster image objects; content is likely vector graphics or outlined content.", "Prefer vector-aware or layout-aware PDF extraction; OCR may be lossy and should not be the first method."


def write_checkpoint(records: list[dict]) -> None:
    CHECKPOINT.parent.mkdir(parents=True, exist_ok=True)
    temporary = CHECKPOINT.with_suffix(".tmp")
    temporary.write_text(json.dumps({
        "checkpoint_version": "stage-3-surface-gw-page-state",
        "filename": FILENAME,
        "source_id": SOURCE_ID,
        "pages_examined": len(records),
        "records": records,
    }, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    temporary.replace(CHECKPOINT)


def load_checkpoint() -> list[dict]:
    if not CHECKPOINT.exists():
        return []
    checkpoint = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
    records = checkpoint.get("records", [])
    pages = [record.get("page") for record in records]
    if checkpoint.get("filename") != FILENAME or len(pages) != len(set(pages)):
        raise ValueError("invalid or duplicate Surface/GW checkpoint")
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-page", type=int, default=1)
    parser.add_argument("--end-page", type=int, default=99)
    parser.add_argument("--reset", action="store_true", help="Delete the checkpoint before starting.")
    args = parser.parse_args()
    if not 1 <= args.start_page <= args.end_page <= 99:
        parser.error("page range must be within 1-99")
    if args.reset and CHECKPOINT.exists():
        CHECKPOINT.unlink()
    records = load_checkpoint()
    existing_pages = {record["page"] for record in records}
    if any(page in existing_pages for page in range(args.start_page, args.end_page + 1)):
        records = [record for record in records if record["page"] not in range(args.start_page, args.end_page + 1)]
    metadata = pdf_metadata()
    for page in range(args.start_page, args.end_page + 1):
        text_count, text_excerpt = direct_text(page)
        image_count, image_details = image_objects(page)
        with tempfile.TemporaryDirectory(prefix="ganga-surface-gw-") as temporary:
            base = Path(temporary) / "page"
            render = run(["pdftoppm", "-f", str(page), "-l", str(page), "-r", "300", "-png", "-singlefile", str(PDF), str(base)])
            image = base.with_suffix(".png")
            if render.returncode != 0 or not image.exists():
                records.append({
                    "filename": FILENAME, "source_id": SOURCE_ID, "page": page,
                    "direct_text_character_count": text_count, "embedded_image_count": image_count,
                    "vector_object_information": {"raster_image_details": image_details, "pdfinfo": metadata},
                    "rendered_width": None, "rendered_height": None, "rendered_file_size": None,
                    "total_pixels": None, "non_white_pixels": None, "non_white_percentage": None,
                    "extraction_state": "UNCERTAIN", "confidence": "LOW",
                    "evidence": f"Poppler rendering failed: {render.stderr.strip()}",
                    "recommended_next_step": "Manual renderer/PDF inspection required.", "text_excerpt": text_excerpt,
                })
                write_checkpoint(records)
                continue
            width, height, total_pixels, non_white = png_stats(image)
            state, confidence, evidence, next_step = classify(text_count, image_count, non_white, total_pixels)
            records.append({
                "filename": FILENAME, "source_id": SOURCE_ID, "page": page,
                "direct_text_character_count": text_count, "embedded_image_count": image_count,
                "vector_object_information": {"raster_image_details": image_details, "pdfinfo": metadata},
                "rendered_width": width, "rendered_height": height, "rendered_file_size": image.stat().st_size,
                "total_pixels": total_pixels, "non_white_pixels": non_white,
                "non_white_percentage": round(non_white / total_pixels * 100, 6) if total_pixels else 0,
                "extraction_state": state, "confidence": confidence, "evidence": evidence,
                "recommended_next_step": next_step, "text_excerpt": text_excerpt,
            })
            write_checkpoint(records)
    records.sort(key=lambda record: record["page"])
    write_checkpoint(records)
    if len(records) != 99 or {record["page"] for record in records} != set(range(1, 100)):
        print(f"Checkpoint saved: {len(records)}/99 pages; final reports withheld.")
        return 0
    states = ("BLANK_SOURCE_PAGE", "IMAGE_BASED_CONTENT", "VECTOR_GRAPHICS_CONTENT", "TEXT_EXTRACTION_FAILURE", "EXTRACTION_VALID", "UNCERTAIN")
    counts = {state: sum(record["extraction_state"] == state for record in records) for state in states}
    output = {
        "analysis_version": "stage-3-surface-gw-page-state-diagnosis",
        "generated_date": date.today().isoformat(),
        "filename": FILENAME, "source_id": SOURCE_ID, "pages_requested": [1, 99],
        "pages_examined": len(records), "ocr_executed": False,
        "summary": counts, "records": records,
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "surface_gw_page_state_analysis.json").write_text(json.dumps(output, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    lines = ["# Surface/GW Page-State Analysis", "", "OCR was not executed. Pages 1-99 were diagnosed with Poppler rendering and PDF text/image inspection only.", "", f"- Pages examined: **{len(records)}/99**"]
    for state in states:
        lines.append(f"- {state}: **{counts[state]}**")
    lines.append("")
    for record in records:
        lines.extend([
            f"## Page {record['page']}",
            f"- State: **{record['extraction_state']}**; confidence: **{record['confidence']}**",
            f"- Direct text characters: **{record['direct_text_character_count']}**; embedded images: **{record['embedded_image_count']}**",
            f"- Render: **{record['rendered_width']} x {record['rendered_height']}**, {record['rendered_file_size']} bytes; pixels: **{record['total_pixels']}**; non-white: **{record['non_white_pixels']} ({record['non_white_percentage']}%)**",
            f"- Evidence: {record['evidence']}", f"- Recommended next step: {record['recommended_next_step']}", "",
        ])
    (REPORT_DIR / "surface_gw_page_state_analysis.md").write_text("\n".join(lines), encoding="utf-8")
    diagnosis = [
        "# Surface/GW Extraction Diagnosis", "", f"- Total pages examined: **{len(records)}/99**", "",
        *[f"- {state}: **{counts[state]}**" for state in states], "",
        "## Interpretation", "",
        "The dominant page state is based on the per-page evidence above. OCR is not executed by this diagnosis.", "",
        "- OCR appropriateness: " + ("No page is objectively identified as requiring raster OCR by this test." if not counts["IMAGE_BASED_CONTENT"] else "Raster OCR may be appropriate for IMAGE_BASED_CONTENT pages after manual confirmation."),
        "- Different extraction method: Consider vector-aware/layout-aware extraction for VECTOR_GRAPHICS_CONTENT pages; do not assume OCR is the best remedy.",
        "- Manual inspection: Required for any UNCERTAIN pages and recommended before changing treatment of this full-document candidate.",
        "",
        "No raw PDF, extracted JSONL, OCR manifest, source metadata, classification, chunk, embedding, vector database, RAG, or API artifact was modified.", "",
    ]
    (REPORT_DIR / "surface_gw_diagnosis.md").write_text("\n".join(diagnosis), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())