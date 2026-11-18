"""Bind a prepared pilot to three saved runs and regenerate the offline analysis.

This command reads text-free artifacts only. It does not run a model, access raw
source prompts, or independently attest the recorded native precision evidence.
"""

import argparse
import json
import os
from pathlib import Path
import sys

from . import input_data, pilot_inference, report


def require(condition, message):
    if not condition:
        raise ValueError(message)


def reference(path, base, expected_sha256=None):
    path = Path(path).resolve()
    return {"path": Path(os.path.relpath(path, Path(base).resolve())).as_posix(),
            "sha256": expected_sha256 if expected_sha256 is not None else pilot_inference.file_hash(path)}


def bind_run(run, pilot, pilot_sha256, precision):
    expected = {"precision": precision, "data_role": pilot["data_role"],
                "population_id": pilot["population_id"], "threshold": pilot["threshold"],
                "threshold_source": pilot["threshold_source"],
                "model_revision": pilot["model_revision"], "tokenizer_revision": pilot["tokenizer_revision"],
                "dataset_revision": pilot["dataset_revision"], "preprocessing_id": pilot["preprocessing_id"],
                "planned_input_schedule_id": pilot["input_schedule_id"], "pilot_manifest_sha256": pilot_sha256,
                "expected_rows": pilot_inference.SIZE, "observed_rows": pilot_inference.SIZE}
    require(all(run.get(key) == value for key, value in expected.items()),
            "Saved run does not match the prepared pilot contract")
    token_hash = run.get("token_schedule_sha256")
    require(input_data.valid_sha(token_hash), "Saved run lacks a valid executed-token schedule hash")
    expected_schedule = "sha256:" + pilot_inference.digest(pilot_inference.canonical(
        {"planned_schedule": pilot["input_schedule_id"], "token_schedule_sha256": token_hash}))
    require(run.get("input_schedule_id") == expected_schedule, "Saved run's executed schedule identity is inconsistent")
    require(isinstance(run.get("predictions"), dict) and run["predictions"].get("path") == "predictions.jsonl",
            "Saved pilot run must reference its fixed local predictions filename")


def compare_pilot(pilot_path, pilot_sha256, runs_directory, output):
    output = Path(output)
    require(not output.exists(), "Output directory already exists; preserve earlier reports")
    pilot, _ = pilot_inference.load_pilot(pilot_path, pilot_sha256)
    output.mkdir(parents=True, exist_ok=False)
    assembly = {"status": "incomplete", "stage": "bind_runs", "pilot_manifest_sha256": pilot_sha256,
                "data_role": pilot["data_role"], "model_inference_performed": False}
    pilot_inference.write_json(output / "assembly.json", assembly)
    try:
        runs = []
        for precision in pilot_inference.PRECISIONS:
            directory = Path(runs_directory) / precision
            path = input_data.fixed_path(directory, "run.json")
            raw = path.read_bytes()
            run = input_data.parsed(raw)
            bind_run(run, pilot, pilot_sha256, precision)
            # Reject symlink redirection; the evaluator checks the declared prediction hash and coverage.
            input_data.fixed_path(directory, "predictions.jsonl")
            runs.append(reference(path, output, pilot_inference.digest(raw)))
        examples = input_data.fixed_path(Path(pilot_path).parent, "examples.jsonl")
        examples_ref = reference(examples, output)
        require(examples_ref["sha256"] == pilot["examples"]["sha256"], "Prepared examples changed during assembly")
        comparison = {"schema_version": 1, "data_role": pilot["data_role"],
                      "population_id": pilot["population_id"], "threshold": pilot["threshold"],
                      "threshold_source": pilot["threshold_source"], "examples": examples_ref, "runs": runs}
        pilot_inference.write_json(output / "comparison.json", comparison)
        assembly["stage"] = "analyze"
        pilot_inference.write_json(output / "assembly.json", assembly)
        # Existing validation rejects incomplete runs, incompatible configurations, altered predictions,
        # invalid scores/labels and missing/extra IDs before any analysis directory is created.
        result = report.analyze(output / "comparison.json")
        assembly["stage"] = "write_report"
        pilot_inference.write_json(output / "assembly.json", assembly)
        report.write_report(result, output / "analysis")
        assembly.update({"status": "complete", "stage": "complete",
                         "comparison_sha256": pilot_inference.file_hash(output / "comparison.json"),
                         "analysis_results_sha256": pilot_inference.file_hash(output / "analysis/results.json"),
                         "rows_per_treatment": {precision: result["quality"][precision]["n"]
                                                for precision in pilot_inference.PRECISIONS},
                         "scope": "Offline descriptive development comparison; native evidence needs its recorded review"})
        pilot_inference.write_json(output / "assembly.json", assembly)
        return assembly
    except Exception as error:
        assembly.update({"status": "incomplete", "error_type": type(error).__name__, "error_details_suppressed": True})
        pilot_inference.write_json(output / "assembly.json", assembly)
        raise ValueError("Pilot comparison incomplete; preserve the output and inspect its assembly stage") from None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("pilot", "runs", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--pilot-sha256", required=True)
    args = parser.parse_args()
    try:
        result = compare_pilot(args.pilot, args.pilot_sha256, args.runs, args.output)
    except (OSError, ValueError):
        print("Pilot comparison did not complete; use a new output directory and preserve failed artifacts.", file=sys.stderr)
        return 2
    print(json.dumps({"status": result["status"], "rows_per_treatment": result["rows_per_treatment"],
                      "model_inference_performed": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
