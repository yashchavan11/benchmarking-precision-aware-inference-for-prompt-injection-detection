"""Offline comparison assembly checks using invented pilot scores only."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from precision_benchmark import pilot_compare as target
from precision_benchmark import pilot_inference
from tests.test_pilot_inference import fixture


def prepared_runs(root):
    pilot_dir = root / "pilot"
    pilot_dir.mkdir()
    pilot_path, pilot, examples, _ = fixture(pilot_dir)
    pilot_sha = pilot_inference.file_hash(pilot_path)
    token_hash = "a" * 64
    schedule = "sha256:" + pilot_inference.digest(pilot_inference.canonical(
        {"planned_schedule": pilot["input_schedule_id"], "token_schedule_sha256": token_hash}))
    for precision in pilot_inference.PRECISIONS:
        directory = root / "runs" / precision
        directory.mkdir(parents=True)
        run_id = "synthetic-" + precision
        rows = [{"example_id": row["example_id"], "run_id": run_id, "score": 0.5, "prediction": 1} for row in examples]
        prediction = directory / "predictions.jsonl"
        prediction.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
        run = {key: pilot[key] for key in ("data_role", "population_id", "threshold", "threshold_source",
                                           "model_revision", "tokenizer_revision", "dataset_revision", "preprocessing_id")}
        run.update({"run_id": run_id, "precision": precision, "status": "complete",
                    "planned_input_schedule_id": pilot["input_schedule_id"], "input_schedule_id": schedule,
                    "pilot_manifest_sha256": pilot_sha, "token_schedule_sha256": token_hash,
                    "environment_id": "synthetic-environment", "code_revision": "synthetic-no-inference",
                    "score_semantics": "p_injection", "precision_evidence": "synthetic-no-treatment",
                    "expected_rows": 128, "observed_rows": 128,
                    "predictions": {"path": "predictions.jsonl", "sha256": pilot_inference.file_hash(prediction)}})
        pilot_inference.write_json(directory / "run.json", run)
    return pilot_path, pilot_sha


class PilotComparisonTests(unittest.TestCase):
    def test_complete_comparison_has_relative_hashed_inputs_and_expected_analysis(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path, sha = prepared_runs(root)
            output = root / "assembled"
            result = target.compare_pilot(path, sha, root / "runs", output)
            self.assertEqual(result["status"], "complete")
            self.assertEqual(result["rows_per_treatment"], {"fp32": 128, "fp16": 128, "int8": 128})
            comparison = json.loads((output / "comparison.json").read_text())
            for entry in [comparison["examples"], *comparison["runs"]]:
                self.assertFalse(Path(entry["path"]).is_absolute())
                self.assertEqual(entry["sha256"], pilot_inference.file_hash(output / entry["path"]))
            analyzed = json.loads((output / "analysis/results.json").read_text())
            self.assertEqual(analyzed["quality"]["fp32"]["accuracy"], 0.5)
            self.assertEqual(analyzed["paired_vs_fp32"]["int8"]["disagreements"], 0)
            before = (output / "comparison.json").read_bytes()
            with self.assertRaises(ValueError):
                target.compare_pilot(path, sha, root / "runs", output)
            self.assertEqual(before, (output / "comparison.json").read_bytes())

    def test_existing_analyzer_rejects_incomplete_incompatible_and_altered_predictions(self):
        for defect in ("incomplete", "environment", "prediction_hash", "coverage"):
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                path, sha = prepared_runs(root)
                run_path = root / "runs/int8/run.json"
                run = json.loads(run_path.read_text())
                if defect == "incomplete":
                    run["status"] = "incomplete"
                elif defect == "environment":
                    run["environment_id"] = "incompatible-allocation"
                else:
                    predictions = root / "runs/int8/predictions.jsonl"
                    predictions.write_text("\n".join(predictions.read_text().splitlines()[:-1]) + "\n")
                    if defect == "coverage":
                        run["predictions"]["sha256"] = pilot_inference.file_hash(predictions)
                pilot_inference.write_json(run_path, run)
                output = root / "failed"
                with self.assertRaises(ValueError):
                    target.compare_pilot(path, sha, root / "runs", output)
                self.assertTrue((output / "comparison.json").exists())
                self.assertFalse((output / "analysis").exists())
                self.assertEqual(json.loads((output / "assembly.json").read_text())["status"], "incomplete")

    def test_all_runs_agreeing_on_wrong_pilot_metadata_still_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path, sha = prepared_runs(root)
            for precision in pilot_inference.PRECISIONS:
                run_path = root / "runs" / precision / "run.json"
                run = json.loads(run_path.read_text())
                run["model_revision"] = "wrong-common-model"
                pilot_inference.write_json(run_path, run)
            output = root / "failed"
            with self.assertRaises(ValueError):
                target.compare_pilot(path, sha, root / "runs", output)
            self.assertEqual(json.loads((output / "assembly.json").read_text())["stage"], "bind_runs")
            self.assertFalse((output / "analysis").exists())

    def test_cli_and_pilot_hash_guard_require_no_native_runtime(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path, sha = prepared_runs(root)
            with self.assertRaises(ValueError):
                target.compare_pilot(path, "0" * 64, root / "runs", root / "bad-hash")
            self.assertFalse((root / "bad-hash").exists())
            process = subprocess.run([sys.executable, "-m", "precision_benchmark.pilot_compare", "--pilot", str(path),
                                      "--pilot-sha256", sha, "--runs", str(root / "runs"), "--output", str(root / "cli")],
                                     capture_output=True, text=True)
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertFalse(json.loads(process.stdout)["model_inference_performed"])


if __name__ == "__main__":
    unittest.main()
