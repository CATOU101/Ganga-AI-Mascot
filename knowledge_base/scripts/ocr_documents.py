#!/usr/bin/env python3
"""Run explicitly requested local OCR jobs from the OCR-required manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "knowledge_base" / "processed" / "ocr_required_manifest.json"
OCR_ROOT = ROOT / "knowledge_base" / "processed" / "ocr"
EXECUTION_MANIFEST = OCR_ROOT / "manifests" / "ocr_execution_manifest.json"
PILOT_REPORT = OCR_ROOT / "reports" / "ocr_pilot_report.md"
TESSERACT_CONFIG = ("--psm", "3")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require_tools() -> tuple[str | None, str | None]:
    return shutil.which("pdftoppm"), shutil.which("tesseract")


def load_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def title_map() -> dict[str, str]:
    path = ROOT / "knowledge_base" / "processed" / "section_review.json"
    if not path.exists():
        return {}
    review = json.loads(path.read_text(encoding="utf-8"))
    return {item["file_name"]: item["title"] for item in review.get("documents", [])}


def source_pdf(filename: str) -> Path:
    return ROOT / "knowledge_base" / "raw_documents" / "GRBMP" / filename


def output_text_path(filename: str, page: int, full_document: bool) -> Path:
    stem = Path(filename).stem
    directory = OCR_ROOT / ("document_ocr" if full_document else "page_ocr") / stem
    return directory / f"page-{page:04d}.txt"


def requested_jobs(manifest: dict, pilot: bool = False) -> list[dict]:
    jobs = []
    pilot_job = None
    for document in manifest.get("documents", []):
        pages = document.get("affected_pages", [])
        if pilot and document.get("ocr_scope") == "PAGE_LEVEL":
            if pages and pilot_job is None:
                pilot_job = (document, pages[0])
            continue
        elif pilot:
            continue
        for page in pages:
            jobs.append(
                {
                    "source_id": document.get("source_id"),
                    "filename": document["filename"],
                    "page": page,
                    "ocr_mode": document["ocr_scope"],
                    "priority": document.get("priority"),
                    "input_path": str(source_pdf(document["filename"]).relative_to(ROOT)),
                }
            )
    if pilot and pilot_job is not None:
        document, page = pilot_job
        jobs.append(
            {
                "source_id": document.get("source_id"),
                "filename": document["filename"],
                "page": page,
                "ocr_mode": document["ocr_scope"],
                "priority": document.get("priority"),
                "input_path": str(source_pdf(document["filename"]).relative_to(ROOT)),
            }
        )
    return jobs


def make_record(job: dict, titles: dict[str, str], status: str, **extra) -> dict:
    return {
        "attempt_id": f"{job['filename']}|page={job['page']}|mode={job['ocr_mode']}",
        "source_id": job["source_id"],
        "filename": job["filename"],
        "title": titles.get(job["filename"]),
        "page": job["page"],
        "ocr_mode": job["ocr_mode"],
        "input_path": job["input_path"],
        "output_path": str(output_text_path(job["filename"], job["page"], job["ocr_mode"] == "FULL_DOCUMENT").relative_to(ROOT)),
        "ocr_engine": "tesseract via pdftoppm" if status != "NOT_ATTEMPTED" else None,
        "ocr_configuration": {"render_dpi": 300, "image_format": "png", "tesseract_config": list(TESSERACT_CONFIG)},
        "timestamp_utc": utc_now(),
        "status": status,
        "attempted": status not in {"NOT_ATTEMPTED", "PENDING_MISSING_DEPENDENCY"},
        "character_count": extra.pop("character_count", 0),
        "confidence": extra.pop("confidence", None),
        **extra,
    }


def preflight(manifest: dict, jobs: list[dict], titles: dict[str, str], pdftoppm: str | None, tesseract: str | None) -> dict:
    records = []
    for job in jobs:
        pdf = source_pdf(job["filename"])
        record = make_record(
            job,
            titles,
            "PENDING_MISSING_DEPENDENCY" if not pdftoppm or not tesseract else "NOT_ATTEMPTED",
            error="Required tools unavailable: pdftoppm and/or tesseract." if not pdftoppm or not tesseract else None,
            input_sha256=sha256(pdf) if pdf.exists() else None,
        )
        records.append(record)
    return {
        "manifest_version": "stage-3-ocr-execution",
        "generated_at_utc": utc_now(),
        "requested_manifest": str(DEFAULT_MANIFEST.relative_to(ROOT)),
        "execution_performed": False,
        "environment": {"pdftoppm": pdftoppm, "tesseract": tesseract},
        "records": records,
        "note": "Preflight only. No OCR was attempted because required local tools are unavailable." if not pdftoppm or not tesseract else "Preflight only. Use --run-manifest or --pilot to execute explicitly requested jobs.",
    }


def run_job(job: dict, titles: dict[str, str], pdftoppm: str, tesseract: str) -> dict:
    pdf = source_pdf(job["filename"])
    output = output_text_path(job["filename"], job["page"], job["ocr_mode"] == "FULL_DOCUMENT")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ganga-ocr-") as temporary:
        image_base = Path(temporary) / "page"
        render = subprocess.run(
            [pdftoppm, "-f", str(job["page"]), "-l", str(job["page"]), "-r", "300", "-png", "-singlefile", str(pdf), str(image_base)],
            capture_output=True,
            text=True,
        )
        if render.returncode != 0:
            return make_record(job, titles, "FAILED", error=f"pdftoppm failed: {render.stderr.strip()}", input_sha256=sha256(pdf))
        image = image_base.with_suffix(".png")
        image_name = image.name
        ocr = subprocess.run([tesseract, image_name, "stdout", *TESSERACT_CONFIG], capture_output=True, text=True, cwd=temporary)
        text = ocr.stdout.strip()
        if ocr.returncode != 0 or not text:
            return make_record(job, titles, "FAILED", error=f"tesseract failed or returned empty text: {ocr.stderr.strip()}", input_sha256=sha256(pdf))
        confidence = None
        confidence_ocr = subprocess.run(
            [tesseract, image_name, "stdout", *TESSERACT_CONFIG, "tsv"],
            capture_output=True,
            text=True,
            cwd=temporary,
        )
        if confidence_ocr.returncode == 0:
            values = []
            for line in confidence_ocr.stdout.splitlines()[1:]:
                fields = line.split("\t")
                if len(fields) >= 11:
                    try:
                        value = float(fields[10])
                    except ValueError:
                        continue
                    if value >= 0:
                        values.append(value)
            if values:
                confidence = round(sum(values) / len(values), 2)
        output.write_text(text + "\n", encoding="utf-8")
        return make_record(job, titles, "SUCCESS", character_count=len(text), confidence=confidence, input_sha256=sha256(pdf))


def write_execution(records: list[dict], environment: dict, performed: bool, note: str) -> None:
    EXECUTION_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    EXECUTION_MANIFEST.write_text(json.dumps({
        "manifest_version": "stage-3-ocr-execution",
        "generated_at_utc": utc_now(),
        "requested_manifest": str(DEFAULT_MANIFEST.relative_to(ROOT)),
        "execution_performed": performed,
        "environment": environment,
        "records": records,
        "note": note,
    }, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def write_pilot_report(job: dict, preflight_data: dict, result: dict | None) -> None:
    PILOT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# OCR Pilot Report",
        "",
        f"- Selected document: `{job['filename']}`",
        f"- Selected page: **{job['page']}**",
        "- Selection basis: first explicitly listed page-level OCR candidate; no content classification was made.",
        "- OCR method: local Poppler `pdftoppm` rendering at 300 DPI followed by Tesseract (`--psm 3`).",
        f"- Detected `pdftoppm`: `{preflight_data['environment'].get('pdftoppm')}`",
        f"- Detected `tesseract`: `{preflight_data['environment'].get('tesseract')}`",
        "",
    ]
    if result is None:
        lines += [
            "## Status: PENDING",
            "",
            "The pilot was not executed because the required local OCR tools are unavailable. No OCR output was produced, no extracted JSONL was changed, and the source PDF was untouched.",
            "",
            "Workflow readiness: **blocked pending local installation/configuration of Poppler and Tesseract**.",
        ]
    else:
        lines += [
            f"## Status: {result['status']}",
            "",
            f"- Output: `{result['output_path']}`",
            f"- Character count: **{result['character_count']}**",
            f"- Error: {result.get('error') or 'none'}",
            "- Interpretation: Tesseract executed, but zero characters means this pilot is not a usable OCR success; the rendered page was blank/no OCR-readable content.",
            "- Provenance check: source filename and page number are recorded in the execution manifest.",
            "- Original PDF modified: **No**.",
        ]
    PILOT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--preflight", action="store_true", help="Record requested jobs and environment without OCR.")
    parser.add_argument("--pilot", action="store_true", help="Execute only the first page-level manifest job.")
    parser.add_argument("--run-manifest", action="store_true", help="Execute every job explicitly listed in the manifest.")
    args = parser.parse_args()
    if sum((args.preflight, args.pilot, args.run_manifest)) != 1:
        parser.error("choose exactly one of --preflight, --pilot, or --run-manifest")
    manifest = load_manifest(args.manifest)
    titles = title_map()
    pdftoppm, tesseract = require_tools()
    jobs = requested_jobs(manifest, pilot=args.pilot)
    if args.preflight:
        data = preflight(manifest, requested_jobs(manifest), titles, pdftoppm, tesseract)
        write_execution(data["records"], data["environment"], False, data["note"])
        return 0 if pdftoppm and tesseract else 2
    if args.pilot and (not pdftoppm or not tesseract):
        data = preflight(manifest, requested_jobs(manifest), titles, pdftoppm, tesseract)
        write_execution(data["records"], data["environment"], False, data["note"])
        if jobs:
            write_pilot_report(jobs[0], data, None)
        return 2
    if not pdftoppm or not tesseract:
        print("OCR pending: install local pdftoppm and tesseract before execution.")
        return 2
    if args.pilot:
        all_jobs = requested_jobs(manifest)
        baseline = preflight(manifest, all_jobs, titles, pdftoppm, tesseract)
        result = run_job(jobs[0], titles, pdftoppm, tesseract)
        records_by_key = {(item["filename"], item["page"]): item for item in baseline["records"]}
        records_by_key[(result["filename"], result["page"])] = result
        results = list(records_by_key.values())
        write_execution(results, {"pdftoppm": pdftoppm, "tesseract": tesseract}, True, "Pilot execution completed for one explicitly selected page; remaining jobs were not attempted.")
        write_pilot_report(jobs[0], {"environment": {"pdftoppm": pdftoppm, "tesseract": tesseract}}, result)
        return 0 if result["status"] == "SUCCESS" else 1
    results = [run_job(job, titles, pdftoppm, tesseract) for job in jobs]
    write_execution(results, {"pdftoppm": pdftoppm, "tesseract": tesseract}, True, "Explicit OCR execution completed; inspect per-page records and validation report.")
    if args.pilot and jobs:
        write_pilot_report(jobs[0], {"environment": {"pdftoppm": pdftoppm, "tesseract": tesseract}}, results[0])
    return 0 if all(item["status"] == "SUCCESS" for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())