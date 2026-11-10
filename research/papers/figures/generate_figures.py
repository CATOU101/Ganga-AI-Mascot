#!/usr/bin/env python3
"""Generate vector result figures directly from the checked-in benchmark JSON.

Uses only the Python standard library. It never runs a benchmark or reads the
knowledge index; it validates dataset hashes and plots saved aggregate results.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
BENCH = ROOT / "research" / "benchmark"
OUT = Path(__file__).resolve().parent
CONFIGS = ("A", "B", "C", "D")
METRIC_LABELS = {
    "precision_at_5": "Precision@5",
    "recall_at_5": "Recall@5",
    "mrr_at_5": "MRR@5",
}


class Figure:
    """Minimal vector drawing surface, exported as PDF 1.4 using base fonts."""

    def __init__(self, width: float, height: float) -> None:
        self.width, self.height = width, height
        self.ops: list[str] = []

    def line(self, x1: float, y1: float, x2: float, y2: float, color: str = "0") -> None:
        self.ops.append(f"{color} G 0.55 w {x1:.2f} {y1:.2f} m {x2:.2f} {y2:.2f} l S")

    def rect(self, x: float, y: float, w: float, h: float, gray: float, stroke: bool = False) -> None:
        self.ops.append(f"{gray:.3f} g {gray:.3f} G 0.45 w {x:.2f} {y:.2f} {w:.2f} {h:.2f} re {'B' if stroke else 'f'}")

    def text(self, x: float, y: float, value: str, size: float = 8, bold: bool = False) -> None:
        value = value.encode("ascii", "replace").decode("ascii")
        value = value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        font = "F2" if bold else "F1"
        self.ops.append(f"BT /{font} {size:.1f} Tf 0 g 1 0 0 1 {x:.2f} {y:.2f} Tm ({value}) Tj ET")

    def save_pdf(self, path: Path) -> None:
        background = f"1 g 0 0 {self.width:.2f} {self.height:.2f} re f"
        stream = (background + "\n" + "\n".join(self.ops)).encode("ascii")
        objects = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {self.width:.2f} {self.height:.2f}] /Resources << /Font << /F1 5 0 R /F2 6 0 R >> >> /Contents 4 0 R >>".encode("ascii"),
            f"<< /Length {len(stream)} >>\nstream\n".encode("ascii") + stream + b"\nendstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
        ]
        data = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = [0]
        for idx, body in enumerate(objects, start=1):
            offsets.append(len(data))
            data.extend(f"{idx} 0 obj\n".encode("ascii"))
            data.extend(body)
            data.extend(b"\nendobj\n")
        xref = len(data)
        data.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode("ascii"))
        for offset in offsets[1:]:
            data.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
        data.extend(f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii"))
        path.write_bytes(data)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_verified(name: str, dataset_name: str, expected_count: int) -> tuple[dict, str]:
    result_path = BENCH / name
    dataset_path = BENCH / dataset_name
    result = json.loads(result_path.read_text(encoding="utf-8"))
    actual_hash = sha256(dataset_path)
    recorded_hash = result["benchmark_metadata"]["dataset_sha256"]
    if actual_hash != recorded_hash:
        raise ValueError(f"Dataset hash mismatch for {dataset_name}: {actual_hash} != {recorded_hash}")
    if result["benchmark_metadata"]["total_queries"] != expected_count:
        raise ValueError(f"Unexpected query count in {name}")
    return result, actual_hash


def axes(fig: Figure, x: float, y: float, w: float, h: float, max_value: float, step: float, label: str) -> None:
    fig.line(x, y, x, y + h)
    fig.line(x, y, x + w, y)
    n = int(round(max_value / step))
    for i in range(n + 1):
        value = i * step
        yy = y + h * value / max_value
        fig.line(x - 2, yy, x + w, yy, "0.82")
        fig.text(x - 25, yy - 2.5, f"{value:.2f}", 6.5)
    fig.text(x + w / 2 - len(label) * 2, y + h + 9, label, 8, True)


def retrieval_figure(results: dict) -> None:
    values = results["aggregate_summary"]["production_gated"]
    fig = Figure(516, 205)
    fig.text(34, 190, "Retrieval ablation on shared dense top-15 candidates (n=30 queries)", 9, True)
    panel_x = (32, 202, 372)
    panel_w, plot_y, plot_h, plot_w = 125, 43, 112, 116
    metric_keys = tuple(METRIC_LABELS)
    ymax, step = 0.16, 0.04
    shades = {"A": 0.15, "B": 0.38, "C": 0.62, "D": 0.84}
    for px, metric in zip(panel_x, metric_keys):
        x0 = px + 24
        axes(fig, x0, plot_y, plot_w, plot_h, ymax, step, METRIC_LABELS[metric])
        slot = plot_w / 4
        for idx, config in enumerate(CONFIGS):
            v = values[config]["overall"][metric]
            bh = plot_h * v / ymax
            bx = x0 + idx * slot + slot * 0.25
            fig.rect(bx, plot_y, slot * 0.5, bh, shades[config], stroke=True)
            fig.text(bx - 1.5, plot_y + bh + 3, f"{v:.4f}", 5.8)
            fig.text(bx + slot * 0.12, plot_y - 11, config, 7, True)
    fig.text(425, 20, "Config.", 6.5)
    fig.save_pdf(OUT / "fig1_retrieval_ablation.pdf")


def category_figure(results: dict) -> None:
    values = results["aggregate_summary"]["production_gated"]
    categories = ("Broad/Thematic", "Technical/Scientific", "Governance/Policy")
    labels = ("Broad", "Technical", "Governance")
    shades = {"A": 0.15, "B": 0.38, "C": 0.62, "D": 0.84}
    fig = Figure(516, 188)
    fig.text(55, 174, "Category MRR@5 by configuration (n=10 queries/category)", 9, True)
    panel_x = (31, 201, 371)
    y, h, ymax = 39, 112, 0.36
    plot_w, barw = 108, 13
    for px, category, label in zip(panel_x, categories, labels):
        x = px + 25
        axes(fig, x, y, plot_w, h, ymax, 0.09, label)
        slot = plot_w / 4
        for ci, config in enumerate(CONFIGS):
            v = values[config]["by_category"][category]["mrr_at_5"]
            bx = x + ci * slot + (slot - barw) / 2
            bh = h * v / ymax
            fig.rect(bx, y, barw, bh, shades[config], stroke=True)
            if v > 0:
                fig.text(bx - 4, y + bh + 2, f"{v:.4f}", 5.4)
            else:
                fig.text(bx + 4, y + 2, "0.0000", 5.4, True)
            fig.text(bx + 3.5, y - 11, config, 6.5, True)
    fig.save_pdf(OUT / "fig2_category_mrr.pdf")


def gate_figure(results: dict) -> None:
    queries = results["query_results"]
    groups = (
        ("Answerable In-Domain", "accepted", "Answerable accepted"),
        ("Unsupported Out-of-Domain", "rejected", "Out-of-domain rejected"),
        ("Dynamic / Time-Sensitive", "current-info-fallback", "Dynamic intercepted"),
    )
    rows = []
    for category, expected_mode_or_outcome, label in groups:
        group = [q for q in queries if q["category"] == category]
        if category == "Dynamic / Time-Sensitive":
            matches = sum(q["actual_mode"] == expected_mode_or_outcome for q in group)
        else:
            matches = sum(q["actual_outcome"] == expected_mode_or_outcome for q in group)
        rows.append((label, matches, len(group)))
    if tuple((count, total) for _, count, total in rows) != ((10, 10), (5, 5), (5, 5)):
        raise ValueError(f"Unexpected evidence-gate group outcomes: {rows}")
    fig = Figure(258, 155)
    fig.text(23, 140, "Evidence-gate outcomes (selected set, n=20)", 8.5, True)
    x, bar_max, top = 135, 80, 112
    for i, (label, successes, n) in enumerate(rows):
        y = top - i * 34
        fig.text(12, y + 4, label, 7)
        fig.line(x, y, x + bar_max, y, "0.80")
        fig.rect(x, y - 5, bar_max * successes / 10, 12, 0.30, stroke=True)
        fig.text(x + bar_max + 8, y - 1, f"{successes}/{n}", 7.5, True)
    fig.text(135, 16, "Matching decisions; scale maximum = 10", 6.5)
    fig.save_pdf(OUT / "fig3_evidence_gate.pdf")


def main() -> None:
    retrieval, retrieval_hash = load_verified(
        "retrieval_ablation_results.json", "domain_queries_30.jsonl", 30
    )
    gate, gate_hash = load_verified(
        "evidence_gate_results.json", "evidence_gate_queries_20.jsonl", 20
    )
    grounded, grounded_hash = load_verified(
        "groundedness_results.json", "groundedness_queries_20.jsonl", 20
    )

    expected = {
        "A": (0.0533, 0.1278, 0.1083),
        "B": (0.0533, 0.1333, 0.1261),
        "C": (0.0533, 0.1333, 0.1261),
        "D": (0.0533, 0.1278, 0.1444),
    }
    observed = retrieval["aggregate_summary"]["production_gated"]
    for config, metrics in expected.items():
        got = tuple(observed[config]["overall"][k] for k in METRIC_LABELS)
        if got != metrics:
            raise ValueError(f"Saved result differs from recorded retrieval target for {config}: {got}")
    if len(gate["query_results"]) != 20 or sum(q["is_correct"] for q in gate["query_results"]) != 20:
        raise ValueError("Evidence-gate saved query outcomes do not match report counts")
    if grounded["overall_summary"]["total_sentences_evaluated"] != 70:
        raise ValueError("Unexpected groundedness sentence denominator")
    summary = grounded["overall_summary"]
    if (summary["grounded_sentences"], summary["total_citations_evaluated"],
            summary["valid_provenance_citations"], summary["citation_binding_alignment_rate"],
            summary["gold_document_match_rate"]) != (70, 56, 56, 1.0, 0.5):
        raise ValueError("Groundedness and citation summary differs from the checked report values")

    gate_groups = {
        "answerable": [q for q in gate["query_results"] if q["category"] == "Answerable In-Domain"],
        "out_of_domain": [q for q in gate["query_results"] if q["category"] == "Unsupported Out-of-Domain"],
        "dynamic": [q for q in gate["query_results"] if q["category"] == "Dynamic / Time-Sensitive"],
    }

    data = {
        "source_artifacts": {
            "retrieval": {"path": "research/benchmark/retrieval_ablation_results.json", "dataset": "research/benchmark/domain_queries_30.jsonl", "dataset_sha256": retrieval_hash, "evaluation": "production_gated"},
            "evidence_gate": {"path": "research/benchmark/evidence_gate_results.json", "dataset": "research/benchmark/evidence_gate_queries_20.jsonl", "dataset_sha256": gate_hash},
            "groundedness": {"path": "research/benchmark/groundedness_results.json", "dataset": "research/benchmark/groundedness_queries_20.jsonl", "dataset_sha256": grounded_hash},
        },
        "retrieval_overall": {k: observed[k]["overall"] for k in CONFIGS},
        "retrieval_categories_mrr_at_5": {k: {c: v["mrr_at_5"] for c, v in observed[k]["by_category"].items()} for k in CONFIGS},
        "evidence_gate_selected_set": {
            "answerable_accepted": {"count": sum(q["actual_outcome"] == "accepted" for q in gate_groups["answerable"]), "total": len(gate_groups["answerable"])},
            "out_of_domain_rejected": {"count": sum(q["actual_outcome"] == "rejected" for q in gate_groups["out_of_domain"]), "total": len(gate_groups["out_of_domain"])},
            "dynamic_intercepted": {"count": sum(q["actual_mode"] == "current-info-fallback" for q in gate_groups["dynamic"]), "total": len(gate_groups["dynamic"])},
        },
        "groundedness_operational_checks": {
            "query_count": summary["total_corpus_queries"],
            "sentences_passing_lexical_heuristic": summary["grounded_sentences"],
            "sentences_evaluated": summary["total_sentences_evaluated"],
            "citations_passing_metadata_checks": summary["valid_provenance_citations"],
            "citations_evaluated": summary["total_citations_evaluated"],
            "limited_source_or_page_alignment_rate": summary["citation_binding_alignment_rate"],
            "queries_with_gold_document_overlap": sum(q["matches_gold_document"] for q in grounded["query_evaluations"]),
            "queries_evaluated_for_gold_overlap": summary["total_corpus_queries"],
            "qualification": "Operational heuristics; not relevance, correctness, or semantic entailment measures.",
        },
        "notes": [
            "Retrieval configurations rerank a shared dense top-15 candidate pool.",
            "Evidence-gate outcomes describe the selected 20-query dataset only.",
            "Groundedness is a lexical heuristic; citation checks are metadata and limited alignment checks, not semantic entailment.",
        ],
    }
    (OUT / "figure_data.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    retrieval_figure(retrieval)
    category_figure(retrieval)
    gate_figure(gate)
    print("Validated three dataset hashes and generated three vector PDF figures.")
    for p in sorted(OUT.glob("fig*.pdf")):
        print(f"{p.name}: {p.stat().st_size} bytes")


if __name__ == "__main__":
    main()
