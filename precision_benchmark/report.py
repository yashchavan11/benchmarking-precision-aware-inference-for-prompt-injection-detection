"""Reproducible descriptive reports from validated, saved prediction files."""

import csv
import json
import platform
from pathlib import Path

from .artifacts import PRECISIONS, load_comparison, sha256
from .evaluation import compare, metrics

QUALITY_FIELDS = ("precision", "n", "benign_support", "injection_support", "tn", "fp", "fn", "tp",
                  "accuracy", "macro_f1", "injection_precision", "injection_recall", "injection_f1",
                  "benign_precision", "benign_recall", "benign_f1", "fpr", "fnr", "roc_auc",
                  "brier", "ece_10_equal_width")
PAIR_FIELDS = ("precision", "n", "both_correct", "introduced_errors", "corrected_errors", "both_wrong",
               "disagreements", "disagreement_rate", "accuracy_delta_pp", "mean_score_delta",
               "mean_absolute_score_delta", "max_absolute_score_delta")
ERROR_FIELDS = ("precision", "example_id", "label", "outcome", "fp32_score", "candidate_score",
                "fp32_prediction", "candidate_prediction", "score_delta", "fp32_threshold_distance",
                "candidate_threshold_distance", "original_tokens", "effective_tokens", "truncated")


def analyze(path):
    manifest, examples, runs, predictions, provenance = load_comparison(path)
    ids = sorted(examples)
    threshold = manifest["threshold"]
    quality, paired, errors, subgroups = {}, {}, [], {}
    for precision in PRECISIONS:
        scores = predictions[precision]
        quality[precision] = metrics([examples[i]["label"] for i in ids], [scores[i] for i in ids], threshold)
        if all("truncated" in examples[i] for i in ids):
            subgroups[precision] = {}
            for truncated in (False, True):
                subset = [i for i in ids if examples[i]["truncated"] == truncated]
                subgroups[precision]["truncated" if truncated else "untruncated"] = (
                    metrics([examples[i]["label"] for i in subset], [scores[i] for i in subset], threshold)
                    if subset else {"n": 0})
        if precision != "fp32":
            paired[precision], rows = compare(examples, predictions["fp32"], scores, threshold)
            errors.extend({"precision": precision, **row} for row in rows)
    return {"schema_version": 1, "data_role": manifest["data_role"],
            "population_id": manifest["population_id"], "threshold": threshold,
            "threshold_source": manifest["threshold_source"], "runs": runs,
            "source_sha256": provenance,
            "analysis_sha256": {p.name: sha256(p) for p in sorted(Path(__file__).parent.glob("*.py"))},
            "python_version": platform.python_version(), "quality": quality,
            "paired_vs_fp32": paired, "errors": errors, "truncation_subgroups": subgroups,
            "limitations": ["Descriptive development analysis; no confidence intervals or significance claims.",
                            "Runtime and memory are unmeasured by this offline evaluator.",
                            "Metadata consistency does not independently verify assets, labels, eligibility, or effective precision.",
                            "Undefined metrics are null (JSON), empty (CSV), or N/A (Markdown)."]}


def display(value):
    if value is None:
        return "N/A"
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def markdown_table(fields, rows):
    return "\n".join(["| " + " | ".join(fields) + " |",
                      "| " + " | ".join("---" for _ in fields) + " |"] +
                     ["| " + " | ".join(display(row.get(key)) for key in fields) + " |" for row in rows])


def render_report(result):
    synthetic = result["data_role"] == "synthetic"
    lines = ["# Precision comparison: " + ("SYNTHETIC DEMONSTRATION" if synthetic else "PRELIMINARY DEVELOPMENT"),
             "", "These values are invented test fixtures, not model results." if synthetic else
             "These are development observations, not held-out benchmark results.", "",
             f"Population: {display(result['population_id'])}; role: {display(result['data_role'])}.",
             f"Shared threshold: {result['threshold']}; positive when score >= threshold.",
             f"Threshold source: {display(result['threshold_source'])}.", "",
             "## Detection quality", "", "All rates are fractions in [0, 1]. Injection is the positive class.", "",
             markdown_table(("precision", "n", "accuracy", "macro_f1", "injection_precision",
                             "injection_recall", "fpr", "fnr", "roc_auc"),
                            [{"precision": p, **result["quality"][p]} for p in PRECISIONS]), "",
             "Full class support, confusion counts, class-specific metrics and calibration summaries are in quality.csv and results.json.",
             "", "## Paired changes versus FP32", "",
             "Corrected means FP32 was wrong and the candidate is right; introduced means the reverse.",
             "Accuracy delta is candidate minus FP32 in percentage points. FP32 is not ground truth.", "",
             markdown_table(("precision", "both_correct", "introduced_errors", "corrected_errors",
                             "both_wrong", "disagreement_rate", "accuracy_delta_pp"),
                            [{"precision": p, **row} for p, row in result["paired_vs_fp32"].items()]), "",
             "error_analysis.csv contains every example wrong in either member of each pair, including shared errors.",
             "It includes score shifts, threshold distances and token lengths when supplied; it contains no prompt text.",
             "", "## Resource measurements", "", "Not available. Offline score analysis does not measure latency, throughput, memory or model size.",
             "Integrate the profiler's matched measurements after its timing and memory boundaries are reviewed.",
             "", "## Provenance", "",
             markdown_table(("precision", "run_id", "code_revision", "environment_id"),
                            [{"precision": p, **result["runs"][p]} for p in PRECISIONS]), "",
             "results.json records complete run metadata and SHA-256 hashes of inputs and analysis source.",
             "", "## Limitations", ""]
    lines.extend("- " + limitation for limitation in result["limitations"])
    return "\n".join(lines) + "\n"


def write_csv(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            # Spreadsheet readers must not execute externally supplied IDs as formulas.
            safe = {k: "'" + v if isinstance(v, str) and v.lstrip().startswith(("=", "+", "-", "@")) else v
                    for k, v in row.items()}
            writer.writerow(safe)


def write_report(result, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    (output / "results.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    write_csv(output / "quality.csv", QUALITY_FIELDS,
              [{"precision": p, **row} for p, row in result["quality"].items()])
    write_csv(output / "paired.csv", PAIR_FIELDS,
              [{"precision": p, **row} for p, row in result["paired_vs_fp32"].items()])
    write_csv(output / "error_analysis.csv", ERROR_FIELDS, result["errors"])
    # Write the readable report last so an interrupted export is not presented as complete.
    (output / "report.md").write_text(render_report(result), encoding="utf-8")
    return output / "report.md"
