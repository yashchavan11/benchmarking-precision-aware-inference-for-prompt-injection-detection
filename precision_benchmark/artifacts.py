"""Read complete, compatible development runs before calculating any metrics."""

import hashlib
import json
from pathlib import Path

from .evaluation import binary, probability

PRECISIONS = ("fp32", "fp16", "int8")
COMMON_FIELDS = ("model_revision", "tokenizer_revision", "dataset_revision",
                 "preprocessing_id", "input_schedule_id", "environment_id", "score_semantics", "code_revision")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text(value, name):
    require(isinstance(value, str) and bool(value.strip()), f"{name} must be a nonempty string")
    return value


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def parse_json(value):
    return json.loads(value, object_pairs_hook=unique_object)


def read_json(path):
    value = parse_json(Path(path).read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"{path}: expected a JSON object")
    return value


def read_rows(path):
    rows = {}
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        require(bool(line.strip()), f"{path}:{line_number}: blank row")
        row = parse_json(line)
        require(isinstance(row, dict), f"{path}:{line_number}: expected a JSON object")
        example_id = text(row.get("example_id"), "example_id")
        require(example_id not in rows, f"{path}: duplicate example_id {example_id}")
        rows[example_id] = row
    require(bool(rows), f"{path}: empty prediction or example file")
    return rows


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def checked_file(base, entry, provenance):
    require(isinstance(entry, dict), "file reference must contain path and sha256")
    relative = text(entry.get("path"), "file path")
    path = base / relative
    expected = text(entry.get("sha256"), "file sha256")
    actual = sha256(path)
    require(actual == expected, f"{relative}: SHA-256 mismatch")
    provenance[str(path)] = actual
    return path


def load_comparison(path):
    path = Path(path)
    manifest = read_json(path)
    require(type(manifest.get("schema_version")) is int and manifest["schema_version"] == 1,
            "schema_version must be 1")
    role = manifest.get("data_role")
    # shortcut: development only; enable held-out analysis after the P1-C freeze and uncertainty checks.
    require(role in ("synthetic", "eligible_training", "eligible_validation"),
            "only synthetic or eligible development data is supported; held-out evaluation is not enabled")
    text(manifest.get("population_id"), "population_id")
    threshold = probability(manifest.get("threshold"), "threshold")
    text(manifest.get("threshold_source"), "threshold_source")
    provenance = {"manifest": sha256(path)}
    examples = read_rows(checked_file(path.parent, manifest.get("examples"), provenance))
    for row in examples.values():
        binary(row.get("label"))
        lengths = ("original_tokens", "effective_tokens", "truncated")
        if any(key in row for key in lengths):
            original, effective = row.get("original_tokens"), row.get("effective_tokens")
            require(type(original) is int and type(effective) is int and 0 <= effective <= original,
                    "token lengths must be integers with 0 <= effective <= original")
            require(type(row.get("truncated")) is bool and row["truncated"] == (effective < original),
                    "truncated must agree with token lengths")
    require(len({"truncated" in row for row in examples.values()}) == 1,
            "supply token lengths for every example or omit them for every example")
    run_entries = manifest.get("runs")
    require(isinstance(run_entries, list) and len(run_entries) == 3,
            "provide exactly three runs: fp32, fp16, int8")
    runs, predictions, run_ids = {}, {}, set()
    for entry in run_entries:
        run_path = checked_file(path.parent, entry, provenance)
        run = read_json(run_path)
        precision = run.get("precision")
        require(isinstance(precision, str) and precision in PRECISIONS and precision not in runs,
                "each precision must occur exactly once: fp32, fp16, int8")
        run_id = text(run.get("run_id"), "run_id")
        require(run_id not in run_ids, "run IDs must be unique")
        run_ids.add(run_id)
        require(run.get("status") == "complete", f"{run_id}: run is not complete")
        require(run.get("data_role") == role and run.get("population_id") == manifest["population_id"],
                f"{run_id}: incompatible population or data role")
        require(probability(run.get("threshold"), "run threshold") == threshold,
                f"{run_id}: threshold differs from comparison")
        require(run.get("threshold_source") == manifest["threshold_source"],
                f"{run_id}: threshold source differs")
        for field in (*COMMON_FIELDS, "precision_evidence"):
            text(run.get(field), field)
        require(run["score_semantics"] == "p_injection", "scores must describe injection, not top-label confidence")
        rows = read_rows(checked_file(run_path.parent, run.get("predictions"), provenance))
        require(set(rows) == set(examples), f"{run_id}: prediction IDs differ from expected coverage")
        scores = {}
        for example_id, row in rows.items():
            require(row.get("run_id") == run_id, f"{run_id}: prediction row has a different run_id")
            score = probability(row.get("score"))
            require(binary(row.get("prediction"), "prediction") == int(score >= threshold),
                    f"{run_id}: prediction does not match score >= threshold")
            if "label" in row:
                require(binary(row["label"]) == examples[example_id]["label"],
                        f"{run_id}: reference-label mismatch")
            scores[example_id] = score
        runs[precision], predictions[precision] = run, scores
    for precision in PRECISIONS[1:]:
        for field in COMMON_FIELDS:
            require(runs[precision][field] == runs["fp32"][field],
                    f"{precision}: incompatible {field}")
    return manifest, examples, runs, predictions, provenance
